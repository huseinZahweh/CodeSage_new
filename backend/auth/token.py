from datetime import datetime, timedelta, timezone
from typing import Annotated, Generator

import jwt
from fastapi import Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from sqlalchemy.orm import Session

from models.user import TokenData
from database import SessionLocal
from model import User
from errors import APIError
from config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None, token_type: str = "access"):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({
        "exp": expire,
        "token_type": token_type
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_access_token_for_user(email: str):
    return create_access_token(
        data={"sub": email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access"
    )

def create_refresh_token_for_user(email: str):
    return create_access_token(
        data={"sub": email},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh"
    )

def verify_token(token: str, expected_type: str = "access") -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("token_type") != expected_type:
            raise InvalidTokenError("Invalid token type")

        email: str = payload.get("sub")
        if email is None:
            raise InvalidTokenError("Missing subject")

        return TokenData(email=email)

    except (InvalidTokenError, jwt.PyJWTError) as e:
        raise APIError("Could not validate credentials", code=401, details={"error": str(e)})

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    token_data = verify_token(token, expected_type="access")

    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise APIError(
            "User not found",
            code=status.HTTP_401_UNAUTHORIZED,
            details={"email": token_data.email}
        )
    return user

def verify_google_token(id_token_str: str):
    try:
        idinfo = id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
        )
        if idinfo.get("aud") != GOOGLE_CLIENT_ID:
            raise ValueError("Invalid audience")

        user_email = idinfo.get("email")
        if not user_email:
            raise ValueError("Email not found in token.")

        return user_email

    except ValueError as e:
        raise APIError("Invalid Google ID token", code=401, details={"error": str(e)})
