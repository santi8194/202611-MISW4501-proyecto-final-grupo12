import time
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from modules.pms.domain.entities import Reservation
from modules.pms.domain.events import (
    PMSReservationConfirmed,
    PMSReservationFailed
)

class ConfirmReservation:

    def __init__(self, repository, event_bus):
        self.repository = repository
        self.event_bus = event_bus

    def execute(self, id_reserva, id_habitacion, fecha_reserva):

        existing_reservation = self.repository.obtain_by_reservation_id(id_reserva)

        print(f"[PMS] Checking existing reservation for id {id_reserva}: {'Found' if existing_reservation else 'Not found'}")

        if existing_reservation:
            return {
                "message": "Reservation already processed",
                "current_reservation_id": existing_reservation.reservation_id,
            }

        # La validacion de habitacion ocupada ahora la hace el PK de la BD (room_id + fecha_reserva)
        # pero mantenemos el sleep para simular latencia y forzar colisiones en los tests.
        time.sleep(0.5)

        try:
            pmsReservation = Reservation.create(
                id_reserva,
                id_habitacion,
                "SUITE",
                "User123",
                "HotelXYZ",
                fecha_reserva
            )

            self.repository.save(pmsReservation)

            # 4. Generar evento de éxito
            pms_event = PMSReservationConfirmed(
                pms_id=pmsReservation.id,
                reservation_id=id_reserva,
                fecha_reserva=fecha_reserva
            )
            self.event_bus.publish_event(
                routing_key=pms_event.routing_key,
                event_type=pms_event.type,
                payload=pms_event.to_dict()
            )

            return pms_event.to_dict()

        except IntegrityError:
            print(f"[PMS] IntegrityError caught for room {id_habitacion} on {fecha_reserva}. Overbooking avoided.")
            
            pms_event = PMSReservationFailed(
                reservation_id=id_reserva,
                reason="Protección contra overbooking: Habitación ya reservada para esta fecha.",
                fecha_reserva=fecha_reserva
            )
        except StaleDataError:
            print(f"[PMS] StaleDataError caught for room {id_habitacion}. Overbooking avoided.")
            pms_event = PMSReservationFailed(
                reservation_id=id_reserva,
                reason="Protección contra overbooking: Habitación ya reservada para esta fecha (Lock Optimista).",
                fecha_reserva=fecha_reserva
            )
        except Exception as e:
            print(f"[PMS] Error inesperado en PMS: {str(e)}")
            pms_event = PMSReservationFailed(
                reservation_id=id_reserva,
                reason=str(e),
                fecha_reserva=fecha_reserva
            )

        # Publicar el evento de fallo
        self.event_bus.publish_event(
            routing_key=pms_event.routing_key,
            event_type=pms_event.type,
            payload=pms_event.to_dict()
        )

        return {
            "event_generated": pms_event.type,
            "motivo": pms_event.reason
        }