from fastapi import APIRouter

router = APIRouter(tags=["Autenticação"])


@router.post("/login")
async def login():
    return {"message": "Login realizado"}


@router.post("/cadastro")
async def cadastro():
    return {"message": "Cadastro realizado"}