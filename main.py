from fastapi import Depends, FastAPI, Body, Header, HTTPException, status
from sqlmodel import Field, Session, SQLModel, create_engine, select

from datetime import datetime
from typing import Annotated
import uuid

MAX_CHARACTER_ALLOWED = 10_000_000

class User(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    name: str = Field(index=True)
    email: str = Field()
    created_at: str = Field()
    
class Paste(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    content: str = Field(max_length=MAX_CHARACTER_ALLOWED)
    created_at: str = Field(default=datetime.now())
    expires_at: str = Field()
    view_count: int | None = Field(default=0)
    is_private: bool | None = Field(default=False)
    
class Tag(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    tag: str = Field()
    
class Paste_Tag(SQLModel, table=True):
    paste_id: int  = Field()
    tag: int = Field(index=True)

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

memory = {}

@app.get("/health", status_code=status.HTTP_200_OK)
def root():
    return {"Status": "Healthy"}

@app.post("/pastebin", status_code=status.HTTP_201_CREATED)
def write_pin(
    paste: Paste,
    session: SessionDep,
    accept: Annotated[str | None, Header()] = None
    ):
    
    if accept is not None and accept.lower() != "application/json":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail={"error": "application/json is only the supproted Accept"})
    
    session.add(paste)
    session.commit()
    session.refresh(paste)
    
    return {"paste_id": paste.id}

@app.get("/pastebin/{paste_id}", status_code=status.HTTP_200_OK)
def read_pin(
    paste_id: int,
    session: SessionDep,
    accept: Annotated[str | None, Header()] = None
    ):
    if accept is not None and accept.lower() != "application/json":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error" : "application/json is only the supproted Accept"})
    
    paste = session.get(Paste, paste_id)
    if not paste:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"})
    
    return paste

@app.put("/pastebin/{paste_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_bin(
    paste_id: int,
    paste: Paste,
    session: SessionDep,
    accept: Annotated[str | None, Header()] = None
    ):
    if accept is not None and accept.lower() != "application/json":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail={"error": "application/json is only the supproted accept"})
    old_paste = session.get(Paste, paste_id)
    if not old_paste:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"})
    
    return

@app.delete("/pastebin/{paste_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bin(paste_id: str, session: SessionDep):
    paste = session.get(Paste, paste_id)
    if not paste:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"})
    session.delete(paste)
    session.commit()
    return