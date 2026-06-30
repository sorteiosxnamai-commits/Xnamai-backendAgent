import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import verificar_token

router = APIRouter()


class AgentChatRequest(BaseModel):
    message: str
    conversationId: str | None = None
    customerId: str | None = None
    mode: str | None = "copilot"
    history: list[dict] | None = None


def _gerar_resposta(message: str, mode: str) -> str:
    texto = message.lower()

    if any(w in texto for w in ["preço", "preco", "valor", "orçamento", "orcamento"]):
        return "Posso preparar um orçamento personalizado. Me informe o produto e a quantidade desejada."

    if any(w in texto for w in ["pedido", "entrega", "prazo"]):
        return "Vou verificar o status do seu pedido. Pode me informar o número do pedido?"

    if any(w in texto for w in ["estoque", "disponível", "disponivel"]):
        return "Consultei o catálogo: temos itens disponíveis. Qual código ou nome do produto você procura?"

    if mode == "suggestion":
        return "Sugestão: confirme os dados do cliente e ofereça uma proposta com prazo de validade de 7 dias."

    if mode == "agent":
        return f"Entendi sua solicitação sobre \"{message[:80]}\". Estou acionando o fluxo de atendimento adequado."

    return "Estou aqui para ajudar. Pode me dar mais detalhes sobre produto, quantidade ou prazo?"


@router.get("/agent/status")
def agent_status(autorizado=Depends(verificar_token)):
    return {
        "online": True,
        "model": "PulseDesk IA Pro",
        "avgResponseTime": "1.2s",
        "questionsAnswered": 128,
    }


@router.post("/agent/chat")
def agent_chat(body: AgentChatRequest, autorizado=Depends(verificar_token)):
    mode = body.mode or "copilot"
    reply = _gerar_resposta(body.message, mode)
    return {
        "reply": reply,
        "conversationId": body.conversationId or f"conv-{uuid.uuid4().hex[:8]}",
        "source": "intelligent",
    }


@router.post("/agent/restart")
def agent_restart(autorizado=Depends(verificar_token)):
    return {
        "success": True,
        "restartedAt": datetime.utcnow().isoformat(),
    }
