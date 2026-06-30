from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "xnamai_secret_key"
ALGORITHM = "HS256"


def criar_token(dados: dict):
    payload = dados.copy()

    payload["exp"] = datetime.utcnow() + timedelta(hours=12)

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )