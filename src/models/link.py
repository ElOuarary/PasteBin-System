from sqlmodel import SQLModel, Field
from typing import TYPE_CHECKING

class PasteTagLink(SQLModel, table=True):
    __tablename__ = "PasteTag"
    
    paste_id: int = Field(foreign_key="pastes.id", primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", primary_key=True)