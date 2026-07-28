from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from .link import PasteTagLink

if TYPE_CHECKING:
    from .paste import Paste


class Tag(SQLModel, table=True):
    __tablename__ = "tags"

    id: int | None = Field(primary_key=True)
    name: str = Field(unique=True)

    linked_pastes: list["Paste"] = Relationship(
        back_populates="linked_tags", link_model=PasteTagLink
    )
