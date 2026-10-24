from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.models.user import User
from app.database.session import get_db
from app.schemas.auth import (
    CurrentUserResponse,
    LogoutRequest,
    PasswordChangeRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService
from app.schemas.auth import (
    TokenResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirmRequest,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get("/me", response_model=CurrentUserResponse)
async def get_my_account(
    current_user: User = Depends(get_current_user),
):
    return CurrentUserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        organization_id=current_user.organization_id,
        role=current_user.role.name,
        must_change_password=current_user.must_change_password,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.login(
        db=db,
        email=form_data.username,
        password=form_data.password,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.refresh_token(
        db=db,
        refresh_token=request.refresh_token,
    )

@router.post(
    "/logout",
    status_code=204,
)
async def logout(
    request: LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    await AuthService.logout(
        db=db,
        refresh_token=request.refresh_token,
    )


@router.post(
    "/change-password",
    status_code=204,
)
async def change_password(
    request: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await AuthService.change_password(
        db=db,
        user=current_user,
        current_password=request.current_password,
        new_password=request.new_password,
    )

@router.post(
    "/password-reset/request",
    response_model=PasswordResetResponse,
)
async def request_password_reset(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    reset_token = await AuthService.request_password_reset(
        db=db,
        email=request.email,
    )

    return PasswordResetResponse(
        message=reset_token,
    )


@router.post(
    "/password-reset/confirm",
    status_code=204,
)
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    await AuthService.reset_password(
        db=db,
        token=request.token,
        new_password=request.new_password,
    )
