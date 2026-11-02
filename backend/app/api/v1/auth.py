"""Authentication API endpoints (P3-07/P3-08)."""

import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.client_ip import client_ip_from
from app.core.config import Settings
from app.core.security import hash_token
from app.db.session import db_manager
from app.schemas.auth import (
    CreateUserRequest,
    EmailOtpRequest,
    EmailOtpSentResponse,
    EmailOtpVerifyRequest,
    LoginRequest,
    LoginResponse,
    PreferencesUpdate,
    RefreshRequest,
    SessionUserResponse,
    UserResponse,
)
from app.services.auth import (
    AccountLockedError,
    AuthService,
    InvalidCredentialsError,
    RefreshTokenInvalidError,
    SessionInvalidError,
)
from app.services.delivery import get_email_delivery
from app.services.verification import (
    OTPExpiredError,
    OTPInvalidError,
    OTPMaxAttemptsError,
    OTPResendCooldownError,
    VerificationService,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

SESSION_COOKIE = "myfarmai_session"


def get_settings(request: Request) -> Settings:
    """Get the app's settings from the request state."""
    return request.app.state.settings  # type: ignore[no-any-return]


async def get_auth_service(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[AuthService]:
    """AuthService bound to an async session that commits on clean request completion."""
    # Repositories await their session calls — sync mode is unsupported for auth.
    async with db_manager.session() as session:
        yield AuthService(session, settings)


async def get_verification_service(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[VerificationService]:
    """VerificationService (E1) — same async-session DI shape as AuthService."""
    async with db_manager.session() as session:
        yield VerificationService(session, settings, get_email_delivery(settings))


def _presented_session_id(request: Request) -> str | None:
    """Session ID from the Android bearer header or the web cookie."""
    bearer = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
    return bearer or request.cookies.get(SESSION_COOKIE)


def _unauthenticated() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"detail": "authentication required", "error_code": "NOT_AUTHENTICATED"},
    )


def _client_ip(request: Request) -> str | None:
    """Client IP honoring only configured trusted proxies (P3-11)."""
    return client_ip_from(request, request.app.state.settings.trusted_proxy_cidrs_list)


def _user_response(user) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        preferred_language=user.preferred_language,
        is_active=user.is_active,
    )


def _login_response(user, access_token: str | None, refresh_token: str | None) -> LoginResponse:
    return LoginResponse(
        user=SessionUserResponse(
            id=str(user.id), email=user.email, full_name=user.full_name, role=user.role.value
        ),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    svc: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    try:
        user, session_id, refresh_token = await svc.login_password(
            body.email,
            body.password,
            client_ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            android=body.android,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "invalid email or password", "error_code": "INVALID_CREDENTIALS"},
        ) from None
    except AccountLockedError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "detail": "Too many failed login attempts. Try again later.",
                "error_code": "ACCOUNT_LOCKED",
            },
            headers={"Retry-After": "900"},
        ) from None

    if body.android:
        return _login_response(user, session_id, refresh_token)
    # Web: session ID lives in an HttpOnly cookie, never in the body.
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        max_age=svc._settings.session_ttl_hours * 3600,
        httponly=True,
        secure=svc._settings.environment == "production",
        samesite="lax",
        path="/",
    )
    return _login_response(user, None, None)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    svc: AuthService = Depends(get_auth_service),
) -> Response:
    session_id = request.cookies.get(SESSION_COOKIE)
    if session_id:
        await svc.logout(session_id, client_ip=_client_ip(request))
    # Match the set_cookie attributes (including secure, which is
    # environment-dependent at login) so browsers actually clear the cookie.
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        secure=svc._settings.environment == "production",
        httponly=True,
        samesite="lax",
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def me(
    request: Request,
    svc: AuthService = Depends(get_auth_service),
) -> UserResponse:
    presented = _presented_session_id(request)
    if not presented:
        raise _unauthenticated()
    try:
        user = await svc.validate_session(presented)
    except SessionInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "session invalid or expired", "error_code": "SESSION_INVALID"},
        ) from None
    return _user_response(user)


@router.patch("/preferences", response_model=UserResponse)
async def update_preferences(
    prefs: PreferencesUpdate,
    request: Request,
    svc: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """P5G: update the authenticated user's preferences (own only)."""
    presented = _presented_session_id(request)
    if not presented:
        raise _unauthenticated()
    try:
        user = await svc.validate_session(presented)
    except SessionInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "session invalid or expired", "error_code": "SESSION_INVALID"},
        ) from None
    user = await svc.update_preferences(user, preferred_language=prefs.preferred_language)
    return _user_response(user)


