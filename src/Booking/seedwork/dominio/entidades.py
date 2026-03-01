from dataclasses import dataclass
from abc import ABC

@dataclass
class Entidad(ABC):
    id: str

@dataclass
class AgregacionRaiz(Entidad, ABC):
    eventos: list = None

    def __post_init__(self):
        self.eventos = []

    def agregar_evento(self, evento):
        self.eventos.append(evento)

    def limpiar_eventos(self):
        self.eventos = []
