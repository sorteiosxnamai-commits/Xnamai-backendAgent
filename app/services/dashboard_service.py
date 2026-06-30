from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:

    def __init__(self):
        self.repository = DashboardRepository()

    def resumo(self):

        return {
            "clientes": self.repository.contar_clientes(),
            "produtos": self.repository.contar_produtos(),
            "pedidos": self.repository.contar_pedidos()
        }