@router.post("/token/refresh", response_model=LoginResponse)
async def refresh(
    request: Request,
    body: RefreshRequest,
    svc: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    try:
        user, access_token, new_refresh = await svc.rotate_refresh(
            body.refresh_token,
            client_ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except RefreshTokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "refresh token invalid", "error_code": "REFRESH_INVALID"},
        ) from None
    return _login_response(user, access_token, new_refresh)


@router.post("/admin/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_user(
    request: Request,
    body: CreateUserRequest,
    svc: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Admin-created accounts only (ADR-008 MVP policy; no public registration)."""
    presented = _presented_session_id(request)
    if not presented:
        raise _unauthenticated()
    try:
        actor = await svc.validate_session(presented)
    except SessionInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "session invalid or expired", "error_code": "SESSION_INVALID"},
        ) from None
    if actor.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "admin role required", "error_code": "FORBIDDEN"},
        )
    try:
        user = await svc.create_user(
            body.email, body.password, full_name=body.full_name, actor_id=actor.id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "email already registered", "error_code": "EMAIL_CONFLICT"},
        ) from None
    return _user_response(user)


# -- passwordless email registration (E1) ------------------------------------


@router.post("/register/email/request-otp", response_model=EmailOtpSentResponse)
async def register_request_otp(
    body: EmailOtpRequest,
    request: Request,
    svc: VerificationService = Depends(get_verification_service),
) -> EmailOtpSentResponse:
    """Issue an email OTP (creating a pending user if the email is unknown).

    Privacy-aware: the response is identical whether or not the address was
    known — no account-existence disclosure.
    """
    try:
        await svc.request_email_otp(body.email)
    except OTPResendCooldownError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "detail": "A code was recently requested. Try again later.",
                "error_code": "OTP_RESEND_COOLDOWN",
            },
            headers={"Retry-After": "60"},
        ) from None
    return EmailOtpSentResponse(
        message="If the email address is valid, a verification code has been sent."
    )


@router.post("/register/email/verify", response_model=LoginResponse)
async def register_verify_otp(
    body: EmailOtpVerifyRequest,
    request: Request,
    response: Response,
    svc: VerificationService = Depends(get_verification_service),
) -> LoginResponse:
    """Verify the email OTP, activate the user, and open a web session."""
    try:
        user, session_id = await svc.verify_email_otp(
            body.email,
            body.code,
            client_ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except OTPInvalidError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": "invalid or used code", "error_code": "OTP_INVALID"},
        ) from None
    except OTPExpiredError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": "code has expired", "error_code": "OTP_EXPIRED"},
        ) from None
    except OTPMaxAttemptsError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "detail": "too many attempts; request a new code",
                "error_code": "OTP_MAX_ATTEMPTS",
            },
        ) from None

    # Web: session ID lives in an HttpOnly cookie, never in the body —
    # identical to the password-login cookie contract.
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        max_age=svc._settings.session_ttl_hours * 3600,
        httponly=True,
        secure=svc._settings.environment == "production",
        samesite="lax",
        path="/",
    )
    return _login_response(user, None, None)


# -- principal resolution for private endpoints (P3-08/P3-09) ---------------


def _sync_validate_session(db: Any, presented: str) -> Any:
    """Sync-mode session validation (test path only).

    Same conditions as AuthService.validate_session minus the idle-timeout
    touch (test-only path; production is async-only).
    """
    from sqlalchemy import func, select

    from app.db.models.session import Session as SessionModel
    from app.db.models.user import User

    stmt = (
        select(User)
        .join(SessionModel, SessionModel.user_id == User.id)
        .where(SessionModel.session_id_hash == hash_token(presented))
        .where(SessionModel.is_revoked.is_(False))
        .where(SessionModel.expires_at > func.now())
        .where(User.is_active.is_(True))
    )
    return db.execute(stmt).scalar_one_or_none()


async def get_current_user_id(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> uuid.UUID:
    """Resolve the authenticated principal's user id, or raise 401.

    Async mode uses AuthService.validate_session (expiry + revocation +
    idle timeout); sync test mode uses the direct SQL helper.
    """
    presented = _presented_session_id(request)
    if not presented:
        raise _unauthenticated()

    user = None
    if db_manager._is_async:
        async with db_manager.session() as session:
            user = await AuthService(session, settings).validate_session(presented)
    else:
        with db_manager.sync_session() as session:  # type: ignore[union-attr]
            user = _sync_validate_session(session, presented)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "session invalid or expired", "error_code": "SESSION_INVALID"},
        )
    return user.id
