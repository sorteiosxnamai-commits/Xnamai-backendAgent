from app.services.mercos_service import MercosService
from app.repositories.cliente_repository import ClienteRepository


class ClienteService:

    def __init__(self):
        self.mercos = MercosService()
        self.repository = ClienteRepository()

    def sincronizar(self):

        clientes = self.mercos.listar_clientes()

        if isinstance(clientes, dict):
            return clientes

        quantidade = 0

        for cliente in clientes:

            nome = cliente.get("nome") or cliente.get("razao_social")

            emails = cliente.get("emails", [])
            email = None

            if emails:
                if isinstance(emails[0], dict):
                    email = emails[0].get("email")
                else:
                    email = emails[0]

            dados = {
                "mercos_id": cliente.get("id"),
                "nome": nome,
                "razao_social": cliente.get("razao_social"),
                "cnpj": cliente.get("cnpj"),
                "inscricao_estadual": cliente.get("inscricao_estadual"),
                "email": email,
                "telefone": cliente.get("telefone"),
                "celular": cliente.get("celular"),
                "endereco": cliente.get("endereco"),
                "numero": cliente.get("numero"),
                "complemento": cliente.get("complemento"),
                "bairro": cliente.get("bairro"),
                "cidade": cliente.get("cidade"),
                "estado": cliente.get("estado"),
                "cep": cliente.get("cep")
            }

            self.repository.salvar(dados)
            quantidade += 1

        return {
            "mensagem": "Sincronização concluída.",
            "clientes_sincronizados": quantidade
        }