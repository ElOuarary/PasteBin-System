from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from dependencies import accept_validation, content_type_validation
from services.pastes import (
    create_paste,
    delete_paste,
    get_paste,
    get_validate_paste,
    update_paste,
)
from src.auth import CurrentUser
from src.config.database import SessionDep
from src.schemas.paste import PasteCreate, PasteRead, PasteUpdate

router = APIRouter(prefix="/paste", tags=["paste"])


@router.post(
    "",
    response_model=PasteRead,
    dependencies=[Depends(content_type_validation), Depends(accept_validation)],
    status_code=status.HTTP_201_CREATED,
)
def write_pin(paste_in: PasteCreate, session: SessionDep, user: CurrentUser):
    return create_paste(session, paste_in, user)


@router.get(
    "/{paste_id}",
    response_model=list[PasteRead],
    dependencies=[Depends(accept_validation)],
    status_code=status.HTTP_200_OK,
)
def read_pin(
    paste_id: Annotated[int, Path(ge=0)], session: SessionDep, user: CurrentUser
):
    return get_paste(session, paste_id, user)


@router.get(
    "",
    response_model=list[PasteRead],
    dependencies=[Depends(accept_validation)],
    status_code=status.HTTP_200_OK,
)
def read_pin_filtred(
    session: SessionDep,
    user: CurrentUser,
    paste_id: int | None = None,
    username: str | None = None,
    tag: str | None = None,
):
    return get_paste(session, user, paste_id, username, tag)


@router.put(
    "/{paste_id}",
    response_model=PasteRead,
    dependencies=[Depends(content_type_validation), Depends(accept_validation)],
    status_code=status.HTTP_202_ACCEPTED,
)
def update_bin(
    paste_id: int, paste_in: PasteUpdate, session: SessionDep, user: CurrentUser
):
    paste_db = get_validate_paste(session, paste_id, user)
    return update_paste(session, paste_db, paste_in)


@router.delete("/{paste_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bin(paste_id: int, session: SessionDep, user: CurrentUser):
    paste_db = get_validate_paste(session, paste_id, user)
    delete_paste(session, paste_db)
