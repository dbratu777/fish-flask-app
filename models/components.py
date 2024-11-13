from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

db = SQLAlchemy()

# Base class to handle common fields
class Measurement(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    reported_value = db.Column(db.Float, nullable=True)
    set_value = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    
class Temperature(Measurement):
    __tablename__ = 'temperatures'

class PH(Measurement):
    __tablename__ = 'ph_levels'

class DissolvedOxygen(Measurement):
    __tablename__ = 'dissolved_oxygen_levels'

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    read = db.Column(db.Boolean, default=False)
    
class Feeder(db.Model):
    __tablename__ = 'feeder'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)

class Maintenance(db.Model):
    __tablename__ = 'maintain'
    id = db.Column(db.Integer, primary_key=True)
    filter_time = db.Column(db.DateTime)
    water_time = db.Column(db.DateTime)

class Device(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(120), unique=True, nullable=False)
    alias = db.Column(db.String(120), nullable=True)
    password = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)