from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db
from models.settings import Setting, AuditLog
from routes.auth import login_required, role_required
from services.audit_service import log_audit

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
@login_required
@role_required(['OWNER'])
def index():
    settings_dict = {
        'company_name': Setting.get_val('company_name', 'Paras Furniture'),
        'company_address': Setting.get_val('company_address', ''),
        'company_city': Setting.get_val('company_city', 'Ahmedabad'),
        'company_state': Setting.get_val('company_state', 'Gujarat'),
        'company_phone': Setting.get_val('company_phone', ''),
        'company_email': Setting.get_val('company_email', ''),
        'currency_symbol': Setting.get_val('currency_symbol', '₹'),
        'date_format': Setting.get_val('date_format', 'DD-MM-YYYY'),
        'inactivity_timeout': Setting.get_val('inactivity_timeout', '30')
    }
    return render_template('settings.html', settings=settings_dict)

@settings_bp.route('/save', methods=['POST'])
@login_required
@role_required(['OWNER'])
def save():
    keys = ['company_name', 'company_address', 'company_city', 'company_state', 'company_phone', 'company_email', 'currency_symbol', 'date_format', 'inactivity_timeout']
    for k in keys:
        val = request.form.get(k, '').strip()
        Setting.set_val(k, val)

    log_audit('UPDATE_SETTINGS', details="System business settings updated.")
    flash('System settings updated successfully.', 'success')
    return redirect(url_for('settings.index'))

@settings_bp.route('/audit-logs')
@login_required
@role_required(['OWNER'])
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return render_template('audit_logs.html', logs=logs)
