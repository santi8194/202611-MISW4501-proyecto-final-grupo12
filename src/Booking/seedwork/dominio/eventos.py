from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class EventoDominio:
    id: uuid.UUID = field(hash=True, default_factory=uuid.uuid4)
    fecha_creacion: datetime = field(default_factory=datetime.now)
