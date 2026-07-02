import json
import logging
import re
import uuid

from app.config.settings import OPENAI_MODEL
from app.services.agent_context_builder import AgentContextBuilder
from app.services.agent_intelligent_engine import generate_reply, generate_suggestion
from app.services.conversas_service import ConversasService
from app.services.openai_provider import call_openai, openai_configured

logger = logging.getLogger(__name__)


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

    def _minimal_context(self, message: str) -> dict:
        return {
            "userMessage": message,
            "salesMetrics": self.context_builder._load_sales_metrics(),
            "platformStats": self.context_builder._platform_stats(),
            "products": [],
            "productsCatalog": "",
            "messages": [],
            "orders": [],
            "relatedOrders": [],
        }

    def chat(
        self,
        message: str,
        conversation_id: str | None = None,
        customer_id: str | None = None,
        mode: str = "copilot",
        history: list[dict] | None = None,
    ) -> dict:
        mode = mode or "copilot"
        conv_id = conversation_id or f"conv-{uuid.uuid4().hex[:8]}"

        try:
            ctx = self.context_builder.build(conversation_id, customer_id, history, message)
        except Exception as exc:
            logger.exception("Erro ao montar contexto do Copiloto: %s", exc)
            ctx = self._minimal_context(message)

        if openai_configured():
            try:
                system_prompt = self.context_builder.to_prompt(ctx)
                ai_reply = call_openai(message, system_prompt, history, mode)
                if ai_reply:
                    return {
                        "reply": ai_reply,
                        "conversationId": conv_id,
                        "source": "openai",
                    }
            except Exception as exc:
                logger.warning("OpenAI no Copiloto falhou: %s", exc)

        try:
            reply = generate_reply(message, ctx, mode)
            return {
                "reply": reply,
                "conversationId": conv_id,
                "source": "intelligent",
            }
        except Exception as exc:
            logger.exception("Erro no Copiloto chat: %s", exc)
            return {
                "reply": (
                    "Não consegui processar agora. Verifique se Mercos/Supabase estão sincronizados "
                    f"e tente de novo. (Erro: {str(exc)[:100]})"
                ),
                "conversationId": conv_id,
                "source": "intelligent",
            }

    def suggest(
        self,
        conversation_id: str,
        customer_id: str | None = None,
    ) -> dict:
        try:
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
        except Exception as exc:
            logger.exception("Erro no Copiloto suggest: %s", exc)
            return {
                "insight": "Copiloto indisponível momentaneamente.",
                "suggestion": "Olá! Recebemos sua mensagem e retornaremos em breve.",
                "priority": "medium",
                "source": "intelligent",
            }


agent_service = AgentService()
