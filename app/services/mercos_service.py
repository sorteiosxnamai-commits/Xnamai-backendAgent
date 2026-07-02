import json
import time

import requests

from app.config.settings import (
    MERCOS_APPLICATION_TOKEN,
    MERCOS_BASE_URL,
    MERCOS_COMPANY_TOKEN,
    mercos_ambiente,
    mercos_base_url_host,
)

MAX_RETRIES = 4
DEFAULT_RETRY_SECONDS = 6


def mercos_configurado() -> bool:
    return bool(MERCOS_APPLICATION_TOKEN and MERCOS_COMPANY_TOKEN and MERCOS_BASE_URL)


def mercos_info() -> dict:
    ambiente = mercos_ambiente()
    return {
        "environment": ambiente,
        "isProduction": ambiente == "production",
        "isSandbox": ambiente == "sandbox",
        "baseUrlHost": mercos_base_url_host(),
        "configured": mercos_configurado(),
    }


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

    def _retry_seconds(self, response: requests.Response) -> float:
        try:
            payload = response.json()
            if isinstance(payload, dict):
                wait = payload.get("tempo_ate_permitir_novamente")
                if wait is not None:
                    return float(wait) + 0.5
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        return float(DEFAULT_RETRY_SECONDS)

    def _get(self, path: str, params: dict | None = None):
        self._validar_config()
        url = f"{MERCOS_BASE_URL}/{path.lstrip('/')}"
        last_response: requests.Response | None = None

        for attempt in range(MAX_RETRIES):
            response = requests.get(
                url,
                headers=self.headers,
                params=params or {},
                timeout=60,
            )
            last_response = response

            if response.status_code != 429:
                response.raise_for_status()
                return response.json()

            if attempt == MAX_RETRIES - 1:
                break

            time.sleep(self._retry_seconds(response))

        if last_response is not None:
            last_response.raise_for_status()
        raise RuntimeError("Mercos não respondeu após tentativas de rate limit")

    def listar_clientes(self, alterado_apos: str | None = None):
        params = {}
        if alterado_apos:
            params["alterado_apos"] = alterado_apos
        return self._get("clientes", params)

    def criar_cliente(self, dados):
        response = requests.post(
            f"{MERCOS_BASE_URL}/clientes",
            headers={
                **self.headers,
                "Content-Type": "application/json",
            },
            json=dados,
        )

        return {
            "status_code": response.status_code,
            "resposta": response.text,
        }

    def listar_produtos(self, alterado_apos: str | None = None):
        params = {}
        if alterado_apos:
            params["alterado_apos"] = alterado_apos
        return self._get("produtos", params)

    def listar_pedidos(self, alterado_apos: str | None = None):
        params = {}
        if alterado_apos:
            params["alterado_apos"] = alterado_apos
        return self._get("pedidos", params)
