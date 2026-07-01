from datetime import datetime

from fastapi import HTTPException

from app.repositories.conversa_repository import ConversaRepository
from app.repositories.mensagem_repository import MensagemRepository


def _map_conversa(row: dict) -> dict:
    return {
        "id": str(row.get("id")),
        "customerId": str(row.get("cliente_mercos_id") or ""),
        "customerName": row.get("customer_name") or "Cliente",
        "customerAvatar": row.get("customer_avatar"),
        "lastMessage": row.get("last_message") or "",
        "lastMessageAt": row.get("last_message_at") or row.get("created_at") or datetime.utcnow().isoformat(),
        "status": row.get("status") or "active",
        "unreadCount": int(row.get("unread_count") or 0),
        "channel": row.get("channel") or "whatsapp",
        "department": row.get("department"),
        "protocol": row.get("protocol"),
        "assignedTo": row.get("assigned_to"),
    }


def _map_mensagem(row: dict) -> dict:
    return {
        "id": str(row.get("id")),
        "conversationId": str(row.get("conversa_id")),
        "content": row.get("content") or "",
        "sender": row.get("sender") or "agent",
        "timestamp": row.get("created_at") or datetime.utcnow().isoformat(),
        "status": row.get("status") or "sent",
    }


class ConversasService:

    def __init__(self):
        self.conversas = ConversaRepository()
        self.mensagens = MensagemRepository()

    def listar_conversas(self) -> list[dict]:
        try:
            rows = self.conversas.listar()
        except Exception as exc:
            if "conversas" in str(exc).lower():
                raise HTTPException(
                    status_code=503,
                    detail="Tabela conversas não existe. Execute supabase/001_conversas_mensagens.sql no Supabase.",
                ) from exc
            raise
        return [_map_conversa(row) for row in rows]

    def listar_mensagens(self, conversa_id: str) -> list[dict]:
        if not self.conversas.obter(conversa_id):
            raise HTTPException(status_code=404, detail="Conversa não encontrada")

        rows = self.mensagens.listar_por_conversa(conversa_id)
        return [_map_mensagem(row) for row in rows]

    def enviar_mensagem(self, conversa_id: str, content: str, sender: str = "agent") -> dict:
        if sender not in {"customer", "agent", "ai"}:
            sender = "agent"

        conversa = self.conversas.obter(conversa_id)
        if not conversa:
            raise HTTPException(status_code=404, detail="Conversa não encontrada")

        mensagem = self.mensagens.criar({
            "conversa_id": conversa_id,
            "content": content.strip(),
            "sender": sender,
            "status": "sent",
        })

        self.conversas.atualizar(conversa_id, {
            "last_message": content.strip(),
            "last_message_at": datetime.utcnow().isoformat(),
        })

        return _map_mensagem(mensagem)

    def contar_conversas(self) -> int:
        try:
            return self.conversas.contar()
        except Exception:
            return 0
