from app.services.supabase_service import supabase


class MensagemRepository:

    def listar_por_conversa(self, workspace_id: str, conversa_id: str) -> list[dict]:
        resposta = (
            supabase
            .table("mensagens")
            .select("*")
            .eq("workspace_id", workspace_id)
            .eq("conversa_id", conversa_id)
            .order("created_at", desc=False)
            .execute()
        )
        return resposta.data or []

    def criar(self, workspace_id: str, dados: dict) -> dict:
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        payload["workspace_id"] = workspace_id
        resposta = supabase.table("mensagens").insert(payload).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados

    def existe_external_id(self, workspace_id: str, external_id: str) -> bool:
        if not external_id:
            return False
        resposta = (
            supabase
            .table("mensagens")
            .select("id")
            .eq("workspace_id", workspace_id)
            .eq("external_id", external_id)
            .limit(1)
            .execute()
        )
        return bool(resposta.data)

    def atualizar(self, workspace_id: str, mensagem_id: str, dados: dict) -> dict | None:
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        resposta = (
            supabase
            .table("mensagens")
            .update(payload)
            .eq("id", mensagem_id)
            .eq("workspace_id", workspace_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def atualizar_por_external_id(self, workspace_id: str, external_id: str, dados: dict) -> dict | None:
        resposta = (
            supabase
            .table("mensagens")
            .update(dados)
            .eq("workspace_id", workspace_id)
            .eq("external_id", external_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None
