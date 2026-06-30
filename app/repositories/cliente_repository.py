from app.services.supabase_service import supabase


class ClienteRepository:

    def salvar(self, cliente: dict):

        return (
            supabase
            .table("clientes")
            .upsert(
                cliente,
                on_conflict="mercos_id"
            )
            .execute()
        )