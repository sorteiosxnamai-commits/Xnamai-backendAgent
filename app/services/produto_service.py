from app.services.mercos_service import MercosService
from app.repositories.produto_repository import ProdutoRepository


class ProdutoService:

    def __init__(self):
        self.mercos = MercosService()
        self.repository = ProdutoRepository()

    def sincronizar(self):

        produtos = self.mercos.listar_produtos()

        if isinstance(produtos, dict):
            return produtos

        quantidade = 0

        for produto in produtos:

            dados = {
                "mercos_id": produto.get("id"),
                "nome": produto.get("nome"),
                "codigo": produto.get("codigo"),
                "unidade": produto.get("unidade"),
                "descricao": produto.get("observacoes"),
                "preco_tabela": produto.get("preco_tabela"),
                "preco_minimo": produto.get("preco_minimo"),
                "saldo_estoque": produto.get("saldo_estoque"),
                "ativo": produto.get("ativo"),
                "ultima_alteracao": produto.get("ultima_alteracao")
            }

            self.repository.salvar(dados)

            quantidade += 1

        return {
            "mensagem": "Sincronização concluída.",
            "produtos_sincronizados": quantidade
        }