from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
import re

class UserRegister(BaseModel):
    fullname: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=50, 
        description="Password must be 8-50 characters, include uppercase, lowercase, digit, and special character"
    )
    confirm_password: str = Field(...)

    @model_validator(mode="after")
    def check_passwords_match(cls, model):
        if model.password != model.confirm_password:
            raise ValueError('Passwords do not match')
        return model

    @field_validator('password')
    @classmethod
    def password_complexity(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @field_validator('fullname')
    @classmethod
    def validate_name(cls, v):
        if not v.replace(" ", "").isalpha():
            raise ValueError("Name must contain only letters and spaces")
        return v.title()


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserData(BaseModel):
    fullname: str
    email: EmailStr

class TokenData(BaseModel):
    email: EmailStr | None = None

class GoogleToken(BaseModel):
    id_token: str
    
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str