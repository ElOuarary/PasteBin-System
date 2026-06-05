from sqlmodel import SQLModel, Field

from datetime import datetime, timezone
from typing import Optional

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(primary_key=True)
    name: str = Field(index=True)
    email: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)