import httpx

from app.config.settings import OPENAI_API_KEY, OPENAI_MODEL

MODE_INSTRUCTIONS = {
    "agent": (
        "Você é o Agente IA do PulseDesk. Responda ao atendente de forma cordial, "
        "cite dados reais do contexto (estoque, pedidos, valores) e proponha ações concretas."
    ),
    "copilot": (
        "Você é o Copiloto IA do PulseDesk. Ajude o ATENDENTE (não fale com o cliente "
        "diretamente, exceto ao sugerir mensagens entre aspas). Use markdown moderado. "
        "Seja específico: cite nomes, valores, códigos de produto e status de pedido do contexto. "
        "Se faltar dado, diga o que falta em vez de inventar."
    ),
    "suggestion": (
        "Retorne APENAS o texto da mensagem pronta para o atendente enviar ao cliente. "
        "Tom profissional, empático, português BR. Sem explicações extras."
    ),
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

    messages: list[dict] = [
        {
            "role": "system",
            "content": f"{MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS['copilot'])}\n\n{system_context}",
        },
    ]

    for item in (history or [])[-10:]:
        role = item.get("role", "user")
        if role not in ("user", "assistant"):
            role = "user"
        messages.append({"role": role, "content": item.get("content", "")})

    messages.append({"role": "user", "content": user_message})

    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "temperature": 0.4,
                "max_tokens": 1200,
                "messages": messages,
            },
            timeout=45.0,
        )
        response.raise_for_status()
        data = response.json()
        return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip() or None
    except Exception:
        return None
