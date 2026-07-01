from datetime import datetime

from app.services.supabase_service import supabase


class PlatformRepository:

    def _now(self) -> str:
        return datetime.utcnow().isoformat()

    # Canais
    def list_canais(self) -> list[dict]:
        resposta = supabase.table("canais").select("*").order("name").execute()
        return resposta.data or []

    def get_canal(self, canal_id: str) -> dict | None:
        resposta = supabase.table("canais").select("*").eq("id", canal_id).limit(1).execute()
        rows = resposta.data or []
        return rows[0] if rows else None

    def create_canal(self, dados: dict) -> dict:
        resposta = supabase.table("canais").insert(dados).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados

    def update_canal(self, canal_id: str, dados: dict) -> dict | None:
        resposta = (
            supabase
            .table("canais")
            .update({**dados, "updated_at": self._now()})
            .eq("id", canal_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    # Funil
    def list_estagios(self) -> list[dict]:
        resposta = supabase.table("funil_estagios").select("*").order("sort_order").execute()
        return resposta.data or []

    def list_negocios(self) -> list[dict]:
        resposta = supabase.table("funil_negocios").select("*").execute()
        return resposta.data or []

    def get_negocio(self, negocio_id: str) -> dict | None:
        resposta = supabase.table("funil_negocios").select("*").eq("id", negocio_id).limit(1).execute()
        rows = resposta.data or []
        return rows[0] if rows else None

    def update_negocio(self, negocio_id: str, dados: dict) -> dict | None:
        resposta = (
            supabase
            .table("funil_negocios")
            .update({**dados, "updated_at": self._now()})
            .eq("id", negocio_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def create_estagio(self, dados: dict) -> dict:
        resposta = supabase.table("funil_estagios").insert(dados).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados

    def create_negocio(self, dados: dict) -> dict:
        resposta = supabase.table("funil_negocios").insert(dados).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados

    # Campanhas
    def list_campanhas(self) -> list[dict]:
        resposta = supabase.table("campanhas").select("*").order("created_at", desc=True).execute()
        return resposta.data or []

    def create_campanha(self, dados: dict) -> dict:
        resposta = supabase.table("campanhas").insert(dados).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados

    # Chatbot
    def list_chatbots(self) -> list[dict]:
        resposta = supabase.table("chatbot_fluxos").select("*").order("name").execute()
        return resposta.data or []

    def get_chatbot(self, flow_id: str) -> dict | None:
        resposta = supabase.table("chatbot_fluxos").select("*").eq("id", flow_id).limit(1).execute()
        rows = resposta.data or []
        return rows[0] if rows else None

    def create_chatbot(self, dados: dict) -> dict:
        resposta = supabase.table("chatbot_fluxos").insert(dados).execute()
        rows = resposta.data or []
        return rows[0] if rows else dados

    def update_chatbot(self, flow_id: str, dados: dict) -> dict | None:
        resposta = (
            supabase
            .table("chatbot_fluxos")
            .update({**dados, "updated_at": self._now()})
            .eq("id", flow_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    # Integrações
    def list_integracoes(self) -> list[dict]:
        resposta = supabase.table("integracoes").select("*").order("name").execute()
        return resposta.data or []

    def get_integracao(self, integration_id: str) -> dict | None:
        resposta = supabase.table("integracoes").select("*").eq("id", integration_id).limit(1).execute()
        rows = resposta.data or []
        return rows[0] if rows else None

    def update_integracao(self, integration_id: str, dados: dict) -> dict | None:
        resposta = (
            supabase
            .table("integracoes")
            .update({**dados, "updated_at": self._now()})
            .eq("id", integration_id)
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
