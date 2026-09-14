from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Path, status
from sqlmodel import Session

from src.config.database import get_session
from src.crud import (
    create_paste,
    delete_expired,
    delete_paste,
    get_paste,
    get_validate_paste,
    update_paste,
)
from src.schemas.paste import PasteCreate, PasteRead, PasteUpdate

SessionDep = Annotated[Session, Depends(get_session)]


def content_type_validation(
    content_type: Annotated[str, Header()] = "application/json",
):
    if content_type.lower() != "application/json":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "application/json is the only supported value for the Content-Type"
            },
        )


def accept_validation(accept: Annotated[str | None, Header()] = None):
    if accept is not None and accept.lower() not in ("*/*", "application/json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "application/json is only supported value for the Accept"},
        )


app = FastAPI()


@app.get("/health", status_code=status.HTTP_200_OK)
def root():
    return {"Status": "Healthy"}


@app.post(
    "/paste",
    response_model=PasteRead,
    dependencies=[Depends(content_type_validation), Depends(accept_validation)],
    status_code=status.HTTP_201_CREATED,
)
def write_pin(paste_in: PasteCreate, session: SessionDep):
    return create_paste(session, paste_in)


@app.get(
    "/paste/{paste_id}",
    response_model=list[PasteRead],
    dependencies=[Depends(accept_validation)],
    status_code=status.HTTP_200_OK,
)
def read_pin(paste_id: Annotated[int, Path(ge=0)], session: SessionDep):
    return get_paste(session, paste_id)


@app.get(
    "/paste",
    response_model=list[PasteRead],
    dependencies=[Depends(accept_validation)],
    status_code=status.HTTP_200_OK,
)
def read_pin_filtred(
    session: SessionDep,
    paste_id: int | None = None,
    user: str | None = None,
    tag: str | None = None,
):

    return get_paste(session, paste_id, user, tag)


@app.put(
    "/paste/{paste_id}",
    response_model=PasteRead,
    dependencies=[Depends(content_type_validation), Depends(accept_validation)],
    status_code=status.HTTP_202_ACCEPTED,
)
def update_bin(paste_id: int, paste_in: PasteUpdate, session: SessionDep):
    paste_db = get_validate_paste(session, paste_id)
    return update_paste(session, paste_db, paste_in)


@app.delete("/paste/{paste_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bin(paste_id: int, session: SessionDep):
    paste_db = get_validate_paste(session, paste_id)
    delete_paste(session, paste_db)


@app.delete("/pastes/expired", status_code=status.HTTP_204_NO_CONTENT)
def delete_expired_bin(session: SessionDep):
    delete_expired(session)
