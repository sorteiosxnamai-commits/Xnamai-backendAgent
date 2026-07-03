from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import obter_usuario_id, security
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
)
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


@router.post("/login")
def login(credentials: LoginRequest):
    return auth_service.login(
        email=credentials.email,
        password=credentials.password,
    )


@router.post("/register")
def register(body: RegisterRequest):
    return auth_service.register(
        name=body.name,
        email=body.email,
        password=body.password,
        company=body.company,
    )


@router.post("/refresh")
def refresh(body: RefreshTokenRequest):
    return auth_service.refresh(body.refreshToken)


@router.post("/logout")
def logout(
    body: LogoutRequest | None = None,
    usuario_id: str = Depends(obter_usuario_id),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    refresh_token = body.refreshToken if body else None
    return auth_service.logout(
        access_token=credentials.credentials,
        usuario_id=usuario_id,
        refresh_token=refresh_token,
    )


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest):
    return auth_service.solicitar_reset_senha(body.email)


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest):
    return auth_service.redefinir_senha(body.token, body.password)


@router.patch("/profile")
def update_profile(
    body: UpdateProfileRequest,
    usuario_id: str = Depends(obter_usuario_id),
):
    return auth_service.atualizar_perfil(
        usuario_id=usuario_id,
        name=body.name,
        company=body.company,
    )
