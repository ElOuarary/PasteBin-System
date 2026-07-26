from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class PasteCreate(SQLModel):
    content: str = Field(min_length=0, max_length=10_000_000)
    expires_at: Optional[datetime] = None
    is_private: Optional[bool] = False
    tags: Optional[list[str]] = None
  
class PasteRead(SQLModel):
    id: int
    content: str
    user: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    view_count: int
    is_private: bool  
    tags: Optional[list[str]] = None
    
class PasteQuery(SQLModel):
    paste_id: int | None = Field(default=None, ge=0)
    user: str | None = None
    tag: str | None = None
    
class PasteUpdate(SQLModel):
    content: Optional[str] = Field(min_length=1, max_length=10_000_000)
    expires_at: Optional[datetime] = None # Need to add validation of the value of the expires datetime to be greater than the current datetime
    is_private: Optional[bool] = None
    tag: Optional[list[str]] = None