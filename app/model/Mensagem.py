from pydantic import BaseModel


class EnviarMensagem(BaseModel):
    message  : str
    id_outro_usuario : int
