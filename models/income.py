from datetime import datetime, date
from models import db

class Bill(db.Model):
    __tablename__ = 'bills'

    id = db.Column(db.Integer, primary_key=True)
    bill_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    bill_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    due_date = db.Column(db.Date, nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    subtotal = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    amount_received = db.Column(db.Float, default=0.0)
    pending_amount = db.Column(db.Float, default=0.0)
    
    payment_status = db.Column(db.String(30), default='PENDING', index=True) # PAID, PARTIALLY_PAID, PENDING, OVERDUE
    payment_method = db.Column(db.String(30), default='Cash', index=True) # Cash, UPI, Bank Transfer, Cheque, Card, Other
    reference_number = db.Column(db.String(100), nullable=True) # Existing invoice/bill reference
    notes = db.Column(db.Text, nullable=True)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    items = db.relationship('BillItem', backref='bill', lazy=True, cascade="all, delete-orphan")
    creator = db.relationship('User', foreign_keys=[created_by])

    def calculate_totals(self, override_status=None):
        """Calculates subtotal, total amount, pending amount, and payment status based on items and received amount."""
        calc_subtotal = sum(item.total_amount for item in self.items)
        if self.subtotal is None or self.subtotal == 0:
            self.subtotal = calc_subtotal

        # Final Bill Amount = Subtotal - Discount + Tax
        disc = self.discount or 0.0
        tx = self.tax or 0.0
        self.total_amount = max(0.0, self.subtotal - disc + tx)

        received = self.amount_received or 0.0
        self.pending_amount = max(0.0, self.total_amount - received)

        if override_status:
            self.payment_status = override_status
        else:
            today_date = date.today()
            if received >= self.total_amount and self.total_amount > 0:
                self.payment_status = 'PAID'
            elif received > 0 and received < self.total_amount:
                self.payment_status = 'PARTIALLY_PAID'
            elif received == 0:
                if self.due_date and self.due_date < today_date:
                    self.payment_status = 'OVERDUE'
                else:
                    self.payment_status = 'PENDING'
            elif received < self.total_amount and self.due_date and self.due_date < today_date:
                self.payment_status = 'OVERDUE'

    def to_dict(self):
        return {
            'id': self.id,
            'bill_number': self.bill_number,
            'bill_date': self.bill_date.strftime('%Y-%m-%d') if self.bill_date else '',
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else '',
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else '',
            'customer_phone': self.customer.phone if self.customer else '',
            'customer_location': self.customer.location or self.customer.city if self.customer else '',
            'subtotal': self.subtotal or 0.0,
            'discount': self.discount or 0.0,
            'tax': self.tax or 0.0,
            'total_amount': self.total_amount or 0.0,
            'amount_received': self.amount_received or 0.0,
            'pending_amount': self.pending_amount or 0.0,
            'payment_status': self.payment_status or 'PENDING',
            'payment_method': self.payment_method or 'Cash',
            'reference_number': self.reference_number or '',
            'notes': self.notes or '',
            'created_by_name': self.creator.full_name if self.creator else '',
            'items_count': len(self.items),
            'items': [item.to_dict() for item in self.items]
        }


class BillItem(db.Model):
    __tablename__ = 'bill_items'

    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('furniture_items.id'), nullable=True)
    item_name = db.Column(db.String(150), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    
    material = db.Column(db.String(100), nullable=True)
    dimensions = db.Column(db.String(100), nullable=True)
    custom_item = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)

    furniture_item = db.relationship('FurnitureItem')

    def calculate_total(self):
        qty = self.quantity or 1
        price = self.unit_price or 0.0
        disc = self.discount or 0.0
        tx = self.tax or 0.0
        self.total_amount = max(0.0, (qty * price) - disc + tx)
        return self.total_amount

    def to_dict(self):
        cat_id = self.furniture_item.category_id if self.furniture_item else None
        cat_name = self.furniture_item.category.name if (self.furniture_item and self.furniture_item.category) else 'Other'
        return {
            'id': self.id,
            'bill_id': self.bill_id,
            'item_id': self.item_id,
            'item_name': self.item_name,
            'category_id': cat_id,
            'category_name': cat_name,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'discount': self.discount,
            'tax': self.tax,
            'total_amount': self.total_amount,
            'material': self.material or '',
            'dimensions': self.dimensions or '',
            'custom_item': self.custom_item,
            'notes': self.notes or ''
        }
