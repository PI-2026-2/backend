from typing import Literal, NewType

from pydantic import BaseModel

class UsuarioCadastro(BaseModel):
    email    : str
    senha    : str
    nome     : str
    telefone : str
    tipo     : Literal["TERAPEUTA"] | Literal["PACIENTE"]

class UsuarioLogin(BaseModel):
    email : str
    senha : str
