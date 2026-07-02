from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.auth import obter_token_payload, requer_admin, verificar_token
from app.services.settings_service import settings_service

router = APIRouter()


class CompanySettingsRequest(BaseModel):
    name: str = Field(min_length=2)
    cnpj: str | None = None
    email: str | None = None
    phone: str | None = None


class NotificationSettingsRequest(BaseModel):
    email: bool = True
    push: bool = True
    newMessage: bool = True
    newLead: bool = False
    dailyReport: bool = True


class ChangePasswordRequest(BaseModel):
    currentPassword: str = Field(min_length=1)
    newPassword: str = Field(min_length=6)


@router.get("/settings/empresa")
def obter_empresa(autorizado=Depends(verificar_token)):
    return settings_service.obter_empresa()


@router.patch("/settings/empresa")
def salvar_empresa(
    body: CompanySettingsRequest,
    _admin: dict = Depends(requer_admin),
):
    return settings_service.salvar_empresa(
        name=body.name,
        cnpj=body.cnpj,
        email=body.email,
        phone=body.phone,
    )


@router.get("/settings/preferencias")
def obter_preferencias(payload: dict = Depends(obter_token_payload)):
    return settings_service.obter_preferencias(payload["sub"])


@router.patch("/settings/preferencias")
def salvar_preferencias(
    body: NotificationSettingsRequest,
    payload: dict = Depends(obter_token_payload),
):
    return settings_service.salvar_preferencias(
        payload["sub"],
        body.model_dump(),
    )


@router.get("/settings/permissoes")
def obter_permissoes(payload: dict = Depends(obter_token_payload)):
    return settings_service.permissoes_do_perfil(payload.get("role") or "user")


@router.post("/settings/alterar-senha")
def alterar_senha(
    body: ChangePasswordRequest,
    payload: dict = Depends(obter_token_payload),
):
    return settings_service.alterar_senha(
        payload["sub"],
        current_password=body.currentPassword,
        new_password=body.newPassword,
    )
