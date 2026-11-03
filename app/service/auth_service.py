from __future__ import annotations

from typing import Annotated, Tuple

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionDep
from app.model.Usuario import InformacoesUsuarioLogin, UsuarioCadastro, UsuarioLogin
from app.model.enums import TipoUsuarioEnum
from app.model.tables import Usuarios
from dotenv import dotenv_values
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
import jwt

config = dotenv_values(".env")

SECRET_KEY = config["SECRET_KEY"]
assert SECRET_KEY != None
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 14 # 14 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
password_hash = PasswordHash.recommended()
credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
)

class AuthService:
    def cadastrar(self, cadastro : UsuarioCadastro, session: SessionDep):
        usuario = Usuarios(
                nome=cadastro.nome,
                telefone=cadastro.telefone,
                data_nascimento=cadastro.data_nascimento,
                genero=cadastro.genero,
                email= cadastro.email,
                senha_hash= self.obter_hash_senha(cadastro.senha),
                tipo=TipoUsuarioEnum(cadastro.tipo)
            )
        session.add(usuario)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(status_code=409, detail="E-mail já cadastrado")
        session.refresh(usuario)
        return usuario

    async def login_obter_token(
            self, form_data: Annotated[UsuarioLogin, Depends()], session : SessionDep,
    ) -> Tuple[Token, InformacoesUsuarioLogin]:
        usuario = self.autenticar_usuario(form_data.email,form_data.senha, session)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.criar_token(
            data={"sub": usuario.email}, expires_delta=access_token_expires
        )
        return (
            Token(access_token=access_token, token_type="bearer"),
            InformacoesUsuarioLogin(
                id=usuario.id,
                email=usuario.email,
                nome_completo=usuario.nome,
                tipo_usuario=self.obter_tipo_usuario(usuario)
            )
        )

    def verificar_senha(self, senha : str, hash_senha : str):
        return password_hash.verify(senha, hash_senha)

    def obter_hash_senha(self, senha : str):
        return password_hash.hash(senha)

    def criar_token(self, data : dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def obter_usuario_atual(self, token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep) -> Usuarios:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            if email is None:
                raise credentials_exception
        except jwt.InvalidTokenError:
            raise credentials_exception
        usuario = session.exec(select(Usuarios).where(Usuarios.email == email)).first()
        if usuario is None:
            raise credentials_exception
        return usuario

    def autenticar_usuario(self, email: str, password: str, session : SessionDep):
        usuario = session.exec(select(Usuarios).where(Usuarios.email == email)).first()
        if usuario is None:
            raise credentials_exception
        if not self.verificar_senha(password, usuario.senha_hash):
            return False
        return usuario

    def obter_tipo_usuario(self, usuario: Usuarios) -> TipoUsuarioEnum:
        return usuario.tipo


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
