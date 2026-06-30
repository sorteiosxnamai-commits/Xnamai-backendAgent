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