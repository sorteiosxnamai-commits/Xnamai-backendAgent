from fastapi import APIRouter
from app.services.supabase_service import supabase

router = APIRouter()

@router.get("/teste")
def testar_conexao():
    try:
        resposta = (
            supabase
            .table("usuarios")
            .select("*")
            .execute()
        )

        return resposta.data

    except Exception as e:
        print("ERRO SUPABASE:", e)
        return {"erro": str(e)}