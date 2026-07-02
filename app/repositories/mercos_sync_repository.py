from datetime import datetime

from app.services.supabase_service import supabase


class MercosSyncRepository:

    def registrar(
        self,
        *,
        tipo: str,
        mensagem: str,
        status: str = "success",
        quantidade: int = 0,
        resumo: dict | None = None,
    ) -> dict | None:
        payload = {
            "tipo": tipo,
            "status": status,
            "mensagem": mensagem,
            "quantidade": quantidade,
            "resumo": resumo,
            "created_at": datetime.utcnow().isoformat(),
        }
        try:
            resposta = supabase.table("mercos_sync_logs").insert(payload).execute()
            rows = resposta.data or []
            return rows[0] if rows else payload
        except Exception:
            return None

    def ultima_sincronizacao(self, tipo: str) -> str | None:
        try:
            resposta = (
                supabase
                .table("mercos_sync_logs")
                .select("created_at")
                .eq("tipo", tipo)
                .eq("status", "success")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            rows = resposta.data or []
            return rows[0].get("created_at") if rows else None
        except Exception:
            return None

    def listar_recentes(self, limite: int = 10) -> list[dict]:
        try:
            resposta = (
                supabase
                .table("mercos_sync_logs")
                .select("*")
                .order("created_at", desc=True)
                .limit(limite)
                .execute()
            )
            return resposta.data or []
        except Exception:
            return []
