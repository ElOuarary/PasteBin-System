from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, UTC

from .link import PasteTagLink
from .user import User

if TYPE_CHECKING:
    from .tag import Tag
    from .user import User

class Paste(SQLModel, table=True):
    __tablename__ = "pastes"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="users.id")
    content: str = Field(nullable=False, min_length=1, max_length=10_000_000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC.utc), index=True)
    expires_at: Optional[datetime] = Field(default=None, index=True)
    view_count: int = Field(default=0)
    is_private: Optional[bool] = Field(default=False)

    linked_user: User = Relationship(back_populates="linked_pastes")
    linked_tags: list["Tag"] = Relationship(back_populates="linked_pastes", link_model=PasteTagLink)