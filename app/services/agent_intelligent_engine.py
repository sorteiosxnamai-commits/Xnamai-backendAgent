import re

from app.services.agent_context_builder import (
    _extract_quantity,
    _find_order,
    _find_product,
    _first_name,
    _format_currency,
    _normalize,
    detect_intent,
)

SENTIMENT = {
    "quote": "Comercial — intenção de compra",
    "tracking": "Ansioso — aguardando entrega",
    "stock": "Consultivo — avaliando produto",
    "technical_visit": "Operacional — precisa de suporte presencial",
    "proposal_followup": "Decisão — analisando proposta",
    "urgent_support": "Urgente — prioridade máxima",
    "closed_positive": "Satisfeito — conversa encerrada",
    "sales_metrics": "Gestão — consulta métricas de venda",
    "general": "Neutro — aguardando direcionamento",
}

STATUS_LABELS = {
    "delivered": "✅ Entregue",
    "shipped": "🚚 Em trânsito",
    "processing": "📦 Em separação",
    "pending": "⏳ Aguardando pagamento",
    "cancelled": "❌ Cancelado",
}


def _combined_text(ctx: dict, message: str | None = None) -> str:
    parts = [
        message or "",
        ctx.get("lastCustomerMessage") or "",
        *(m.get("content", "") for m in ctx.get("messages", []) if m.get("sender") == "customer"),
    ]
    return " ".join(parts)


def summarize_conversation(ctx: dict) -> str:
    name = _first_name(ctx) or (ctx.get("conversation") or {}).get("customerName", "Cliente")
    intent = detect_intent(ctx)
    customer_msgs = [m.get("content", "") for m in ctx.get("messages", []) if m.get("sender") == "customer"]
    topics = "\n".join(f"• {m}" for m in customer_msgs) or f"• {ctx.get('lastCustomerMessage') or 'Sem mensagens'}"
    customer = ctx.get("customer") or {}
    conv = ctx.get("conversation") or {}

    return (
        f"**Resumo — {name}**\n\n"
        f"**Situação:** {SENTIMENT.get(intent, intent)}\n\n"
        f"**Demandas:**\n{topics}\n\n"
        f"**Canal:** {conv.get('channel', '—')} | **Protocolo:** {conv.get('protocol', '—')}\n\n"
        f"**Perfil:** {customer.get('company', '—')} | {customer.get('ordersCount', 0)} pedidos | "
        f"{_format_currency(float(customer.get('totalSpent') or 0))}\n\n"
        f"**Recomendação:** Responder com objetividade e próximo passo concreto."
    )


