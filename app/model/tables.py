from datetime import date, datetime
from operator import index
from typing import Literal
from pydantic import EmailStr
from sqlalchemy.orm import foreign
from sqlalchemy.orm.relationships import _RelationshipDeclared
from sqlmodel import ARRAY, Column, Field, Relationship, SQLModel, String, JSON, UniqueConstraint, table, Enum
import uuid

from enums import RespostasCartasEnum, StatusProgramacoesSemanaisEnum, StatusUsuario, TipoUsuarioEnum



class Usuarios(SQLModel, table=True):
    id : int = Field(default=None, primary_key=True)
    email : str = Field(unique=True)
    senha_hash : str = Field()
    tipo : TipoUsuarioEnum = Field(
        sa_column=Column(Enum(TipoUsuarioEnum), nullable=False)
    )

    terapeutas : list["PerfisTerapeutas"] = Relationship(back_populates="usuarios")
    pacientes : list["PerfisPacientes"] = Relationship(back_populates="usuarios")
    cartas_criadas : list["Cartas"] = Relationship(back_populates="usuarios")

class PerfisTerapeutas(SQLModel, table=True):
    __tablename__ = "perfis_terapeutas"
    
    id : int = Field(default=None, primary_key=True)
    nome: str = Field()
    registro_profissional : str = Field()
    especialidade : str = Field()
    descricao : str = Field()
    telefone : str = Field()
    status : StatusUsuario = Field(
        sa_column=Column(Enum(StatusUsuario), nullable=False)
    )
    usuario_id : int = Field(foreign_key="usuarios.id", unique=True)

    usuario : Usuarios = Relationship(back_populates="perfis_terapeutas")

    pacientes : list["PerfisPacientes"] = Relationship(back_populates="perfis_terapeutas")
    programacoes_semanais : list["ProgramacoesSemanais"] = Relationship(back_populates="perfis_terapeutas")
    avaliacoes : list["AvaliacoesTerapeutas"] = Relationship(back_populates="perfis_terapeutas")
    anotacoes : list["AnotacoesTerapeutas"] = Relationship(back_populates="perfis_terapeutas")
    laudos_pacientes : list["LaudosPacientes"] = Relationship(back_populates="perfis_terapeutas")

class PerfisPacientes(SQLModel, table=True):
    __tablename__ = "perfis_pacientes"
    
    id : int = Field(default=None, primary_key=True)
    nome : str = Field()
    telefone : str = Field()
    data_nascimento : date = Field()
    genero : str = Field()
    status : StatusUsuario = Field(
        sa_column=Column(Enum(StatusUsuario), nullable=False)
    )

    usuario_id : int = Field(foreign_key="usuarios.id", unique=True)
    terapeuta_id : int = Field(foreign_key="perfis_terapeutas.id")

    usuario : Usuarios = Relationship(back_populates="perfis_pacientes")

    programacoes_semanais : list["ProgramacoesSemanais"] = Relationship(back_populates="perfis_pacientes")
    respostas_cartas : list["RespostasCartas"] = Relationship(back_populates="perfis_pacientes")
    anotacoes_terapeutas : list["AnotacoesTerapeutas"] = Relationship(back_populates="perfis_pacientes")
    laudos : list["LaudosPacientes"] = Relationship(back_populates="perfis_pacientes")

    

class Cartas(SQLModel, table=True):
    id : int = Field(default=None, primary_key=True)
    frente : str = Field()
    verso : str = Field()
    ativa : bool = Field(default=True)
    
    criado_por_usuario_id : int = Field(foreign_key="usuarios.id")

    usuario : Usuarios = Relationship(back_populates="cartas")

    cartas_etiquetas : list["CartasEtiquetas"] = Relationship(back_populates="cartas")
    programacao_cartas : list["ProgramacoesCartas"] = Relationship(back_populates="cartas")
    

class ProgramacoesCartas(SQLModel, table=True):
    __tablename__ = "programacoes_cartas"
    __table_args__ = (
        UniqueConstraint("programacao_id", "carta_id")
    )
    id : int = Field(default=None, primary_key=True)
    
    programacao_id : int = Field(foreign_key="programacoes_semanais.id", index=True)
    carta_id : int = Field(foreign_key="cartas.id", index=True)

    programacao_semanal : ProgramacoesSemanais = Relationship(back_populates="programacoes_cartas")
    carta : Cartas = Relationship(back_populates="programacoes_cartas")

    respostas_cartas : list["ProgramacoesCartas"] = Relationship(back_populates="programacoes_cartas")
    

