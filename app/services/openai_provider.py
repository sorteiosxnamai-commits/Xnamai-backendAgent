import httpx
import logging
import time

from app.config.settings import OPENAI_API_KEY, OPENAI_MODEL
from app.services.agent_knowledge import SUGGESTION_BEHAVIOR

logger = logging.getLogger(__name__)

COPILOT_SYSTEM = """
Voce e o Copiloto IA Elite do PulseDesk — consultor comercial e de suporte senior.
O atendente humano usa sua resposta para resolver qualquer duvida do cliente sem escalar.

Voce TEM acesso a dados reais abaixo: clientes, produtos, pedidos, conversas, metricas e funil.
Use-os sempre antes de dizer que falta informacao.

## Formato (sempre)
Diagnostico:
O que o atendente precisa saber ou fazer (1-2 frases).

Analise:
Resposta completa com numeros EXATOS do contexto. Interprete, nao apenas liste.
Para follow-ups vagos ("me ajuda", "e agora?"): leia o historico do chat e oriente o PROXIMO passo — nunca repita a resposta anterior.

Mensagem pronta:
Texto entre aspas, tom humano, pronto para enviar ao cliente.

Proximo passo:
Acao concreta com prazo.

Alerta: (opcional — urgencia, estoque baixo, risco)

## Regras
- Portugues do Brasil, natural e profissional — sem emojis, sem markdown
- NUNCA invente dados — so use o contexto
- Pedidos Mercos = vendas reais; oportunidades CRM = pipeline (nao confundir)
- Responda qualquer tema: preco, prazo, pagamento, garantia, troca, reclamacao, metricas, funil, catalogo
- Se faltar dado especifico, diga exatamente o que pedir ao cliente ou sincronizar no Mercos
"""

AGENT_SYSTEM = """
Voce e o Agente IA do PulseDesk em modo autonomo.
Responda ao cliente final de forma cordial, resolvendo a duvida completamente.
Use dados reais do contexto. Se nao souber, peca a informacao faltante.
"""

SUGGESTION_SYSTEM = f"""
Voce gera sugestoes para atendentes humanos.
{SUGGESTION_BEHAVIOR}
Retorne JSON valido: {{"insight":"...","suggestion":"mensagem pronta para o cliente","priority":"low|medium|high"}}
"""

MODE_SYSTEM = {
    "copilot": COPILOT_SYSTEM,
    "agent": AGENT_SYSTEM,
    "suggestion": SUGGESTION_SYSTEM,
}


def openai_configured() -> bool:
    key = OPENAI_API_KEY or ""
    return key.startswith("sk-")


def _parse_completion(data: dict, mode: str) -> str | None:
    choices = data.get("choices") or []
    if not choices:
        logger.warning("OpenAI retornou choices vazio (%s)", mode)
        return None
    message = choices[0].get("message") or {}
    content = message.get("content")
    return content.strip() if isinstance(content, str) and content.strip() else None


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
            "content": f"{system_prompt}\n\n---\n\n# CONTEXTO EM TEMPO REAL\n\n{system_context[:90000]}",
        },
    ]

    for item in (history or [])[-20]:
        role = item.get("role", "user")
        if role not in ("user", "assistant"):
            role = "user"
        content = item.get("content", "")
        if content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    payload: dict = {
        "model": OPENAI_MODEL,
        "temperature": 0.5,
        "max_tokens": 3000,
        "messages": messages,
    }

    if mode == "suggestion":
        payload["response_format"] = {"type": "json_object"}
        payload["temperature"] = 0.25

    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=90.0,
            )
            response.raise_for_status()
            return _parse_completion(response.json(), mode)
        except Exception as exc:
            last_exc = exc
            logger.warning("OpenAI falhou (%s) tentativa %s: %s", mode, attempt + 1, exc)
            if attempt == 0:
                time.sleep(1.0)

    if last_exc:
        logger.warning("OpenAI esgotou tentativas (%s): %s", mode, last_exc)
    return None
