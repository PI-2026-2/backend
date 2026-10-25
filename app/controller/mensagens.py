from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status

from app.database import SessionDep
from app.model.Mensagem import EnviarMensagem
from app.service.auth_service import AuthService

from ..service.message_service import MessageService

router = APIRouter(tags=["Mensagens"])

@router.get("/mensagens")
async def obter_mensagens(authorization: Annotated[str, Header()],id_outro_usuario : int ,message_service: Annotated[MessageService, Depends()], session: SessionDep, auth_service: Annotated[AuthService, Depends()]):
    token = authorization.split(" ")[1]
    return await message_service.obter_mensagens(token, id_outro_usuario,session, auth_service)

@router.post("/mensagens")
async def enviar_mensagem(authorization: Annotated[str, Header()], mensagem : EnviarMensagem, message_service: Annotated[MessageService, Depends()], session: SessionDep, auth_service: Annotated[AuthService, Depends()]):
    token = authorization.split(" ")[1]
    return await message_service.enviar_mensagem(mensagem, token, session, auth_service)
