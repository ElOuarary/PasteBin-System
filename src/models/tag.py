from sqlmodel import SQLModel, Field

from typing import Optional

class Tag(SQLModel, table=True):
    __tablename__ = "tags"
    
    id: Optional[int] = Field(primary_key=True)
    name: str = Field(unique=True)
    
class PasteBinTag(SQLModel, table=True):
    __tablename__ = "PasteBinTags"
    
    paste_id: int = Field(primary_key=True)
    tag_id: int = Field(primary_key=True)
    