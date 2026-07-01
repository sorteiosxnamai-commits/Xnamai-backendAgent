from datetime import datetime

from app.services.supabase_service import supabase


class ConversaRepository:

    def listar(self) -> list[dict]:
        resposta = (
            supabase
            .table("conversas")
            .select("*")
            .order("last_message_at", desc=True)
            .execute()
        )
        return resposta.data or []

    def obter(self, conversa_id: str) -> dict | None:
        resposta = (
            supabase
            .table("conversas")
            .select("*")
            .eq("id", conversa_id)
            .limit(1)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def criar(self, dados: dict) -> dict:
        resposta = supabase.table("conversas").insert(dados).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados

    def atualizar(self, conversa_id: str, dados: dict) -> dict | None:
        resposta = (
            supabase
            .table("conversas")
            .update({**dados, "updated_at": datetime.utcnow().isoformat()})
            .eq("id", conversa_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def contar(self) -> int:
        resposta = supabase.table("conversas").select("*", count="exact").execute()
        return resposta.count or 0
