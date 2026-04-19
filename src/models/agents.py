from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class AgentStatus(str, Enum):
    """官職（エージェント）の状態定義"""
    IDLE = "idle"           # 待機中（Sprint 1対象）
    THINKING = "thinking"   # 思案中（Sprint 1対象）
    WORKING = "working"     # 作業中
    ERROR = "error"         # 異常事態
    RETRYING = "retrying"   # 復旧試行中

class Agent(BaseModel):
    """官職（エージェント）のエンティティモデル"""
    id: str = Field(..., description="官職の識別子 (例: tonoben, toneri_1)")
    role: str = Field(..., description="役職名（頭弁、舎人など）")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="現在の活動状態")
    current_task_id: Optional[str] = Field(None, description="現在取り組んでいる政務のID")
    last_heartbeat: Optional[float] = Field(None, description="最終生存確認時刻（UNIXタイムスタンプ）")