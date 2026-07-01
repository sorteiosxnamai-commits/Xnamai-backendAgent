import re
import unicodedata
from datetime import datetime

from app.repositories.dashboard_repository import DashboardRepository
from app.services.agent_knowledge import full_knowledge_base
from app.services.conversas_service import ConversasService
from app.services.pulsedesk_adapter import listar_clientes, listar_pedidos, listar_produtos, obter_cliente


def _format_currency(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


class AgentContextBuilder:
    def __init__(self):
        self.conversas = ConversasService()
        self.dashboard = DashboardRepository()

    def build(
        self,
        conversation_id: str | None = None,
        customer_id: str | None = None,
        history: list[dict] | None = None,
        user_message: str | None = None,
    ) -> dict:
        conversation = None
        messages: list[dict] = []
        all_conversations: list[dict] = []

        try:
            all_conversations = self.conversas.listar_conversas()
        except Exception:
            all_conversations = []

        if conversation_id:
            conversation = next((c for c in all_conversations if c["id"] == conversation_id), None)
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

        search_text = " ".join(filter(None, [
            user_message or "",
            *(m.get("content", "") for m in messages if m.get("sender") == "customer"),
        ]))

        if not customer_id:
            customer_id = self._resolve_customer_id(search_text, all_conversations)

        customer = None
        customer_detail = None
        orders: list[dict] = []
        if customer_id:
            customer = obter_cliente(str(customer_id))
            if customer:
                customer_detail = dict(customer)
                pedidos_resp = listar_pedidos(page=1, page_size=500)
                orders = [
                    o for o in pedidos_resp.get("data", [])
                    if str(o.get("customerId")) == str(customer_id)
                ]
                customer["ordersCount"] = len(orders)
                customer["totalSpent"] = sum(float(o.get("total") or 0) for o in orders)
                customer_detail["orders"] = orders[:10]

        products = self._load_relevant_products(search_text)
        related_orders = self._search_orders(search_text, orders)

        last_customer_msg = None
        for msg in reversed(messages):
            if msg.get("sender") == "customer":
                last_customer_msg = msg.get("content")
                break
        if not last_customer_msg and conversation:
            last_customer_msg = conversation.get("lastMessage")

        products_catalog = self._format_catalog(products)
        platform_stats = self._platform_stats()

        return {
            "conversation": conversation,
            "allConversations": all_conversations[:8],
            "customer": customer,
            "customerDetail": customer_detail,
            "messages": messages,
            "lastCustomerMessage": last_customer_msg,
            "productsCatalog": products_catalog,
            "products": products,
            "orders": orders[:10],
            "relatedOrders": related_orders,
            "platformStats": platform_stats,
            "userMessage": user_message,
        }

    def _resolve_customer_id(self, text: str, conversations: list[dict]) -> str | None:
        norm = _normalize(text)
        for conv in conversations:
            name = _normalize(conv.get("customerName") or "")
            if name and len(name) > 4 and name in norm:
                return conv.get("customerId")
            first = name.split(" ")[0] if name else ""
            if first and len(first) > 3 and first in norm:
                return conv.get("customerId")

        words = [w for w in re.findall(r"[a-záàâãéêíóôõúç]{4,}", norm) if w not in _STOP_WORDS]
        for word in words[:3]:
            result = listar_clientes(page=1, page_size=5, search=word)
            items = result.get("data") or []
            if items:
                return items[0].get("id")
        return None

    def _load_relevant_products(self, search_text: str) -> list[dict]:
        terms = self._extract_search_terms(search_text)
        found: dict[str, dict] = {}

        for term in terms[:4]:
            resp = listar_produtos(page=1, page_size=15, search=term)
            for p in resp.get("data") or []:
                found[str(p.get("id"))] = p

        if len(found) < 20:
            resp = listar_produtos(page=1, page_size=40)
            for p in resp.get("data") or []:
                found[str(p.get("id"))] = p

        return list(found.values())[:40]

    def _extract_search_terms(self, text: str) -> list[str]:
        norm = _normalize(text)
        terms = []
        for code in re.findall(r"\b[a-z]{0,3}-?\d{2,5}\b", norm):
            if len(code) >= 3:
                terms.append(code)
        for word in re.findall(r"[a-záàâãéêíóôõúç]{4,}", norm):
            if word not in _STOP_WORDS:
                terms.append(word)
        return terms

    def _search_orders(self, text: str, customer_orders: list[dict]) -> list[dict]:
        nums = re.findall(r"#?(\d{3,})", text or "")
        if not nums:
            return customer_orders[:3]
        pedidos_resp = listar_pedidos(page=1, page_size=200)
        all_orders = pedidos_resp.get("data") or []
        matched = []
        for num in nums:
            for order in all_orders:
                if num in str(order.get("number", "")):
                    matched.append(order)
        return matched or customer_orders[:3]

    def _format_catalog(self, products: list[dict]) -> str:
        if not products:
            return "Nenhum produto sincronizado — oriente sync Mercos em Configurações."
        return "\n".join(
            f"- {p.get('code')} | {p.get('name')} | {_format_currency(float(p.get('price') or 0))} | "
            f"estoque: {p.get('stock', 0)} un. | categoria: {p.get('category', 'Geral')}"
            for p in products
        )

    def _platform_stats(self) -> dict:
        try:
            return {
                "clientes": self.dashboard.contar_clientes() or 0,
                "produtos": self.dashboard.contar_produtos() or 0,
                "pedidos": self.dashboard.contar_pedidos() or 0,
            }
        except Exception:
            return {"clientes": 0, "produtos": 0, "pedidos": 0}

    def to_prompt(self, ctx: dict) -> str:
        intent = detect_intent(ctx)
        lines = [
            full_knowledge_base(),
            "",
            "## Dados em tempo real (prioridade máxima — use estes números)",
        ]

        stats = ctx.get("platformStats") or {}
        lines.extend([
            "",
            "### Plataforma",
            f"- Clientes cadastrados: {stats.get('clientes', 0)}",
            f"- Produtos no catálogo: {stats.get('produtos', 0)}",
            f"- Pedidos registrados: {stats.get('pedidos', 0)}",
        ])

        conv = ctx.get("conversation")
        if conv:
            lines.extend([
                "",
                "### Conversa ativa",
                f"- Cliente: {conv.get('customerName')}",
                f"- ID cliente Mercos: {conv.get('customerId') or 'N/A'}",
                f"- Canal: {conv.get('channel')} | Status: {conv.get('status')}",
                f"- Protocolo: {conv.get('protocol') or 'N/A'} | Depto: {conv.get('department') or 'N/A'}",
                f"- Atribuído a: {conv.get('assignedTo') or 'N/A'}",
                f"- Não lidas: {conv.get('unreadCount', 0)}",
                f"- Intenção detectada: {intent}",
                f"- Última mensagem: {conv.get('lastMessage')}",
            ])

        all_conv = ctx.get("allConversations") or []
        if all_conv and not conv:
            lines.append("")
            lines.append("### Conversas recentes")
            for c in all_conv[:5]:
                lines.append(
                    f"- {c.get('customerName')} ({c.get('channel')}): {str(c.get('lastMessage', ''))[:80]}"
                )

        customer = ctx.get("customer")
        if customer:
            lines.extend([
                "",
                "### Cliente (CRM / Mercos)",
                f"- Nome: {customer.get('name')}",
                f"- Empresa: {customer.get('company')}",
                f"- E-mail: {customer.get('email') or 'N/A'}",
                f"- Telefone: {customer.get('phone') or 'N/A'}",
                f"- Cidade: {customer.get('city') or 'N/A'}",
                f"- Pedidos: {customer.get('ordersCount', 0)} | Lifetime: {_format_currency(float(customer.get('totalSpent') or 0))}",
            ])

        for label, order_list in [
            ("Pedidos do cliente", ctx.get("orders") or []),
            ("Pedidos mencionados na pergunta", ctx.get("relatedOrders") or []),
        ]:
            if order_list:
                lines.append("")
                lines.append(f"### {label}")
                for order in order_list[:8]:
                    lines.append(
                        f"- Nº {order.get('number')} | status: {order.get('status')} | "
                        f"{_format_currency(float(order.get('total') or 0))} | "
                        f"{order.get('items', 1)} itens | cliente: {order.get('customerName') or '—'}"
                    )

        messages = ctx.get("messages") or []
        if messages:
            lines.append("")
            lines.append("### Histórico completo da conversa")
            for msg in messages[-20:]:
                sender = msg.get("sender")
                who = "Cliente" if sender == "customer" else "IA" if sender == "ai" else "Atendente"
                lines.append(f"{who}: {msg.get('content')}")

        lines.extend([
            "",
            "### Catálogo de produtos (relevante para esta pergunta)",
            ctx.get("productsCatalog") or "Sem produtos.",
        ])

        return "\n".join(lines)


_STOP_WORDS = {
    "para", "como", "qual", "quando", "onde", "sobre", "preciso", "quero", "pode",
    "pedido", "cliente", "conversa", "resuma", "sugira", "status", "liste", "produto",
    "produtos", "catalogo", "mensagem", "resposta", "copiloto", "pulse", "desk",
}


def detect_intent(ctx: dict, message: str | None = None) -> str:
    parts = [
        message or "",
        ctx.get("lastCustomerMessage") or "",
        ctx.get("userMessage") or "",
        *(m.get("content", "") for m in ctx.get("messages", []) if m.get("sender") == "customer"),
    ]
    norm = _normalize(" ".join(parts))

    if re.search(r"urgente|suporte urgente|imediato|reclam", norm):
        return "urgent_support"
    if re.search(r"orcamento|cotacao|preco|valor|unidades|desconto", norm):
        return "quote"
    if re.search(r"pedido|entrega|rastreio|chega|prazo", norm):
        return "tracking"
    if re.search(r"estoque|disponivel|produto|catalogo", norm):
        return "stock"
    if re.search(r"visita|tecnica|agendar|instalacao|manutencao", norm):
        return "technical_visit"
    if re.search(r"proposta|analisar|recebi|negoci", norm):
        return "proposal_followup"
    if re.search(r"garantia|troca|devolu", norm):
        return "warranty"
    if re.search(r"pagamento|parcel|boleto|pix|credito", norm):
        return "payment"
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
        for part in pname.split():
            if len(part) > 3 and part in norm:
                return product
    return None


def _extract_quantity(text: str) -> int | None:
    match = re.search(r"(\d+)\s*(unidades?|un\.?|pcs?|pecas?)?", text, re.I)
    return int(match.group(1)) if match else None


def _find_order(ctx: dict, text: str) -> dict | None:
    related = ctx.get("relatedOrders") or []
    if related:
        return related[0]
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
