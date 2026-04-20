from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import time
import uuid

class Message(BaseModel):
    """官職間で交わされる文（メッセージ）の型定義"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="文の識別子")
    timestamp: float = Field(default_factory=time.time, description="投函時刻")
    sender_id: str = Field(..., description="差出人 (例: tonoben)")
    receiver_id: str = Field(..., description="宛先 (例: toneri_1)")
    message_type: str = Field(..., description="用件 (例: TASK_ASSIGNED, REVIEW_REQUEST)")
    task_id: Optional[str] = Field(None, description="関連する政務ID")
    content: Dict[str, Any] = Field(default_factory=dict, description="詳細な伝言内容")