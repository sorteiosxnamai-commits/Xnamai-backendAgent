from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import verificar_token
from app.services.platform_store import platform_store

router = APIRouter()


class SendMessageRequest(BaseModel):
    content: str
    sender: str = "agent"


@router.get("/conversas")
def get_conversas(autorizado=Depends(verificar_token)):
    return platform_store.get_conversations()


@router.get("/conversas/{conversation_id}/mensagens")
def get_mensagens(conversation_id: str, autorizado=Depends(verificar_token)):
    return platform_store.get_messages(conversation_id)


@router.post("/conversas/{conversation_id}/mensagens")
def send_mensagem(
    conversation_id: str,
    body: SendMessageRequest,
    autorizado=Depends(verificar_token),
):
    return platform_store.send_message(conversation_id, body.content, body.sender)
