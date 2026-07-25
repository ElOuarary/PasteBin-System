from sqlmodel import SQLModel, Field
from pydantic import field_validator

from datetime import datetime
from typing import Optional

class PasteCreate(SQLModel):
    content: str
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
    expires_at: Optional[datetime] = None # Need to add validation of the value of the expires datetime to be greater than the current datetime
    is_private: Optional[bool] = None
    tag: Optional[list[str]] = None