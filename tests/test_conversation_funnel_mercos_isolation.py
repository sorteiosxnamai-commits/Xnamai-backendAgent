from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from app.repositories.conversa_repository import ConversaRepository
from app.repositories.mensagem_repository import MensagemRepository
from app.repositories.mercos_sync_repository import MercosSyncRepository


class ConversationFunnelMercosIsolationTests(TestCase):
    def test_conversation_lookup_scopes_id_and_workspace(self):
        client = MagicMock()
        client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value.data = []
        with patch("app.repositories.conversa_repository.supabase", client):
            self.assertIsNone(ConversaRepository().obter("workspace-a", "conversation-b"))

        query = client.table.return_value.select.return_value
        self.assertEqual(query.eq.call_args.args, ("id", "conversation-b"))
        self.assertEqual(query.eq.return_value.eq.call_args.args, ("workspace_id", "workspace-a"))

    def test_message_update_cannot_change_workspace(self):
        client = MagicMock()
        client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        with patch("app.repositories.mensagem_repository.supabase", client):
            MensagemRepository().atualizar(
                "workspace-a",
                "message-a",
                {"workspace_id": "workspace-b", "status": "sent"},
            )

        payload = client.table.return_value.update.call_args.args[0]
        self.assertNotIn("workspace_id", payload)
        self.assertEqual(payload["status"], "sent")

    def test_mercos_logs_are_scoped_to_workspace(self):
        client = MagicMock()
        client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
        with patch("app.repositories.mercos_sync_repository.supabase", client):
            self.assertEqual(MercosSyncRepository().listar_recentes("workspace-a"), [])

        self.assertIn(
            call.eq("workspace_id", "workspace-a"),
            client.table.return_value.select.return_value.method_calls,
        )
