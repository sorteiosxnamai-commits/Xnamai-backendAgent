from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import verificar_token
from app.services.platform_service import platform_service

router = APIRouter()


class ChannelCreate(BaseModel):
    type: str
    name: str


class ChannelPatch(BaseModel):
    name: str | None = None
    phone: str | None = None
    connected: bool | None = None


class MoveDealRequest(BaseModel):
    dealId: str
    stageId: str


class CampaignCreate(BaseModel):
    name: str
    channel: str
    status: str
    recipients: int
    scheduledAt: str | None = None


class ChatbotCreate(BaseModel):
    name: str
    channel: str
    active: bool = True


class ChatbotPatch(BaseModel):
    name: str | None = None
    active: bool | None = None


@router.get("/canais")
def get_canais(autorizado=Depends(verificar_token)):
    return platform_service.get_channels()


@router.post("/canais")
def connect_canal(body: ChannelCreate, autorizado=Depends(verificar_token)):
    return platform_service.connect_channel(body.type, body.name)


@router.patch("/canais/{channel_id}")
def update_canal(channel_id: str, body: ChannelPatch, autorizado=Depends(verificar_token)):
    channel = platform_service.update_channel(channel_id, body.model_dump(exclude_none=True))
    if not channel:
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    return channel


@router.post("/canais/{channel_id}/toggle")
def toggle_canal(channel_id: str, autorizado=Depends(verificar_token)):
    channel = platform_service.toggle_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    return channel


@router.get("/funil")
def get_funil(autorizado=Depends(verificar_token)):
    return platform_service.get_funnel()


@router.post("/funil/mover")
def mover_funil(body: MoveDealRequest, autorizado=Depends(verificar_token)):
    if not platform_service.move_deal(body.dealId, body.stageId):
        raise HTTPException(status_code=404, detail="Negócio não encontrado")
    return {"success": True}


@router.post("/funil/sincronizar")
def sincronizar_funil(autorizado=Depends(verificar_token)):
    from app.services.funil_sync_service import funil_sync_service

    return funil_sync_service.sincronizar()


@router.get("/campanhas")
def get_campanhas(autorizado=Depends(verificar_token)):
    return platform_service.get_campaigns()


@router.post("/campanhas")
def create_campanha(body: CampaignCreate, autorizado=Depends(verificar_token)):
    return platform_service.add_campaign(body.model_dump())


@router.get("/chatbot/fluxos")
def get_chatbots(autorizado=Depends(verificar_token)):
    return platform_service.get_chatbots()


@router.post("/chatbot/fluxos")
def create_chatbot(body: ChatbotCreate, autorizado=Depends(verificar_token)):
    return platform_service.add_chatbot(body.model_dump())


@router.post("/chatbot/fluxos/{flow_id}/toggle")
def toggle_chatbot(flow_id: str, autorizado=Depends(verificar_token)):
    flow = platform_service.toggle_chatbot(flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Fluxo não encontrado")
    return flow


@router.patch("/chatbot/fluxos/{flow_id}")
def update_chatbot(flow_id: str, body: ChatbotPatch, autorizado=Depends(verificar_token)):
    flow = platform_service.update_chatbot(flow_id, body.model_dump(exclude_none=True))
    if not flow:
        raise HTTPException(status_code=404, detail="Fluxo não encontrado")
    return flow


@router.get("/integracoes")
def get_integracoes(autorizado=Depends(verificar_token)):
    return platform_service.get_integrations()


@router.post("/integracoes/{integration_id}/toggle")
def toggle_integracao(integration_id: str, autorizado=Depends(verificar_token)):
    item = platform_service.toggle_integration(integration_id)
    if not item:
        raise HTTPException(status_code=404, detail="Integração não encontrada")
    return item
