from enum import Enum

class TipoUsuarioEnum(str, Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    TERAPEUTA     = "TERAPEUTA"
    PACIENTE      = "PACIENTE"
    
class StatusProgramacoesSemanaisEnum(str, Enum):
    ABERTA        = "ABERTA"
    CONCLUIDA     = "CONCLUIDA"
    EXPIRADA      = "EXPIRADA"

class RespostasCartasEnum(str, Enum):
    PENDENTE      = "PENDENTE"
    RESPONDIDA    = "RESPONDIDA"

class StatusUsuario(str, Enum):
    ATIVO         = "ATIVO"
    INATIVO       = "INATIVO"
