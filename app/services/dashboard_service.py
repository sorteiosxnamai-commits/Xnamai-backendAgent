from collections import defaultdict
from datetime import datetime, timedelta

from app.repositories.conversa_repository import ConversaRepository
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.mensagem_repository import MensagemRepository
from app.services.supabase_service import supabase


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _day_key(dt: datetime) -> str:
    return dt.strftime("%d/%m")


def _contar_por_dia(rows: list[dict], date_field: str, days: int = 7) -> dict[str, int]:
    hoje = datetime.utcnow().date()
    inicio = hoje - timedelta(days=days - 1)
    buckets: dict[str, int] = defaultdict(int)

    for row in rows:
        dt = _parse_date(row.get(date_field))
        if not dt:
            continue
        dia = dt.date()
        if inicio <= dia <= hoje:
            buckets[_day_key(dt)] += 1

    return buckets


def _labels_ultimos_dias(days: int = 7) -> list[str]:
    hoje = datetime.utcnow().date()
    return [
        _day_key(datetime.combine(hoje - timedelta(days=i), datetime.min.time()))
        for i in range(days - 1, -1, -1)
    ]


def _formatar_tempo_resposta(minutos: float) -> str:
    if minutos <= 0:
        return "—"
    if minutos < 1:
        return f"{int(minutos * 60)}s"
    mins = int(minutos)
    segs = int((minutos - mins) * 60)
    if segs:
        return f"{mins}m {segs}s"
    return f"{mins}min"


def _calcular_tempo_resposta_medio(mensagens: list[dict]) -> str:
    por_conversa: dict[str, list[dict]] = defaultdict(list)
    for msg in mensagens:
        por_conversa[str(msg.get("conversa_id"))].append(msg)

    deltas: list[float] = []
    for msgs in por_conversa.values():
        ordenadas = sorted(msgs, key=lambda m: m.get("created_at") or "")
        for i, msg in enumerate(ordenadas):
            if msg.get("sender") != "customer":
                continue
            for prox in ordenadas[i + 1:]:
                if prox.get("sender") in {"agent", "ai"}:
                    t1 = _parse_date(msg.get("created_at"))
                    t2 = _parse_date(prox.get("created_at"))
                    if t1 and t2 and t2 > t1:
                        deltas.append((t2 - t1).total_seconds() / 60)
                    break

    if not deltas:
        return "—"
    return _formatar_tempo_resposta(sum(deltas) / len(deltas))


class DashboardService:

    def __init__(self):
        self.repository = DashboardRepository()
        self.conversas = ConversaRepository()
        self.mensagens = MensagemRepository()

    def resumo(self):
        return {
            "clientes": self.repository.contar_clientes(),
            "produtos": self.repository.contar_produtos(),
            "pedidos": self.repository.contar_pedidos(),
        }

    def _contar_conversas_por_status(self) -> dict[str, int]:
        try:
            rows = self.conversas.listar()
        except Exception:
            return {"active": 0, "waiting": 0, "closed": 0}

        counts = {"active": 0, "waiting": 0, "closed": 0}
        for row in rows:
            status = row.get("status") or "active"
            if status in counts:
                counts[status] += 1
        return counts

    def _carregar_linhas(self, tabela: str, campo_data: str = "created_at") -> list[dict]:
        try:
            resposta = supabase.table(tabela).select(campo_data).execute()
            return resposta.data or []
        except Exception:
            return []

    def _stats_mensagens(self) -> dict:
        try:
            resposta = supabase.table("mensagens").select("sender,conversa_id,created_at").execute()
            rows = resposta.data or []
        except Exception:
            return {"total": 0, "ai": 0, "bot_pct": 0, "avg_response": "—"}

        total = len(rows)
        ai = sum(1 for r in rows if r.get("sender") == "ai")
        bot_pct = round((ai / total) * 100) if total else 0
        return {
            "total": total,
            "ai": ai,
            "bot_pct": bot_pct,
            "avg_response": _calcular_tempo_resposta_medio(rows),
        }

    def montar(self) -> dict:
        status = self._contar_conversas_por_status()
        msg_stats = self._stats_mensagens()

        clientes_rows = self._carregar_linhas("clientes")
        pedidos_rows = self._carregar_linhas("pedidos")
        conversas_rows = self._carregar_linhas("conversas", "last_message_at")
        if not conversas_rows:
            conversas_rows = self._carregar_linhas("conversas", "created_at")

        clientes_dia = _contar_por_dia(clientes_rows, "created_at")
        pedidos_dia = _contar_por_dia(pedidos_rows, "created_at")
        conversas_dia = _contar_por_dia(conversas_rows, "last_message_at")
        if not any(conversas_dia.values()):
            conversas_dia = _contar_por_dia(conversas_rows, "created_at")

        labels = _labels_ultimos_dias()
        chart = [
            {
                "name": label,
                "conversas": conversas_dia.get(label, 0),
                "pedidos": pedidos_dia.get(label, 0),
                "clientes": clientes_dia.get(label, 0),
            }
            for label in labels
        ]

        total_conversas = sum(status.values())
        closed = status["closed"]
        bot_pct = msg_stats["bot_pct"]

        return {
            "stats": {
                "activeConversations": status["active"],
                "closedConversations": closed,
                "waitingQueue": status["waiting"],
                "avgResponseTime": msg_stats["avg_response"],
                "nps": min(100, 50 + closed * 5 + bot_pct // 2) if total_conversas else 0,
                "csat": round(3.5 + min(1.5, (closed / max(total_conversas, 1)) * 1.5 + bot_pct / 200), 1) if total_conversas else 0,
                "aiOnline": True,
                "campaignsSent": 0,
                "botResolved": bot_pct,
            },
            "conversationsChart": chart,
            "ordersChart": chart,
            "responseTimeChart": chart,
            "_meta": {
                "clientes": self.repository.contar_clientes() or 0,
                "produtos": self.repository.contar_produtos() or 0,
                "pedidos": self.repository.contar_pedidos() or 0,
                "conversas": total_conversas,
                "mensagens": msg_stats["total"],
            },
        }
