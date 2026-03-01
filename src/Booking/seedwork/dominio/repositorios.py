from abc import ABC, abstractmethod
from typing import List, Any
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

class Mapeador(ABC):
    @abstractmethod
    def obtener_tipo(self) -> type:
        ...

    @abstractmethod
    def entidad_a_dto(self, entidad: Entidad) -> Any:
        ...

    @abstractmethod
    def dto_a_entidad(self, dto: Any) -> Entidad:
        ...
