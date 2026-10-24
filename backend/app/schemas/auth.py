from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    organization_id: int
    role: str
    must_change_password: bool

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=128)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetResponse(BaseModel):
    message: str
    
class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str
