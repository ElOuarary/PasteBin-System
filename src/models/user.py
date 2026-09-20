import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Column, DateTime, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .paste import Paste


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int = Field(primary_key=True)
    username: str = Field(index=True)
    email: str
    hashed_password: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), index=True),
    )

    linked_pastes: list["Paste"] = Relationship(
        back_populates="linked_user", cascade_delete=True
    )