def suggest_replies(ctx: dict, message: str | None = None) -> str:
    text = _combined_text(ctx, message)
    intent = detect_intent(ctx, message)
    name = _first_name(ctx)

    if intent == "quote":
        product = _find_product(ctx, text) or (ctx.get("products") or [{}])[0]
        qty = _extract_quantity(text) or 50
        price = float(product.get("price") or 0)
        discount = 0.08 if qty >= 20 else 0.05 if qty >= 10 else 0
        total = price * qty * (1 - discount)
        return (
            f"**3 sugestões para {name or 'o cliente'}:**\n\n"
            f"1️⃣ \"Olá{', ' + name if name else ''}! Temos **{product.get('stock', 0)} un.** do "
            f"{product.get('name')} ({product.get('code')}). Para {qty} unidades: "
            f"**{_format_currency(total)}**{' (desconto volume)' if discount else ''}. Envio proposta em 2h?\"\n\n"
            f"2️⃣ \"Verifiquei estoque e prazo: entrega em 5 dias úteis. Prefere à vista ou parcelado?\"\n\n"
            f"3️⃣ \"Reservei as unidades por 48h. Confirma CNPJ e endereço para formalizar o orçamento.\""
        )

    if intent == "tracking":
        order = _find_order(ctx, text)
        num = (order or {}).get("number", "—")
        status = (order or {}).get("status", "processing")
        status_pt = STATUS_LABELS.get(status, status)
        total = float((order or {}).get("total") or 0)
        return (
            f"**3 sugestões para {name or 'o cliente'}:**\n\n"
            f"1️⃣ \"Olá{', ' + name if name else ''}! Pedido **{num}** ({_format_currency(total)}) "
            f"está **{status_pt}**. Envio rastreio agora.\"\n\n"
            f"2️⃣ \"Acionei logística para priorizar seu pedido. Retorno em 30 min.\"\n\n"
            f"3️⃣ \"Peço desculpas pela espera. Escalamos internamente — confirmação ainda hoje.\""
        )

    if intent == "stock":
        product = _find_product(ctx, text) or (ctx.get("products") or [{}])[0]
        return (
            f"**3 sugestões:**\n\n"
            f"1️⃣ \"Sim! **{product.get('stock', 0)} un.** do {product.get('name')} ({product.get('code')}) "
            f"por {_format_currency(float(product.get('price') or 0))}. Reservo para você?\"\n\n"
            f"2️⃣ \"Temos estoque. Acima de 10 unidades, desconto de 5–8%. Envio tabela?\"\n\n"
            f"3️⃣ \"Disponível agora. Entrega em 3–5 dias úteis. Qual quantidade precisa?\""
        )

    if intent == "sales_metrics":
        reply = handle_sales_metrics(ctx, message)
        if reply:
            return reply

    protocol = (ctx.get("conversation") or {}).get("protocol", "PD-URG")
    fallbacks = {
        "urgent_support": (
            f"**3 sugestões (URGENTE):**\n\n"
            f"1️⃣ \"Recebi sua solicitação. Retorno em 15 min. Protocolo: {protocol}.\"\n\n"
            f"2️⃣ \"Prioridade máxima — supervisor notificado.\"\n\n"
            f"3️⃣ \"Entendo a urgência. Volto com solução concreta em instantes.\""
        ),
        "technical_visit": (
            f"**3 sugestões:**\n\n"
            f"1️⃣ \"Agendo visita — terça 14h ou quinta 10h. Qual prefere?\"\n\n"
            f"2️⃣ \"Informe endereço em {(ctx.get('customer') or {}).get('city', 'sua região')} e equipamentos.\"\n\n"
            f"3️⃣ \"Visita técnica — manutenção ou instalação nova?\""
        ),
        "proposal_followup": (
            "**3 sugestões:**\n\n"
            "1️⃣ \"Vi que está analisando a proposta. Posso esclarecer algum item?\"\n\n"
            "2️⃣ \"Ajustamos condições de pagamento se precisar.\"\n\n"
            "3️⃣ \"Qualquer dúvida sobre prazo, me avise.\""
        ),
        "closed_positive": (
            "**3 sugestões:**\n\n"
            "1️⃣ \"Ficamos felizes em ajudar! Avalie nosso atendimento de 1 a 5.\"\n\n"
            "2️⃣ \"Obrigado pela confiança! Estamos à disposição.\"\n\n"
            "3️⃣ \"Foi um prazer atender você. Até a próxima!\""
        ),
    }
    if intent in fallbacks:
        return fallbacks[intent]

    return (
        f"**3 sugestões:**\n\n"
        f"1️⃣ \"Olá{', ' + name if name else ''}! Obrigado pelo contato. Como posso ajudar?\"\n\n"
        f"2️⃣ \"Recebi sua mensagem e já estou verificando. Retorno em instantes.\"\n\n"
        f"3️⃣ \"Para agilizar: confirma produto, pedido ou assunto principal?\""
    )


def _is_sales_metrics_question(norm: str) -> bool:
    return bool(re.search(
        r"vendas?|vendemos|vendido|faturamento|receita|retenc|retido|metricas?|"
        r"funil|pipeline|ticket|conversao|volume bruto|quanto vend|quantas vend|"
        r"pedidos confirmados|relatorio de vend",
        norm,
    ))


