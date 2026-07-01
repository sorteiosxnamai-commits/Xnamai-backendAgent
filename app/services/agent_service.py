import json
import re
import uuid

from app.config.settings import OPENAI_MODEL
from app.services.agent_context_builder import AgentContextBuilder
from app.services.agent_intelligent_engine import generate_reply, generate_suggestion
from app.services.conversas_service import ConversasService
from app.services.openai_provider import call_openai, openai_configured


class AgentService:
    def __init__(self):
        self.context_builder = AgentContextBuilder()
        self.conversas = ConversasService()

    def _model_label(self) -> str:
        if openai_configured():
            return f"OpenAI {OPENAI_MODEL}"
        return "PulseDesk IA (dados Supabase)"

    def status(self) -> dict:
        try:
            total = len(self.conversas.listar_conversas())
        except Exception:
            total = 0
        return {
            "online": True,
            "model": self._model_label(),
            "avgResponseTime": "2.5s" if openai_configured() else "1.2s",
            "questionsAnswered": total,
            "openaiEnabled": openai_configured(),
        }

    def build_context(
        self,
        conversation_id: str | None = None,
        customer_id: str | None = None,
        history: list[dict] | None = None,
        user_message: str | None = None,
    ) -> dict:
        return self.context_builder.build(conversation_id, customer_id, history, user_message)

    def chat(
        self,
        message: str,
        conversation_id: str | None = None,
        customer_id: str | None = None,
        mode: str = "copilot",
        history: list[dict] | None = None,
    ) -> dict:
        ctx = self.context_builder.build(conversation_id, customer_id, history, message)
        system_prompt = self.context_builder.to_prompt(ctx)
        mode = mode or "copilot"

        ai_reply = call_openai(message, system_prompt, history, mode)
        if ai_reply:
            return {
                "reply": ai_reply,
                "conversationId": conversation_id or f"conv-{uuid.uuid4().hex[:8]}",
                "source": "openai",
            }

        reply = generate_reply(message, ctx, mode)
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
        if ctx.get("lastCustomerMessage"):
            ctx = self.context_builder.build(
                conversation_id,
                customer_id,
                user_message=ctx.get("lastCustomerMessage"),
            )
        system_prompt = self.context_builder.to_prompt(ctx)

        prompt = (
            "Analise a conversa e gere JSON com insight, suggestion (mensagem pronta para o cliente) "
            'e priority (low|medium|high).\n\n'
            f'Última mensagem do cliente: {ctx.get("lastCustomerMessage") or ""}'
        )

        raw = call_openai(prompt, system_prompt, [], "suggestion")
        if raw:
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    return {
                        "insight": parsed.get("insight", ""),
                        "suggestion": parsed.get("suggestion", ""),
                        "priority": parsed.get("priority", "medium"),
                        "source": "openai",
                    }
                except json.JSONDecodeError:
                    pass

        suggestion = generate_suggestion(ctx)
        return {**suggestion, "source": "intelligent"}


agent_service = AgentService()
