from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .user import User
    from .tag import Tag

class Paste(SQLModel, table=True):
    __tablename__ = "pastes"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="users.id")
    content: str = Field(nullable=False, max_length=10_000_000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    expires_at: Optional[datetime] = Field(default=None, index=True)
    view_count: int = Field(default=0)
    is_private: Optional[bool] = Field(default=False)

    user: "User" = Relationship(back_populates="pastes")
    tags: list["Tag"] = Relationship(back_populates="pastes")
