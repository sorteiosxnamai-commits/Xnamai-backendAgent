from fastapi import APIRouter, Depends

from app.core.auth import verificar_token
from app.services.sincronizacao_service import SincronizacaoService

router = APIRouter()

sincronizacao = SincronizacaoService()


@router.post("/sincronizar")
def sincronizar(
    autorizado=Depends(verificar_token)
):
    return sincronizacao.sincronizar_tudo()