from fastapi import HTTPException, status

from app.core.password import hash_senha
from app.repositories.usuario_repository import UsuarioRepository

PERFIS_VALIDOS = {"admin", "supervisor", "vendedor", "user"}


class UsuarioService:

    def __init__(self):
        self.repository = UsuarioRepository()

    def _mapear(self, usuario: dict) -> dict:
        return {
            "id": str(usuario.get("id")),
            "name": usuario.get("nome") or usuario.get("email", "").split("@")[0],
            "email": usuario.get("email", ""),
            "role": usuario.get("perfil") or "user",
            "company": usuario.get("empresa") or "PulseDesk",
            "active": usuario.get("ativo") is not False,
            "createdAt": usuario.get("created_at"),
        }

    def listar(self) -> list[dict]:
        return [self._mapear(u) for u in self.repository.listar()]

    def criar(
        self,
        *,
        name: str,
        email: str,
        password: str,
        role: str = "user",
        company: str | None = None,
    ) -> dict:
        email_normalizado = email.strip().lower()
        perfil = (role or "user").strip().lower()

        if perfil not in PERFIS_VALIDOS:
            raise HTTPException(status_code=400, detail="Perfil inválido")

        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Senha deve ter no mínimo 6 caracteres")

        if self.repository.buscar_por_email(email_normalizado):
            raise HTTPException(status_code=409, detail="Este e-mail já está cadastrado")

        dados = {
            "email": email_normalizado,
            "senha_hash": hash_senha(password),
            "nome": name.strip(),
            "perfil": perfil,
            "ativo": True,
        }
        if company and company.strip():
            dados["empresa"] = company.strip()

        usuario = self.repository.criar(dados)
        return self._mapear(usuario)

    def atualizar(
        self,
        usuario_id: str,
        *,
        actor_id: str,
        actor_role: str,
        name: str | None = None,
        role: str | None = None,
        active: bool | None = None,
        company: str | None = None,
    ) -> dict:
        usuario = self.repository.buscar_por_id(usuario_id)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        is_admin = actor_role == "admin"
        if not is_admin and actor_id != usuario_id:
            raise HTTPException(status_code=403, detail="Sem permissão para alterar este usuário")

        dados: dict = {}

        if name is not None and name.strip():
            dados["nome"] = name.strip()

        if company is not None:
            dados["empresa"] = company.strip() or None

        if is_admin:
            if role is not None:
                perfil = role.strip().lower()
                if perfil not in PERFIS_VALIDOS:
                    raise HTTPException(status_code=400, detail="Perfil inválido")
                dados["perfil"] = perfil

            if active is not None:
                if actor_id == usuario_id and active is False:
                    raise HTTPException(
                        status_code=400,
                        detail="Você não pode desativar sua própria conta",
                    )
                dados["ativo"] = active

        if not dados:
            return self._mapear(usuario)

        atualizado = self.repository.atualizar(usuario_id, dados)
        return self._mapear(atualizado or usuario)


usuario_service = UsuarioService()
