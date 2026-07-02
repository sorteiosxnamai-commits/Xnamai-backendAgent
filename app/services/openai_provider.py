import httpx
import logging

from app.config.settings import OPENAI_API_KEY, OPENAI_MODEL
from app.services.agent_knowledge import SUGGESTION_BEHAVIOR

logger = logging.getLogger(__name__)

COPILOT_SYSTEM = """
Você é o **Copiloto IA Elite** do PulseDesk — o especialista comercial e de suporte mais capaz da equipe.
Sua missão: permitir que o atendente resolva **qualquer dúvida do cliente** sem precisar consultar outras pessoas.

## Competências
- Orçamentos, descontos, condições de pagamento e negociação B2B
- Status de pedidos, prazos, rastreio e logística
- Estoque, catálogo, substitutos e encomendas
- Garantia, troca, devolução e reclamações
- Suporte técnico, visitas e instalação
- Análise de tom, urgência e risco de churn

## Formato de resposta (sempre)
1. **Diagnóstico** — o que o cliente precisa (1–2 frases)
2. **Resposta** — dados concretos do contexto (valores, códigos, status)
3. **Mensagem pronta** — texto entre aspas para o atendente copiar e enviar
4. **Próximo passo** — ação clara e prazo
5. **Alerta** (se aplicável) — urgência, estoque baixo, risco

## Regras
- Português do Brasil, texto limpo e direto — sem emojis, sem asteriscos, sem bullets (•)
- Para métricas de venda: frases curtas, uma informação por linha, sem markdown
- NUNCA invente dados — use o contexto ou diga o que falta
- Seja proativo: antecipe frete, desconto, alternativa de produto
- Mensagens ao cliente: tom humano, empático, profissional
"""

AGENT_SYSTEM = """
Você é o Agente IA do PulseDesk em modo autônomo.
Responda ao cliente final de forma cordial, resolvendo a dúvida completamente.
Use dados reais do contexto. Se não souber, peça a informação faltante.
"""

SUGGESTION_SYSTEM = f"""
Você gera sugestões para atendentes humanos.
{SUGGESTION_BEHAVIOR}
Retorne JSON válido: {{"insight":"...","suggestion":"mensagem pronta para o cliente","priority":"low|medium|high"}}
"""

MODE_SYSTEM = {
    "copilot": COPILOT_SYSTEM,
    "agent": AGENT_SYSTEM,
    "suggestion": SUGGESTION_SYSTEM,
}


def openai_configured() -> bool:
    key = OPENAI_API_KEY or ""
    return key.startswith("sk-")


def call_openai(
    user_message: str,
    system_context: str,
    history: list[dict] | None = None,
    mode: str = "copilot",
) -> str | None:
    if not openai_configured():
        return None

    system_prompt = MODE_SYSTEM.get(mode, COPILOT_SYSTEM)

    messages: list[dict] = [
        {
            "role": "system",
            "content": f"{system_prompt}\n\n---\n\n# CONTEXTO EM TEMPO REAL\n\n{system_context[:80000]}",
        },
    ]

    for item in (history or [])[-16]:
        role = item.get("role", "user")
        if role not in ("user", "assistant"):
            role = "user"
        content = item.get("content", "")
        if content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    payload: dict = {
        "model": OPENAI_MODEL,
        "temperature": 0.35,
        "max_tokens": 2500,
        "messages": messages,
    }

    if mode == "suggestion":
        payload["response_format"] = {"type": "json_object"}
        payload["temperature"] = 0.25

    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            logger.warning("OpenAI retornou choices vazio (%s)", mode)
            return None
        message = choices[0].get("message") or {}
        content = message.get("content")
        return content.strip() if isinstance(content, str) and content.strip() else None
    except Exception as exc:
        logger.warning("OpenAI falhou (%s): %s", mode, exc)
        return None
