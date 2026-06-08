from sqlmodel import SQLModel, Relationship, Field
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .paste import Paste

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(primary_key=True)
    name: str = Field(index=True)
    email: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

    pastes: list["Paste"] = Relationship(back_populates="user")