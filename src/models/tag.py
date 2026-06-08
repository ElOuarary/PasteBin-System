from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING

from .link import PasteTagLink

if TYPE_CHECKING:
    from .paste import Paste

class Tag(SQLModel, table=True):
    __tablename__ = "tags"

    id: Optional[int] = Field(primary_key=True)
    name: str = Field(unique=True)

    linked_pastes: list["Paste"] = Relationship(back_populates="linked_tags", link_model=PasteTagLink)