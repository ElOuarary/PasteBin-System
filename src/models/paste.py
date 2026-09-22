import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Column, DateTime, Field, Index, Relationship, SQLModel

from .link import PasteTagLink
from .user import User

if TYPE_CHECKING:
    from .tag import Tag


class Paste(SQLModel, table=True):
    __tablename__ = "pastes"

    id: int = Field(primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="users.id")
    content: str = Field(nullable=False, min_length=1, max_length=10_000_000)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), index=True),
    )
    expires_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), index=True)
    )
    view_count: int = Field(default=0)
    is_private: bool = Field(default=False)

    linked_user: User = Relationship(back_populates="linked_pastes")
    linked_tags: list["Tag"] = Relationship(
        back_populates="linked_pastes", link_model=PasteTagLink
    )

    __table_args__ = (
        Index(
            "content_idx",
            "content",
            postgresql_ops={"content": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
    )
