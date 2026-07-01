from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import verificar_token
from app.services.pulsedesk_adapter import (
    dashboard_data,
    listar_clientes,
    listar_produtos,
    listar_pedidos,
    obter_cliente,
    mercos_status,
    mercos_logs,
)
from app.services.cliente_service import ClienteService
from app.services.produto_service import ProdutoService
from app.services.pedido_service import PedidoService

router = APIRouter()

cliente_service = ClienteService()
produto_service = ProdutoService()
pedido_service = PedidoService()


class MercosSyncRequest(BaseModel):
    type: str = "all"


@router.get("/dashboard")
def get_dashboard(autorizado=Depends(verificar_token)):
    return dashboard_data()


@router.get("/clientes")
def get_clientes(
    page: int = 1,
    pageSize: int = 10,
    search: str = "",
    autorizado=Depends(verificar_token),
):
    return listar_clientes(page=page, page_size=pageSize, search=search)


@router.get("/clientes/{cliente_id}")
def get_cliente(cliente_id: str, autorizado=Depends(verificar_token)):
    cliente = obter_cliente(cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


@router.get("/produtos")
def get_produtos(
    page: int = 1,
    pageSize: int = 10,
    search: str = "",
    category: str | None = None,
    autorizado=Depends(verificar_token),
):
    return listar_produtos(page=page, page_size=pageSize, search=search, category=category)


@router.get("/pedidos")
def get_pedidos(
    page: int = 1,
    pageSize: int = 10,
    search: str = "",
    status: str | None = None,
    autorizado=Depends(verificar_token),
):
    return listar_pedidos(page=page, page_size=pageSize, search=search, status=status)


@router.get("/mercos/status")
def get_mercos_status(autorizado=Depends(verificar_token)):
    return mercos_status()


@router.get("/mercos/logs")
def get_mercos_logs(autorizado=Depends(verificar_token)):
    return mercos_logs()


@router.post("/mercos/sincronizar")
def sincronizar_mercos(
    body: MercosSyncRequest,
    autorizado=Depends(verificar_token),
):
    tipo = body.type

    try:
        if tipo == "customers":
            resultado = cliente_service.sincronizar()
            qtd = resultado.get("clientes_sincronizados", 0)
            return {"success": True, "message": f"Clientes sincronizados: {qtd}"}

        if tipo == "products":
            resultado = produto_service.sincronizar()
            qtd = resultado.get("produtos_sincronizados", 0)
            return {"success": True, "message": f"Produtos sincronizados: {qtd}"}

        if tipo == "orders":
            resultado = pedido_service.sincronizar()
            qtd = resultado.get("pedidos_sincronizados", 0)
            return {"success": True, "message": f"Pedidos sincronizados: {qtd}"}

        c = cliente_service.sincronizar()
        p = produto_service.sincronizar()
        o = pedido_service.sincronizar()
        return {
            "success": True,
            "message": (
                f"Sincronização concluída — "
                f"clientes: {c.get('clientes_sincronizados', 0)}, "
                f"produtos: {p.get('produtos_sincronizados', 0)}, "
                f"pedidos: {o.get('pedidos_sincronizados', 0)}"
            ),
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Falha ao sincronizar com Mercos: {exc}",
        ) from exc


@router.post("/auth/logout")
def logout(autorizado=Depends(verificar_token)):
    return {"success": True}
