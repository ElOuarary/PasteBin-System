from sqlmodel import SQLModel

from datetime import datetime
from typing import Optional

class PasteCreate(SQLModel):
    content: str
    expires_at: Optional[datetime] = None
    is_private: Optional[bool] = False
    tag: Optional[str] = None
  
class PasteRead(SQLModel):
    id: int
    content: str
    created_at: datetime
    expires_at: Optional[datetime]
    view_count: int
    is_private: bool  
    tag: Optional[str] = None
class PasteUpdate(SQLModel):
    expires_at: Optional[datetime] = None
    is_private: Optional[bool] = None
    tag: Optional[str] = None