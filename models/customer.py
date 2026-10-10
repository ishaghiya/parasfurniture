from datetime import datetime
from models import db

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    alternate_phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(80), nullable=True, index=True)
    state = db.Column(db.String(80), default='Gujarat')
    pincode = db.Column(db.String(10), nullable=True)
    location = db.Column(db.String(100), nullable=True, index=True)
    customer_type = db.Column(db.String(50), default='Individual') # Individual, Business, Contractor, Builder, Interior Designer, Architect, Other
    gst_number = db.Column(db.String(30), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    bills = db.relationship('Bill', backref='customer', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'alternate_phone': self.alternate_phone,
            'email': self.email,
            'address': self.address,
            'city': self.city or '',
            'state': self.state or 'Gujarat',
            'pincode': self.pincode or '',
            'location': self.location or self.city or '',
            'customer_type': self.customer_type or 'Individual',
            'gst_number': self.gst_number or '',
            'notes': self.notes or '',
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }
