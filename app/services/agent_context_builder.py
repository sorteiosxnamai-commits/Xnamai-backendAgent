import re
import unicodedata
from datetime import datetime

from app.services.conversas_service import ConversasService
from app.services.pulsedesk_adapter import listar_pedidos, listar_produtos, obter_cliente


def _format_currency(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class AgentContextBuilder:
    def __init__(self):
        self.conversas = ConversasService()

    def build(
        self,
        conversation_id: str | None = None,
        customer_id: str | None = None,
        history: list[dict] | None = None,
    ) -> dict:
        conversation = None
        messages: list[dict] = []

        if conversation_id:
            try:
                conversas = self.conversas.listar_conversas()
                conversation = next((c for c in conversas if c["id"] == conversation_id), None)
            except Exception:
                conversation = None

            if conversation:
                customer_id = customer_id or conversation.get("customerId")
                try:
                    messages = self.conversas.listar_mensagens(conversation_id)
                except Exception:
                    messages = []

        if history:
            for i, item in enumerate(history):
                role = item.get("role", "user")
                messages.append({
                    "id": f"h-{i}",
                    "conversationId": conversation_id or "",
                    "content": item.get("content", ""),
                    "sender": "customer" if role == "user" else "ai",
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "read",
                })

        customer = None
        customer_detail = None
        if customer_id:
            customer = obter_cliente(str(customer_id))
            if customer:
                customer_detail = dict(customer)
                pedidos_resp = listar_pedidos(page=1, page_size=200)
                orders = [
                    o for o in pedidos_resp.get("data", [])
                    if str(o.get("customerId")) == str(customer_id)
                ]
                customer["ordersCount"] = len(orders)
                customer["totalSpent"] = sum(float(o.get("total") or 0) for o in orders)
                customer_detail["orders"] = orders[:5]
                customer_detail["purchasedProducts"] = customer.get("purchasedProducts") or []

        last_customer_msg = None
        for msg in reversed(messages):
            if msg.get("sender") == "customer":
                last_customer_msg = msg.get("content")
                break
        if not last_customer_msg and conversation:
            last_customer_msg = conversation.get("lastMessage")

        produtos_resp = listar_produtos(page=1, page_size=12)
        products = produtos_resp.get("data", [])
        products_catalog = "\n".join(
            f"{p.get('code')} ({p.get('name')}): {_format_currency(float(p.get('price') or 0))}, estoque {p.get('stock', 0)}"
            for p in products
        ) or "Nenhum produto sincronizado — rode sync Mercos."

        return {
            "conversation": conversation,
            "customer": customer,
            "customerDetail": customer_detail,
            "messages": messages,
            "lastCustomerMessage": last_customer_msg,
            "productsCatalog": products_catalog,
            "products": products,
            "orders": customer_detail.get("orders", []) if customer_detail else [],
        }

    def to_prompt(self, ctx: dict) -> str:
        intent = detect_intent(ctx)
        lines = [
            "Você é o Copiloto IA do PulseDesk (Tironitech), plataforma de atendimento omnichannel B2B.",
            "Responda em português do Brasil, de forma profissional, empática e orientada a ação.",
            "Use SEMPRE os dados abaixo. Cite valores, estoque e prazos quando disponíveis.",
            "Para sugestões: escreva mensagens prontas para o atendente copiar e enviar ao cliente.",
            "Para resumos: inclua tom do cliente, urgência e próximo passo recomendado.",
        ]

        conv = ctx.get("conversation")
        if conv:
            lines.extend([
                "",
                "## Conversa ativa",
                f"- Cliente: {conv.get('customerName')}",
                f"- Canal: {conv.get('channel')}",
                f"- Status: {conv.get('status')}",
                f"- Protocolo: {conv.get('protocol') or 'N/A'}",
                f"- Departamento: {conv.get('department') or 'N/A'}",
                f"- Intenção detectada: {intent}",
                f"- Última mensagem: {conv.get('lastMessage')}",
            ])

        customer = ctx.get("customer")
        if customer:
            lines.extend([
                "",
                "## Cliente",
                f"- Nome: {customer.get('name')}",
                f"- Empresa: {customer.get('company')}",
                f"- Cidade: {customer.get('city')}",
                f"- Pedidos: {customer.get('ordersCount', 0)} | Total: {_format_currency(float(customer.get('totalSpent') or 0))}",
            ])

        orders = ctx.get("orders") or []
        if orders:
            lines.append("")
            lines.append("## Pedidos recentes")
            for order in orders:
                lines.append(
                    f"- {order.get('number')}: {order.get('status')}, "
                    f"{_format_currency(float(order.get('total') or 0))}, {order.get('items', 1)} itens"
                )

        messages = ctx.get("messages") or []
        if messages:
            lines.append("")
            lines.append("## Histórico recente")
            for msg in messages[-8:]:
                sender = msg.get("sender")
                who = "Cliente" if sender == "customer" else "IA" if sender == "ai" else "Atendente"
                lines.append(f"{who}: {msg.get('content')}")

        lines.extend(["", "## Catálogo (amostra)", ctx.get("productsCatalog") or ""])
        return "\n".join(lines)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def detect_intent(ctx: dict, message: str | None = None) -> str:
    parts = [
        message or "",
        ctx.get("lastCustomerMessage") or "",
        *(m.get("content", "") for m in ctx.get("messages", []) if m.get("sender") == "customer"),
    ]
    norm = _normalize(" ".join(parts))

    if re.search(r"urgente|suporte urgente|imediato", norm):
        return "urgent_support"
    if re.search(r"orcamento|cotacao|preco|unidades", norm):
        return "quote"
    if re.search(r"pedido|entrega|rastreio|chega", norm):
        return "tracking"
    if re.search(r"estoque|disponivel|produto", norm):
        return "stock"
    if re.search(r"visita|tecnica|agendar", norm):
        return "technical_visit"
    if re.search(r"proposta|analisar|recebi", norm):
        return "proposal_followup"
    if re.search(r"obrigad|excelente|otimo atendimento", norm):
        return "closed_positive"
    return "general"


def _first_name(ctx: dict) -> str:
    customer = ctx.get("customer") or {}
    conv = ctx.get("conversation") or {}
    name = customer.get("name") or conv.get("customerName") or ""
    return name.split(" ")[0] if name else ""


def _find_product(ctx: dict, text: str) -> dict | None:
    norm = _normalize(text)
    for product in ctx.get("products") or []:
        code = _normalize(product.get("code") or "")
        pname = _normalize(product.get("name") or "")
        if code and code in norm:
            return product
        if pname and pname in norm:
            return product
        last_word = pname.split(" ")[-1] if pname else ""
        if last_word and len(last_word) > 3 and last_word in norm:
            return product
    return None


def _extract_quantity(text: str) -> int | None:
    match = re.search(r"(\d+)\s*(unidades?|un\.?|pcs?|pecas?)?", text, re.I)
    return int(match.group(1)) if match else None


def _find_order(ctx: dict, text: str) -> dict | None:
    orders = ctx.get("orders") or []
    if orders:
        return orders[0]
    pedidos_resp = listar_pedidos(page=1, page_size=100)
    all_orders = pedidos_resp.get("data", [])
    num_match = re.search(r"#?(\d{3,})", text or "")
    if num_match:
        num = num_match.group(1)
        for order in all_orders:
            if num in str(order.get("number", "")):
                return order
    customer_id = (ctx.get("customer") or {}).get("id")
    if customer_id:
        for order in all_orders:
            if str(order.get("customerId")) == str(customer_id):
                return order
    return all_orders[0] if all_orders else None
