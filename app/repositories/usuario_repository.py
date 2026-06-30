from app.services.supabase_service import supabase


class UsuarioRepository:

    def buscar_por_email(self, email: str) -> dict | None:
        resposta = (
            supabase
            .table("usuarios")
            .select("*")
            .eq("email", email.strip().lower())
            .limit(1)
            .execute()
        )

        rows = resposta.data or []
        return rows[0] if rows else None

    def criar(self, dados: dict) -> dict:
        resposta = (
            supabase
            .table("usuarios")
            .insert(dados)
            .execute()
        )

        rows = resposta.data or []
        return rows[0] if rows else dados

    def listar_emails(self) -> list[str]:
        resposta = (
            supabase
            .table("usuarios")
            .select("email")
            .execute()
        )

        return [row["email"] for row in (resposta.data or [])]
