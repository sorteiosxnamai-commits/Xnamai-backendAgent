from app.services.supabase_service import supabase


class CatalogRepository:
    """Leitura segura do catálogo legado; não grava nem altera produtos."""

    def contar_produtos(self) -> int:
        resposta = supabase.table("produtos").select("id", count="exact").execute()
        return int(resposta.count or 0)
