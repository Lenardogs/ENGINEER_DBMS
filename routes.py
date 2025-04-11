import calendar
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, db
from models import User, SolderingTip, MachineCalibration, OvertimeLogbook, EquipmentDowntime
from forms import LoginForm, UserForm, SolderingTipForm, MachineCalibrationForm, OvertimeLogbookForm, EquipmentDowntimeForm, ReportForm

# Home/Dashboard route
@app.route('/')
@login_required
def dashboard():
    # Count records for each module
    soldering_tips_count = SolderingTip.query.count()
    machine_calibrations_count = MachineCalibration.query.count()
    overtime_logs_count = OvertimeLogbook.query.count()
    equipment_downtimes_count = EquipmentDowntime.query.count()
    
    # Get recent records
    recent_soldering = SolderingTip.query.order_by(SolderingTip.created_at.desc()).limit(5).all()
    recent_calibrations = MachineCalibration.query.order_by(MachineCalibration.created_at.desc()).limit(5).all()
    recent_overtime = OvertimeLogbook.query.order_by(OvertimeLogbook.created_at.desc()).limit(5).all()
    recent_downtimes = EquipmentDowntime.query.order_by(EquipmentDowntime.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                           soldering_tips_count=soldering_tips_count,
                           machine_calibrations_count=machine_calibrations_count,
                           overtime_logs_count=overtime_logs_count,
                           equipment_downtimes_count=equipment_downtimes_count,
                           recent_soldering=recent_soldering,
                           recent_calibrations=recent_calibrations,
                           recent_overtime=recent_overtime,
                           recent_downtimes=recent_downtimes)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# User management routes (admin only)
@app.route('/users')
@login_required
def user_management():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    search_query = request.args.get('search', '')
    if search_query:
        users = User.query.filter(
            User.username.ilike(f'%{search_query}%')
        ).all()
    else:
        users = User.query.all()
    form = UserForm()
    return render_template('user_management.html', users=users, form=form, search_query=search_query)

@app.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    form = UserForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('user_management'))
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('user_management'))
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            is_admin=form.is_admin.data
        )
        db.session.add(user)
        db.session.commit()
        flash('User created successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'danger')
    
    return redirect(url_for('user_management'))

@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        # Check if username or email already exists but skip current user
        username_check = User.query.filter_by(username=form.username.data).first()
        if username_check and username_check.id != user_id:
            flash('Username already exists.', 'danger')
            return redirect(url_for('user_management'))
            
        email_check = User.query.filter_by(email=form.email.data).first()
        if email_check and email_check.id != user_id:
            flash('Email already exists.', 'danger')
            return redirect(url_for('user_management'))
        
        user.username = form.username.data
        user.email = form.email.data
        user.is_admin = form.is_admin.data
        
        # Only update password if a new one is provided
        if form.password.data:
            user.password_hash = generate_password_hash(form.password.data)
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('user_management'))
    
    return render_template('user_management.html', users=User.query.all(), form=form, edit_user=user)

@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Prevent deleting self
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('user_management'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('user_management'))

# Soldering Tip Requisition routes
@app.route('/soldering-tips')
@login_required
def soldering_tips():
    search_query = request.args.get('search', '')
    if search_query:
        tips = SolderingTip.query.filter(
            SolderingTip.machine_name.ilike(f'%{search_query}%')
        ).order_by(SolderingTip.date.desc()).all()
    else:
        tips = SolderingTip.query.order_by(SolderingTip.date.desc()).all()
    form = SolderingTipForm()
    return render_template('soldering_tip.html', tips=tips, form=form, search_query=search_query)

