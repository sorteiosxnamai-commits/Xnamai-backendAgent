from fastapi import APIRouter
from app.core.security import criar_token

router = APIRouter()


@router.post("/login")
def login():

    token = criar_token({
        "usuario": "admin"
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }