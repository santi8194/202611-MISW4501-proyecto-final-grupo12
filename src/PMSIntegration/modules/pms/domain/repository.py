from abc import ABC, abstractmethod
from modules.pms.domain.entities import Reservation


class ReservationRepository(ABC):

    @abstractmethod
    def save(self, reservation: Reservation):
        pass