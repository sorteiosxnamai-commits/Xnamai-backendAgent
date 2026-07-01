import requests

from app.config.settings import (
    MERCOS_APPLICATION_TOKEN,
    MERCOS_BASE_URL,
    MERCOS_COMPANY_TOKEN,
)


def mercos_configurado() -> bool:
    return bool(MERCOS_APPLICATION_TOKEN and MERCOS_COMPANY_TOKEN and MERCOS_BASE_URL)


class MercosService:

    def __init__(self):
        self.headers = {
            "ApplicationToken": MERCOS_APPLICATION_TOKEN,
            "CompanyToken": MERCOS_COMPANY_TOKEN,
            "Accept": "application/json",
        }

    def _validar_config(self) -> None:
        if not mercos_configurado():
            raise RuntimeError(
                "Mercos não configurado. Defina MERCOS_APPLICATION_TOKEN, "
                "MERCOS_COMPANY_TOKEN e MERCOS_BASE_URL no Render."
            )

    def listar_clientes(self, alterado_apos: str | None = None):
        self._validar_config()
        params = {}
        if alterado_apos:
            params["alterado_apos"] = alterado_apos

        response = requests.get(
            f"{MERCOS_BASE_URL}/clientes",
            headers=self.headers,
            params=params,
            timeout=60,
        )

        response.raise_for_status()
        return response.json()

    def criar_cliente(self, dados):
        response = requests.post(
            f"{MERCOS_BASE_URL}/clientes",
            headers={
                **self.headers,
                "Content-Type": "application/json"
            },
            json=dados
        )

        return {
            "status_code": response.status_code,
            "resposta": response.text
        }

    def listar_produtos(self, alterado_apos: str | None = None):
        self._validar_config()
        params = {}
        if alterado_apos:
            params["alterado_apos"] = alterado_apos

        response = requests.get(
            f"{MERCOS_BASE_URL}/produtos",
            headers=self.headers,
            params=params,
            timeout=60,
        )

        response.raise_for_status()

        return response.json()

    def listar_pedidos(self, alterado_apos: str | None = None):
        self._validar_config()
        params = {}
        if alterado_apos:
            params["alterado_apos"] = alterado_apos

        response = requests.get(
            f"{MERCOS_BASE_URL}/pedidos",
            headers=self.headers,
            params=params,
            timeout=60,
        )

        response.raise_for_status()

        return response.json()