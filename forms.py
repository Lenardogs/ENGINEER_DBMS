from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, IntegerField, FloatField, DateField, HiddenField, SubmitField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[Optional(), Length(min=6, max=64)])
    confirm_password = PasswordField('Confirm Password', validators=[
        Optional(), 
        EqualTo('password', message='Passwords must match')
    ])
    is_admin = BooleanField('Admin Privileges')

class SolderingTipForm(FlaskForm):
    machine_name = StringField('Machine Name', validators=[DataRequired(), Length(max=100)])
    engineer_name = SelectField('Engineer Name', validators=[DataRequired()], choices=[])  # Will be populated dynamically
    personnel_name = StringField('Personnel Name', validators=[DataRequired(), Length(max=100)])
    shift = SelectField('Shift', choices=[('morning', 'Morning'), ('afternoon', 'Afternoon'), ('night', 'Night')], validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])

class MachineCalibrationForm(FlaskForm):
    machine_name = StringField('Machine Name', validators=[DataRequired()])
    days_per_calibration = IntegerField('Days per Calibration', validators=[DataRequired(), NumberRange(min=1)])
    location_line = SelectField('Location/Line', choices=[
        ('AOK', 'AOK'),
        ('GRANDSTREAM', 'GRANDSTREAM'),
        ('INTRACOM', 'INTRACOM'),
        ('D-LINK', 'D-LINK'),
        ('PC POWER', 'PC POWER')
    ], validators=[DataRequired()])
    operator_name = StringField('Operator Name', validators=[DataRequired()])
    date = DateField('Calibration Date', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Save')

class OvertimeLogbookForm(FlaskForm):
    employee_name = SelectField('Employee Name', choices=[], validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    hours = FloatField('Hours', validators=[DataRequired(), NumberRange(min=0.5, max=24)])

class EquipmentDowntimeForm(FlaskForm):
    equipment_name = StringField('Equipment Name', validators=[DataRequired(), Length(max=100)])
    product_name = StringField('Product Name', validators=[DataRequired(), Length(max=100)])
    issue = TextAreaField('Issue', validators=[DataRequired()])
    downtime_minutes = IntegerField('Downtime (minutes)', validators=[DataRequired(), NumberRange(min=1)])
    shift = SelectField('Shift', choices=[('morning', 'Morning'), ('afternoon', 'Afternoon'), ('night', 'Night')], validators=[DataRequired()])
    action_taken = TextAreaField('Action Taken', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])

class ReportForm(FlaskForm):
    report_type = SelectField('Report Type', choices=[
        ('soldering_tips', 'Soldering Tip Requisition'),
        ('machine_calibrations', 'Machine Calibration Scheduler'),
        ('overtime_logbook', 'Overtime Logbook'),
        ('equipment_downtime', 'Equipment Downtime Record'),
        ('maintenance_reports', 'Maintenance and Abnormality Reports')
    ], validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])

class MaintenanceReportForm(FlaskForm):
    model_id = StringField('Model ID', validators=[DataRequired()])
    model_name = StringField('Model Name', validators=[DataRequired(), Length(max=100)])
    client_name = SelectField('Client Name', choices=[
        ('grandstream', 'Grandstream'),
        ('aok', 'AOK'),
        ('d-link', 'D-Link'),
        ('srs', 'SRS'),
        ('intracom', 'Intracom')
    ], validators=[DataRequired()])
    station = SelectField('Station', choices=[
        ('smt', 'SMT'),
        ('dip', 'DIP'),
        ('assy', 'ASSY'),
        ('packaging', 'PACKAGING')
    ], validators=[DataRequired()])
    affected_component = StringField('Affected Component', validators=[DataRequired(), Length(max=200)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    problem_description = TextAreaField('Problem Description', validators=[DataRequired()])
    evidence = FileField('Evidence')
    analysis = TextAreaField('Analysis', validators=[DataRequired()])

class ITInventoryForm(FlaskForm):
    item_name = StringField('Item Name', validators=[DataRequired()])
    total_quantity = IntegerField('Total Quantity', validators=[DataRequired(), NumberRange(min=0)])
    acquired_qty = IntegerField('Acquired Qty', validators=[DataRequired(), NumberRange(min=0)])
    