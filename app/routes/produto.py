from fastapi import APIRouter
from app.services.mercos_service import MercosService

router = APIRouter()

mercos = MercosService()

@router.get("/produtos")
def listar_produtos():
    return mercos.listar_produtos()