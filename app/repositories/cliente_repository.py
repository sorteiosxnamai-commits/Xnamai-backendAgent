from app.services.supabase_service import supabase


class ClienteRepository:
    def salvar(self, workspace_id: str, cliente: dict):
        payload = {key: value for key, value in cliente.items() if key != "workspace_id"}
        payload["workspace_id"] = workspace_id
        mercos_id = payload.get("mercos_id")
        if mercos_id is not None:
            existente = (
                supabase.table("clientes")
                .select("id")
                .eq("workspace_id", workspace_id)
                .eq("mercos_id", mercos_id)
                .limit(1)
                .execute()
                .data
                or []
            )
            if existente:
                return (
                    supabase.table("clientes")
                    .update(payload)
                    .eq("id", existente[0]["id"])
                    .eq("workspace_id", workspace_id)
                    .execute()
                )
        return supabase.table("clientes").insert(payload).execute()

    def listar_com_telefone(self, workspace_id: str, limite: int | None = None) -> list[dict]:
        query = (
            supabase.table("clientes")
            .select("mercos_id,nome,razao_social,telefone,celular")
            .eq("workspace_id", workspace_id)
            .order("nome")
        )
        if limite and limite > 0:
            query = query.limit(limite)
        resposta = query.execute()
        return resposta.data or []

    def listar(self, workspace_id: str) -> list[dict]:
        resposta = (
            supabase.table("clientes")
            .select("*")
            .eq("workspace_id", workspace_id)
            .execute()
        )
        return resposta.data or []

    def obter(self, workspace_id: str, customer_id: str) -> dict | None:
        for column in ("id", "mercos_id"):
            rows = (
                supabase.table("clientes")
                .select("*")
                .eq("workspace_id", workspace_id)
                .eq(column, customer_id)
                .limit(1)
                .execute()
                .data
                or []
            )
            if rows:
                return rows[0]
        return None
