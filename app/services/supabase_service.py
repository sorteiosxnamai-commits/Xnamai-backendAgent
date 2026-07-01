from supabase import Client, create_client

from app.config.settings import SUPABASE_KEY, SUPABASE_URL

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL e SUPABASE_KEY devem estar configurados (Render → Environment)."
            )
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


class _SupabaseProxy:
    def __getattr__(self, name: str):
        return getattr(get_supabase(), name)


supabase = _SupabaseProxy()
