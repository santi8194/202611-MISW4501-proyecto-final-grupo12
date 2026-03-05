from abc import ABC, abstractmethod

class Despachador(ABC):
    """
    Abstracción sobre el broker de mensajería (Puerto).
    Define el contrato para publicar eventos y comandos.
    """

    @abstractmethod
    def publicar_evento(self, evento, topico: str):
        """
        Publica un evento de dominio transformado a un evento de integración.
        """
        pass

    @abstractmethod
    def publicar_comando(self, comando, routing_key: str):
        """
        Publica un comando para la ejecución de una acción por otro servicio.
        """
        pass

    @abstractmethod
    def cerrar(self):
        """
        Cierra la conexión o libera recursos del despachador, si es necesario.
        """
        pass
