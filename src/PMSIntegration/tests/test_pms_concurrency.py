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
    # Insert a dummy base record that both threads will try to 'UPDATE' conceptually, 
    # Or in our case since it's an UPSERT (merge) with optimistic locking, 
    # we need the record to already exist so the version check triggers on the second thread.
    
    room_id_test = "101"
    initial_res = ReservationModel(
        id=str(uuid4()),
        reservation_id="BASE-ID-123",
        room_id=room_id_test,
        room_type="SUITE",
        guest_name="Base User",
        state="AVAILABLE",
        hotel_id="HotelXYZ",
        version=1
    )
    db.add(initial_res)
    db.commit()
    db.close()
    
    yield room_id_test # Pass room id to test
    
    Base.metadata.drop_all(bind=engine)


def test_concurrent_reservations_optimistic_locking(setup_db):
    room_id = setup_db
    
    repo1 = MockRepository()
    bus1 = MockEventBus()
    use_case_1 = ConfirmReservation(repo1, bus1)

    repo2 = MockRepository()
    bus2 = MockEventBus()
    use_case_2 = ConfirmReservation(repo2, bus2)
    
    # We need to forcefully make them update the SAME database record to trigger the optimistic lock StaleDataError.
    # Because `create()` generates a random `id` and `merge()` upserts based on Primary Key (`id`),
    # if they have different `id`s, they will just INSERT two different rows and locking won't trigger.
    # Let's intercept the `create` to force them to use the SAME PK so they collide on update.
    
    # Get the PK of the base record
    db = SessionLocal()
    base_record = db.query(ReservationModel).filter_by(room_id=room_id).first()
    shared_pk = base_record.id
    db.close()
    
    original_create = Reservation.create
    
    def mocked_create(*args, **kwargs):
        res = original_create(*args, **kwargs)
        res.id = shared_pk  # Force same PK so `merge` translates to `UPDATE`
        return res
        
    Reservation.create = staticmethod(mocked_create)

    results = []

    def run_use_case(use_case, res_id, r_id):
        res = use_case.execute(res_id, r_id)
        results.append((res_id, res))

    # We start two threads attempting to book the same room, resolving to the same PK.
    t1 = threading.Thread(target=run_use_case, args=(use_case_1, "RES-1LA", room_id))
    t2 = threading.Thread(target=run_use_case, args=(use_case_2, "RES-2LB", room_id))

    t1.start()
    t2.start()

    t1.join()
    t2.join()
    
    # Restore original method
    Reservation.create = staticmethod(original_create)

    events_fired = bus1.events + bus2.events
    
    success_count = events_fired.count("ConfirmacionPmsExitosaEvt")
    failure_count = events_fired.count("ReservaRechazadaPmsEvt")

    # One must succeed (UPDATE version 1 -> 2)
    assert success_count == 1
    # The other must fail (UPDATE version 1 -> 2 triggers StaleDataError because version is already 2)
    assert failure_count == 1
