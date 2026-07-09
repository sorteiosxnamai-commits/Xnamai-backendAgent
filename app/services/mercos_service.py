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
MAX_PAGINAS = 500


def _eh_produto_exemplo(produto: dict) -> bool:
    nome = str(produto.get("nome") or "").lower()
    return "[exemplo]" in nome


def _filtrar_produtos_reais(produtos: list[dict]) -> list[dict]:
    """Ignora catálogo demo padrão da Mercos sandbox ([Exemplo] ...)."""
    return [p for p in produtos if not _eh_produto_exemplo(p)]


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

    def _request_get(self, path: str, params: dict | None = None) -> requests.Response:
        """GET com retry em 429 (critério obrigatório de homologação Mercos)."""
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
                return response

            if attempt == MAX_RETRIES - 1:
                break

            time.sleep(self._retry_seconds(response))

        if last_response is not None:
            last_response.raise_for_status()
        raise RuntimeError("Mercos não respondeu após tentativas de rate limit")

    def _get(self, path: str, params: dict | None = None):
        return self._request_get(path, params).json()

    @staticmethod
    def _limitou_registros(response: requests.Response) -> bool:
        return str(response.headers.get("MEUSPEDIDOS_LIMITOU_REGISTROS", "")).strip() == "1"

    @staticmethod
    def _ultima_alteracao(registros: list[dict]) -> str | None:
        for row in reversed(registros):
            valor = row.get("ultima_alteracao")
            if valor:
                return str(valor)
        return None

    def _listar_paginado(self, path: str, alterado_apos: str | None = None) -> list | dict:
        """Percorre todas as páginas com alterado_apos (critério obrigatório de homologação)."""
        todos: list[dict] = []
        cursor = alterado_apos

        for pagina in range(MAX_PAGINAS):
            params: dict[str, str] = {}
            if cursor:
                params["alterado_apos"] = cursor

            response = self._request_get(path, params)
            data = response.json()

            if isinstance(data, dict):
                return data
            if not isinstance(data, list):
                break
            if not data:
                break

            todos.extend(data)

            if not self._limitou_registros(response):
                break

            novo_cursor = self._ultima_alteracao(data)
            if not novo_cursor or novo_cursor == cursor:
                break

            cursor = novo_cursor
            if pagina < MAX_PAGINAS - 1:
                time.sleep(0.25)

        return todos

    def listar_clientes(self, alterado_apos: str | None = None):
        return self._listar_paginado("clientes", alterado_apos)

    def criar_cliente(self, dados):
        self._validar_config()
        response = requests.post(
            f"{MERCOS_BASE_URL}/clientes",
            headers={
                **self.headers,
                "Content-Type": "application/json",
            },
            json=dados,
            timeout=60,
        )

        return {
            "status_code": response.status_code,
            "resposta": response.text,
            "meuspedidosid": response.headers.get("meuspedidosid"),
        }

    def alterar_cliente(self, mercos_id: int | str, dados: dict):
        """PUT /clientes/{id} — altera cliente no Mercos."""
        self._validar_config()
        response = requests.put(
            f"{MERCOS_BASE_URL}/clientes/{mercos_id}",
            headers={
                **self.headers,
                "Content-Type": "application/json",
            },
            json=dados,
            timeout=60,
        )

        return {
            "status_code": response.status_code,
            "resposta": response.text,
            "meuspedidosid": response.headers.get("meuspedidosid"),
        }

    def listar_produtos(self, alterado_apos: str | None = None):
        produtos = self._listar_paginado("produtos", alterado_apos)
        if isinstance(produtos, list):
            return _filtrar_produtos_reais(produtos)
        return produtos

    def criar_produto(self, dados: dict):
        """POST /produtos — inclui produto simples no Mercos."""
        self._validar_config()
        response = requests.post(
            f"{MERCOS_BASE_URL}/produtos",
            headers={
                **self.headers,
                "Content-Type": "application/json",
            },
            json=dados,
            timeout=60,
        )

        return {
            "status_code": response.status_code,
            "resposta": response.text,
            "meuspedidosid": response.headers.get("meuspedidosid"),
        }

    def listar_pedidos(self, alterado_apos: str | None = None):
        return self._listar_paginado("pedidos", alterado_apos)

    def obter_cliente(self, mercos_id: int | str):
        return self._get(f"clientes/{mercos_id}")

    def obter_produto(self, mercos_id: int | str):
        return self._get(f"produtos/{mercos_id}")

    def obter_pedido(self, mercos_id: int | str):
        return self._get(f"pedidos/{mercos_id}")

    def listar_tabelas_preco(self, alterado_apos: str | None = None):
        return self._listar_paginado("tabelas_preco", alterado_apos)

    def listar_condicoes_pagamento(self, alterado_apos: str | None = None):
        return self._listar_paginado("condicoes_pagamento", alterado_apos)

    def listar_transportadoras(self, alterado_apos: str | None = None):
        return self._listar_paginado("transportadoras", alterado_apos)

    def listar_politicas_comerciais(self, alterado_apos: str | None = None):
        return self._listar_paginado("politicas_comerciais", alterado_apos)

    def status_homologacao(self) -> dict:
        """Resumo técnico para evidências de homologação Mercos."""
        info = mercos_info()
        checks = {
            "tokensConfigurados": info.get("configured"),
            "ambienteSandbox": info.get("isSandbox"),
            "throttling429": True,
            "paginacaoAlteradoApos": True,
            "syncIncrementalPedidos": True,
            "syncIncrementalClientes": True,
            "syncIncrementalProdutos": True,
        }

        apis_leitura = {
            "clientes": False,
            "produtos": False,
            "pedidos": False,
            "tabelas_preco": False,
            "condicoes_pagamento": False,
            "transportadoras": False,
            "politicas_comerciais": False,
        }
        contagens: dict[str, int] = {}
        erros: dict[str, str] = {}

        if info.get("configured"):
            probes = {
                "clientes": self.listar_clientes,
                "produtos": self.listar_produtos,
                "pedidos": self.listar_pedidos,
                "tabelas_preco": self.listar_tabelas_preco,
                "condicoes_pagamento": self.listar_condicoes_pagamento,
                "transportadoras": self.listar_transportadoras,
                "politicas_comerciais": self.listar_politicas_comerciais,
            }
            for nome, fn in probes.items():
                try:
                    resultado = fn()
                    if isinstance(resultado, dict):
                        erros[nome] = str(resultado.get("mensagem") or resultado)
                    elif isinstance(resultado, list):
                        apis_leitura[nome] = True
                        contagens[nome] = len(resultado)
                except Exception as exc:
                    erros[nome] = str(exc)

        pronto = (
            checks["tokensConfigurados"]
            and checks["throttling429"]
            and checks["paginacaoAlteradoApos"]
            and apis_leitura["clientes"]
            and apis_leitura["produtos"]
            and apis_leitura["pedidos"]
        )

        return {
            "prontoParaHomologacao": pronto,
            "ambiente": info,
            "criteriosObrigatorios": checks,
            "apisLeitura": apis_leitura,
            "contagens": contagens,
            "erros": erros,
            "documentacao": "https://docs.mercos.com/reference/homologação",
        }
