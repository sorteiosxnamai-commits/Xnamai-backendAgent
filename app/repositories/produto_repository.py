from app.services.supabase_service import supabase


class ProdutoRepository:

    def salvar(self, produto: dict):

        return (
            supabase
            .table("produtos")
            .upsert(
                produto,
                on_conflict="mercos_id"
            )
            .execute()
        )

    def remover_obsoletos(self, mercos_ids_validos: set[int]) -> int:
        """Remove do Supabase produtos Mercos obsoletos ou demo [Exemplo]."""
        rows = (
            supabase
            .table("produtos")
            .select("id, mercos_id, nome")
            .execute()
            .data
            or []
        )
        removidos = 0
        for row in rows:
            mercos_id = row.get("mercos_id")
            if mercos_id is None:
                continue
            nome = str(row.get("nome") or "").lower()
            if "[exemplo]" in nome or int(mercos_id) not in mercos_ids_validos:
                supabase.table("produtos").delete().eq("id", row["id"]).execute()
                removidos += 1
        return removidos