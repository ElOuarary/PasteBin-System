from fastapi import Depends, FastAPI, Query, status

from src.config.database import SessionDep
from routers import pastes
from services.pastes import search_pastes, delete_expired
from src.schemas.paste import PasteRead
from dependencies import accept_validation

app = FastAPI()
app.include_router(pastes.router)


@app.get("/health", status_code=status.HTTP_200_OK)
def root():
    return {"Status": "Healthy"}

@app.get(
    "/pastes",
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

@app.delete("/pastes/expired", status_code=status.HTTP_204_NO_CONTENT)
def delete_expired_bin(session: SessionDep):
    delete_expired(session)