from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from sqlmodel import select

from routers import paste, pastes
from src.auth import Token, create_access_token
from src.config.database import SessionDep
from src.models.user import User
from src.schemas.user import UserRegistryForm

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
    user: User = session.exec(
        select(User).where(User.username == registry_form.username)
    ).first()
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username is already taken"
        )

    hashed_password: str = password_hash.hash(registry_form.password)
    user: User = User(
        username=registry_form.username,
        email=registry_form.email,
        hashed_password=hashed_password,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "username": user.username}


@app.post("/login", response_model=Token)
def login(session: SessionDep, login_form: OAuth2PasswordRequestForm = Depends()):
    user = session.exec(
        select(User).where(User.username == login_form.username)
    ).first()
    if user is None or not password_hash.verify(
        login_form.password, user.hashed_password
    ):
        # we can run seperate condition by first checking the existing of the username if it does not exists, we verify the hash to prevent time attacking
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username or passowrd is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_access_token(user.id), "token_type": "Bearer"}
