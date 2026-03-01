from abc import ABC, abstractmethod
from typing import List

class UnidadTrabajo(ABC):
    @abstractmethod
    def __enter__(self):
        ...

    @abstractmethod
    def __exit__(self, type, value, traceback):
        ...

    @abstractmethod
    def commit(self):
        ...

    @abstractmethod
    def rollback(self):
        ...

    @abstractmethod
    def agregar_eventos(self, eventos: List):
        """Agrega los eventos generados por el dominio a la cola de la UoW para despacharlos post-commit"""
        ...
