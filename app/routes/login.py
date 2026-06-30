from fastapi import APIRouter

from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


@router.post("/login")
def login(credentials: LoginRequest):
    return auth_service.login(
        email=credentials.email,
        password=credentials.password,
    )


@router.post("/register")
def register(body: RegisterRequest):
    return auth_service.register(
        name=body.name,
        email=body.email,
        password=body.password,
        company=body.company,
    )
