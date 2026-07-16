from app.services.supabase_service import supabase


class PedidoRepository:

    def salvar(self, workspace_id: str, pedido: dict):
        payload = {key: value for key, value in pedido.items() if key != "workspace_id"}
        payload["workspace_id"] = workspace_id
        return (
            supabase
            .table("pedidos")
            .upsert(payload, on_conflict="mercos_id")
            .execute()
        )

    def listar(self, workspace_id: str) -> list[dict]:
        resposta = supabase.table("pedidos").select("*").eq("workspace_id", workspace_id).execute()
        return resposta.data or []
