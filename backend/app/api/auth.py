from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.cookies import REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies
from app.core.deps import get_current_user, require_csrf
from app.core.limiter import limiter
from app.core.security import (
    create_access_token,
    generate_opaque_token,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    DevTokenResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import PasswordChange, UserRead, UserUpdate
from app.services import auth as auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


def _user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


def _build_token_response(
    *,
    response: Response,
    db: Session,
    user: User,
    remember: bool,
    request: Request,
) -> TokenResponse:
    refresh, refresh_exp = auth_service.issue_refresh_token(
        db,
        user=user,
        remember=remember,
        user_agent=_user_agent(request),
        ip_address=_client_ip(request),
    )
    access, access_exp = create_access_token(user_id=user.id, role=user.role.value)
    csrf = generate_opaque_token(24)
    set_auth_cookies(response, refresh_token=refresh, csrf_token=csrf, expires_at=refresh_exp)
    return TokenResponse(
        access_token=access,
        expires_at=int(access_exp.timestamp()),
        user=UserRead.model_validate(user),
    )


# ───────────────────── public endpoints ─────────────────────

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
def register(
    request: Request,
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user, _ = auth_service.register_client(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    return _build_token_response(
        response=response, db=db, user=user, remember=False, request=request
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = auth_service.authenticate(db, email=payload.email, password=payload.password)
    return _build_token_response(
        response=response, db=db, user=user, remember=payload.remember, request=request
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> TokenResponse:
    raw_token = request.cookies.get(REFRESH_COOKIE)
    if not raw_token:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    user, new_refresh, new_exp = auth_service.rotate_refresh_token(
        db,
        raw_token=raw_token,
        user_agent=_user_agent(request),
        ip_address=_client_ip(request),
    )
    access, access_exp = create_access_token(user_id=user.id, role=user.role.value)
    csrf = generate_opaque_token(24)
    set_auth_cookies(response, refresh_token=new_refresh, csrf_token=csrf, expires_at=new_exp)
    return TokenResponse(
        access_token=access,
        expires_at=int(access_exp.timestamp()),
        user=UserRead.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> MessageResponse:
    raw_token = request.cookies.get(REFRESH_COOKIE)
    if raw_token:
        auth_service.revoke_refresh_token(db, raw_token=raw_token)
    clear_auth_cookies(response)
    return MessageResponse(message="Signed out")


@router.post("/forgot-password", response_model=DevTokenResponse)
@limiter.limit("5/minute")
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> DevTokenResponse:
    auth_service.issue_password_reset(db, email=payload.email)
    # Always respond identically — never reveal whether the email exists.
    return DevTokenResponse(
        message="If an account exists for that email, a reset link has been sent.",
    )


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("10/minute")
def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    auth_service.consume_password_reset(
        db, token=payload.token, new_password=payload.new_password
    )
    return MessageResponse(message="Password updated. Please sign in.")


@router.post("/verify-email", response_model=UserRead)
def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db),
) -> UserRead:
    user = auth_service.consume_verification(db, token=payload.token)
    return UserRead.model_validate(user)


# ───────────────────── authenticated endpoints ─────────────────────

@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> UserRead:
    updated = auth_service.update_profile(
        db, user=user, full_name=payload.full_name, email=payload.email
    )
    return UserRead.model_validate(updated)


@router.patch("/password", response_model=MessageResponse)
def change_password(
    payload: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> MessageResponse:
    auth_service.change_password(
        db,
        user=user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return MessageResponse(message="Password updated. Sign in again on other devices.")
