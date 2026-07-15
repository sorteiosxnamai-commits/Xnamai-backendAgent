from fastapi import APIRouter, Depends

from app.core.internal_auth import require_nitrus_internal_token
from app.schemas.persona_runtime import ActivePersonaRuntime
from app.services.persona_runtime_service import persona_runtime_service


router = APIRouter()


@router.get(
    "/internal/workspaces/{workspace_id}/active-persona",
    response_model=ActivePersonaRuntime,
    dependencies=[Depends(require_nitrus_internal_token)],
)
def obter_persona_ativa(workspace_id: str) -> ActivePersonaRuntime:
    return persona_runtime_service.require_active_runtime(workspace_id)
