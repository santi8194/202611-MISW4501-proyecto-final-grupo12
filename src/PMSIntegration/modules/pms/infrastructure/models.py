from sqlalchemy import Column, String, Integer, Index
from .database import Base

class ReservationModel(Base):
    __tablename__ = "reservations"

    id = Column(String, primary_key=True)
    reservation_id = Column(String)
    room_id = Column(String)
    room_type = Column(String)
    guest_name = Column(String)
    state = Column(String)
    hotel_id = Column(String)
    fecha_reserva = Column(String)
    version = Column(Integer, nullable=False, default=1)

    # -----------------------------------------------------------------------
    # Protección contra overbooking con historial completo:
    #
    # Índice único PARCIAL (solo PostgreSQL):
    #   - Solo aplica cuando state != 'CANCELLED'.
    #   - Permite N registros CANCELLED para (room_id, fecha_reserva),
    #     preservando el historial de cancelaciones.
    #   - Bloquea atómicamente un segundo registro ACTIVO para la misma
    #     habitación y fecha, eliminando el race condition TOCTOU.
    #   - En SQLite (entorno local / fallback), este índice es ignorado.
    #     La validación recae en obtain_active_by_room_and_date().
    # -----------------------------------------------------------------------
    __table_args__ = (
        Index(
            'idx_room_date_active',
            'room_id',
            'fecha_reserva',
            unique=True,
            postgresql_where=(Column('state') != 'CANCELLED')
        ),
    )

    # Bloqueo Optimista: protege actualizaciones concurrentes al mismo registro.
    # SQLAlchemy lanzará StaleDataError si la versión no coincide en un UPDATE.
    __mapper_args__ = {
        "version_id_col": version
    }