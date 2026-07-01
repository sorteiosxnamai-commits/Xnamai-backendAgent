from fastapi import APIRouter, Depends

from app.core.auth import obter_usuario_id
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
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
