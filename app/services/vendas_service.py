from collections import defaultdict
from datetime import datetime, timedelta

from app.repositories.conversa_repository import ConversaRepository
from app.repositories.platform_repository import PlatformRepository
from app.services.pulsedesk_adapter import listar_pedidos


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _sum_total(items: list[dict]) -> float:
    return sum(_safe_float(i.get("total")) for i in items)


class VendasService:

    def __init__(self):
        self.conversas = ConversaRepository()
        self.platform = PlatformRepository()

    def _load_pedidos(self) -> list[dict]:
        try:
            resp = listar_pedidos(page=1, page_size=500)
            return resp.get("data") or []
        except Exception:
            return []

    def _load_funil(self) -> list[dict]:
        try:
            estagios = self.platform.list_estagios()
            negocios = self.platform.list_negocios()
        except Exception:
            return []

        por_estagio: dict[str, list[dict]] = defaultdict(list)
        for negocio in negocios:
            por_estagio[str(negocio.get("stage_id"))].append(negocio)

        return [
            {
                "id": estagio["id"],
                "name": estagio["name"],
                "sortOrder": int(estagio.get("sort_order") or 0),
                "dealsCount": len(por_estagio.get(str(estagio["id"]), [])),
                "dealsValue": sum(_safe_float(n.get("value")) for n in por_estagio.get(str(estagio["id"]), [])),
            }
            for estagio in sorted(estagios, key=lambda e: int(e.get("sort_order") or 0))
        ]

    def _vendas_por_dia(self, pedidos: list[dict], days: int = 30) -> list[dict]:
        hoje = datetime.utcnow().date()
        inicio = hoje - timedelta(days=days - 1)
        buckets: dict[str, dict] = {}

        for i in range(days):
            dia = hoje - timedelta(days=days - 1 - i)
            key = dia.strftime("%d/%m")
            buckets[key] = {"name": key, "vendas": 0, "valor": 0.0}

        for pedido in pedidos:
            if pedido.get("status") == "cancelled":
                continue
            dt = _parse_date(pedido.get("createdAt"))
            if not dt or dt.date() < inicio or dt.date() > hoje:
                continue
            key = dt.strftime("%d/%m")
            if key in buckets:
                buckets[key]["vendas"] += 1
                buckets[key]["valor"] += _safe_float(pedido.get("total"))

        return list(buckets.values())

    def metricas(self) -> dict:
        pedidos = self._load_pedidos()
        funil_estagios = self._load_funil()

        by_status: dict[str, list[dict]] = defaultdict(list)
        for pedido in pedidos:
            by_status[pedido.get("status") or "pending"].append(pedido)

        delivered = by_status["delivered"]
        shipped = by_status["shipped"]
        processing = by_status["processing"]
        pending = by_status["pending"]
        cancelled = by_status["cancelled"]

        vendas_fechadas = delivered + shipped
        em_processamento = pending + processing
        pedidos_validos = [p for p in pedidos if p.get("status") != "cancelled"]

        volume_bruto = _sum_total(pedidos_validos)
        valor_retido = _sum_total(delivered)
        valor_total_vendido = _sum_total(vendas_fechadas)
        valor_pipeline = _sum_total(em_processamento)
        valor_cancelado = _sum_total(cancelled)

        quantidade_vendas = len(vendas_fechadas) if vendas_fechadas else len(pedidos_validos)
        ticket_medio = valor_total_vendido / quantidade_vendas if quantidade_vendas else 0

        try:
            conversas = self.conversas.listar()
            conversas_ativas = sum(1 for c in conversas if c.get("status") != "closed")
        except Exception:
            conversas_ativas = 0

        pipeline_valor = sum(s.get("dealsValue", 0) for s in funil_estagios)
        pipeline_qtd = sum(s.get("dealsCount", 0) for s in funil_estagios)

        # Funil estilo Mercado Livre: topo amplo → base = receita retida
        etapas_funil = []
        if funil_estagios:
            for estagio in funil_estagios:
                etapas_funil.append({
                    "id": estagio["id"],
                    "label": estagio["name"],
                    "quantidade": estagio["dealsCount"],
                    "valor": round(estagio["dealsValue"], 2),
                    "tipo": "funil",
                })

        etapas_funil.extend([
            {
                "id": "pedidos-abertos",
                "label": "Pedidos em aberto",
                "quantidade": len(em_processamento),
                "valor": round(valor_pipeline, 2),
                "tipo": "pedido",
            },
            {
                "id": "pedidos-enviados",
                "label": "Enviados / em trânsito",
                "quantidade": len(shipped),
                "valor": round(_sum_total(shipped), 2),
                "tipo": "pedido",
            },
            {
                "id": "pedidos-entregues",
                "label": "Entregues (receita retida)",
                "quantidade": len(delivered),
                "valor": round(valor_retido, 2),
                "tipo": "receita",
            },
        ])

        if conversas_ativas and etapas_funil:
            etapas_funil.insert(0, {
                "id": "conversas",
                "label": "Contatos / Conversas",
                "quantidade": conversas_ativas,
                "valor": round(pipeline_valor, 2),
                "tipo": "topo",
            })

        topo_qtd = etapas_funil[0]["quantidade"] if etapas_funil else max(quantidade_vendas, 1)
        for etapa in etapas_funil:
            etapa["conversaoPct"] = round((etapa["quantidade"] / topo_qtd) * 100, 1) if topo_qtd else 0

        taxa_conversao = round((quantidade_vendas / topo_qtd) * 100, 1) if topo_qtd else 0
        taxa_retencao = round((valor_retido / volume_bruto) * 100, 1) if volume_bruto else 0

        return {
            "quantidadeVendas": quantidade_vendas,
            "valorTotalVendido": round(valor_total_vendido, 2),
            "volumeBruto": round(volume_bruto, 2),
            "valorRetido": round(valor_retido, 2),
            "valorPipeline": round(valor_pipeline, 2),
            "valorCancelado": round(valor_cancelado, 2),
            "ticketMedio": round(ticket_medio, 2),
            "taxaConversao": taxa_conversao,
            "taxaRetencao": taxa_retencao,
            "pipelineNegocios": pipeline_qtd,
            "pipelineValor": round(pipeline_valor, 2),
            "funil": etapas_funil,
            "porStatus": [
                {
                    "status": "delivered",
                    "label": "Entregues",
                    "quantidade": len(delivered),
                    "valor": round(_sum_total(delivered), 2),
                },
                {
                    "status": "shipped",
                    "label": "Enviados",
                    "quantidade": len(shipped),
                    "valor": round(_sum_total(shipped), 2),
                },
                {
                    "status": "processing",
                    "label": "Processando",
                    "quantidade": len(processing),
                    "valor": round(_sum_total(processing), 2),
                },
                {
                    "status": "pending",
                    "label": "Pendentes",
                    "quantidade": len(pending),
                    "valor": round(_sum_total(pending), 2),
                },
                {
                    "status": "cancelled",
                    "label": "Cancelados",
                    "valor": round(valor_cancelado, 2),
                    "quantidade": len(cancelled),
                },
            ],
            "vendasPorDia": self._vendas_por_dia(pedidos),
        }


vendas_service = VendasService()
