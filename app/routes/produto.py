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


@router.post("/produtos/sincronizar")
def sincronizar_produtos(
    autorizado=Depends(verificar_token)
):
    return produto_service.sincronizar()