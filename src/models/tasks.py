from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List, Dict, Any

class TaskStatus(str, Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    DOING = "doing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"

class SettingInfo(BaseModel):
    bloom_level: Optional[int] = None
    depends_on: List[str] = Field(default_factory=list)
    priority: int = 1
    goal: Optional[str] = None
    command: Optional[str] = None
    type: Optional[str] = None

class AssignedInfo(BaseModel):
    to: Optional[str] = None
    echo_message: Optional[str] = None

class AnswerInfo(BaseModel):
    status: Optional[str] = None
    summary: Optional[str] = None
    details: Optional[str] = None

class ExecutionInfo(BaseModel):
    status: Optional[str] = None
    action: Optional[str] = None
    path: Optional[str] = None
    logs: Optional[str] = None
    last_error: Optional[str] = None

class ReviewInfo(BaseModel):
    status: Optional[str] = None
    score: Optional[int] = None
    feedback: Optional[str] = None

class RetryInfo(BaseModel):
    count: int = 0
    max_limit: int = 5
    reason: List[str] = Field(default_factory=list)

class TimingInfo(BaseModel):
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

class Task(BaseModel):
    """政務（タスク）の完全版エンティティモデル"""
    id: str
    status: TaskStatus = TaskStatus.CREATED
    setting: SettingInfo = Field(default_factory=SettingInfo)
    assigned: AssignedInfo = Field(default_factory=AssignedInfo)
    answer: AnswerInfo = Field(default_factory=AnswerInfo)
    execution: ExecutionInfo = Field(default_factory=ExecutionInfo)
    review: ReviewInfo = Field(default_factory=ReviewInfo)
    retry: RetryInfo = Field(default_factory=RetryInfo)
    timing: TimingInfo = Field(default_factory=TimingInfo)