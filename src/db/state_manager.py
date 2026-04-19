from models.tasks import Task       
from models.events import Event
from db.redis_client import RedisClient
from db.yaml_store import YamlStore
import uuid
from models.state import SystemState
from models.lock import FileLock
from models.agents import Agent
import time

class StateManager:
    """Redis(現在)とYAML(過去の記録)の両方を統括し、朝廷の真実を守る大納言"""
    def __init__(self):
        self.redis = RedisClient()
        self.yaml = YamlStore()

    def update_task(self, task: Task, event_type: str = "TASK_UPDATED") -> None:
        """
        政務の状態を更新し、RedisとYAMLの両方に記す。
        同時にイベントを発行する。
        """
        # 1. Redisへの書き込み（現在の状態）
        self.redis.save_task(task)
        
        # 2. YAMLへの書き込み（永続履歴）
        self.yaml.save_history(entity_type="task", entity_id=task.id, data=task.model_dump())
        
        # 3. イベントの発行（朝廷への布告）
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            task_id=task.id,
            agent_id=task.agent_id,
            details={"status": task.status.value}
        )
        self.redis.add_event(event)
        self.yaml.save_history(entity_type="event", entity_id="stream_log", data=event.model_dump())
        
        # 平安貴族風のログ出力（世界観の維持）
        print(f"【詔勅更新】政務 '{task.id}' が '{task.status.value}' の状態となり申した。")

    def update_agent(self, agent: Agent, event_type: str = "AGENT_UPDATED") -> None:
        """官職の状態を更新"""
        self.redis.save_agent(agent)
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
        print(f"【施錠】{lock.locked_by} が '{lock.target_path}' の専有を開始いたしました。")
        return True