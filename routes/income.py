from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models import db
from models.user import User
from models.customer import Customer
from models.income import Bill, BillItem
from models.furniture import FurnitureCategory, FurnitureItem
from routes.auth import login_required, role_required
from services.audit_service import log_audit

income_bp = Blueprint('income', __name__, url_prefix='/income')

@income_bp.route('/')
@login_required
def index():
    # Filter parameters
    search_q = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    customer_id = request.args.get('customer_id', type=int)
    city_filter = request.args.get('city', '').strip()
    location_filter = request.args.get('location', '').strip()
    item_category_id = request.args.get('item_category_id', type=int)
    payment_status = request.args.get('payment_status', '').strip()
    payment_method = request.args.get('payment_method', '').strip()
    employee_id = request.args.get('employee_id', type=int)

    query = Bill.query.filter_by(is_deleted=False)

    if search_q:
        query = query.join(Customer).outerjoin(BillItem).filter(
            (Bill.bill_number.ilike(f'%{search_q}%')) |
            (Customer.name.ilike(f'%{search_q}%')) |
            (Customer.phone.ilike(f'%{search_q}%')) |
            (Customer.location.ilike(f'%{search_q}%')) |
            (BillItem.item_name.ilike(f'%{search_q}%'))
        ).distinct()

    if date_from:
        try:
            d_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Bill.bill_date >= d_from)
        except ValueError:
            pass

    if date_to:
        try:
            d_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Bill.bill_date <= d_to)
        except ValueError:
            pass

    if customer_id:
        query = query.filter(Bill.customer_id == customer_id)

    if city_filter:
        query = query.join(Customer).filter(Customer.city.ilike(f'%{city_filter}%'))

    if location_filter:
        query = query.join(Customer).filter(
            (Customer.location.ilike(f'%{location_filter}%')) | (Customer.city.ilike(f'%{location_filter}%'))
        )

    if item_category_id:
        query = query.join(BillItem).join(FurnitureItem).filter(FurnitureItem.category_id == item_category_id).distinct()

    if payment_status:
        query = query.filter(Bill.payment_status == payment_status)

    if payment_method:
        query = query.filter(Bill.payment_method == payment_method)

    if employee_id:
        query = query.filter(Bill.created_by == employee_id)

    bills = query.order_by(Bill.bill_date.desc(), Bill.id.desc()).all()

    # Dropdown lists for filters
    customers = Customer.query.filter_by(is_deleted=False).order_by(Customer.name.asc()).all()
    categories = FurnitureCategory.query.filter_by(is_active=True).order_by(FurnitureCategory.name.asc()).all()
    employees = User.query.filter_by(is_active=True).order_by(User.full_name.asc()).all()
    
    cities = db.session.query(Customer.city).filter(Customer.is_deleted==False, Customer.city.isnot(None)).distinct().all()
    city_list = sorted([c[0] for c in cities if c[0]])

    return render_template(
        'income/list.html',
        bills=bills,
        customers=customers,
        categories=categories,
        employees=employees,
        city_list=city_list,
        filters=request.args
    )

