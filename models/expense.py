from datetime import datetime, date
from models import db

class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    default_type = db.Column(db.String(50), default='BUSINESS') # WORKER, OFFICE, FOOD, FACTORY, MATERIAL, TRANSPORT, BUSINESS, OTHER
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    expenses = db.relationship('Expense', backref='category', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'default_type': self.default_type,
            'description': self.description or '',
            'is_active': self.is_active
        }

class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    expense_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)
    expense_type = db.Column(db.String(50), default='BUSINESS', index=True)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    
    payment_method = db.Column(db.String(30), default='Cash', index=True) # Cash, UPI, Bank Transfer, Cheque, Card, Other
    vendor = db.Column(db.String(120), nullable=True, index=True) # Person / Vendor name
    receipt_number = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    attachment_path = db.Column(db.String(255), nullable=True)
    
    recurring = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(30), default='PAID') # PAID, PENDING
    notes = db.Column(db.Text, nullable=True)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    creator = db.relationship('User', foreign_keys=[created_by])

    def to_dict(self):
        return {
            'id': self.id,
            'expense_date': self.expense_date.strftime('%Y-%m-%d') if self.expense_date else '',
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else '',
            'expense_type': self.expense_type or '',
            'description': self.description,
            'amount': self.amount,
            'payment_method': self.payment_method or 'Cash',
            'vendor': self.vendor or '',
            'receipt_number': self.receipt_number or '',
            'location': self.location or '',
            'recurring': self.recurring,
            'status': self.status or 'PAID',
            'notes': self.notes or '',
            'created_by_name': self.creator.full_name if self.creator else '',
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }
