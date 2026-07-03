from fastapi import APIRouter, Depends

from app.core.auth import verificar_token
from app.services.system_status_service import system_status_service

router = APIRouter()


@router.get("/sistema/status")
def get_system_status(autorizado=Depends(verificar_token)):
    return system_status_service.get_status()
