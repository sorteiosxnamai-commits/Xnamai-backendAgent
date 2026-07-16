from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import obter_workspace_context, requer_admin, verificar_token
from app.services.whatsapp_service import whatsapp_service

router = APIRouter()


class WhatsAppConnectRequest(BaseModel):
    name: str = Field(min_length=2, default="WhatsApp Comercial")
    phoneNumberId: str | None = None
    accessToken: str | None = None
    displayPhone: str | None = None
    wabaId: str | None = None


@router.get("/whatsapp/status")
def get_whatsapp_status(autorizado=Depends(verificar_token), workspace=Depends(obter_workspace_context)):
    return whatsapp_service.status(workspace["workspaceId"])


@router.post("/whatsapp/testar-conexao")
def testar_whatsapp(autorizado=Depends(verificar_token), workspace=Depends(obter_workspace_context)):
    try:
        return whatsapp_service.testar_conexao(workspace["workspaceId"])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/whatsapp/conectar")
def conectar_whatsapp(
    body: WhatsAppConnectRequest,
    _admin: dict = Depends(requer_admin),
    workspace=Depends(obter_workspace_context),
):
    try:
        return whatsapp_service.conectar_canal(
            workspace_id=workspace["workspaceId"],
            name=body.name,
            phone_number_id=body.phoneNumberId,
            access_token=body.accessToken,
            display_phone=body.displayPhone,
            waba_id=body.wabaId,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
