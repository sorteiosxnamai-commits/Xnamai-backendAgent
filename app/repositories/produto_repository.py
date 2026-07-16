from app.services.supabase_service import supabase


class ProdutoRepository:
    """Persistencia de produtos sempre limitada ao workspace informado."""

    def salvar(self, workspace_id: str, produto: dict):
        payload = {key: value for key, value in produto.items() if key != "workspace_id"}
        payload["workspace_id"] = workspace_id
        mercos_id = payload.get("mercos_id")
        if mercos_id is not None:
            existente = (
                supabase.table("produtos")
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
                    supabase.table("produtos")
                    .update(payload)
                    .eq("id", existente[0]["id"])
                    .eq("workspace_id", workspace_id)
                    .execute()
                )
        return supabase.table("produtos").insert(payload).execute()

    def listar(self, workspace_id: str) -> list[dict]:
        resposta = (
            supabase.table("produtos")
            .select("*")
            .eq("workspace_id", workspace_id)
            .execute()
        )
        return resposta.data or []

    def obter(self, workspace_id: str, product_id: str) -> dict | None:
        resposta = (
            supabase.table("produtos")
            .select("*")
            .eq("workspace_id", workspace_id)
            .eq("id", product_id)
            .limit(1)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None
