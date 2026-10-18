from typing import Annotated

from fastapi import APIRouter, Body, Depends

from app.database import SessionDep
from app.model.Usuario import UsuarioCadastro, UsuarioLogin

from ..service.auth_service import AuthService

router = APIRouter(tags=["Autenticação"])


@router.post("/login")
async def login(login : UsuarioLogin, auth_service: Annotated[AuthService, Depends()], session: SessionDep):
    token = await auth_service.login_obter_token(form_data=login, session=session)
    return {"token": token}


@router.post("/cadastro")
async def cadastro(cadastro: UsuarioCadastro, auth_service: Annotated[AuthService, Depends()], session: SessionDep):
    resultado = auth_service.cadastrar(cadastro, session)
    return {"cadastro" : resultado}

    
