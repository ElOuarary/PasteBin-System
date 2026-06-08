from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

from .link import PasteTagLink

if TYPE_CHECKING:
    from .tag import Tag
    from .user import User

class Paste(SQLModel, table=True):
    __tablename__ = "pastes"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None)
    content: str = Field(nullable=False, max_length=10_000_000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    expires_at: Optional[datetime] = Field(default=None, index=True)
    view_count: int = Field(default=0)
    is_private: Optional[bool] = Field(default=False)

    linked_tags: list["Tag"] = Relationship(back_populates="linked_pastes", link_model=PasteTagLink)