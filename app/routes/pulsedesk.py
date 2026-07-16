from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import obter_workspace_context, verificar_token
from app.core.permissions import requer_permissao
from app.services.pulsedesk_adapter import (
    dashboard_data,
    listar_clientes,
    listar_produtos,
    listar_pedidos,
    obter_cliente,
)
from app.services.vendas_service import vendas_service
from app.services.rankings_service import rankings_service

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(workspace=Depends(obter_workspace_context)):
    return dashboard_data(workspace["workspaceId"])


@router.get("/vendas/metricas")
def get_vendas_metricas(
    workspace=Depends(obter_workspace_context),
    _: dict = Depends(requer_permissao("viewReports")),
):
    return vendas_service.metricas(workspace["workspaceId"])


@router.get("/vendas/rankings")
def get_vendas_rankings(
    limit: int = 10,
    workspace=Depends(obter_workspace_context),
    _: dict = Depends(requer_permissao("viewReports")),
):
    return rankings_service.rankings(workspace["workspaceId"], limit=limit)


@router.get("/clientes")
def get_clientes(
    page: int = 1,
    pageSize: int = 10,
    search: str = "",
    workspace=Depends(obter_workspace_context),
):
    return listar_clientes(workspace["workspaceId"], page=page, page_size=pageSize, search=search)


@router.get("/clientes/{cliente_id}")
def get_cliente(cliente_id: str, workspace=Depends(obter_workspace_context)):
    cliente = obter_cliente(workspace["workspaceId"], cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


@router.get("/produtos")
def get_produtos(
    page: int = 1,
    pageSize: int = 10,
    search: str = "",
    category: str | None = None,
    workspace=Depends(obter_workspace_context),
):
    return listar_produtos(workspace["workspaceId"], page=page, page_size=pageSize, search=search, category=category)


@router.get("/pedidos")
def get_pedidos(
    page: int = 1,
    pageSize: int = 10,
    search: str = "",
    status: str | None = None,
    workspace=Depends(obter_workspace_context),
):
    return listar_pedidos(workspace["workspaceId"], page=page, page_size=pageSize, search=search, status=status)