def handle_sales_metrics(ctx: dict, message: str | None = None) -> str | None:
    norm = _normalize(message or ctx.get("userMessage") or "")
    if not _is_sales_metrics_question(norm):
        return None

    metrics = ctx.get("salesMetrics") or {}
    if not metrics:
        return (
            "Métricas de venda indisponíveis no momento. "
            "Verifique os pedidos no Mercos ou abra a página Relatórios."
        )

    qtd = metrics.get("quantidadeVendas", 0)
    valor = float(metrics.get("valorTotalVendido") or 0)
    retido = float(metrics.get("valorRetido") or 0)
    pipeline = float(metrics.get("valorPipeline") or 0)
    bruto = float(metrics.get("volumeBruto") or 0)
    ticket = float(metrics.get("ticketMedio") or 0)
    concluidas = metrics.get("quantidadeConcluidas", 0)
    entregues = metrics.get("quantidadeEntregues", 0)
    taxa_ret = metrics.get("taxaRetencao", 0)
    taxa_conv = metrics.get("taxaConversao", 0)
    oportunidades = metrics.get("pipelineNegocios", 0)
    pipeline_valor = float(metrics.get("pipelineValor") or 0)

    lines = [
        "Métricas de venda",
        "",
        "Resumo comercial",
        f"Vendas confirmadas: {qtd}",
        f"Valor vendido: {_format_currency(valor)}",
        f"Enviadas ou entregues: {concluidas}",
        f"Entregues: {entregues}",
        f"Receita retida: {_format_currency(retido)} ({taxa_ret}% do bruto)",
        f"Pipeline em aberto: {_format_currency(pipeline)}",
        f"Volume bruto: {_format_currency(bruto)}",
        f"Ticket médio: {_format_currency(ticket)}",
        f"Oportunidades no funil: {oportunidades} ({_format_currency(pipeline_valor)})",
        f"Conversão contato para entrega: {taxa_conv}%",
    ]

    funil = metrics.get("funil") or []
    if funil:
        lines.extend(["", "Funil de vendas"])
        for step in funil[:6]:
            val = float(step.get("valor") or 0)
            valor_txt = _format_currency(val) if val > 0 else "sem valor monetário"
            lines.append(
                f"{step.get('label')}: {step.get('quantidade', 0)} unidades, "
                f"{valor_txt}, {step.get('conversaoPct', 0)}% do topo"
            )

    lines.extend([
        "",
        "Detalhes completos na página Relatórios.",
        "",
        "Sugestão de resposta:",
        f"Temos {qtd} pedidos confirmados totalizando {_format_currency(valor)}. "
        f"{entregues} já foram entregues, com {_format_currency(retido)} de receita concretizada.",
    ])

    return "\n".join(lines)


def handle_stock_and_quote(ctx: dict, message: str) -> str | None:
    text = _combined_text(ctx, message)
    if not re.search(r"estoque|preco|orcamento|produto|catalogo", _normalize(message)):
        if not _find_product(ctx, text):
            return None

    product = _find_product(ctx, text) or (ctx.get("products") or [None])[0]
    if not product:
        return "📦 Nenhum produto no catálogo. Sincronize produtos via Mercos."

    qty = _extract_quantity(text) or 1
    price = float(product.get("price") or 0)
    stock = int(product.get("stock") or 0)
    discount = 0.08 if qty >= 20 else 0.05 if qty >= 10 else 0
    final_total = price * qty * (1 - discount)

    stock_ok = "✅ Pode reservar e enviar proposta agora." if stock >= qty else "⚠️ Estoque parcial — sugira entrega fracionada."
    return (
        f"📦 **Consulta ao catálogo**\n\n"
        f"**{product.get('name')}** ({product.get('code')})\n"
        f"• Estoque: **{stock} unidades**\n"
        f"• Unitário: {_format_currency(price)}\n"
        f"• Qtd. solicitada: {qty}\n"
        f"• Total: **{_format_currency(final_total)}**"
        f"{f' (−{discount * 100:.0f}% volume)' if discount else ''}\n\n"
        f"{stock_ok}"
    )


def handle_order_tracking(ctx: dict, message: str) -> str | None:
    if not re.search(r"pedido|entrega|rastreio|chega|\d{3,}", _normalize(_combined_text(ctx, message))):
        return None

    order = _find_order(ctx, message)
    if not order:
        return "📍 Nenhum pedido encontrado para este cliente. Peça o número do pedido ou sincronize via Mercos."

    num = order.get("number", "—")
    status = order.get("status", "pending")
    customer = ctx.get("customer") or {}
    conv = ctx.get("conversation") or {}
    return (
        f"📍 **Rastreamento — {num}**\n\n"
        f"• Cliente: {customer.get('name') or conv.get('customerName', '—')}\n"
        f"• Status: {STATUS_LABELS.get(status, status)}\n"
        f"• Valor: {_format_currency(float(order.get('total') or 0))}\n"
        f"• Itens: {order.get('items', 1)}\n\n"
        f"💡 Envie o status proativamente e ofereça prioridade se houver urgência."
    )


