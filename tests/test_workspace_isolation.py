from unittest import TestCase
from unittest.mock import MagicMock, patch

from app.repositories.cliente_repository import ClienteRepository
from app.repositories.produto_repository import ProdutoRepository


class WorkspaceIsolationRepositoryTests(TestCase):
    def _supabase(self, existing: list[dict] | None = None) -> MagicMock:
        client = MagicMock()
        client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = existing or []
        client.table.return_value.insert.return_value.execute.return_value.data = []
        client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        return client

    def test_product_save_forces_context_workspace(self):
        client = self._supabase()
        with patch("app.repositories.produto_repository.supabase", client):
            ProdutoRepository().salvar("workspace-a", {"mercos_id": 10, "workspace_id": "workspace-b"})

        payload = client.table.return_value.insert.call_args
        self.assertEqual(payload.args[0]["workspace_id"], "workspace-a")

    def test_customer_save_forces_context_workspace(self):
        client = self._supabase()
        with patch("app.repositories.cliente_repository.supabase", client):
            ClienteRepository().salvar("workspace-a", {"mercos_id": 11, "workspace_id": "workspace-b"})

        payload = client.table.return_value.insert.call_args
        self.assertEqual(payload.args[0]["workspace_id"], "workspace-a")

    def test_product_lookup_scopes_id_and_workspace(self):
        client = MagicMock()
        client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        with patch("app.repositories.produto_repository.supabase", client):
            result = ProdutoRepository().obter("workspace-a", "product-b")

        self.assertIsNone(result)
        query = client.table.return_value.select.return_value
        self.assertEqual(query.eq.call_args.args, ("workspace_id", "workspace-a"))
        self.assertEqual(query.eq.return_value.eq.call_args.args, ("id", "product-b"))
