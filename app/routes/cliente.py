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


@router.post("/clientes")
def criar_cliente(
    dados: dict,
    autorizado=Depends(verificar_token)
):
    return mercos.criar_cliente(dados)


@router.get("/pedidos")
def listar_pedidos(
    autorizado=Depends(verificar_token)
):
    return mercos.listar_pedidos()


@router.post("/clientes/sincronizar")
def sincronizar_clientes(
    autorizado=Depends(verificar_token)
):
    return cliente_service.sincronizar()