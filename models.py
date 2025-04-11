from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class SolderingTip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine_name = db.Column(db.String(100), nullable=False)
    engineer_name = db.Column(db.String(100), nullable=False)
    personnel_name = db.Column(db.String(100), nullable=False)
    shift = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SolderingTip {self.machine_name} {self.date}>'

class MachineCalibration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine_name = db.Column(db.String(100), nullable=False)
    days_per_calibration = db.Column(db.Integer, nullable=False)
    location_line = db.Column(db.String(100), nullable=False)
    operator_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MachineCalibration {self.machine_name}>'

class OvertimeLogbook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<OvertimeLogbook {self.employee_name} {self.date}>'

class EquipmentDowntime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_name = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    issue = db.Column(db.Text, nullable=False)
    downtime_minutes = db.Column(db.Integer, nullable=False)
    shift = db.Column(db.String(20), nullable=False)
    action_taken = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EquipmentDowntime {self.equipment_name} {self.date}>'
