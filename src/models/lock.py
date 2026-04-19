from pydantic import BaseModel, Field

class FileLock(BaseModel):
    """巻物（ファイル）の排他制御（ロック）"""
    target_path: str = Field(..., description="対象ファイルのパス")
    locked_by: str = Field(..., description="ロックを保持しているエージェントID")
    locked_at: float = Field(..., description="ロック取得時刻")
    expires_at: float = Field(..., description="ロック有効期限（TTL計算用）")