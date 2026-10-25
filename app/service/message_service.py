from typing import Annotated
from datetime import datetime
from copy import deepcopy

from fastapi import Depends
from sqlmodel import select

from app.database import SessionDep
from app.model.Mensagem import EnviarMensagem
from app.model.enums import TipoUsuarioEnum
from app.model.tables import Mensagens, Usuarios
from app.service.auth_service import AuthService, TokenData


class MessageService:
    async def obter_mensagens(self, token : str, id_outro_usuario : int, session: SessionDep, auth_service: Annotated[AuthService, Depends()]):
        usuario = await auth_service.obter_usuario_atual(token, session)
        tipo_usuario = auth_service.obter_tipo_usuario(usuario)
        if tipo_usuario == 'PACIENTE':
            mensagens = session.exec(
                select(Mensagens).where(
                    Mensagens.paciente_id == usuario.pacientes[0].id
                ).where(
                    Mensagens.terapeuta_id == id_outro_usuario
                )
            ).one_or_none()
            return mensagens
        else:
            mensagens = session.exec(
                select(Mensagens).where(
                    Mensagens.terapeuta_id == usuario.terapeutas[0].id
                ).where(
                    Mensagens.paciente_id == id_outro_usuario
                )
            ).one_or_none()
            return mensagens

    async def enviar_mensagem(self, mensagem : EnviarMensagem, token : str, session: SessionDep, auth_service: Annotated[AuthService, Depends()]):
        usuario = await auth_service.obter_usuario_atual(token, session)
        tipo_usuario = auth_service.obter_tipo_usuario(usuario)
        if tipo_usuario == 'PACIENTE':
            mensagens = session.exec(
                select(Mensagens).where(
                    Mensagens.paciente_id == usuario.pacientes[0].id
                ).where(
                    Mensagens.terapeuta_id == mensagem.id_outro_usuario
                )
            ).one_or_none()
            if mensagens == None:
                mensagens = Mensagens(
                    paciente_id=usuario.pacientes[0].id,
                    terapeuta_id=mensagem.id_outro_usuario,
                    mensagens = []
                )
            lista_mensagens = deepcopy(mensagens.mensagens)
            lista_mensagens.append(
                  {
                    "actor"    : TipoUsuarioEnum.TERAPEUTA,
                    "datetime" : str(datetime.now()),
                    "message"  : mensagem.message
                  }
            )
            mensagens.mensagens = lista_mensagens
            session.add(mensagens)
        else:
            mensagens = session.exec(
                select(Mensagens).where(
                    Mensagens.terapeuta_id == usuario.terapeutas[0].id
                ).where(
                    Mensagens.paciente_id == mensagem.id_outro_usuario
                )
            ).one_or_none()
            if mensagens == None:
                mensagens = Mensagens(
                    paciente_id= mensagem.id_outro_usuario,
                    terapeuta_id= usuario.terapeutas[0].id,
                    mensagens=[]
                )
            lista_mensagens = deepcopy(mensagens.mensagens)
            lista_mensagens.append(
                  {
                    "actor"    : TipoUsuarioEnum.TERAPEUTA,
                    "datetime" : str(datetime.now()),
                    "message"  : mensagem.message
                  }
            )
            mensagens.mensagens = lista_mensagens
            session.add(mensagens)
        session.commit()
        return None
