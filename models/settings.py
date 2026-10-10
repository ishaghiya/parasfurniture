from datetime import datetime
from models import db

class Setting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)

    @classmethod
    def get_val(cls, key, default=None):
        item = cls.query.filter_by(key=key).first()
        return item.value if item else default

    @classmethod
    def set_val(cls, key, value):
        item = cls.query.filter_by(key=key).first()
        if not item:
            item = cls(key=key, value=str(value))
            db.session.add(item)
        else:
            item.value = str(value)
        db.session.commit()

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(80), nullable=False)
    action = db.Column(db.String(100), nullable=False) # e.g. "ADD_BILL", "DELETE_EXPENSE", "LOGIN"
    table_name = db.Column(db.String(80), nullable=True)
    record_id = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.now, index=True)
    details = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'table_name': self.table_name or '',
            'record_id': self.record_id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else '',
            'details': self.details or ''
        }
