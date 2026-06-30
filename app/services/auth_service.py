from fastapi import HTTPException, status

from app.core.password import hash_senha, verificar_senha
from app.core.security import criar_token
from app.repositories.usuario_repository import UsuarioRepository


class AuthService:

    def __init__(self):
        self.repository = UsuarioRepository()

    def login(self, email: str, password: str) -> dict:
        usuario = self.repository.buscar_por_email(email)

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos",
            )

        if usuario.get("ativo") is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo",
            )

        senha_hash = usuario.get("senha_hash") or ""
        if not verificar_senha(password, senha_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos",
            )

        user = self._mapear_usuario(usuario)
        token = criar_token({
            "sub": str(usuario.get("id")),
            "email": user["email"],
            "role": user["role"],
        })

        return {"token": token, "user": user}

    def register(self, name: str, email: str, password: str, company: str | None = None) -> dict:
        email_normalizado = email.strip().lower()

        if self.repository.buscar_por_email(email_normalizado):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este e-mail já está cadastrado",
            )

        usuario = self.repository.criar({
            "email": email_normalizado,
            "senha_hash": hash_senha(password),
            "nome": name.strip(),
            "perfil": "user",
            "ativo": True,
        })

        user = self._mapear_usuario(usuario)
        if company:
            user["company"] = company.strip()

        token = criar_token({
            "sub": str(usuario.get("id")),
            "email": user["email"],
            "role": user["role"],
        })

        return {"token": token, "user": user}

    def _mapear_usuario(self, usuario: dict) -> dict:
        return {
            "id": str(usuario.get("id")),
            "name": usuario.get("nome") or usuario.get("email", "").split("@")[0],
            "email": usuario.get("email", ""),
            "role": usuario.get("perfil") or "user",
            "company": "PulseDesk",
            "avatar": usuario.get("avatar"),
        }
