from datetime import datetime

from fastapi import HTTPException

from app.repositories.settings_repository import SettingsRepository
from app.repositories.workspace_repository import WorkspaceRepository

WORKSPACE_ADMIN_ROLES = {"owner", "admin"}
WORKSPACE_ROLES = {"owner", "admin", "supervisor", "seller", "member"}
ONBOARDING_STATUSES = {"pending", "in_progress", "complete"}
ONBOARDING_PATCH_STATUSES = {"pending", "in_progress"}
SALES_MODELS = {"b2b", "b2c", "mixed"}


class WorkspaceService:
    def __init__(self):
        self.repo = WorkspaceRepository()
        self.settings_repo = SettingsRepository()

    def _missing_schema(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return any(name in text for name in ("workspace_members", "workspaces", "workspace_settings", "workspace_onboarding"))

    def get_current_workspace_context(self, usuario: dict) -> dict:
        account_type = usuario.get("account_type") if usuario.get("account_type") == "system_admin" else "workspace_user"
        try:
            membership = self.repo.buscar_membership_ativo(str(usuario.get("id")))
        except Exception as exc:
            if self._missing_schema(exc):
                raise HTTPException(status_code=503, detail="Execute supabase/014_workspace_foundation.sql no Supabase.") from exc
            raise

        if not membership:
            raise HTTPException(status_code=403, detail="Usuário não pertence a um workspace ativo")

        workspace = membership.get("workspaces") or self.repo.buscar_workspace(str(membership.get("workspace_id")))
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace não encontrado")
        if workspace.get("status") != "active":
            raise HTTPException(status_code=403, detail="Workspace inativo")

        onboarding = self.repo.obter_onboarding(str(workspace.get("id"))) or {}

        return {
            "workspaceId": str(workspace.get("id")),
            "workspaceName": workspace.get("name") or usuario.get("empresa") or "NITRUS",
            "workspaceRole": membership.get("role") or "member",
            "onboardingStatus": onboarding.get("status") or "complete",
            "accountType": account_type,
        }

    def criar_workspace_inicial(self, *, user_id: str, name: str) -> dict:
        workspace = self.repo.criar_workspace(name=name)
        workspace_id = str(workspace.get("id"))
        if not workspace_id:
            raise HTTPException(status_code=500, detail="Não foi possível criar o workspace")
        self.repo.criar_membership(workspace_id=workspace_id, user_id=user_id, role="owner")
        self.repo.criar_settings(workspace_id, {"currency": "BRL", "primary_contact": None})
        self.repo.criar_onboarding(workspace_id, status="pending", current_step="business")
        return workspace

    def _settings_response(self, row: dict | None) -> dict:
        row = row or {}
        sales_channels = row.get("sales_channels") or []
        if not isinstance(sales_channels, list):
            sales_channels = []
        return {
            "segment": row.get("segment"),
            "website": row.get("website"),
            "country": row.get("country"),
            "currency": row.get("currency"),
            "salesModel": row.get("sales_model"),
            "salesChannels": sales_channels,
            "businessHours": row.get("business_hours"),
            "primaryContact": row.get("primary_contact"),
            "agentDisplayName": row.get("agent_display_name"),
            "agentRole": row.get("agent_role"),
            "agentLanguage": row.get("agent_language"),
            "agentPrimaryChannel": row.get("agent_primary_channel"),
        }

    def obter_workspace_atual(self, usuario: dict) -> dict:
        context = self.get_current_workspace_context(usuario)
        workspace = self.repo.buscar_workspace(context["workspaceId"])
        settings = self.repo.obter_settings(context["workspaceId"]) or {}
        return {
            "id": context["workspaceId"],
            "name": workspace.get("name") if workspace else context["workspaceName"],
            "brandName": workspace.get("brand_name") if workspace else None,
            "role": context["workspaceRole"],
            "status": workspace.get("status") if workspace else "active",
            "accountType": context["accountType"],
            "onboardingStatus": context["onboardingStatus"],
            "settings": self._settings_response(settings),
        }

    def _legacy_empresa(self) -> dict:
        try:
            return self.settings_repo.obter_empresa() or {}
        except Exception:
            return {}

    def obter_empresa_settings(self, usuario: dict) -> dict:
        context = self.get_current_workspace_context(usuario)
        workspace = self.repo.buscar_workspace(context["workspaceId"]) or {}
        settings = self.repo.obter_settings(context["workspaceId"]) or {}
        legacy = self._legacy_empresa()
        mapped = self._settings_response(settings)
        return {
            "name": workspace.get("name") or legacy.get("nome") or "NITRUS",
            "brandName": workspace.get("brand_name") or "",
            "cnpj": settings.get("cnpj") or legacy.get("cnpj") or "",
            "email": settings.get("primary_contact") or legacy.get("email") or "",
            "phone": settings.get("phone") or legacy.get("telefone") or "",
            **mapped,
        }

    def _require_workspace_admin(self, context: dict) -> None:
        if context.get("workspaceRole") not in WORKSPACE_ADMIN_ROLES:
            raise HTTPException(status_code=403, detail="Você não possui permissão para alterar a empresa")

    def salvar_empresa_settings(self, usuario: dict, payload: dict) -> dict:
        context = self.get_current_workspace_context(usuario)
        self._require_workspace_admin(context)

        workspace_update: dict = {}
        if payload.get("name") is not None:
            name = str(payload.get("name") or "").strip()
            if not name:
                raise HTTPException(status_code=400, detail="Nome da empresa é obrigatório")
            workspace_update["name"] = name
        if payload.get("brandName") is not None:
            workspace_update["brand_name"] = str(payload.get("brandName") or "").strip() or None
        if workspace_update:
            self.repo.atualizar_workspace(context["workspaceId"], workspace_update)

        sales_model = payload.get("salesModel")
        if sales_model and sales_model not in SALES_MODELS:
            raise HTTPException(status_code=400, detail="Modelo de vendas inválido")

        settings_payload = {
            "segment": payload.get("segment"),
            "website": payload.get("website"),
            "country": payload.get("country"),
            "currency": payload.get("currency"),
            "sales_model": sales_model,
            "sales_channels": payload.get("salesChannels"),
            "business_hours": payload.get("businessHours"),
            "primary_contact": payload.get("primaryContact") or payload.get("email"),
            "agent_display_name": payload.get("agentDisplayName"),
            "agent_role": payload.get("agentRole"),
            "agent_language": payload.get("agentLanguage"),
            "agent_primary_channel": payload.get("agentPrimaryChannel"),
            "cnpj": payload.get("cnpj"),
            "phone": payload.get("phone"),
        }
        clean_settings = {key: value for key, value in settings_payload.items() if value is not None}
        if clean_settings:
            self.repo.salvar_settings(context["workspaceId"], clean_settings)

        return self.obter_empresa_settings(usuario)

    def _onboarding_response(self, row: dict | None) -> dict:
        row = row or {}
        completed_steps = row.get("completed_steps") or []
        if not isinstance(completed_steps, list):
            completed_steps = []
        return {
            "status": row.get("status") or "complete",
            "currentStep": row.get("current_step"),
            "completedSteps": completed_steps,
            "startedAt": row.get("started_at"),
            "completedAt": row.get("completed_at"),
        }

    def obter_onboarding(self, usuario: dict) -> dict:
        context = self.get_current_workspace_context(usuario)
        row = self.repo.obter_onboarding(context["workspaceId"])
        if not row:
            raise HTTPException(status_code=404, detail="Onboarding não encontrado")
        return self._onboarding_response(row)

    def atualizar_onboarding(self, usuario: dict, payload: dict) -> dict:
        context = self.get_current_workspace_context(usuario)
        self._require_workspace_admin(context)
        status = payload.get("status")
        if status and status not in ONBOARDING_PATCH_STATUSES:
            raise HTTPException(status_code=400, detail="Use /onboarding/complete para concluir o onboarding")

        dados: dict = {}
        if payload.get("currentStep") is not None:
            dados["current_step"] = payload.get("currentStep")
        if payload.get("completedSteps") is not None:
            dados["completed_steps"] = payload.get("completedSteps") or []
        if status is not None:
            dados["status"] = status

        if not dados:
            return self.obter_onboarding(usuario)

        row = self.repo.salvar_onboarding(context["workspaceId"], dados)
        return self._onboarding_response(row)

    def concluir_onboarding(self, usuario: dict) -> dict:
        context = self.get_current_workspace_context(usuario)
        self._require_workspace_admin(context)
        workspace = self.repo.buscar_workspace(context["workspaceId"])
        if not workspace or not (workspace.get("name") or "").strip():
            raise HTTPException(status_code=400, detail="O onboarding ainda possui campos obrigatórios pendentes")

        self.repo.salvar_onboarding(context["workspaceId"], {
            "status": "complete",
            "current_step": "activation",
            "completed_steps": ["business", "operation", "catalog", "channels", "activation"],
            "completed_at": datetime.utcnow().isoformat(),
        })
        return self.obter_workspace_atual(usuario)


workspace_service = WorkspaceService()
