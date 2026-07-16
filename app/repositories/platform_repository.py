from datetime import datetime

from app.services.supabase_service import supabase


class PlatformRepository:

    def _now(self) -> str:
        return datetime.utcnow().isoformat()

    # Canais
    def list_canais(self, workspace_id: str) -> list[dict]:
        resposta = supabase.table("canais").select("*").eq("workspace_id", workspace_id).order("name").execute()
        return resposta.data or []

    def get_canal(self, workspace_id: str, canal_id: str) -> dict | None:
        resposta = supabase.table("canais").select("*").eq("id", canal_id).eq("workspace_id", workspace_id).limit(1).execute()
        rows = resposta.data or []
        return rows[0] if rows else None

    def get_canal_by_phone_number_id(self, phone_number_id: str) -> dict | None:
        resposta = (
            supabase
            .table("canais")
            .select("*")
            .eq("phone_number_id", phone_number_id)
            .limit(1)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def create_canal(self, workspace_id: str, dados: dict) -> dict:
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        payload["workspace_id"] = workspace_id
        resposta = supabase.table("canais").insert(payload).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados

    def update_canal(self, workspace_id: str, canal_id: str, dados: dict) -> dict | None:
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        resposta = (
            supabase
            .table("canais")
            .update({**payload, "updated_at": self._now()})
            .eq("id", canal_id)
            .eq("workspace_id", workspace_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    # Funil
    def list_estagios(self, workspace_id: str) -> list[dict]:
        resposta = supabase.table("funil_estagios").select("*").eq("workspace_id", workspace_id).order("sort_order").execute()
        return resposta.data or []

    def list_negocios(self, workspace_id: str) -> list[dict]:
        resposta = supabase.table("funil_negocios").select("*").eq("workspace_id", workspace_id).execute()
        return resposta.data or []

    def get_negocio(self, workspace_id: str, negocio_id: str) -> dict | None:
        resposta = supabase.table("funil_negocios").select("*").eq("workspace_id", workspace_id).eq("id", negocio_id).limit(1).execute()
        rows = resposta.data or []
        return rows[0] if rows else None

    def update_negocio(self, workspace_id: str, negocio_id: str, dados: dict) -> dict | None:
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        resposta = (
            supabase
            .table("funil_negocios")
            .update({**payload, "updated_at": self._now()})
            .eq("workspace_id", workspace_id)
            .eq("id", negocio_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def create_estagio(self, workspace_id: str, dados: dict) -> dict:
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        payload["workspace_id"] = workspace_id
        resposta = supabase.table("funil_estagios").insert(payload).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados

    def create_negocio(self, workspace_id: str, dados: dict) -> dict:
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        payload["workspace_id"] = workspace_id
        resposta = supabase.table("funil_negocios").insert(payload).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados

    # Campanhas
    def list_campanhas(self, workspace_id: str) -> list[dict]:
        resposta = supabase.table("campanhas").select("*").eq("workspace_id", workspace_id).order("created_at", desc=True).execute()
        return resposta.data or []

    def create_campanha(self, workspace_id: str, dados: dict) -> dict:
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        payload["workspace_id"] = workspace_id
        resposta = supabase.table("campanhas").insert(payload).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados

    def get_campanha(self, workspace_id: str, campanha_id: str) -> dict | None:
        resposta = supabase.table("campanhas").select("*").eq("id", campanha_id).eq("workspace_id", workspace_id).limit(1).execute()
        rows = resposta.data or []
        return rows[0] if rows else None

    def update_campanha(self, workspace_id: str, campanha_id: str, dados: dict) -> dict | None:
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        resposta = (
            supabase
            .table("campanhas")
            .update(payload)
            .eq("id", campanha_id)
            .eq("workspace_id", workspace_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    # Chatbot
    def list_chatbots(self, workspace_id: str) -> list[dict]:
        resposta = supabase.table("chatbot_fluxos").select("*").eq("workspace_id", workspace_id).order("name").execute()
        return resposta.data or []

    def get_chatbot(self, workspace_id: str, flow_id: str) -> dict | None:
        resposta = supabase.table("chatbot_fluxos").select("*").eq("id", flow_id).eq("workspace_id", workspace_id).limit(1).execute()
        rows = resposta.data or []
        return rows[0] if rows else None

    def create_chatbot(self, workspace_id: str, dados: dict) -> dict:
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        payload["workspace_id"] = workspace_id
        resposta = supabase.table("chatbot_fluxos").insert(payload).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados

    def update_chatbot(self, workspace_id: str, flow_id: str, dados: dict) -> dict | None:
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        resposta = (
            supabase
            .table("chatbot_fluxos")
            .update({**payload, "updated_at": self._now()})
            .eq("id", flow_id)
            .eq("workspace_id", workspace_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def get_active_chatbot(self, channel: str) -> dict | None:
        resposta = (
            supabase
            .table("chatbot_fluxos")
            .select("*")
            .eq("channel", channel)
            .eq("active", True)
            .order("name")
            .limit(1)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def increment_chatbot_stats(
        self,
        flow_id: str,
        triggers_delta: int = 0,
        resolved_delta: int = 0,
    ) -> dict | None:
        flow = self.get_chatbot(flow_id)
        if not flow:
            return None
        dados: dict = {}
        if triggers_delta:
            dados["triggers"] = int(flow.get("triggers") or 0) + triggers_delta
        if resolved_delta:
            dados["resolved"] = int(flow.get("resolved") or 0) + resolved_delta
        if not dados:
            return flow
        return self.update_chatbot(flow_id, dados)

    # Integrações
    def list_integracoes(self, workspace_id: str) -> list[dict]:
        resposta = supabase.table("integracoes").select("*").eq("workspace_id", workspace_id).order("name").execute()
        return resposta.data or []

    def get_integracao(self, workspace_id: str, integration_id: str) -> dict | None:
        resposta = supabase.table("integracoes").select("*").eq("id", integration_id).eq("workspace_id", workspace_id).limit(1).execute()
        rows = resposta.data or []
        return rows[0] if rows else None

    def update_integracao(self, workspace_id: str, integration_id: str, dados: dict) -> dict | None:
        payload = {key: value for key, value in dados.items() if key != "workspace_id"}
        resposta = (
            supabase
            .table("integracoes")
            .update({**payload, "updated_at": self._now()})
            .eq("id", integration_id)
            .eq("workspace_id", workspace_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def create_integracao(self, dados: dict) -> dict:
        resposta = supabase.table("integracoes").insert(dados).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados

    def count_canais(self) -> int:
        resposta = supabase.table("canais").select("*", count="exact").limit(0).execute()
        return resposta.count or 0
