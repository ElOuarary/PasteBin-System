from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlmodel import Session

from src.config.database import init_db, get_session
from src.models import Paste
from src.schemas.paste import PasteCreate, PasteRead, PasteUpdate

from src.crud import PasteExpiredException, create_paste, get_paste, update_paste, delete_paste, _is_expired

from typing import Annotated

from contextlib import asynccontextmanager

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health", status_code=status.HTTP_200_OK)
def root():
    return {"Status": "Healthy"}

@app.post("/pastebin", response_model=PasteRead, status_code=status.HTTP_201_CREATED)
def write_pin(
    paste_in: PasteCreate,
    session: SessionDep,
    accept: Annotated[str | None, Header()] = None
    ):    
    if accept is not None and accept.lower() != "application/json":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail={"error": "application/json is only the supproted Accept"})
    return create_paste(session, paste_in)

@app.get("/pastebin/{paste_id}", response_model=PasteRead, status_code=status.HTTP_200_OK)
def read_pin(
    paste_id: int,
    session: SessionDep,
    accept: Annotated[str | None, Header()] = None
    ):
    if accept is not None and accept.lower() != "application/json":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error" : "application/json is only the supproted Accept"})
    try:
        paste = get_paste(session, paste_id)
        if paste is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"})
        return paste
    except PasteExpiredException as e:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail={"error": "content no longer available"})

@app.put("/pastebin/{paste_id}", response_model=PasteRead, status_code=status.HTTP_202_ACCEPTED)
def update_bin(
    paste_id: int,
    paste_in: PasteUpdate,
    session: SessionDep,
    accept: Annotated[str | None, Header()] = None
    ):
    if accept is not None and accept.lower() != "application/json":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail={"error": "application/json is only the supproted accept"})
    paste_db = session.get(Paste, paste_id)
    if paste_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"})
    elif paste_in.expires_at is None and paste_db.expires_at is not None and _is_expired(paste_db.expires_at):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail={"error": "content no longer available"})
    return update_paste(session, paste_db, paste_in)

@app.delete("/pastebin/{paste_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bin(paste_id: str, session: SessionDep):
    paste_db = session.get(Paste, paste_id)
    if paste_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"})
    delete_paste(session, paste_db)