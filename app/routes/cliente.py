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


@router.put("/pedidos/{pedido_id}")
def alterar_pedido(
    pedido_id: int,
    dados: dict,
    autorizado=Depends(verificar_token),
):
    """Altera pedido no Mercos (API v2)."""
    return mercos.alterar_pedido(pedido_id, dados)


@router.get("/pedidos/{pedido_id}")
def obter_pedido(
    pedido_id: int,
    autorizado=Depends(verificar_token),
):
    return mercos.obter_pedido(pedido_id)


@router.post("/clientes/sincronizar")
def sincronizar_clientes(
    autorizado=Depends(verificar_token)
):
    return cliente_service.sincronizar()


@router.get("/segmentos")
def listar_segmentos(
    autorizado=Depends(verificar_token),
):
    return mercos.listar_segmentos()


@router.get("/tipos-pedido")
def listar_tipos_pedido(
    autorizado=Depends(verificar_token),
):
    return mercos.listar_tipos_pedido()


@router.get("/usuarios-mercos")
def listar_usuarios_mercos(
    autorizado=Depends(verificar_token),
):
    return mercos.listar_usuarios_mercos()


@router.post("/titulos")
def criar_titulo(
    dados: dict,
    autorizado=Depends(verificar_token),
):
    return mercos.criar_titulo(dados)


@router.put("/titulos/{titulo_id}")
def alterar_titulo(
    titulo_id: int,
    dados: dict,
    autorizado=Depends(verificar_token),
):
    return mercos.alterar_titulo(titulo_id, dados)
