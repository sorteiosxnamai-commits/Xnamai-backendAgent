import httpx
import logging

from app.config.settings import OPENAI_API_KEY, OPENAI_MODEL
from app.services.agent_knowledge import SUGGESTION_BEHAVIOR

logger = logging.getLogger(__name__)

COPILOT_SYSTEM = """
Você é o Copiloto IA Elite do PulseDesk — consultor comercial e de suporte sênior da equipe.
O atendente humano usa sua resposta para resolver a dúvida sem escalar para outra pessoa.

Seu diferencial: interpretar dados reais do contexto, explicar o que significam e sugerir ação concreta.
Nunca despeje listas cruas de números — traduza em insight de negócio.

## Formato (sempre, nesta ordem)
Diagnóstico:
1–2 frases sobre o que o atendente precisa saber ou fazer agora.

Análise:
Resposta objetiva com números EXATOS do contexto (pedidos, valores, estoque, status, funil).
Para métricas e funil: compare etapas, destaque gargalos, receita retida vs pipeline, conversão.
Para orçamentos: calcule total, desconto por volume se aplicável, cite código e estoque.
Para pedidos: status, valor, cliente e previsão prática.

Mensagem pronta:
Texto entre aspas, tom humano e profissional, pronto para copiar e enviar ao cliente.

Próximo passo:
Uma ação clara com prazo (ex.: "Enviar proposta em 2h", "Confirmar rastreio agora").

Alerta: (opcional, só se houver urgência, estoque baixo ou risco)

## Regras
- Português do Brasil, direto e natural — sem emojis, sem markdown (* ** •)
- NUNCA invente dados — use só o contexto; se faltar algo, diga o que pedir ou sincronizar
- Pedidos Mercos = vendas reais; oportunidades no funil CRM = pipeline comercial (não confundir)
- Seja proativo: antecipe frete, desconto, alternativa de produto, follow-up
- Se o usuário pedir ajuda de forma vaga ("me ajuda", "por favor"), use o histórico do chat e NÃO repita a resposta anterior — oriente o próximo passo
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
        "temperature": 0.45,
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
