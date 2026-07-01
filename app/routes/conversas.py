from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.auth import verificar_token
from app.services.conversas_service import ConversasService

router = APIRouter()
conversas_service = ConversasService()


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1)
    sender: str = "agent"


@router.get("/conversas")
def get_conversas(autorizado=Depends(verificar_token)):
    return conversas_service.listar_conversas()


@router.get("/conversas/{conversation_id}/mensagens")
def get_mensagens(conversation_id: str, autorizado=Depends(verificar_token)):
    return conversas_service.listar_mensagens(conversation_id)


@router.post("/conversas/{conversation_id}/mensagens")
def send_mensagem(
    conversation_id: str,
    body: SendMessageRequest,
    autorizado=Depends(verificar_token),
):
    return conversas_service.enviar_mensagem(
        conversation_id,
        body.content,
        body.sender,
    )
