from jose import jwt
from datetime import datetime, timedelta

from app.config.settings import JWT_ALGORITHM, JWT_SECRET


def criar_token(dados: dict):
    payload = dados.copy()

    payload["exp"] = datetime.utcnow() + timedelta(hours=12)

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
