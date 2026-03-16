from sqlalchemy import create_engine, Column, String, Integer, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()

class TestModel(Base):
    __tablename__ = 'test_table'
    id = Column(String, primary_key=True)
    room = Column(String)
    fecha = Column(String)

    __table_args__ = (
        UniqueConstraint('room', 'fecha', name='uq_room_fecha'),
    )

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

try:
    session.add(TestModel(id="1", room="101", fecha="2026"))
    session.commit()
    print("First insert passed")
    
    session.add(TestModel(id="2", room="101", fecha="2026"))
    session.commit()
    print("Second insert passed! ERROR!")
except Exception as e:
    print(f"Exception caught: {type(e)}")

