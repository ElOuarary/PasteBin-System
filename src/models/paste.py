from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel, Column, DateTime

from .link import PasteTagLink
from .user import User

if TYPE_CHECKING:
    from .tag import Tag


class Paste(SQLModel, table=True):
    __tablename__ = "pastes"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="users.id")
    content: str = Field(nullable=False, min_length=1, max_length=10_000_000)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)), index=True
    )
    expires_at: datetime | None = Field(default=None, index=True, sa_column=Column(DateTime(timezone=True)))
    view_count: int = Field(default=0)
    is_private: bool | None = Field(default=False)

    linked_user: User = Relationship(back_populates="linked_pastes")
    linked_tags: list["Tag"] = Relationship(
        back_populates="linked_pastes", link_model=PasteTagLink
    )
