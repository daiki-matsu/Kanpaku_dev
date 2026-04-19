from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class Event(BaseModel):
    """朝廷内で発生した事象（イベント）のエンティティモデル"""
    event_id: str = Field(..., description="事象の識別子")
    timestamp: datetime = Field(default_factory=datetime.now, description="事象発生時刻")
    event_type: str = Field(..., description="事象の種類 (例: TASK_ASSIGNED, AGENT_ERROR)")
    agent_id: Optional[str] = Field(None, description="関連する官職のID")
    task_id: Optional[str] = Field(None, description="関連する政務のID")
    details: Dict[str, Any] = Field(default_factory=dict, description="詳細な申し送り事項")