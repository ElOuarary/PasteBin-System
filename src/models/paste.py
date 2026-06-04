from sqlmodel import SQLModel, Field, Relationship

from .user import User
from .tag import Tag

from datetime import datetime, timezone
from typing import Optional

class Paste(SQLModel, table=True):
    __tablename__ = "pastes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str | None = Field(default=None, foreign_key="users.id")
    content: str = Field(nullable=False, max_length=10_000_000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(default=None)
    view_count: int = Field(default=0)
    is_private: Optional[bool] = Field(default=False)
    tag_id: Optional[int] = Field(default=None, foreign_key="tags.id")