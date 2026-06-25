from fastapi import FastAPI

from app.routes.cliente import router as cliente_router
from app.routes.produto import router as produto_router
from app.routes.login import router as login_router
from app.routes.database import router as database_router

app = FastAPI(
    title="Xnamai Backend",
    version="1.0.0"
)

app.include_router(
    login_router,
    prefix="/auth",
    tags=["Auth"]
)

app.include_router(
    cliente_router,
    prefix="/mercos",
    tags=["Mercos"]
)

app.include_router(
    produto_router,
    prefix="/mercos",
    tags=["Mercos"]
)

app.include_router(
    database_router,
    prefix="/database",
    tags=["Database"]
)

@app.get("/")
def home():
    return {
        "status": "online"
    }