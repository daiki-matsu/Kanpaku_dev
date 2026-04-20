import redis
import json
from typing import Optional
from models.tasks import Task
from models.agents import Agent
from models.events import Event
from models.state import SystemState
from models.lock import FileLock
from models.message import Message

class RedisClient:
    """蔵（Redis）への出し入れを司る司（つかさ）"""
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def save_task(self, task: Task) -> None:
        """政務（タスク）をHashとして保存"""
        task_data = json.loads(task.model_dump_json())
        # None値を空文字列に変換してRedisエラーを防止
        for key, value in task_data.items():
            if isinstance(value, dict):
                task_data[key] = json.dumps(value)
            elif value is None:
                task_data[key] = "null"  # Use "null" string instead of empty string
        self.client.hset(f"tasks:{task.id}", mapping=task_data)

    def get_task(self, task_id: str) -> Optional[Task]:
        """政務を読み出す"""
        data = self.client.hgetall(f"tasks:{task_id}")
        if not data:
            return None
        
        # Redisから取得したデータを適切な型に変換
        for key, value in data.items():
            if value == "" or value == "null":
                data[key] = None
            elif key.endswith('_at') or key in ['priority', 'count', 'limit', 'max_limit']:
                try:
                    data[key] = int(value) if value and value != "null" else None
                except (ValueError, TypeError):
                    data[key] = None
            elif key in ['setting', 'assigned', 'answer', 'execution', 'review', 'retry', 'timing']:
                # Convert JSON strings back to dicts
                try:
                    data[key] = json.loads(value) if value and value != "null" else {}
                except (ValueError, TypeError):
                    data[key] = {}
        
        return Task(**data)

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """官職（エージェント）情報を読み出す"""
        data = self.client.hgetall(f"agents:{agent_id}")
        if not data:
            return None
        
        # Redisから取得したデータを適切な型に変換
        if 'last_heartbeat' in data and data['last_heartbeat']:
            try:
                data['last_heartbeat'] = float(data['last_heartbeat'])
            except (ValueError, TypeError):
                data['last_heartbeat'] = None
        
        # 空文字列をNoneに戻す
        for key, value in data.items():
            if value == "":
                data[key] = None
        
        return Agent(**data)

    def save_agent(self, agent: Agent) -> None:
        """官職（エージェント）の現況をHashとして保存"""
        agent_data = json.loads(agent.model_dump_json())
        # None値を空文字列に変換してRedisエラーを防止
        for key, value in agent_data.items():
            if value is None:
                agent_data[key] = ""
        
        self.client.hset(f"agents:{agent.id}", mapping=agent_data)

    def add_event(self, event: Event) -> None:
        """事象（イベント）をStreamに追記"""
        # Eventモデルを辞書化。日時は文字列にしてStreamに格納
        event_dict = event.model_dump()
        event_dict['timestamp'] = event_dict['timestamp'].isoformat()
        
        # Convert None values to "null" strings for Redis
        for key, value in event_dict.items():
            if value is None:
                event_dict[key] = "null"
            elif isinstance(value, dict):
                event_dict[key] = json.dumps(value)
        
        self.client.xadd("events:stream", event_dict)

    def save_state(self, state: SystemState) -> None:
        """朝廷の全体状況を保存（キーは単一）"""
        state_data = json.loads(state.model_dump_json())
        # None値を空文字列に変換してRedisエラーを防止
        for key, value in state_data.items():
            if value is None:
                state_data[key] = ""
        self.client.hset("system:state", mapping=state_data)

    def save_lock(self, lock: FileLock) -> None:
        """ファイルのロック状態を保存"""
        # ロックはキーそのものにTTLを設定することも可能ですが、
        # まずはHashとして状態を保存します。
        key = f"lock:{lock.target_path}"
        self.client.hset(key, mapping=json.loads(lock.model_dump_json()))
        
        # Redisの期限切れ機能（TTL）と連動させる場合
        ttl_seconds = int(lock.expires_at - lock.locked_at)
        if ttl_seconds > 0:
            self.client.expire(key, ttl_seconds)

    def delete_lock(self, target_path: str) -> None:
        """ロックの解除"""
        self.client.delete(f"lock:{target_path}")

    # ---------------------------------------------------------
    # 通信網（Inbox & Pub/Sub）関連のメソッド
    # ---------------------------------------------------------
    def push_inbox(self, agent_id: str, message: Message) -> None:
        """
        宛先の文箱（Inbox）へ文を投函する。
        新しいものを左（先頭）から押し込む（LPUSH）
        """
        self.client.lpush(f"inbox:{agent_id}", message.model_dump_json())

    def pop_inbox(self, agent_id: str) -> Optional[Message]:
        """
        文箱（Inbox）から最も古い文を取り出す。
        右（末尾）から取り出すことで、入れられた順（FIFO）に処理する（RPOP）
        """
        data = self.client.rpop(f"inbox:{agent_id}")
        return Message.model_validate_json(data) if data else None

    def publish_notification(self, channel: str, event_type: str) -> None:
        """
        特定の官職（チャンネル）へ向けて狼煙（Pub/Sub）を上げる。
        例: channel="notify:toneri_1", event_type="WAKE_UP"
        """
        self.client.publish(channel, event_type)

    def get_pubsub(self):
        """
        狼煙（Pub/Sub）を見張るための見張り台（PubSubオブジェクト）を用意する。
        ※エージェントの待機ループ内で使用します
        """
        return self.client.pubsub(ignore_subscribe_messages=True)