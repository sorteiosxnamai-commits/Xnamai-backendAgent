from fastapi import APIRouter, Depends, Query

from app.core.internal_auth import require_nitrus_internal_token
from app.schemas.persona_runtime import ActivePersonaRuntime
from app.schemas.catalog import CatalogPage
from app.repositories.catalog_repository import CatalogRepository
from app.services.persona_runtime_service import persona_runtime_service


router = APIRouter()
catalog_repository = CatalogRepository()


@router.get(
    "/internal/workspaces/{workspace_id}/active-persona",
    response_model=ActivePersonaRuntime,
    dependencies=[Depends(require_nitrus_internal_token)],
)
def obter_persona_ativa(workspace_id: str) -> ActivePersonaRuntime:
    return persona_runtime_service.require_active_runtime(workspace_id)


@router.get("/internal/workspaces/{workspace_id}/catalog/products", response_model=CatalogPage)
def listar_catalogo(
    workspace_id: str,
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=80),
    status: str | None = Query(default=None, pattern="^(active|inactive)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=100),
) -> CatalogPage:
    rows, has_next = catalog_repository.listar_por_workspace(
        workspace_id,
        search=search,
        category=category,
        status=status,
        page=page,
        limit=limit,
    )
    return CatalogPage(
        items=[catalog_repository.to_agent_product(row) for row in rows],
        page=page,
        limit=limit,
        hasNext=has_next,
    )
