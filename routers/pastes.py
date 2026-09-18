from fastapi import APIRouter, Query, Depends, status

from src.config.database import SessionDep
from services.pastes import search_pastes, delete_expired
from src.schemas.paste import PasteRead
from dependencies import accept_validation

router = APIRouter(prefix="/pastes", tags=["pastes"])

@router.get(
    "",
    response_model=list[PasteRead],
    dependencies=[Depends(accept_validation)],
    status_code=status.HTTP_200_OK,
)
def search_bin(
    session: SessionDep,
    search: str,
    limit: int | None = Query(default=1000, ge=0, le=1000),
    offset: int | None = Query(default=0, ge=0),
):
    return search_pastes(session, search, limit, offset)

@router.delete("/expired", status_code=status.HTTP_204_NO_CONTENT)
def delete_expired_bin(session: SessionDep):
    delete_expired(session)