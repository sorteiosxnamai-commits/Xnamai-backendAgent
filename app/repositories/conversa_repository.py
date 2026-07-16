from datetime import datetime

from app.services.conversa_cliente_link import enriquecer_dados_conversa_com_cliente_id
from app.services.supabase_service import supabase


class ConversaRepository:

    def listar(self, workspace_id: str) -> list[dict]:
        resposta = (
            supabase
            .table("conversas")
            .select("*")
            .eq("workspace_id", workspace_id)
            .order("last_message_at", desc=True)
            .execute()
        )
        return resposta.data or []

    def obter(self, workspace_id: str, conversa_id: str) -> dict | None:
        resposta = (
            supabase
            .table("conversas")
            .select("*")
            .eq("id", conversa_id)
            .eq("workspace_id", workspace_id)
            .limit(1)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def obter_por_thread(self, workspace_id: str, canal_id: str, external_thread_id: str) -> dict | None:
        resposta = (
            supabase
            .table("conversas")
            .select("*")
            .eq("workspace_id", workspace_id)
            .eq("canal_id", canal_id)
            .eq("external_thread_id", external_thread_id)
            .limit(1)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def criar(self, workspace_id: str, dados: dict) -> dict:
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        payload["workspace_id"] = workspace_id
        payload = enriquecer_dados_conversa_com_cliente_id(payload)
        resposta = supabase.table("conversas").insert(payload).execute()
        rows = resposta.data or []
        return rows[0] if rows else payload

    def atualizar(self, workspace_id: str, conversa_id: str, dados: dict) -> dict | None:
        existente = None
        if not dados.get("cliente_id"):
            existente = self.obter(workspace_id, conversa_id)
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        payload = enriquecer_dados_conversa_com_cliente_id(payload, existente=existente)
        resposta = (
            supabase
            .table("conversas")
            .update({**payload, "updated_at": datetime.utcnow().isoformat()})
            .eq("id", conversa_id)
            .eq("workspace_id", workspace_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def contar(self, workspace_id: str) -> int:
        resposta = supabase.table("conversas").select("*", count="exact").eq("workspace_id", workspace_id).execute()
        return resposta.count or 0
