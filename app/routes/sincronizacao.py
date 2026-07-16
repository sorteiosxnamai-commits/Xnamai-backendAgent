from fastapi import APIRouter, Depends

from app.core.auth import obter_workspace_context
from app.core.permissions import requer_permissao
from app.services.sincronizacao_service import SincronizacaoService

router = APIRouter()

sincronizacao = SincronizacaoService()


@router.post("/sincronizar")
def sincronizar(
    workspace=Depends(obter_workspace_context),
    _: dict = Depends(requer_permissao("manageIntegrations")),
):
    return sincronizacao.sincronizar_tudo(workspace["workspaceId"])
