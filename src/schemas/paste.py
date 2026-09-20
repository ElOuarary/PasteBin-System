from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel


class PasteCreate(SQLModel):
    content: str = Field(min_length=1, max_length=10_000_000)
    expires_at: datetime | None = None
    is_private: bool | None = False
    tags: list[str] | None = None


class PasteRead(SQLModel):
    id: UUID
    content: str
    user: str | None = None
    created_at: datetime
    expires_at: datetime | None = None
    view_count: int
    is_private: bool
    tags: list[str] | None = None


class PasteQuery(SQLModel):
    paste_id: UUID | None = None
    user: str | None = None
    tag: str | None = None


class PasteUpdate(SQLModel):
    content: str | None = Field(default=None, min_length=1, max_length=10_000_000)
    expires_at: datetime | None = (
        None  # Need to add validation of the value of the expires datetime to be greater than the current datetime
    )
    is_private: bool | None = None
    tags: list[str] | None = None
