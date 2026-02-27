from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Comando(ABC):
    ...

class Handler(ABC):
    @abstractmethod
    def handle(self, comando: Comando):
        raise NotImplementedError()

def ejecutar_comando(comando: Comando):
    # Aquí irá un event bus simple o mapeo directo
    raise NotImplementedError("El ruteador de comandos será implementado en el dispatcher/mediator")
