from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from pwdlib import PasswordHash

from src.security import Token, create_access_token
from src.config.database import SessionDep
from src.models import User
from src.schemas.user import UserRegistryForm

password_hash = PasswordHash.recommended()

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(registry_form: UserRegistryForm, session: SessionDep):
    user: User = session.exec(
        select(User).where(User.username == registry_form.username)
    ).first()
    user_email: User = session.exec(
        select(User).where(User.email == registry_form.email)
    ).first()
    if user is not None or user_email is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail= "Username or email is already taken"
        )

    hashed_password: str = password_hash.hash(registry_form.password)
    user: User = User(
        username=registry_form.username,
        email=registry_form.email,
        hashed_password=hashed_password,
        role="user"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "username": user.username}


@router.post("/login", response_model=Token, status_code=status.HTTP_201_CREATED)
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
            detail="Username or password is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_access_token(user.id, user.role), "token_type": "Bearer"}