@app.route('/soldering-tips/add', methods=['POST'])
@login_required
def add_soldering_tip():
    form = SolderingTipForm()
    if form.validate_on_submit():
        tip = SolderingTip(
            machine_name=form.machine_name.data,
            engineer_name=form.engineer_name.data,
            personnel_name=form.personnel_name.data,
            shift=form.shift.data,
            date=form.date.data
        )
        db.session.add(tip)
        db.session.commit()
        flash('Soldering tip requisition added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'danger')
    
    return redirect(url_for('soldering_tips'))

@app.route('/soldering-tips/edit/<int:tip_id>', methods=['GET', 'POST'])
@login_required
def edit_soldering_tip(tip_id):
    tip = SolderingTip.query.get_or_404(tip_id)
    form = SolderingTipForm(obj=tip)
    
    if form.validate_on_submit():
        tip.machine_name = form.machine_name.data
        tip.engineer_name = form.engineer_name.data
        tip.personnel_name = form.personnel_name.data
        tip.shift = form.shift.data
        tip.date = form.date.data
        
        db.session.commit()
        flash('Soldering tip requisition updated successfully!', 'success')
        return redirect(url_for('soldering_tips'))
    
    # For GET request, show the form with current values
    return render_template('soldering_tip.html', 
                           tips=SolderingTip.query.order_by(SolderingTip.date.desc()).all(), 
                           form=form, 
                           edit_tip=tip)

@app.route('/soldering-tips/delete/<int:tip_id>', methods=['POST'])
@login_required
def delete_soldering_tip(tip_id):
    tip = SolderingTip.query.get_or_404(tip_id)
    db.session.delete(tip)
    db.session.commit()
    flash('Soldering tip requisition deleted successfully!', 'success')
    return redirect(url_for('soldering_tips'))

# Machine Calibration Scheduler routes
@app.route('/machine-calibrations')
@login_required
def machine_calibrations():
    search_query = request.args.get('search', '')
    if search_query:
        calibrations = MachineCalibration.query.filter(
            MachineCalibration.machine_name.ilike(f'%{search_query}%')
        ).all()
    else:
        calibrations = MachineCalibration.query.all()
    form = MachineCalibrationForm()
    return render_template('machine_calibration.html', calibrations=calibrations, form=form, search_query=search_query)

@app.route('/machine-calibrations/add', methods=['POST'])
@login_required
def add_machine_calibration():
    form = MachineCalibrationForm()
    if form.validate_on_submit():
        calibration = MachineCalibration(
            machine_name=form.machine_name.data,
            days_per_calibration=form.days_per_calibration.data,
            location_line=form.location_line.data,
            operator_name=form.operator_name.data
        )
        db.session.add(calibration)
        db.session.commit()
        flash('Machine calibration schedule added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'danger')
    
    return redirect(url_for('machine_calibrations'))

@app.route('/machine-calibrations/edit/<int:calibration_id>', methods=['GET', 'POST'])
@login_required
def edit_machine_calibration(calibration_id):
    calibration = MachineCalibration.query.get_or_404(calibration_id)
    form = MachineCalibrationForm(obj=calibration)
    
    if form.validate_on_submit():
        calibration.machine_name = form.machine_name.data
        calibration.days_per_calibration = form.days_per_calibration.data
        calibration.location_line = form.location_line.data
        calibration.operator_name = form.operator_name.data
        
        db.session.commit()
        flash('Machine calibration schedule updated successfully!', 'success')
        return redirect(url_for('machine_calibrations'))
    
    return render_template('machine_calibration.html', 
                           calibrations=MachineCalibration.query.all(), 
                           form=form, 
                           edit_calibration=calibration)

@app.route('/machine-calibrations/delete/<int:calibration_id>', methods=['POST'])
@login_required
def delete_machine_calibration(calibration_id):
    calibration = MachineCalibration.query.get_or_404(calibration_id)
    db.session.delete(calibration)
    db.session.commit()
    flash('Machine calibration schedule deleted successfully!', 'success')
    return redirect(url_for('machine_calibrations'))

# Overtime Logbook routes
@app.route('/overtime-logbook')
@login_required
def overtime_logbook():
    search_query = request.args.get('search', '')
    if search_query:
        logs = OvertimeLogbook.query.filter(
            OvertimeLogbook.employee_name.ilike(f'%{search_query}%')
        ).order_by(OvertimeLogbook.date.desc()).all()
    else:
        logs = OvertimeLogbook.query.order_by(OvertimeLogbook.date.desc()).all()
    form = OvertimeLogbookForm()
    return render_template('overtime_logbook.html', logs=logs, form=form, search_query=search_query)

@app.route('/overtime-logbook/add', methods=['POST'])
@login_required
def add_overtime_log():
    form = OvertimeLogbookForm()
    if form.validate_on_submit():
        log = OvertimeLogbook(
            employee_name=form.employee_name.data,
            date=form.date.data,
            hours=form.hours.data
        )
        db.session.add(log)
        db.session.commit()
        flash('Overtime log added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'danger')
    
    return redirect(url_for('overtime_logbook'))

@app.route('/overtime-logbook/edit/<int:log_id>', methods=['GET', 'POST'])
@login_required
def edit_overtime_log(log_id):
    log = OvertimeLogbook.query.get_or_404(log_id)
    form = OvertimeLogbookForm(obj=log)
    
    if form.validate_on_submit():
        log.employee_name = form.employee_name.data
        log.date = form.date.data
        log.hours = form.hours.data
        
        db.session.commit()
        flash('Overtime log updated successfully!', 'success')
        return redirect(url_for('overtime_logbook'))
    
    return render_template('overtime_logbook.html', 
                           logs=OvertimeLogbook.query.order_by(OvertimeLogbook.date.desc()).all(), 
                           form=form, 
                           edit_log=log)

@app.route('/overtime-logbook/delete/<int:log_id>', methods=['POST'])
@login_required
def delete_overtime_log(log_id):
    log = OvertimeLogbook.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    flash('Overtime log deleted successfully!', 'success')
    return redirect(url_for('overtime_logbook'))

# Equipment Downtime routes
@app.route('/equipment-downtime')
@login_required
def equipment_downtime():
    search_query = request.args.get('search', '')
    if search_query:
        downtimes = EquipmentDowntime.query.filter(
            EquipmentDowntime.equipment_name.ilike(f'%{search_query}%')
        ).order_by(EquipmentDowntime.date.desc()).all()
    else:
        downtimes = EquipmentDowntime.query.order_by(EquipmentDowntime.date.desc()).all()
    form = EquipmentDowntimeForm()
    return render_template('equipment_downtime.html', downtimes=downtimes, form=form, search_query=search_query)

@app.route('/equipment-downtime/add', methods=['POST'])
@login_required
def add_equipment_downtime():
    form = EquipmentDowntimeForm()
    if form.validate_on_submit():
        downtime = EquipmentDowntime(
            equipment_name=form.equipment_name.data,
            product_name=form.product_name.data,
            issue=form.issue.data,
            downtime_minutes=form.downtime_minutes.data,
            shift=form.shift.data,
            action_taken=form.action_taken.data,
            date=form.date.data
        )
        db.session.add(downtime)
        db.session.commit()
        flash('Equipment downtime record added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", 'danger')
    
    return redirect(url_for('equipment_downtime'))

@app.route('/equipment-downtime/edit/<int:downtime_id>', methods=['GET', 'POST'])
@login_required
def edit_equipment_downtime(downtime_id):
    downtime = EquipmentDowntime.query.get_or_404(downtime_id)
    form = EquipmentDowntimeForm(obj=downtime)
    
    if form.validate_on_submit():
        downtime.equipment_name = form.equipment_name.data
        downtime.product_name = form.product_name.data
        downtime.issue = form.issue.data
        downtime.downtime_minutes = form.downtime_minutes.data
        downtime.shift = form.shift.data
        downtime.action_taken = form.action_taken.data
        downtime.date = form.date.data
        
        db.session.commit()
        flash('Equipment downtime record updated successfully!', 'success')
        return redirect(url_for('equipment_downtime'))
    
    return render_template('equipment_downtime.html', 
                           downtimes=EquipmentDowntime.query.order_by(EquipmentDowntime.date.desc()).all(), 
                           form=form, 
                           edit_downtime=downtime)

@app.route('/equipment-downtime/delete/<int:downtime_id>', methods=['POST'])
@login_required
def delete_equipment_downtime(downtime_id):
    downtime = EquipmentDowntime.query.get_or_404(downtime_id)
    db.session.delete(downtime)
    db.session.commit()
    flash('Equipment downtime record deleted successfully!', 'success')
    return redirect(url_for('equipment_downtime'))

# Reports routes
@app.route('/reports')
@login_required
def reports():
    form = ReportForm()
    return render_template('reports.html', form=form)

@app.route('/reports/generate', methods=['POST'])
@login_required
def generate_report():
    form = ReportForm()
    if form.validate_on_submit():
        report_type = form.report_type.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        
        # Ensure end date is end of the day for inclusive queries
        end_date = datetime.combine(end_date, datetime.max.time())
        
        if report_type == 'soldering_tips':
            records = SolderingTip.query.filter(SolderingTip.date.between(start_date, end_date)).all()
            return render_template('reports.html', 
                                  form=form, 
                                  records=records, 
                                  report_type=report_type,
                                  start_date=start_date,
                                  end_date=end_date.date())
                                  
        elif report_type == 'machine_calibrations':
            records = MachineCalibration.query.all()  # No date filter as calibrations aren't date-specific
            return render_template('reports.html', 
                                  form=form, 
                                  records=records, 
                                  report_type=report_type,
                                  start_date=start_date,
                                  end_date=end_date.date())
                                  
        elif report_type == 'overtime_logbook':
            records = OvertimeLogbook.query.filter(OvertimeLogbook.date.between(start_date, end_date)).all()
            return render_template('reports.html', 
                                  form=form, 
                                  records=records, 
                                  report_type=report_type,
                                  start_date=start_date,
                                  end_date=end_date.date())
                                  
        elif report_type == 'equipment_downtime':
            records = EquipmentDowntime.query.filter(EquipmentDowntime.date.between(start_date, end_date)).all()
            return render_template('reports.html', 
                                  form=form, 
                                  records=records, 
                                  report_type=report_type,
                                  start_date=start_date,
                                  end_date=end_date.date())
    
    return render_template('reports.html', form=form)

# API routes for dashboard charts
@app.route('/api/dashboard/soldering_tips_data')
@login_required
def soldering_tips_data():
    # Get data for past 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Query data
    data = SolderingTip.query.filter(SolderingTip.date.between(start_date, end_date)).all()
    
    # Format data for chart - count by day
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(31)]
    counts = [0] * 31
    
    for tip in data:
        day_index = (tip.date.date() - start_date.date()).days
        if 0 <= day_index < 31:
            counts[day_index] += 1
    
    return jsonify({
        'labels': dates,
        'datasets': [{
            'label': 'Soldering Tips',
            'data': counts,
            'borderColor': 'rgba(75, 192, 192, 1)',
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'fill': True
        }]
    })

@app.route('/api/dashboard/overtime_data')
@login_required
def overtime_data():
    # Get data for past 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Query data
    data = OvertimeLogbook.query.filter(OvertimeLogbook.date.between(start_date, end_date)).all()
    
    # Format data for chart - sum hours by day
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(31)]
    hours = [0] * 31
    
    for log in data:
        day_index = (log.date.date() - start_date.date()).days
        if 0 <= day_index < 31:
            hours[day_index] += log.hours
    
    return jsonify({
        'labels': dates,
        'datasets': [{
            'label': 'Overtime Hours',
            'data': hours,
            'borderColor': 'rgba(153, 102, 255, 1)',
            'backgroundColor': 'rgba(153, 102, 255, 0.2)',
            'fill': True
        }]
    })

@app.route('/api/dashboard/downtime_data')
@login_required
def downtime_data():
    # Get data for past 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Query data
    data = EquipmentDowntime.query.filter(EquipmentDowntime.date.between(start_date, end_date)).all()
    
    # Format data for chart - sum downtime by day
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(31)]
    downtimes = [0] * 31
    
    for record in data:
        day_index = (record.date.date() - start_date.date()).days
        if 0 <= day_index < 31:
            downtimes[day_index] += record.downtime_minutes
    
    return jsonify({
        'labels': dates,
        'datasets': [{
            'label': 'Equipment Downtime (minutes)',
            'data': downtimes,
            'borderColor': 'rgba(255, 99, 132, 1)',
            'backgroundColor': 'rgba(255, 99, 132, 0.2)',
            'fill': True
        }]
    })

@app.route('/api/dashboard/calibration_data')
@login_required
def calibration_data():
    # Get all calibration records
    calibrations = MachineCalibration.query.all()
    
    # Group by days per calibration
    days_data = {}
    for cal in calibrations:
        days = cal.days_per_calibration
        if days in days_data:
            days_data[days] += 1
        else:
            days_data[days] = 1
    
    # Sort by days
    sorted_days = sorted(days_data.keys())
    
    return jsonify({
        'labels': [f'{d} days' for d in sorted_days],
        'datasets': [{
            'label': 'Machines by Calibration Frequency',
            'data': [days_data[d] for d in sorted_days],
            'backgroundColor': [
                'rgba(255, 99, 132, 0.6)',
                'rgba(54, 162, 235, 0.6)',
                'rgba(255, 206, 86, 0.6)',
                'rgba(75, 192, 192, 0.6)',
                'rgba(153, 102, 255, 0.6)',
                'rgba(255, 159, 64, 0.6)'
            ],
            'borderColor': [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(153, 102, 255, 1)',
                'rgba(255, 159, 64, 1)'
            ],
            'borderWidth': 1
        }]
    })
