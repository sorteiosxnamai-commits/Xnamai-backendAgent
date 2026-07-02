from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt

from app.config.settings import JWT_ALGORITHM, JWT_SECRET

security = HTTPBearer()


def verificar_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return True

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )


def obter_usuario_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    return obter_token_payload(credentials).get("sub", "")


def obter_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        return {
            "sub": str(user_id),
            "email": payload.get("email"),
            "role": payload.get("role") or "user",
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


def requer_admin(
    payload: dict = Depends(obter_token_payload),
) -> dict:
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem executar esta ação")
    return payload
