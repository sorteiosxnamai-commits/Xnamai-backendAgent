import requests
from datetime import datetime, timedelta

from app.config.settings import (
    MERCOS_APPLICATION_TOKEN,
    MERCOS_COMPANY_TOKEN,
    MERCOS_BASE_URL
)


class MercosService:

    def __init__(self):
        self.headers = {
            "ApplicationToken": MERCOS_APPLICATION_TOKEN,
            "CompanyToken": MERCOS_COMPANY_TOKEN,
            "Accept": "application/json"
        }

    def listar_clientes(self):
        data = (
            datetime.now() - timedelta(days=365)
        ).strftime("%Y-%m-%d %H:%M:%S")

        response = requests.get(
            f"{MERCOS_BASE_URL}/clientes",
            headers=self.headers,
            params={
                "alterado_apos": data
            }
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

    def listar_produtos(self):
        data = (
            datetime.now() - timedelta(days=365)
        ).strftime("%Y-%m-%d %H:%M:%S")

        response = requests.get(
            f"{MERCOS_BASE_URL}/produtos",
            headers=self.headers,
            params={
                "alterado_apos": data
            }
        )

        response.raise_for_status()

        return response.json()

    def listar_pedidos(self):
        data = (
            datetime.now() - timedelta(days=365)
        ).strftime("%Y-%m-%d %H:%M:%S")

        response = requests.get(
            f"{MERCOS_BASE_URL}/pedidos",
            headers=self.headers,
            params={
                "alterado_apos": data
            }
        )

        response.raise_for_status()

        return response.json()