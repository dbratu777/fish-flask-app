import random
import datetime
import time
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Measurement(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    reported_value = Column(Float, nullable=True)
    set_value = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

    @classmethod
    def create_with_last_known(cls, session):
        last_record = session.query(cls).order_by(cls.timestamp.desc()).first()
        if last_record:
            reported_value = last_record.reported_value
            set_value = last_record.set_value
        else:
            reported_value = 0.0
            set_value = 0.0
        
        return cls(reported_value=reported_value, set_value=set_value)

class Temperature(Measurement):
    __tablename__ = 'temperatures'

    @classmethod
    def create_with_last_known(cls, session):
        return super().create_with_last_known(session)

class PH(Measurement):
    __tablename__ = 'ph_levels'

    @classmethod
    def create_with_last_known(cls, session):
        return super().create_with_last_known(session)

class DissolvedOxygen(Measurement):
    __tablename__ = 'dissolved_oxygen_levels'

    @classmethod
    def create_with_last_known(cls, session):
        return super().create_with_last_known(session)

class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True)
    type = Column(Integer, nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(String(200), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    read = Column(Boolean, default=False)

# Set up the database engine
engine = create_engine('sqlite:///instance/values.db', echo=True) 
Base.metadata.create_all(engine)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()

def generate_random_temperature():
    new_temperature = Temperature.create_with_last_known(session)
    new_temperature.reported_value = random.uniform(65.0, 85.0)
    new_temperature.timestamp = datetime.datetime.now(datetime.timezone.utc)
    return new_temperature

def generate_random_ph():
    new_ph = PH.create_with_last_known(session)
    new_ph.reported_value = random.uniform(6.5, 8.5)
    new_ph.timestamp = datetime.datetime.now(datetime.timezone.utc)
    return new_ph

def generate_random_oxygen():
    new_oxygen = DissolvedOxygen.create_with_last_known(session)
    new_oxygen.reported_value = random.uniform(6.5, 8.5)
    new_oxygen.timestamp = datetime.datetime.now(datetime.timezone.utc)
    return new_oxygen

def generate_random_alert():
    titles = ["Temperature Alert", "pH Alert", "Oxygen Level Alert"]
    descriptions = [
        "The temperature exceeded the set threshold.",
        "The pH level dropped below the critical value.",
        "Oxygen levels are dangerously low.",
    ]
    type = random.randint(0, 2)
    read = False
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    title = titles[type]
    description = descriptions[type]
    return Alert(type=type, title=title, description=description, timestamp=timestamp, read=read)

def insert_random_data():
    temp_record = generate_random_temperature()
    session.add(temp_record)

    time.sleep(5)
    ph_record = generate_random_ph()
    session.add(ph_record)

    time.sleep(5)
    oxygen_record = generate_random_oxygen()
    session.add(oxygen_record)

    time.sleep(5)
    alert_record = generate_random_alert()
    session.add(alert_record)

    session.commit()

try:
    while True:
        insert_random_data()
        print("Inserted random data into the database.")
        time.sleep(5)
except KeyboardInterrupt:
    print("Data insertion stopped.")
finally:
    session.close()
