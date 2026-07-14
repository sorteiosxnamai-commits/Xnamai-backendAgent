from fastapi import APIRouter, Depends

from app.core.auth import obter_usuario_atual
from app.schemas.workspace import OnboardingUpdate
from app.services.workspace_service import workspace_service

router = APIRouter()


@router.get("/workspace/current")
def obter_workspace_atual(usuario: dict = Depends(obter_usuario_atual)):
    return workspace_service.obter_workspace_atual(usuario)


@router.get("/onboarding")
def obter_onboarding(usuario: dict = Depends(obter_usuario_atual)):
    return workspace_service.obter_onboarding(usuario)


@router.patch("/onboarding")
def atualizar_onboarding(
    body: OnboardingUpdate,
    usuario: dict = Depends(obter_usuario_atual),
):
    return workspace_service.atualizar_onboarding(
        usuario,
        body.model_dump(exclude_unset=True),
    )


@router.post("/onboarding/complete")
def concluir_onboarding(usuario: dict = Depends(obter_usuario_atual)):
    return workspace_service.concluir_onboarding(usuario)
