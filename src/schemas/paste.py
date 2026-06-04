from sqlmodel import SQLModel

from datetime import datetime
from typing import Optional

class PasteCreate(SQLModel):
    content: str
    expires_at: Optional[datetime] = None
    is_private: Optional[bool] = False
  
class PasteRead(SQLModel):
    id: int
    content: str
    created_at: datetime
    expires_at: datetime
    view_count: int
    is_private: bool  
    
class PasteUpdate(SQLModel):
    expires_at: Optional[datetime] = None
    is_private: Optional[bool] = None