@income_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        bill_number = request.form.get('bill_number', '').strip()
        bill_date_str = request.form.get('bill_date', '').strip()
        due_date_str = request.form.get('due_date', '').strip()
        payment_method = request.form.get('payment_method', 'Cash')
        reference_number = request.form.get('reference_number', '').strip()
        bill_notes = request.form.get('notes', '').strip()

        # Customer selection or creation
        customer_id = request.form.get('customer_id', type=int)
        client_name = request.form.get('client_name', '').strip()
        client_phone = request.form.get('client_phone', '').strip()
        client_alternate = request.form.get('client_alternate', '').strip()
        client_email = request.form.get('client_email', '').strip()
        client_address = request.form.get('client_address', '').strip()
        client_city = request.form.get('client_city', 'Ahmedabad').strip()
        client_state = request.form.get('client_state', 'Gujarat').strip()
        client_pincode = request.form.get('client_pincode', '').strip()
        client_location = request.form.get('client_location', '').strip() or client_city
        customer_type = request.form.get('customer_type', 'Individual')
        gst_number = request.form.get('gst_number', '').strip()

        # Validate basic bill info
        if not bill_number or not bill_date_str or not client_name or not client_phone:
            flash('Bill Number, Bill Date, Client Name, and Contact Number are required.', 'danger')
            return redirect(url_for('income.add'))

        # Check duplicate bill number
        existing_bill = Bill.query.filter_by(bill_number=bill_number, is_deleted=False).first()
        if existing_bill:
            flash(f'Bill Number "{bill_number}" already exists in the system. Please use a unique Bill Number.', 'danger')
            return redirect(url_for('income.add'))

        # Get or Create Customer
        if customer_id:
            customer = Customer.query.get(customer_id)
        else:
            customer = Customer.query.filter_by(phone=client_phone, is_deleted=False).first()

        if not customer:
            customer = Customer(
                name=client_name,
                phone=client_phone,
                alternate_phone=client_alternate,
                email=client_email,
                address=client_address,
                city=client_city,
                state=client_state,
                pincode=client_pincode,
                location=client_location,
                customer_type=customer_type,
                gst_number=gst_number
            )
            db.session.add(customer)
            db.session.flush() # get customer.id

        # Parse Dates
        try:
            b_date = datetime.strptime(bill_date_str, '%Y-%m-%d').date()
        except ValueError:
            b_date = date.today()

        d_date = None
        if due_date_str:
            try:
                d_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Overall Financials
        bill_discount = float(request.form.get('overall_discount', 0.0) or 0.0)
        bill_tax = float(request.form.get('overall_tax', 0.0) or 0.0)
        amount_received = float(request.form.get('amount_received', 0.0) or 0.0)
        override_status = request.form.get('payment_status', '').strip() if session.get('role') == 'OWNER' else None

        # Create Bill record
        new_bill = Bill(
            bill_number=bill_number,
            bill_date=b_date,
            due_date=d_date,
            customer_id=customer.id,
            discount=bill_discount,
            tax=bill_tax,
            amount_received=amount_received,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=bill_notes,
            created_by=session['user_id']
        )
        db.session.add(new_bill)
        db.session.flush() # get new_bill.id

        # Process Furniture Items
        item_names = request.form.getlist('item_name[]')
        item_cat_ids = request.form.getlist('item_category_id[]')
        item_item_ids = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        item_discounts = request.form.getlist('item_discount[]')
        item_taxes = request.form.getlist('item_tax[]')
        materials = request.form.getlist('material[]')
        dimensions_list = request.form.getlist('dimensions[]')

        subtotal_sum = 0.0

        for i in range(len(item_names)):
            iname = item_names[i].strip()
            if not iname:
                continue

            qty = int(quantities[i]) if i < len(quantities) and quantities[i] else 1
            price = float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0.0
            disc = float(item_discounts[i]) if i < len(item_discounts) and item_discounts[i] else 0.0
            tx = float(item_taxes[i]) if i < len(item_taxes) and item_taxes[i] else 0.0
            mat = materials[i].strip() if i < len(materials) else ''
            dims = dimensions_list[i].strip() if i < len(dimensions_list) else ''
            
            f_item_id = int(item_item_ids[i]) if i < len(item_item_ids) and item_item_ids[i].isdigit() else None

            bill_item = BillItem(
                bill_id=new_bill.id,
                item_id=f_item_id,
                item_name=iname,
                quantity=max(1, qty),
                unit_price=max(0.0, price),
                discount=max(0.0, disc),
                tax=max(0.0, tx),
                material=mat,
                dimensions=dims
            )
            item_total = bill_item.calculate_total()
            subtotal_sum += item_total
            db.session.add(bill_item)

        new_bill.subtotal = subtotal_sum
        new_bill.calculate_totals(override_status=override_status if override_status else None)
        
        db.session.commit()

        log_audit('ADD_BILL', table_name='bills', record_id=new_bill.id, details=f"Created bill #{new_bill.bill_number} for {customer.name} - ₹{new_bill.total_amount:,.2f}")
        flash(f'Client Bill #{new_bill.bill_number} recorded successfully!', 'success')
        return redirect(url_for('income.view_bill', bill_id=new_bill.id))

    # GET method
    customers = Customer.query.filter_by(is_deleted=False).order_by(Customer.name.asc()).all()
    categories = FurnitureCategory.query.filter_by(is_active=True).order_by(FurnitureCategory.name.asc()).all()
    
    # Auto-generate next bill number recommendation (e.g. PF-1001)
    last_bill = Bill.query.order_by(Bill.id.desc()).first()
    next_num_seq = (last_bill.id + 1001) if last_bill else 1001
    suggested_bill_no = f"PF-{next_num_seq}"

    return render_template(
        'income/add.html',
        customers=customers,
        categories=categories,
        suggested_bill_no=suggested_bill_no,
        today_date=date.today().strftime('%Y-%m-%d')
    )

@income_bp.route('/view/<int:bill_id>')
@login_required
def view_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    if bill.is_deleted:
        flash('Bill record has been deleted.', 'warning')
        return redirect(url_for('income.index'))
    return render_template('income/view.html', bill=bill)