class AvaliacoesTerapeutas(SQLModel, table=True):
    __tablename__ = "avaliacoes_terapeutas"
    
    id : int = Field(default=None, primary_key=True)
    avaliacao : str = Field()
    nota : int = Field()
    criado_em : datetime = Field()

    resposta_id : int = Field(foreign_key="respostas_cartas.id")
    terapeuta_id : int = Field(foreign_key="perfis_terapeutas.id")

    resposta : RespostasCartas = Relationship(back_populates="avaliacoes_terapeutas")
    terapeuta : PerfisTerapeutas = Relationship(back_populates="avaliacoes_terapeutas")

class ProgramacoesSemanais(SQLModel, table=True):
    __tablename__ = "programacoes_semanais"
    __tableargs__ = (
        ("paciente_id", "inicio_semana")
    )
    
    id : int = Field(default=None, primary_key=True)
    inicio_semana : date = Field(index=True)
    fim_semana : date = Field()
    status: StatusProgramacoesSemanaisEnum = Field(
        sa_column=Column(Enum(StatusProgramacoesSemanaisEnum), nullable=False)
    )
    criado_em : datetime = Field()

    terapeuta_id : int = Field(foreign_key="perfis_terapeutas.id")
    paciente_id : int = Field(foreign_key="perfis_pacientes.id", index=True)

    terapeuta : PerfisTerapeutas = Relationship(back_populates="programacoes_semanais")
    paciente : PerfisPacientes = Relationship(back_populates="programacoes_semanais")

    programacao_cartas : list["ProgramacoesCartas"] = Relationship(back_populates="programacao_cartas")
    

class AnotacoesTerapeutas(SQLModel, table=True):
    __tablename__ = "anotacoes_terapeutas"
    
    id : int = Field(default=None, primary_key=True)
    titulo : str = Field()
    conteudo : str = Field()
    criado_em : datetime = Field()
    
    terapeuta_id : int = Field(foreign_key="perfis_terapeutas.id")
    paciente_id : int = Field(foreign_key="perfis_pacientes.id")

    terapeuta : PerfisTerapeutas = Relationship(back_populates="anotacoes_terapeutas")
    paciente : PerfisPacientes = Relationship(back_populates="anotacoes_terapeutas")

class RespostasCartas(SQLModel, table=True):
    __tablename__ = "respostas_cartas"
    
    id : int = Field(default=None, primary_key=True)
    texto : str | None = Field(default=None)
    status : RespostasCartasEnum = Field(
        sa_column=Column(Enum(RespostasCartasEnum), nullable=False, default=RespostasCartasEnum.PENDENTE)
    )
    respondida_em : datetime = Field()

    programacao_carta_id : int = Field(foreign_key="programacao_cartas.id", unique=True)
    paciente_id : int = Field(foreign_key="perfis_pacientes.id")

    programacao_carta : ProgramacoesCartas = Relationship(back_populates="respostas_cartas")
    paciente : PerfisPacientes = Relationship(back_populates="respostas_cartas")

    avaliacoes_terapeutas : list["AvaliacoesTerapeutas"] = Relationship(back_populates="respostas_cartas")
    

class LaudosPacientes(SQLModel, table=True):
    __tablename__ = "laudos_pacientes"
    
    id : int = Field(default=None, primary_key=True)
    titulo : str = Field()
    conteudo : str = Field()
    criado_em : datetime = Field()
    
    paciente_id : int = Field(foreign_key="perfis_pacientes.id")
    criado_por_terapeuta_id : int = Field(foreign_key="perfis_terapeutas.id")

    paciente : PerfisPacientes = Relationship(back_populates="laudos_pacientes")
    terapeuta : PerfisTerapeutas = Relationship(back_populates="laudos_pacientes")
    

class Etiquetas(SQLModel, table=True):
    id : int = Field(default=None, primary_key=True)
    nome : str = Field(unique=True)
    
    cartas_etiquetas : CartasEtiquetas = Relationship(back_populates="etiquetas")

class CartasEtiquetas(SQLModel, table=True):
    __tablename__ = "cartas_etiquetas"
    
    carta_id : int = Field(foreign_key="cartas.id", index=True)
    etiqueta_id : int = Field(foreign_key="etiquetas.id", index=True)

    carta : Cartas = Relationship(back_populates="cartas_etiquetas")
    etiqueta : Etiquetas = Relationship(back_populates="cartas_etiquetas")