def generate_reply(message: str, ctx: dict, mode: str = "copilot") -> str:
    norm = _normalize(message)

    if re.search(r"resum|sumari", norm):
        return summarize_conversation(ctx)
    if re.search(r"sugest|sugira|resposta", norm):
        return suggest_replies(ctx, message)
    if re.search(r"transcri|audio", norm):
        intent = detect_intent(ctx)
        return (
            f"🎙️ **Transcrição simulada** (última mensagem do cliente):\n\n"
            f"\"{ctx.get('lastCustomerMessage') or '—'}\"\n\n"
            f"**Análise IA:**\n• Tom: {SENTIMENT.get(intent, intent)}\n"
            f"• Urgência: {'Alta' if intent in ('urgent_support', 'tracking') else 'Média'}"
        )
    if re.search(r"texto magic|tom de voz|profissional", norm):
        name = _first_name(ctx) or "cliente"
        company = (ctx.get("customer") or {}).get("company", "sua empresa")
        return (
            f"✍️ **Texto sugerido (tom PulseDesk):**\n\n"
            f"Prezado(a) {name},\n\nAgradecemos o contato e a confiança na {company}. "
            f"Analisamos sua solicitação e retornaremos com a melhor solução.\n\n"
            f"Atenciosamente,\nEquipe PulseDesk"
        )

    if re.search(r"quem e|qual cliente|dados do cliente", norm):
        customer = ctx.get("customer")
        if customer:
            return (
                f"👤 **{customer.get('name')}**\n\n"
                f"• Empresa: {customer.get('company')}\n"
                f"• {customer.get('city')}\n"
                f"• {customer.get('ordersCount', 0)} pedidos · "
                f"{_format_currency(float(customer.get('totalSpent') or 0))}\n"
                f"• Canal: {(ctx.get('conversation') or {}).get('channel', '—')}"
            )

    if re.search(r"protocolo", norm):
        protocol = (ctx.get("conversation") or {}).get("protocol", "N/A")
        return f"Protocolo desta conversa: **{protocol}**"

    if re.search(r"sentimento|tom|humor|urgencia", norm):
        intent = detect_intent(ctx)
        priority = "high" if intent in ("urgent_support", "tracking", "quote") else "medium"
        return (
            f"**Análise da conversa:**\n• Tom: {SENTIMENT.get(intent, intent)}\n"
            f"• Prioridade: {priority}\n• Intent: {intent}"
        )

    if re.search(r"garantia|troca|devolu", norm):
        return (
            "**Garantia e trocas (política):**\n"
            "• Garantia: 12 meses contra defeito de fabricação\n"
            "• Troca/devolução: 7 dias corridos, produto lacrado + NF\n"
            "• Logística reversa: por conta do cliente, salvo defeito\n\n"
            '**Mensagem sugerida:** "Posso iniciar a análise — me envie a NF e fotos do produto?"'
        )

    if re.search(r"pagamento|parcel|boleto|pix", norm):
        return (
            "**Formas de pagamento:**\n"
            "• PIX ou boleto à vista\n"
            "• 3x sem juros (pedidos > R$ 3.000)\n"
            "• 6x com análise de crédito\n\n"
            '**Mensagem sugerida:** "Qual forma prefere? Envio link de pagamento ou boleto agora."'
        )

    sales_reply = handle_sales_metrics(ctx, message)
    if sales_reply:
        return sales_reply

    stock_reply = handle_stock_and_quote(ctx, message)
    if stock_reply:
        return stock_reply

    order_reply = handle_order_tracking(ctx, message)
    if order_reply:
        return order_reply

    if re.search(r"estoque|produto|catalogo", norm):
        lines = [
            f"• **{p.get('code')}** — {p.get('name')}: {_format_currency(float(p.get('price') or 0))} ({p.get('stock', 0)} un.)"
            for p in (ctx.get("products") or [])[:8]
        ]
        if lines:
            return f"📋 **Catálogo:**\n\n" + "\n".join(lines) + "\n\nInforme código ou nome para orçamento."
        return "📋 Catálogo vazio — sincronize produtos via Mercos."

    if mode == "agent" and re.search(r"\b(oi|ola|bom dia|boa tarde|boa noite)\b", norm):
        return (
            "Olá! Sou o Copiloto IA do PulseDesk. Consulto produtos, estoque, pedidos e "
            "histórico de clientes em tempo real. Peça resumos, sugestões ou orçamentos."
        )

    contextual = _contextual_copilot_reply(ctx, message)
    if contextual:
        return contextual

    return suggest_replies(ctx, message)


