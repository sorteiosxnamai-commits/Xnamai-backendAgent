from datetime import datetime, timedelta
import math

from app.services.supabase_service import supabase
from app.repositories.dashboard_repository import DashboardRepository


def _paginate(items: list, page: int, page_size: int) -> dict:
    total = len(items)
    total_pages = max(1, math.ceil(total / page_size)) if page_size else 1
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": items[start:end],
        "total": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": total_pages,
    }


def _map_cliente(row: dict) -> dict:
    nome = row.get("nome") or row.get("razao_social") or "Cliente"
    return {
        "id": str(row.get("mercos_id") or row.get("id") or nome),
        "name": nome,
        "email": row.get("email") or "",
        "phone": row.get("telefone") or row.get("celular") or "",
        "company": row.get("razao_social") or nome,
        "city": row.get("cidade") or "",
        "ordersCount": 0,
        "totalSpent": 0.0,
        "lastContact": row.get("ultima_alteracao") or datetime.utcnow().isoformat(),
        "synced": True,
    }


def _map_produto(row: dict) -> dict:
    return {
        "id": str(row.get("mercos_id") or row.get("id") or row.get("codigo") or ""),
        "code": row.get("codigo") or "",
        "name": row.get("nome") or "",
        "price": float(row.get("preco_tabela") or 0),
        "stock": int(row.get("saldo_estoque") or 0),
        "category": row.get("unidade") or "Geral",
        "synced": True,
    }


def _map_pedido(row: dict, clientes_por_id: dict | None = None) -> dict:
    status_map = {
        "1": "pending",
        "2": "processing",
        "3": "shipped",
        "4": "delivered",
        "5": "cancelled",
        "pendente": "pending",
        "processando": "processing",
        "enviado": "shipped",
        "entregue": "delivered",
        "cancelado": "cancelled",
    }
    raw_status = str(row.get("situacao") or row.get("status") or "1").lower()
    cliente_id = row.get("cliente_mercos_id") or row.get("cliente_id")
    cliente_nome = ""
    if clientes_por_id and cliente_id is not None:
        cliente = clientes_por_id.get(str(cliente_id), {})
        cliente_nome = cliente.get("nome") or cliente.get("razao_social") or ""

    return {
        "id": str(row.get("mercos_id") or row.get("id") or ""),
        "number": str(row.get("numero") or row.get("mercos_id") or row.get("id") or ""),
        "customerId": str(cliente_id or ""),
        "customerName": cliente_nome,
        "status": status_map.get(raw_status, "pending"),
        "total": float(row.get("valor_total") or row.get("total") or 0),
        "createdAt": row.get("created_at") or datetime.utcnow().isoformat(),
        "items": int(row.get("quantidade_itens") or row.get("itens") or 1),
    }


def _clientes_index() -> dict:
    resposta = supabase.table("clientes").select("mercos_id,nome,razao_social").execute()
    return {
        str(row.get("mercos_id")): row
        for row in (resposta.data or [])
        if row.get("mercos_id") is not None
    }


def listar_clientes(page: int = 1, page_size: int = 10, search: str = "") -> dict:
    resposta = supabase.table("clientes").select("*").execute()
    rows = resposta.data or []

    if search:
        termo = search.lower()
        rows = [
            row for row in rows
            if termo in (row.get("nome") or "").lower()
            or termo in (row.get("email") or "").lower()
            or termo in (row.get("telefone") or "").lower()
            or termo in (row.get("cidade") or "").lower()
            or termo in (row.get("razao_social") or "").lower()
        ]

    return _paginate([_map_cliente(row) for row in rows], page, page_size)


def obter_cliente(cliente_id: str) -> dict | None:
    resposta = supabase.table("clientes").select("*").eq("mercos_id", cliente_id).execute()
    rows = resposta.data or []
    if not rows:
        resposta = supabase.table("clientes").select("*").eq("id", cliente_id).execute()
        rows = resposta.data or []
    if not rows:
        return None

    cliente = _map_cliente(rows[0])
    cliente["orders"] = []
    cliente["purchasedProducts"] = []
    cliente["lastService"] = cliente["lastContact"]
    return cliente


def listar_produtos(page: int = 1, page_size: int = 10, search: str = "", category: str | None = None) -> dict:
    resposta = supabase.table("produtos").select("*").execute()
    rows = resposta.data or []

    if search:
        termo = search.lower()
        rows = [
            row for row in rows
            if termo in (row.get("nome") or "").lower()
            or termo in (row.get("codigo") or "").lower()
        ]

    if category:
        rows = [row for row in rows if (row.get("unidade") or "Geral") == category]

    return _paginate([_map_produto(row) for row in rows], page, page_size)


def listar_pedidos(page: int = 1, page_size: int = 10, search: str = "", status: str | None = None) -> dict:
    try:
        resposta = supabase.table("pedidos").select("*").execute()
        rows = resposta.data or []
    except Exception:
        rows = []

    clientes = _clientes_index()
    mapped = [_map_pedido(row, clientes) for row in rows]

    if search:
        termo = search.lower()
        mapped = [
            item for item in mapped
            if termo in item["number"].lower()
            or termo in item["customerName"].lower()
        ]

    if status:
        mapped = [item for item in mapped if item["status"] == status]

    return _paginate(mapped, page, page_size)


def dashboard_data() -> dict:
    repo = DashboardRepository()
    clientes = repo.contar_clientes() or 0
    produtos = repo.contar_produtos() or 0
    pedidos = repo.contar_pedidos() or 0

    chart = []
    for i in range(6, -1, -1):
        dia = datetime.utcnow() - timedelta(days=i)
        chart.append({
            "name": dia.strftime("%d/%m"),
            "conversas": 0,
            "pedidos": pedidos // 7 if pedidos else 0,
            "clientes": clientes // 7 if clientes else 0,
        })

    return {
        "stats": {
            "activeConversations": 0,
            "closedConversations": 0,
            "waitingQueue": 0,
            "avgResponseTime": "0min",
            "nps": 0,
            "csat": 0,
            "aiOnline": True,
            "campaignsSent": 0,
            "botResolved": 0,
        },
        "conversationsChart": chart,
        "ordersChart": chart,
        "responseTimeChart": [
            {"name": p["name"], "conversas": 0, "pedidos": p["pedidos"], "clientes": p["clientes"]}
            for p in chart
        ],
    }


def mercos_status() -> dict:
    repo = DashboardRepository()
    return {
        "connected": True,
        "lastSync": datetime.utcnow().isoformat(),
        "syncedProducts": repo.contar_produtos() or 0,
        "syncedCustomers": repo.contar_clientes() or 0,
        "syncedOrders": repo.contar_pedidos() or 0,
    }


def mercos_logs() -> list:
    return [
        {
            "id": "1",
            "type": "all",
            "status": "success",
            "message": "Integração Mercos ativa",
            "timestamp": datetime.utcnow().isoformat(),
        }
    ]
