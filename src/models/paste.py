from sqlmodel import SQLModel, Field

from datetime import datetime
from typing import Optional

class Paste(SQLModel, table=True):
    __tabelname__ = "pastes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(nullable=False, max_length=10_000_000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    view_count: int = Field(default=0)
    is_private: bool = Field(default=False)