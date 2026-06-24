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
            "accept": "application/json"
        }

    def listar_clientes(self):
        response = requests.get(
            f"{MERCOS_BASE_URL}/clientes",
            headers=self.headers
        )

        return response.json()

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

        return response.json()

    def criar_cliente(self, dados):
        response = requests.post(
            f"{MERCOS_BASE_URL}/clientes",
            headers={
                **self.headers,
                "content-type": "application/json"
            },
            json=dados
        )

        return {
            "status_code": response.status_code,
            "resposta": response.text
        }

    def listar_pedidos(self):
        data = (
            datetime.now() - timedelta(days=365)
        ).strftime("%Y-%m-%d %H:%M:%S")

        response = requests.get(
            "https://sandbox.mercos.com/api/v2/pedidos",
            headers=self.headers,
            params={
                "alterado_apos": data
            }
        )

        return response.json()