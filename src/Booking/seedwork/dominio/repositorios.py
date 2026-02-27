from abc import ABC, abstractmethod
from typing import List
from Booking.seedwork.dominio.entidades import Entidad

class Repositorio(ABC):
    @abstractmethod
    def agregar(self, entidad: Entidad):
        ...

    @abstractmethod
    def actualizar(self, entidad: Entidad):
        ...
        
    @abstractmethod
    def eliminar(self, entidad_id: str):
        ...

    @abstractmethod
    def obtener_por_id(self, id: str) -> Entidad:
        ...

    @abstractmethod
    def obtener_todos(self) -> List[Entidad]:
        ...
