import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from routes.auth import login_required, role_required
from services.backup_service import create_database_backup, restore_database_from_file, BACKUP_FOLDER
from services.audit_service import log_audit

backup_bp = Blueprint('backup', __name__, url_prefix='/backup')

@backup_bp.route('/')
@login_required
@role_required(['OWNER'])
def index():
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    backups_list = []
    for f in os.listdir(BACKUP_FOLDER):
        if f.endswith('.db'):
            fpath = os.path.join(BACKUP_FOLDER, f)
            stat = os.stat(fpath)
            backups_list.append({
                'filename': f,
                'size_kb': round(stat.st_size / 1024, 1),
                'created_at': f
            })
    backups_list.sort(key=lambda x: x['filename'], reverse=True)
    return render_template('backup.html', backups=backups_list)

@backup_bp.route('/create', methods=['POST'])
@login_required
@role_required(['OWNER'])
def create():
    try:
        b_path, b_name = create_database_backup()
        log_audit('BACKUP_DATABASE', details=f"Database backup created: {b_name}")
        flash(f'Database backup "{b_name}" created successfully.', 'success')
    except Exception as e:
        flash(f'Error creating database backup: {e}', 'danger')
    return redirect(url_for('backup.index'))

@backup_bp.route('/download/<filename>')
@login_required
@role_required(['OWNER'])
def download(filename):
    fpath = os.path.join(BACKUP_FOLDER, filename)
    if os.path.exists(fpath):
        return send_file(fpath, as_attachment=True, download_name=filename)
    flash('Backup file not found.', 'danger')
    return redirect(url_for('backup.index'))

@backup_bp.route('/restore', methods=['POST'])
@login_required
@role_required(['OWNER'])
def restore():
    if 'backup_file' not in request.files:
        flash('No file uploaded.', 'danger')
        return redirect(url_for('backup.index'))

    file = request.files['backup_file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('backup.index'))

    if file and file.filename.endswith('.db'):
        temp_path = os.path.join(BACKUP_FOLDER, 'temp_restore.db')
        file.save(temp_path)
        try:
            restore_database_from_file(temp_path)
            os.remove(temp_path)
            log_audit('RESTORE_DATABASE', details=f"Database restored from uploaded file: {file.filename}")
            flash('Database restored successfully! A safety backup of the previous database was saved automatically.', 'success')
        except Exception as e:
            flash(f'Database restore failed: {e}', 'danger')
    else:
        flash('Invalid file format. Must be a valid .db SQLite file.', 'danger')

    return redirect(url_for('backup.index'))