@income_bp.route('/edit/<int:bill_id>', methods=['GET', 'POST'])
@login_required
@role_required(['OWNER'])
def edit_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    if bill.is_deleted:
        flash('Cannot edit a deleted bill.', 'danger')
        return redirect(url_for('income.index'))

    if request.method == 'POST':
        bill.bill_number = request.form.get('bill_number', bill.bill_number).strip()
        bill_date_str = request.form.get('bill_date', '').strip()
        due_date_str = request.form.get('due_date', '').strip()
        bill.payment_method = request.form.get('payment_method', 'Cash')
        bill.reference_number = request.form.get('reference_number', '').strip()
        bill.notes = request.form.get('notes', '').strip()

        if bill_date_str:
            try:
                bill.bill_date = datetime.strptime(bill_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        if due_date_str:
            try:
                bill.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                bill.due_date = None

        bill.discount = float(request.form.get('overall_discount', 0.0) or 0.0)
        bill.tax = float(request.form.get('overall_tax', 0.0) or 0.0)
        bill.amount_received = float(request.form.get('amount_received', 0.0) or 0.0)
        override_status = request.form.get('payment_status', '').strip()

        # Update Customer details
        customer = bill.customer
        customer.name = request.form.get('client_name', customer.name).strip()
        customer.phone = request.form.get('client_phone', customer.phone).strip()
        customer.city = request.form.get('client_city', customer.city).strip()
        customer.location = request.form.get('client_location', customer.location).strip()

        # Replace items
        BillItem.query.filter_by(bill_id=bill.id).delete()

        item_names = request.form.getlist('item_name[]')
        quantities = request.form.getlist('quantity[]')
        unit_prices = request.form.getlist('unit_price[]')
        item_discounts = request.form.getlist('item_discount[]')
        item_taxes = request.form.getlist('item_tax[]')
        materials = request.form.getlist('material[]')
        dimensions_list = request.form.getlist('dimensions[]')

        subtotal_sum = 0.0

        for i in range(len(item_names)):
            iname = item_names[i].strip()
            if not iname:
                continue

            qty = int(quantities[i]) if i < len(quantities) and quantities[i] else 1
            price = float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0.0
            disc = float(item_discounts[i]) if i < len(item_discounts) and item_discounts[i] else 0.0
            tx = float(item_taxes[i]) if i < len(item_taxes) and item_taxes[i] else 0.0
            mat = materials[i].strip() if i < len(materials) else ''
            dims = dimensions_list[i].strip() if i < len(dimensions_list) else ''

            bill_item = BillItem(
                bill_id=bill.id,
                item_name=iname,
                quantity=max(1, qty),
                unit_price=max(0.0, price),
                discount=max(0.0, disc),
                tax=max(0.0, tx),
                material=mat,
                dimensions=dims
            )
            item_total = bill_item.calculate_total()
            subtotal_sum += item_total
            db.session.add(bill_item)

        bill.subtotal = subtotal_sum
        bill.calculate_totals(override_status=override_status)
        db.session.commit()

        log_audit('EDIT_BILL', table_name='bills', record_id=bill.id, details=f"Updated Bill #{bill.bill_number}")
        flash(f'Bill #{bill.bill_number} updated successfully.', 'success')
        return redirect(url_for('income.view_bill', bill_id=bill.id))

    categories = FurnitureCategory.query.filter_by(is_active=True).order_by(FurnitureCategory.name.asc()).all()
    return render_template('income/edit.html', bill=bill, categories=categories)

@income_bp.route('/delete/<int:bill_id>', methods=['POST'])
@login_required
@role_required(['OWNER'])
def delete_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    bill.is_deleted = True
    bill.deleted_at = datetime.now()
    db.session.commit()

    log_audit('DELETE_BILL', table_name='bills', record_id=bill.id, details=f"Soft-deleted bill #{bill.bill_number}")
    flash(f'Bill #{bill.bill_number} deleted successfully.', 'info')
    return redirect(url_for('income.index'))

@income_bp.route('/duplicate/<int:bill_id>')
@login_required
def duplicate_bill(bill_id):
    existing = Bill.query.get_or_404(bill_id)
    
    # Auto-generate unique bill number for duplicate
    last_bill = Bill.query.order_by(Bill.id.desc()).first()
    next_num_seq = (last_bill.id + 1001) if last_bill else 1001
    new_bill_no = f"PF-{next_num_seq}-DUP"

    new_bill = Bill(
        bill_number=new_bill_no,
        bill_date=date.today(),
        customer_id=existing.customer_id,
        subtotal=existing.subtotal,
        discount=existing.discount,
        tax=existing.tax,
        total_amount=existing.total_amount,
        amount_received=0.0,
        pending_amount=existing.total_amount,
        payment_status='PENDING',
        payment_method=existing.payment_method,
        notes=f"Duplicated from #{existing.bill_number}",
        created_by=session['user_id']
    )
    db.session.add(new_bill)
    db.session.flush()

    for item in existing.items:
        dup_item = BillItem(
            bill_id=new_bill.id,
            item_id=item.item_id,
            item_name=item.item_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount=item.discount,
            tax=item.tax,
            total_amount=item.total_amount,
            material=item.material,
            dimensions=item.dimensions
        )
        db.session.add(dup_item)

    db.session.commit()
    log_audit('DUPLICATE_BILL', table_name='bills', record_id=new_bill.id, details=f"Duplicated Bill #{existing.bill_number} to #{new_bill_no}")
    flash(f'Bill #{existing.bill_number} duplicated as #{new_bill_no}. You can edit it now.', 'success')
    return redirect(url_for('income.edit_bill', bill_id=new_bill.id))
