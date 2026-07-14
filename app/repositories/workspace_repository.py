from datetime import datetime

from app.services.supabase_service import supabase


class WorkspaceRepository:
    def buscar_membership_ativo(self, user_id: str) -> dict | None:
        resposta = (
            supabase
            .table("workspace_members")
            .select("*, workspaces(*)")
            .eq("user_id", user_id)
            .eq("status", "active")
            .limit(1)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def listar_members_workspace(self, workspace_id: str) -> list[dict]:
        resposta = (
            supabase
            .table("workspace_members")
            .select("*")
            .eq("workspace_id", workspace_id)
            .eq("status", "active")
            .execute()
        )
        return resposta.data or []

    def buscar_workspace(self, workspace_id: str) -> dict | None:
        resposta = (
            supabase
            .table("workspaces")
            .select("*")
            .eq("id", workspace_id)
            .limit(1)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def criar_workspace(self, name: str, brand_name: str | None = None) -> dict:
        resposta = (
            supabase
            .table("workspaces")
            .insert({
                "name": name,
                "brand_name": brand_name,
                "status": "active",
            })
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else {"name": name, "brand_name": brand_name, "status": "active"}

    def atualizar_workspace(self, workspace_id: str, dados: dict) -> dict:
        resposta = (
            supabase
            .table("workspaces")
            .update({**dados, "updated_at": datetime.utcnow().isoformat()})
            .eq("id", workspace_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else {"id": workspace_id, **dados}

    def criar_membership(self, workspace_id: str, user_id: str, role: str) -> dict:
        resposta = (
            supabase
            .table("workspace_members")
            .insert({
                "workspace_id": workspace_id,
                "user_id": user_id,
                "role": role,
                "status": "active",
            })
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else {"workspace_id": workspace_id, "user_id": user_id, "role": role}

    def obter_settings(self, workspace_id: str) -> dict | None:
        resposta = (
            supabase
            .table("workspace_settings")
            .select("*")
            .eq("workspace_id", workspace_id)
            .limit(1)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def criar_settings(self, workspace_id: str, dados: dict | None = None) -> dict:
        payload = {"workspace_id": workspace_id, **(dados or {})}
        resposta = supabase.table("workspace_settings").insert(payload).execute()
        rows = resposta.data or []
        return rows[0] if rows else payload

    def salvar_settings(self, workspace_id: str, dados: dict) -> dict:
        existente = self.obter_settings(workspace_id)
        payload = {**dados, "updated_at": datetime.utcnow().isoformat()}
        if existente:
            resposta = (
                supabase
                .table("workspace_settings")
                .update(payload)
                .eq("workspace_id", workspace_id)
                .execute()
            )
        else:
            resposta = (
                supabase
                .table("workspace_settings")
                .insert({"workspace_id": workspace_id, **payload})
                .execute()
            )
        rows = resposta.data or []
        return rows[0] if rows else {"workspace_id": workspace_id, **payload}

    def obter_onboarding(self, workspace_id: str) -> dict | None:
        resposta = (
            supabase
            .table("workspace_onboarding")
            .select("*")
            .eq("workspace_id", workspace_id)
            .limit(1)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else None

    def criar_onboarding(self, workspace_id: str, status: str = "pending", current_step: str | None = "business") -> dict:
        payload = {
            "workspace_id": workspace_id,
            "status": status,
            "current_step": current_step,
            "completed_steps": [],
        }
        resposta = supabase.table("workspace_onboarding").insert(payload).execute()
        rows = resposta.data or []
        return rows[0] if rows else payload

    def salvar_onboarding(self, workspace_id: str, dados: dict) -> dict:
        payload = {**dados, "updated_at": datetime.utcnow().isoformat()}
        resposta = (
            supabase
            .table("workspace_onboarding")
            .update(payload)
            .eq("workspace_id", workspace_id)
            .execute()
        )
        rows = resposta.data or []
        return rows[0] if rows else {"workspace_id": workspace_id, **payload}
