import time
import pytest
import threading
from uuid import uuid4
from sqlalchemy.orm.exc import StaleDataError

from modules.pms.application.commands.confirm_reservation import ConfirmReservation
from modules.pms.domain.entities import Reservation
from modules.pms.infrastructure.models import ReservationModel
from modules.pms.infrastructure.database import SessionLocal, Base, engine


class MockRepository:
    def __init__(self):
        self.db = SessionLocal()

    def obtain_by_reservation_id(self, reservation_id):
        return None  # Bypass simple check for this test

    def obtain_by_room_id(self, room_id):
        return None  # Bypass simple check for this test

    def save(self, reservation):
        
        # Simulating the exact repository save behavior
        model = ReservationModel(
            id=reservation.id,
            reservation_id=reservation.reservation_id,
            room_id=reservation.room_id,
            room_type=reservation.room_type,
            guest_name=reservation.guest_name,
            hotel_id=reservation.hotel_id,
            fecha_reserva=reservation.fecha_reserva,
            state=reservation.state,
            version=reservation.version
        )
        self.db.merge(model)
        self.db.commit()


class MockEventBus:
    def __init__(self):
        self.events = []

    def publish_event(self, routing_key, event_type, data):
        self.events.append(event_type)


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    room_id_test = "101"
    fecha_reserva_test = "2026-11-01"
    
    db.close()
    
    yield room_id_test, fecha_reserva_test # Pass room id and date to test
    
    Base.metadata.drop_all(bind=engine)


def test_concurrent_reservations_optimistic_locking(setup_db):
    room_id, fecha_reserva = setup_db
    
    repo1 = MockRepository()
    bus1 = MockEventBus()
    use_case_1 = ConfirmReservation(repo1, bus1)

    repo2 = MockRepository()
    bus2 = MockEventBus()
    use_case_2 = ConfirmReservation(repo2, bus2)
    
    # No PK mocking is needed anymore. Because of the UniqueConstraint on (room_id, fecha_reserva),
    # generating two different `id`s (UUIDs) will still result in the database natively blocking
    # the second INSERT with an `IntegrityError`. This is much cleaner and closer to reality.

    results = []

    def run_use_case(use_case, res_id, r_id, fecha):
        res = use_case.execute(res_id, r_id, fecha)
        results.append((res_id, res))

    # We start two threads attempting to book the same room, resolving to the same PK.
    t1 = threading.Thread(target=run_use_case, args=(use_case_1, "RES-1LA", room_id, fecha_reserva))
    t2 = threading.Thread(target=run_use_case, args=(use_case_2, "RES-2LB", room_id, fecha_reserva))

    t1.start()
    t2.start()

    t1.join()
    t2.join()
    
    t2.join()

    events_fired = bus1.events + bus2.events
    
    success_count = events_fired.count("ConfirmacionPmsExitosaEvt")
    failure_count = events_fired.count("ReservaRechazadaPmsEvt")

    # One must succeed (INSERT successful)
    assert success_count == 1
    # The other must fail (INSERT triggers IntegrityError because UNIQUE(room_id, fecha_reserva) constraint violated)
    assert failure_count == 1