def _contextual_copilot_reply(ctx: dict, message: str) -> str | None:
    conv = ctx.get("conversation")
    customer = ctx.get("customer")
    if not conv and not customer:
        return None

    intent = detect_intent(ctx, message)
    name = _first_name(ctx) or (conv or {}).get("customerName", "Cliente")
    last = ctx.get("lastCustomerMessage") or (conv or {}).get("lastMessage") or ""
    suggestion = generate_suggestion(ctx)

    lines = [
        f"**Análise — {name}**",
        f"• {SENTIMENT.get(intent, intent)}",
    ]
    if conv:
        lines.append(f"• Canal **{conv.get('channel')}** | Status **{conv.get('status')}** | Protocolo **{conv.get('protocol') or '—'}**")
    if customer:
        lines.append(
            f"• Cliente: **{customer.get('ordersCount', 0)} pedidos** · "
            f"{_format_currency(float(customer.get('totalSpent') or 0))} · {customer.get('city') or '—'}"
        )
    if last:
        lines.append(f"• Última mensagem: _\"{last[:150]}{'…' if len(last) > 150 else ''}\"_")

    orders = ctx.get("orders") or []
    if orders:
        o = orders[0]
        lines.append(f"• Pedido recente: **{o.get('number')}** ({o.get('status')}) — {_format_currency(float(o.get('total') or 0))}")

    product = _find_product(ctx, _combined_text(ctx, message))
    if product:
        lines.append(
            f"• Produto relacionado: **{product.get('name')}** ({product.get('code')}) — "
            f"{_format_currency(float(product.get('price') or 0))}, estoque **{product.get('stock', 0)}**"
        )

    lines.extend([
        "",
        f"**Insight:** {suggestion['insight']}",
        "",
        "**Mensagem sugerida (copiar e enviar):**",
        f"\"{suggestion['suggestion']}\"",
        "",
        "_Comandos: `resuma conversa` · `sugira resposta` · `status pedido` · `quantas vendas` · `catálogo`_",
    ])
    return "\n".join(lines)


def generate_suggestion(ctx: dict) -> dict:
    intent = detect_intent(ctx)
    name = _first_name(ctx)
    last = ctx.get("lastCustomerMessage") or (ctx.get("conversation") or {}).get("lastMessage") or ""
    protocol = (ctx.get("conversation") or {}).get("protocol", "PD-URG")

    fallbacks = {
        "quote": {
            "insight": "Intenção de compra detectada — montar orçamento.",
            "suggestion": f"Olá {name}! Preparo o orçamento em até 2h. Confirma produto e quantidade?",
            "priority": "high",
        },
        "tracking": {
            "insight": "Cliente aguarda status de entrega.",
            "suggestion": "Consultei seu pedido — envio status e rastreio agora.",
            "priority": "high",
        },
        "stock": {
            "insight": "Consulta de estoque.",
            "suggestion": "Temos unidades disponíveis. Deseja reserva ou tabela para volume?",
            "priority": "medium",
        },
        "urgent_support": {
            "insight": "Atendimento urgente — escalar imediatamente.",
            "suggestion": f"Recebi sua urgência. Retorno em 15 min. Protocolo: {protocol}.",
            "priority": "high",
        },
        "warranty": {
            "insight": "Dúvida sobre garantia ou troca.",
            "suggestion": "Nossa garantia é de 12 meses. Pode me enviar a NF e fotos do produto para agilizar a análise?",
            "priority": "medium",
        },
        "payment": {
            "insight": "Cliente quer saber formas de pagamento.",
            "suggestion": "Aceitamos PIX, boleto e parcelamento em 3x sem juros (pedidos acima de R$ 3.000). Qual prefere?",
            "priority": "medium",
        },
        "sales_metrics": {
            "insight": "Consulta sobre métricas de venda — use os números de Relatórios.",
            "suggestion": (
                f"Temos {(ctx.get('salesMetrics') or {}).get('quantidadeVendas', 0)} vendas confirmadas. "
                "Posso detalhar funil, receita retida ou pipeline?"
            ),
            "priority": "medium",
        },
        "general": {
            "insight": f"Conversa via {(ctx.get('conversation') or {}).get('channel', 'canal')}: \"{last[:50]}...\"",
            "suggestion": f"Olá {name}! Obrigado pelo contato. Como posso ajudá-lo hoje?",
            "priority": "low",
        },
    }
    return fallbacks.get(intent, fallbacks["general"])
