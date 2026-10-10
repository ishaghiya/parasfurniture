from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db
from models.user import User
from services.audit_service import log_audit

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        # Check if user must change password
        if session.get('must_change_password') and request.endpoint != 'auth.change_password_forced' and request.endpoint != 'auth.logout':
            flash('You must change your default password before proceeding.', 'danger')
            return redirect(url_for('auth.change_password_forced'))
            
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    """roles can be a list e.g. ['OWNER'] or ['OWNER', 'EMPLOYEE']"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('auth.login'))
            user_role = session.get('role')
            if user_role not in roles:
                flash('Access denied. You do not have permission to access this resource.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.is_active and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['full_name'] = user.full_name
            session['role'] = user.role
            session['must_change_password'] = user.must_change_password

            log_audit('LOGIN', table_name='users', record_id=user.id, details=f"User {user.username} logged in.", user_id=user.id, username=user.username)

            if user.must_change_password:
                flash('First login detected! Please change your default password immediately.', 'info')
                return redirect(url_for('auth.change_password_forced'))

            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            log_audit('FAILED_LOGIN_ATTEMPT', details=f"Failed login attempt for username: {username}")
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')

@auth_bp.route('/change-password-forced', methods=['GET', 'POST'])
def change_password_forced():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.get(session['user_id'])
    if not user or not user.must_change_password:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not new_password or len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
        elif new_password != confirm_password:
            flash('New password and confirmation do not match.', 'danger')
        elif user.check_password(new_password):
            flash('New password cannot be the same as the default password.', 'warning')
        else:
            user.set_password(new_password)
            user.must_change_password = False
            db.session.commit()
            session['must_change_password'] = False

            log_audit('PASSWORD_CHANGE_FORCED', table_name='users', record_id=user.id, details="Default password updated.")
            flash('Password changed successfully! Welcome to Paras Furniture.', 'success')
            return redirect(url_for('dashboard.index'))

    return render_template('force_password_change.html')

@auth_bp.route('/logout')
def logout():
    if 'user_id' in session:
        log_audit('LOGOUT', details=f"User {session.get('username')} logged out.")
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
