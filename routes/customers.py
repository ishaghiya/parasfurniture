from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models import db
from models.customer import Customer
from models.income import Bill, BillItem
from routes.auth import login_required, role_required
from services.audit_service import log_audit

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

@customers_bp.route('/')
@login_required
def index():
    search_query = request.args.get('search', '').strip()
    city_filter = request.args.get('city', '').strip()
    type_filter = request.args.get('customer_type', '').strip()

    query = Customer.query.filter_by(is_deleted=False)

    if search_query:
        query = query.filter(
            (Customer.name.ilike(f'%{search_query}%')) |
            (Customer.phone.ilike(f'%{search_query}%')) |
            (Customer.city.ilike(f'%{search_query}%'))
        )
    if city_filter:
        query = query.filter(Customer.city.ilike(f'%{city_filter}%'))
    if type_filter:
        query = query.filter_by(customer_type=type_filter)

    customers_raw = query.order_by(Customer.name.asc()).all()

    # Calculate aggregations for each customer
    customer_data = []
    for c in customers_raw:
        active_bills = [b for b in c.bills if not b.is_deleted]
        total_bills = len(active_bills)
        total_purchase = sum(b.total_amount for b in active_bills)
        amount_paid = sum(b.amount_received for b in active_bills)
        amount_pending = sum(b.pending_amount for b in active_bills)
        
        last_bill = max(active_bills, key=lambda b: b.bill_date) if active_bills else None
        last_purchase_date = last_bill.bill_date.strftime('%d-%m-%Y') if last_bill else 'N/A'

        customer_dict = c.to_dict()
        customer_dict.update({
            'total_bills': total_bills,
            'total_purchase': total_purchase,
            'amount_paid': amount_paid,
            'amount_pending': amount_pending,
            'last_purchase_date': last_purchase_date
        })
        customer_data.append(customer_dict)

    # Distinct cities for filter dropdown
    cities = db.session.query(Customer.city).filter(Customer.is_deleted==False, Customer.city.isnot(None)).distinct().all()
    city_list = sorted([c[0] for c in cities if c[0]])

    return render_template('customers/list.html', customers=customer_data, cities=city_list, search_query=search_query, city_filter=city_filter, type_filter=type_filter)

@customers_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        alternate_phone = request.form.get('alternate_phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', 'Gujarat').strip()
        pincode = request.form.get('pincode', '').strip()
        location = request.form.get('location', '').strip() or city
        customer_type = request.form.get('customer_type', 'Individual')
        gst_number = request.form.get('gst_number', '').strip()
        notes = request.form.get('notes', '').strip()

        if not name or not phone:
            flash('Customer Name and Contact Number are required.', 'danger')
            return redirect(url_for('customers.index'))

        customer = Customer(
            name=name,
            phone=phone,
            alternate_phone=alternate_phone,
            email=email,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            location=location,
            customer_type=customer_type,
            gst_number=gst_number,
            notes=notes
        )
        db.session.add(customer)
        db.session.commit()

        log_audit('ADD_CUSTOMER', table_name='customers', record_id=customer.id, details=f"Added customer: {name} ({phone})")
        flash(f'Customer "{name}" added successfully.', 'success')
        return redirect(url_for('customers.index'))

    return redirect(url_for('customers.index'))

@customers_bp.route('/<int:customer_id>')
@login_required
def profile(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if customer.is_deleted:
        flash('Customer record has been deleted.', 'warning')
        return redirect(url_for('customers.index'))

    bills = [b for b in customer.bills if not b.is_deleted]
    bills.sort(key=lambda x: x.bill_date, reverse=True)

    total_purchase = sum(b.total_amount for b in bills)
    total_paid = sum(b.amount_received for b in bills)
    total_pending = sum(b.pending_amount for b in bills)

    # Collect purchased furniture items summary
    purchased_items = {}
    for b in bills:
        for item in b.items:
            iname = item.item_name
            if iname not in purchased_items:
                purchased_items[iname] = {'quantity': 0, 'total_spent': 0.0, 'category': item.to_dict()['category_name']}
            purchased_items[iname]['quantity'] += item.quantity
            purchased_items[iname]['total_spent'] += item.total_amount

    return render_template(
        'customers/profile.html',
        customer=customer,
        bills=bills,
        total_purchase=total_purchase,
        total_paid=total_paid,
        total_pending=total_pending,
        purchased_items=purchased_items
    )

@customers_bp.route('/edit/<int:customer_id>', methods=['POST'])
@login_required
def edit(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    customer.name = request.form.get('name', customer.name).strip()
    customer.phone = request.form.get('phone', customer.phone).strip()
    customer.alternate_phone = request.form.get('alternate_phone', '').strip()
    customer.email = request.form.get('email', '').strip()
    customer.address = request.form.get('address', '').strip()
    customer.city = request.form.get('city', '').strip()
    customer.state = request.form.get('state', 'Gujarat').strip()
    customer.pincode = request.form.get('pincode', '').strip()
    customer.location = request.form.get('location', '').strip() or customer.city
    customer.customer_type = request.form.get('customer_type', 'Individual')
    customer.gst_number = request.form.get('gst_number', '').strip()
    customer.notes = request.form.get('notes', '').strip()

    db.session.commit()
    log_audit('EDIT_CUSTOMER', table_name='customers', record_id=customer.id, details=f"Updated customer details for {customer.name}")
    flash('Customer details updated successfully.', 'success')
    return redirect(url_for('customers.profile', customer_id=customer.id))

@customers_bp.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    results = Customer.query.filter(
        Customer.is_deleted == False,
        (Customer.name.ilike(f'%{q}%')) | (Customer.phone.ilike(f'%{q}%'))
    ).limit(10).all()
    return jsonify([c.to_dict() for c in results])
