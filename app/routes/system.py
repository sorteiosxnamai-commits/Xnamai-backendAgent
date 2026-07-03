from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import requer_admin, verificar_token
from app.services.demo_cleanup_service import limpar_demo
from app.services.system_status_service import system_status_service

router = APIRouter()


class LimparDemoRequest(BaseModel):
    incluirMercos: bool = False


@router.get("/sistema/status")
def get_system_status(autorizado=Depends(verificar_token)):
    return system_status_service.get_status()


@router.post("/sistema/limpar-demo")
def limpar_dados_demo(body: LimparDemoRequest | None = None, _: dict = Depends(requer_admin)):
    return limpar_demo(incluir_mercos=bool(body and body.incluirMercos))
