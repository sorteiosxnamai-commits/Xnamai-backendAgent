from app.services.supabase_service import supabase


class DashboardRepository:

    def contar_clientes(self, workspace_id: str):
        resposta = (
            supabase
            .table("clientes")
            .select("*", count="exact")
            .eq("workspace_id", workspace_id)
            .execute()
        )

        return resposta.count

    def contar_produtos(self, workspace_id: str):
        resposta = (
            supabase
            .table("produtos")
            .select("*", count="exact")
            .eq("workspace_id", workspace_id)
            .execute()
        )

        return resposta.count

    def contar_pedidos(self, workspace_id: str):
        resposta = (
            supabase
            .table("pedidos")
            .select("*", count="exact")
            .eq("workspace_id", workspace_id)
            .execute()
        )

        return resposta.count
