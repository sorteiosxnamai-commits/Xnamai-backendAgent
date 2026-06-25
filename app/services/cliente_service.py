from app.services.mercos_service import MercosService
from app.services.supabase_service import supabase


class ClienteService:

    def __init__(self):
        self.mercos = MercosService()

    def sincronizar_clientes(self):

        clientes = self.mercos.listar_clientes()

        quantidade = 0

        for cliente in clientes:

            dados = {
                "mercos_id": cliente.get("id"),
                "razao_social": cliente.get("razao_social"),
                "nome_fantasia": cliente.get("nome_fantasia"),
                "tipo": cliente.get("tipo"),
                "cpf_cnpj": cliente.get("cnpj")
            }

            (
                supabase
                .table("clientes")
                .upsert(
                    dados,
                    on_conflict="mercos_id"
                )
                .execute()
            )

            quantidade += 1

        return {
            "clientes_sincronizados": quantidade
        }