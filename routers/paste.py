from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from services.pastes import (
    create_paste,
    delete_paste,
    get_paste,
    get_validate_paste,
    update_paste,
)
from src.schemas.paste import PasteCreate, PasteRead, PasteUpdate
from dependencies import content_type_validation, accept_validation
from src.config.database import SessionDep

router = APIRouter(prefix="/paste", tags=["paste"])

@router.post(
    "",
    response_model=PasteRead,
    dependencies=[Depends(content_type_validation), Depends(accept_validation)],
    status_code=status.HTTP_201_CREATED,
)
def write_pin(paste_in: PasteCreate, session: SessionDep):
    return create_paste(session, paste_in)

@router.get(
    "/{paste_id}",
    response_model=list[PasteRead],
    dependencies=[Depends(accept_validation)],
    status_code=status.HTTP_200_OK,
)
def read_pin(paste_id: Annotated[int, Path(ge=0)], session: SessionDep):
    return get_paste(session, paste_id)


@router.get(
    "",
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


@router.put(
    "/{paste_id}",
    response_model=PasteRead,
    dependencies=[Depends(content_type_validation), Depends(accept_validation)],
    status_code=status.HTTP_202_ACCEPTED,
)
def update_bin(paste_id: int, paste_in: PasteUpdate, session: SessionDep):
    paste_db = get_validate_paste(session, paste_id)
    return update_paste(session, paste_db, paste_in)


@router.delete("/{paste_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bin(paste_id: int, session: SessionDep):
    paste_db = get_validate_paste(session, paste_id)
    delete_paste(session, paste_db)
