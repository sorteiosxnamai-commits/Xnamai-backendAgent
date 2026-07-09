from fastapi import APIRouter, Depends

from app.core.auth import verificar_token
from app.services.mercos_service import MercosService
from app.services.produto_service import ProdutoService

router = APIRouter()

mercos = MercosService()
produto_service = ProdutoService()


@router.get("/produtos")
def listar_produtos(
    autorizado=Depends(verificar_token)
):
    return mercos.listar_produtos()


@router.get("/produtos/{produto_id}")
def obter_produto(
    produto_id: int,
    autorizado=Depends(verificar_token),
):
    return mercos.obter_produto(produto_id)


@router.post("/produtos")
def criar_produto(
    dados: dict,
    autorizado=Depends(verificar_token),
):
    return mercos.criar_produto(dados)


@router.post("/produtos/sincronizar")
def sincronizar_produtos(
    autorizado=Depends(verificar_token)
):
    return produto_service.sincronizar()