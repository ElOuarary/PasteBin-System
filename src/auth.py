import uuid
from datetime import datetime, UTC, timedelta

import jwt

from fastapi import HTTPException, Depends, status 
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

SECRET_KEY = "a1606a690dfc05a18f8165f41200d26ff23925ce78b61628bfa6bdf60f1e5a88"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(id: int):
    now = datetime.now(UTC)
    payload = {
        "sub": id,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)


def get_payload(token: str = Depends(OAuth2PasswordBearer)) -> dict:
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    return payload

def get_user_id(payload: dict = Depends(get_payload)):
    user_id = payload.get("sub", None)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user_id

UserDep: int = Depends(get_user_id)