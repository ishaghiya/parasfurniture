from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db
from models.user import User
from routes.auth import login_required, role_required
from services.audit_service import log_audit

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/')
@login_required
@role_required(['OWNER'])
def index():
    users_list = User.query.order_by(User.role.asc(), User.username.asc()).all()
    return render_template('users/list.html', users=users_list)

@users_bp.route('/add', methods=['POST'])
@login_required
@role_required(['OWNER'])
def add():
    username = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'EMPLOYEE')

    if not username or not full_name or not password:
        flash('Username, Full Name, and Password are required.', 'danger')
        return redirect(url_for('users.index'))

    existing = User.query.filter_by(username=username).first()
    if existing:
        flash(f'Username "{username}" is already taken.', 'warning')
        return redirect(url_for('users.index'))

    new_user = User(
        username=username,
        full_name=full_name,
        role=role,
        must_change_password=True,
        is_active=True
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    log_audit('ADD_USER', table_name='users', record_id=new_user.id, details=f"Created user {username} with role {role}")
    flash(f'User "{username}" created successfully.', 'success')
    return redirect(url_for('users.index'))

@users_bp.route('/reset-password/<int:user_id>', methods=['POST'])
@login_required
@role_required(['OWNER'])
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password', '')

    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'danger')
        return redirect(url_for('users.index'))

    user.set_password(new_password)
    user.must_change_password = True
    db.session.commit()

    log_audit('RESET_USER_PASSWORD', table_name='users', record_id=user.id, details=f"Reset password for user {user.username}")
    flash(f'Password reset for user "{user.username}". User must change password on next login.', 'success')
    return redirect(url_for('users.index'))

@users_bp.route('/toggle-status/<int:user_id>', methods=['POST'])
@login_required
@role_required(['OWNER'])
def toggle_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        flash('Cannot deactivate primary admin account.', 'danger')
        return redirect(url_for('users.index'))

    user.is_active = not user.is_active
    db.session.commit()

    status_str = 'activated' if user.is_active else 'deactivated'
    log_audit('TOGGLE_USER_STATUS', table_name='users', record_id=user.id, details=f"User {user.username} {status_str}")
    flash(f'User "{user.username}" {status_str}.', 'info')
    return redirect(url_for('users.index'))
