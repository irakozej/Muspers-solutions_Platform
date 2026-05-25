from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRead


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    full_name: str = Field(min_length=1, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)
    remember: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: int  # unix seconds
    user: UserRead


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class MessageResponse(BaseModel):
    message: str


class DevTokenResponse(BaseModel):
    """Returned in development to make manual e2e testing trivial. Never set in prod."""
    message: str
    dev_token: str | None = None
    dev_link: str | None = None
