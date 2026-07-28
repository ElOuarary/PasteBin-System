from sqlmodel import Field, SQLModel


class PasteTagLink(SQLModel, table=True):
    __tablename__ = "PasteTag"

    paste_id: int = Field(foreign_key="pastes.id", primary_key=True)
    tag_id: int = Field(foreign_key="tags.id", primary_key=True)
