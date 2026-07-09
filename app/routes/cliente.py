from fastapi import APIRouter, Depends

from app.services.mercos_service import MercosService
from app.services.cliente_service import ClienteService
from app.core.auth import verificar_token

router = APIRouter()

mercos = MercosService()
cliente_service = ClienteService()


@router.get("/clientes")
def listar_clientes(
    autorizado=Depends(verificar_token)
):
    return mercos.listar_clientes()


@router.get("/clientes/{cliente_id}")
def obter_cliente(
    cliente_id: int,
    autorizado=Depends(verificar_token),
):
    return mercos.obter_cliente(cliente_id)


@router.post("/clientes")
def criar_cliente(
    dados: dict,
    autorizado=Depends(verificar_token)
):
    return mercos.criar_cliente(dados)


@router.put("/clientes/{cliente_id}")
def alterar_cliente(
    cliente_id: int,
    dados: dict,
    autorizado=Depends(verificar_token),
):
    return mercos.alterar_cliente(cliente_id, dados)


@router.get("/pedidos")
def listar_pedidos(
    autorizado=Depends(verificar_token)
):
    return mercos.listar_pedidos()


@router.post("/pedidos")
def criar_pedido(
    dados: dict,
    autorizado=Depends(verificar_token),
):
    """Cria pedido simples no Mercos (API v2)."""
    return mercos.criar_pedido(dados)


@router.post("/clientes/sincronizar")
def sincronizar_clientes(
    autorizado=Depends(verificar_token)
):
    return cliente_service.sincronizar()