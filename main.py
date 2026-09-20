from fastapi import FastAPI, status, HTTPException
from pwdlib import PasswordHash
from sqlmodel import select

from src.config.database import SessionDep
from src.schemas.user import UserRegistryForm
from src.models.user import User
from routers import paste, pastes

password_hash = PasswordHash.recommended()

app = FastAPI()
app.include_router(paste.router)
app.include_router(pastes.router)

@app.get("/health", status_code=status.HTTP_200_OK)
def root():
    return {"Status": "Healthy"}

# Need validation constraints on the email and password reserved for later
@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(registry_form: UserRegistryForm, session: SessionDep):
    user: User = session.exec(select(User).where(User.username == registry_form.username)).first()
    if user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User name is already taken")

    hashed_password: str = password_hash.hash(registry_form.password)
    user: User = User(username=registry_form.username, email=registry_form.email, hashed_password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "username": user.username}