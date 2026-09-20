from datetime import datetime, UTC, timedelta
import uuid

import jwt

from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel
from sqlmodel import select

from src.config.database import SessionDep
from src.schemas.user import UserRegistryForm
from src.models.user import User
from routers import paste, pastes

SECRET_KEY = "a1606a690dfc05a18f8165f41200d26ff23925ce78b61628bfa6bdf60f1e5a88"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

password_hash = PasswordHash.recommended()

class Token(BaseModel):
    access_token: str
    token_type: str

oauth2_schema = OAuth2PasswordBearer("login")


def create_access_token(username: str):
    now = datetime.now(UTC)
    payload = {
        "sub": username,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)

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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is already taken")

    hashed_password: str = password_hash.hash(registry_form.password)
    user: User = User(username=registry_form.username, email=registry_form.email, hashed_password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "username": user.username}

# Need to change the value that is passed to the access token, using a jwt instead
@app.post("/login", response_model=Token)
def login(session: SessionDep, login_form: OAuth2PasswordRequestForm = Depends()):
    user = session.exec(select(User).where(User.username == login_form.username)).first()
    if user is None or not password_hash.verify(login_form.password, user.hashed_password):
        # we can run seperate condition by first checking the existing of the username if it does not exists, we verify the hash to prevent time attacking
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username or passowrd is invalid", headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": create_access_token(user.username), "token_type": "Bearer"}
