from app.services.mercos_service import MercosService
from app.repositories.pedido_repository import PedidoRepository


class PedidoService:

    def __init__(self):
        self.mercos = MercosService()
        self.repository = PedidoRepository()

    def sincronizar(self):
        pedidos = self.mercos.listar_pedidos()

        if isinstance(pedidos, dict):
            return pedidos

        quantidade = 0

        for pedido in pedidos:
            items = pedido.get("items") or []
            dados = {
                "mercos_id": pedido.get("id"),
                "numero": str(pedido.get("numero") or pedido.get("id") or ""),
                "cliente_mercos_id": pedido.get("cliente_id"),
                "valor_total": pedido.get("total") or 0,
                "situacao": str(pedido.get("status") or "pendente"),
            }

            self.repository.salvar(dados)
            quantidade += 1

        return {
            "mensagem": "Sincronização concluída.",
            "pedidos_sincronizados": quantidade,
        }
