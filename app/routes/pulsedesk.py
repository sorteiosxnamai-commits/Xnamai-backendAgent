import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import verificar_token
from app.core.permissions import requer_permissao
from app.services.pulsedesk_adapter import (
    dashboard_data,
    listar_clientes,
    listar_produtos,
    listar_pedidos,
    obter_cliente,
    mercos_status,
    mercos_logs,
)
from app.services.mercos_service import MercosService, mercos_info
from app.services.cliente_service import ClienteService
from app.services.produto_service import ProdutoService
from app.services.pedido_service import PedidoService
from app.services.vendas_service import vendas_service
from app.services.rankings_service import rankings_service
from app.repositories.mercos_sync_repository import MercosSyncRepository

router = APIRouter()

cliente_service = ClienteService()
produto_service = ProdutoService()
pedido_service = PedidoService()
sync_logs = MercosSyncRepository()


def _registrar_sync(tipo: str, mensagem: str, quantidade: int = 0) -> None:
    sync_logs.registrar(tipo=tipo, mensagem=mensagem, quantidade=quantidade)


def _sincronizar_funil_apos_pedidos() -> str:
    from app.services.funil_sync_service import funil_sync_service

    try:
        resultado = funil_sync_service.sincronizar()
        mensagem = resultado.get("message") or "Funil sincronizado."
        sync_logs.registrar(
            tipo="funil",
            mensagem=mensagem,
            quantidade=resultado.get("dealsCreated") or 0,
            resumo=resultado,
        )
        return mensagem
    except Exception as exc:
        aviso = f"Pedidos OK, mas funil não sincronizou: {exc}"
        sync_logs.registrar(tipo="funil", mensagem=aviso, status="error")
        return aviso


class MercosSyncRequest(BaseModel):
    type: str = "all"
    confirmProduction: bool = False


def _exigir_confirmacao_producao(body: MercosSyncRequest) -> None:
    info = mercos_info()
    if not info.get("isProduction"):
        return
    if body.type == "all" and not body.confirmProduction:
        raise HTTPException(
            status_code=400,
            detail=(
                "Ambiente de PRODUÇÃO Mercos — confirme explicitamente antes de sincronizar tudo. "
                "Envie confirmProduction: true no body."
            ),
        )


@router.get("/dashboard")
def get_dashboard(autorizado=Depends(verificar_token)):
    return dashboard_data()


@router.get("/vendas/metricas")
def get_vendas_metricas(_: dict = Depends(requer_permissao("viewReports"))):
    return vendas_service.metricas()


@router.get("/vendas/rankings")
def get_vendas_rankings(
    limit: int = 10,
    _: dict = Depends(requer_permissao("viewReports")),
):
    return rankings_service.rankings(limit=limit)


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


@router.get("/mercos/homologacao")
def get_mercos_homologacao(_: dict = Depends(requer_permissao("manageIntegrations"))):
    return MercosService().status_homologacao()


@router.post("/mercos/testar-conexao")
def testar_conexao_mercos(autorizado=Depends(verificar_token)):
    try:
        clientes = MercosService().listar_clientes()
        if isinstance(clientes, dict):
            raise HTTPException(
                status_code=502,
                detail=clientes.get("mensagem") or "Resposta inválida do Mercos",
            )
        if not isinstance(clientes, list):
            raise HTTPException(status_code=502, detail="Mercos não retornou lista de clientes")
        return {
            "ok": True,
            "message": f"Mercos respondeu com sucesso ({len(clientes)} clientes na API)",
            "clientes": len(clientes),
        }
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        detail = str(exc)
        if "401" in detail:
            detail = "Token inválido ou ambiente incorreto (sandbox vs produção). Verifique MERCOS_* no Render."
        raise HTTPException(status_code=502, detail=f"Falha ao conectar com Mercos: {detail}") from exc


@router.post("/mercos/sincronizar")
def sincronizar_mercos(
    body: MercosSyncRequest,
    _: dict = Depends(requer_permissao("manageIntegrations")),
):
    tipo = body.type

    try:
        _exigir_confirmacao_producao(body)
        ambiente = mercos_info().get("environment") or "unknown"
        prefix = f"[{ambiente}] "

        if tipo == "customers":
            resultado = cliente_service.sincronizar()
            qtd = resultado.get("clientes_sincronizados", 0)
            msg = f"{prefix}Clientes sincronizados: {qtd}"
            _registrar_sync("customers", msg, qtd)
            return {"success": True, "message": msg}

        if tipo == "products":
            resultado = produto_service.sincronizar()
            qtd = resultado.get("produtos_sincronizados", 0)
            msg = f"{prefix}Produtos sincronizados: {qtd}"
            _registrar_sync("products", msg, qtd)
            return {"success": True, "message": msg}

        if tipo == "orders":
            resultado = pedido_service.sincronizar()
            qtd = resultado.get("pedidos_sincronizados", 0)
            msg = resultado.get("mensagem") or f"{prefix}Pedidos sincronizados: {qtd}"
            funil_msg = _sincronizar_funil_apos_pedidos()
            return {
                "success": True,
                "message": f"{msg} {funil_msg}",
                "resumo": resultado.get("resumo"),
            }

        c = cliente_service.sincronizar()
        time.sleep(6)
        p = produto_service.sincronizar()
        time.sleep(6)
        o = pedido_service.sincronizar(incremental=False)
        msg = (
            f"{prefix}Sincronização concluída — "
            f"clientes: {c.get('clientes_sincronizados', 0)}, "
            f"produtos: {p.get('produtos_sincronizados', 0)}, "
            f"pedidos: {o.get('pedidos_sincronizados', 0)}"
        )
        _registrar_sync(
            "all",
            msg,
            (c.get("clientes_sincronizados", 0) + p.get("produtos_sincronizados", 0) + o.get("pedidos_sincronizados", 0)),
        )
        funil_msg = _sincronizar_funil_apos_pedidos()
        return {"success": True, "message": f"{msg}. {funil_msg}", "resumo": o.get("resumo")}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Falha ao sincronizar com Mercos: {exc}",
        ) from exc


