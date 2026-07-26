from datetime import datetime, UTC
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Relationship, Field


if TYPE_CHECKING:
    from .paste import Paste

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(primary_key=True)
    name: str = Field(index=True)
    email: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    
    linked_pastes: list["Paste"] = Relationship(back_populates="linked_user")