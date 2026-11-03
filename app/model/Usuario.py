from datetime import date
from typing import Literal, NewType

from pydantic import BaseModel

from app.model.enums import TipoUsuarioEnum

class UsuarioCadastro(BaseModel):
    email    : str
    senha    : str
    nome     : str
    telefone : str
    data_nascimento: date
    genero: str
    tipo     : Literal["TERAPEUTA"] | Literal["PACIENTE"]

class UsuarioLogin(BaseModel):
    email : str
    senha : str

class InformacoesUsuarioLogin(BaseModel):
    id : int
    email : str
    nome_completo : str
    tipo_usuario  : TipoUsuarioEnum 
