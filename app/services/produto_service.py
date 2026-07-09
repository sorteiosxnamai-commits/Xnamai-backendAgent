from app.services.mercos_service import MercosService
from app.repositories.produto_repository import ProdutoRepository
from app.repositories.mercos_sync_repository import MercosSyncRepository


class ProdutoService:

    def __init__(self):
        self.mercos = MercosService()
        self.repository = ProdutoRepository()
        self.sync_logs = MercosSyncRepository()

    def sincronizar(self, *, incremental: bool = True):

        alterado_apos = None
        if incremental:
            alterado_apos = self.sync_logs.ultima_sincronizacao("products")

        produtos = self.mercos.listar_produtos(alterado_apos=alterado_apos)

        if isinstance(produtos, dict):
            return produtos

        quantidade = 0
        mercos_ids_validos: set[int] = set()

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

            if produto.get("id") is not None:
                mercos_ids_validos.add(int(produto["id"]))

            quantidade += 1

        # NUNCA apagar no sync incremental: o Mercos só devolve o que mudou.
        # Se apagarmos o resto, o catálogo some (ex.: só sobra Cabo HDMI).
        removidos = 0
        if alterado_apos is None and mercos_ids_validos:
            removidos = self.repository.remover_obsoletos(mercos_ids_validos)

        mensagem = (
            f"Produtos sincronizados: {quantidade}"
            + (f", removidos: {removidos}." if removidos else ".")
        )
        self.sync_logs.registrar(tipo="products", mensagem=mensagem, quantidade=quantidade)

        return {
            "mensagem": "Sincronização concluída.",
            "produtos_sincronizados": quantidade,
            "produtos_removidos": removidos,
            "incremental": bool(alterado_apos),
        }