import uuid
from datetime import datetime

from app.services.agent_context_builder import AgentContextBuilder
from app.services.agent_intelligent_engine import generate_reply, generate_suggestion
from app.services.conversas_service import ConversasService


class AgentService:
    def __init__(self):
        self.context_builder = AgentContextBuilder()
        self.conversas = ConversasService()

    def status(self) -> dict:
        try:
            total = len(self.conversas.listar_conversas())
        except Exception:
            total = 0
        return {
            "online": True,
            "model": "PulseDesk IA (dados Supabase)",
            "avgResponseTime": "1.2s",
            "questionsAnswered": total,
        }

    def build_context(
        self,
        conversation_id: str | None = None,
        customer_id: str | None = None,
        history: list[dict] | None = None,
    ) -> dict:
        return self.context_builder.build(conversation_id, customer_id, history)

    def chat(
        self,
        message: str,
        conversation_id: str | None = None,
        customer_id: str | None = None,
        mode: str = "copilot",
        history: list[dict] | None = None,
    ) -> dict:
        ctx = self.context_builder.build(conversation_id, customer_id, history)
        reply = generate_reply(message, ctx, mode or "copilot")
        return {
            "reply": reply,
            "conversationId": conversation_id or f"conv-{uuid.uuid4().hex[:8]}",
            "source": "intelligent",
        }

    def suggest(
        self,
        conversation_id: str,
        customer_id: str | None = None,
    ) -> dict:
        ctx = self.context_builder.build(conversation_id, customer_id)
        suggestion = generate_suggestion(ctx)
        return {**suggestion, "source": "intelligent"}


agent_service = AgentService()
