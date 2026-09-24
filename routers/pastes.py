from fastapi import APIRouter, Depends, Query, status

from dependencies import accept_validation
from services.pastes import delete_expired, search_pastes
from src.config.database import SessionDep
from src.models import User
from src.schemas.paste import PasteRead
from src.security import role_required

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
    user: User = Depends(role_required(["admin", "user"])),
    limit: int | None = Query(default=1000, ge=0, le=1000),
    offset: int | None = Query(default=0, ge=0),
):
    return search_pastes(session, user, search, limit, offset)


@router.delete("/expired", status_code=status.HTTP_204_NO_CONTENT)
def delete_expired_bin(
    session: SessionDep, user: User = Depends(role_required(["admin"]))
):
    delete_expired(session)
