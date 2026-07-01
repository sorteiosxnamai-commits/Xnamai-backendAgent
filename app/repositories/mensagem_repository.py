from app.services.supabase_service import supabase


class MensagemRepository:

    def listar_por_conversa(self, conversa_id: str) -> list[dict]:
        resposta = (
            supabase
            .table("mensagens")
            .select("*")
            .eq("conversa_id", conversa_id)
            .order("created_at", desc=False)
            .execute()
        )
        return resposta.data or []

    def criar(self, dados: dict) -> dict:
        resposta = supabase.table("mensagens").insert(dados).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados
