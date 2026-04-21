from models.tasks import Task, TaskStatus
from models.events import Event
from db.redis_client import RedisClient
from db.yaml_store import YamlStore
import uuid
import json
from models.state import SystemState
from models.lock import FileLock
from models.agents import Agent
from models.message import Message
from utility.messages import HeianMessages
import time

class StateManager:
    """Redis(現在)とYAML(過去の記録)の両方を統括し、朝廷の真実を守る大納言"""
    def __init__(self):
        self.redis = RedisClient()
        self.yaml = YamlStore()

    # 朝廷の絶対的な掟（許可される状態遷移の定義）
    # ※やり直し（failed -> assigned 等）を考慮し、後段のSprintも見据えた遷移を定義
    VALID_TRANSITIONS = {
        TaskStatus.CREATED: [TaskStatus.ASSIGNED],
        TaskStatus.ASSIGNED: [TaskStatus.DOING],
        TaskStatus.DOING: [TaskStatus.REVIEWING, TaskStatus.ASSIGNED, TaskStatus.FAILED],
        TaskStatus.REVIEWING: [TaskStatus.COMPLETED, TaskStatus.ASSIGNED],
        TaskStatus.COMPLETED: [],
        TaskStatus.FAILED: []
    }

    def update_task(self, task: Task, event_type: str = "TASK_UPDATED") -> None:
        """
        政務の状態を更新し、RedisとYAMLの両方に記す。
        その際、状態遷移の掟とリトライ上限を厳格に検分する。
        """
        # 1. 蔵から現在の姿（更新前）を取得
        current_task = self.redis.get_task(task.id)

        if current_task:
            # 2. 状態遷移の掟（バリデーション）チェック
            # Skip validation for new task creation (TASK_CREATED event)
            if event_type != "TASK_CREATED" and current_task.status != task.status:
                allowed_next_states = self.VALID_TRANSITIONS.get(current_task.status, [])
                if task.status not in allowed_next_states:
                    error_msg = HeianMessages.STATE_VIOLATION.format(
                        task_id=task.id,
                        old_status=current_task.status.value,
                        new_status=task.status.value
                    )
                    print(error_msg)
                    # 不正な更新は朝廷を揺るがすため、例外を投げて書き込みをブロック
                    raise ValueError(error_msg)

            # 3. やり直し（リトライ）の管理
            # 作業中（doing）からアサイン（assigned）へ戻る、または実行ステータスがerrorになった場合
            if current_task.status == TaskStatus.DOING and (
                task.status == TaskStatus.ASSIGNED or task.execution.status == "error"
            ):
                task.retry.count += 1
                task.retry.reason.append("doing_failed")
                print(HeianMessages.TASK_RETRY.format(
                    task_id=task.id,
                    count=task.retry.count,
                    limit=task.retry.max_limit
                ))

                # リトライ上限超過の検分
                if task.retry.count > task.retry.max_limit:
                    print(HeianMessages.TASK_FAILED.format(task_id=task.id))
                    task.status = TaskStatus.FAILED
                    event_type = "TASK_FAILED"
                    # FAILED時は実行ステータスも強制的に書き換え
                    task.execution.status = "failed"

        # 4. Redisへの書き込み（現在の状態）
        self.redis.save_task(task)
        
        # 5. YAMLへの書き込み（永続履歴）
        self.yaml.save_history(entity_type="task", entity_id=task.id, data=json.loads(task.model_dump_json()))
        
        # 6. イベントの発行（朝廷への布告）
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            task_id=task.id,
            agent_id=task.assigned.to if task.assigned else None,
            details={"status": task.status.value}
        )
        self.redis.add_event(event)
        self.yaml.save_history(entity_type="event", entity_id="stream_log", data=json.loads(event.model_dump_json()))
        
        print(HeianMessages.TASK_UPDATED.format(
            task_id=task.id,
            status=task.status.value
        ))

    def update_agent(self, agent: Agent, event_type: str = "AGENT_UPDATED") -> None:
        """官職の状態を更新"""
        self.redis.save_agent(agent)
        self.yaml.save_history(entity_type="agent", entity_id=agent.id, data=json.loads(agent.model_dump_json()))
        self.yaml.save_history(entity_type="agent", entity_id=agent.id, data=agent.model_dump())
        # イベントの発行も必要に応じて追加

    def update_state(self, state: SystemState) -> None:
        """全体状況（ダッシュボード用）の更新"""
        state.last_updated = time.time()
        self.redis.save_state(state)
        self.yaml.save_history(entity_type="state", entity_id="system_state", data=state.model_dump())

    def update_lock(self, lock: FileLock) -> bool:
        """ロックの取得と記録"""
        # 実際にはRedisのSETNX等でアトミックに取る必要がありますが、整合性記録層としての処理
        self.redis.save_lock(lock)
        self.yaml.save_history(entity_type="lock", entity_id=lock.target_path.replace("/", "_"), data=lock.model_dump())
        print(HeianMessages.LOCK_ACQUIRED.format(
            lock=lock
        ))
        return True

    def send_message(self, message: Message) -> None:
        """
        特定の官職へ文を送り、同時に狼煙を上げて知らせる。
        """
        # 1. Inboxへ投函（データ消失防止）
        self.redis.push_inbox(agent_id=message.receiver_id, message=message)
        
        # 2. 狼煙（Pub/Sub）を上げる（即時起床用）
        # チャンネル名は "notify:{agent_id}" とする
        channel = f"notify:{message.receiver_id}"
        self.redis.publish_notification(channel=channel, event_type=message.message_type)
        
        print(HeianMessages.MESSAGE_SENT.format(
            sender_id=message.sender_id,
            receiver_id=message.receiver_id,
            msg_type=message.message_type
        ))