from pydantic import BaseModel, Field

class SystemState(BaseModel):
    """朝廷（システム全体）の状況"""
    active_agents: int = Field(default=0, description="稼働中の官職数")
    tasks_doing: int = Field(default=0, description="実行中の政務数")
    tasks_completed: int = Field(default=0, description="完了した政務数")
    last_updated: float = Field(..., description="最終更新時刻")