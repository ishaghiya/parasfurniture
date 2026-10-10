from flask import session
from models import db
from models.settings import AuditLog

def log_audit(action, table_name=None, record_id=None, details=None, user_id=None, username=None):
    try:
        curr_user_id = user_id or session.get('user_id')
        curr_username = username or session.get('username') or 'System'
        
        log_entry = AuditLog(
            user_id=curr_user_id,
            username=curr_username,
            action=action,
            table_name=table_name,
            record_id=record_id,
            details=details
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging audit: {e}")
