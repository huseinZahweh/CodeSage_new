from fastapi import APIRouter, Response, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from model import User
from models.user import UserRegister, UserLogin, GoogleToken, ForgotPasswordRequest, ResetPasswordRequest
from database import SessionLocal
from auth.token import (
    hash_password, verify_password,
    create_access_token_for_user,
    create_refresh_token_for_user,
    verify_token, verify_google_token
)
from errors import APIError
from auth.token import SECRET_KEY, ALGORITHM
import jwt

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
async def create_user(user: UserRegister, db: Session = Depends(get_db)): 
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise APIError("Email already registered", code=400, details={"email": user.email})
    
    hashed_pass = hash_password(user.password)

    new_user = User(fullname=user.fullname, email=user.email, hashed_password= hashed_pass)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)


    return {"message": "Successfully Signed in!"}

@router.post("/login")
async def login_user(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    user_data = db.query(User).filter(User.email == user.email).first()
    if not user_data:
        raise APIError("Invalid Credentials", code=401, details={"email": user.email})

    if not verify_password(user.password, user_data.hashed_password):
        raise APIError("Invalid Credentials", code=401)

    access_token = create_access_token_for_user(user.email)
    refresh_token = create_refresh_token_for_user(user.email)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=7*24*60*60,  
        secure=True,  
        samesite="strict"
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh")
async def refresh_token(request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise APIError("Refresh token missing", code=401)

    try:
        token_data = verify_token(refresh_token)
    except APIError as e:
        raise APIError("Invalid refresh token", code=401)

    new_access_token = create_access_token_for_user(token_data.email)

    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/google-login")
async def login_with_google(token: GoogleToken, response: Response, db: Session = Depends(get_db)):
    user_email = verify_google_token(token.id_token)
    
    user_data = db.query(User).filter(User.email == user_email).first()
    if not user_data:
        new_user = User(
            fullname=user_email.split("@")[0], 
            email=user_email,
            hashed_password=None,  
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    
    access_token = create_access_token_for_user(user_email)
    refresh_token = create_refresh_token_for_user(user_email)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=3*24*60*60
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    expire = datetime.utcnow() + timedelta(hours=1)
    reset_token = jwt.encode({"sub": user.email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

    print(f"Reset token for {user.email}: {reset_token}") 
    return {"message": "Password reset token sent to your email"}

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(request.token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(request.new_password)

    user.hashed_password = hashed_password
    db.commit()

    return {"message": "Password updated successfully"}