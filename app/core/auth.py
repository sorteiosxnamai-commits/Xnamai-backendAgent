from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt

SECRET_KEY = "xnamai_secret_key"
ALGORITHM = "HS256"

security = HTTPBearer()

def verificar_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        jwt.get_unverified_claims(token)

        return True

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )