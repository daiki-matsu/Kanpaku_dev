import redis
import json
from typing import Optional
from models.tasks import Task
from models.agents import Agent
from models.events import Event
from models.state import SystemState
from models.lock import FileLock

class RedisClient:
    """蔵（Redis）への出し入れを司る司（つかさ）"""
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def save_task(self, task: Task) -> None:
        """政務（タスク）をHashとして保存"""
        self.client.hset(f"tasks:{task.id}", mapping=json.loads(task.model_dump_json()))

    def get_task(self, task_id: str) -> Optional[Task]:
        """政務を読み出す"""
        data = self.client.hgetall(f"tasks:{task_id}")
        return Task(**data) if data else None

    def save_agent(self, agent: Agent) -> None:
        """官職（エージェント）の現況をHashとして保存"""
        self.client.hset(f"agents:{agent.id}", mapping=json.loads(agent.model_dump_json()))

    def add_event(self, event: Event) -> None:
        """事象（イベント）をStreamに追記"""
        # Eventモデルを辞書化。日時は文字列にしてStreamに格納
        event_dict = event.model_dump()
        event_dict['timestamp'] = event_dict['timestamp'].isoformat()
        self.client.xadd("events:stream", event_dict)

    def save_state(self, state: SystemState) -> None:
        """朝廷の全体状況を保存（キーは単一）"""
        self.client.hset("system:state", mapping=json.loads(state.model_dump_json()))

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