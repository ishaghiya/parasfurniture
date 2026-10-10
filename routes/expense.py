from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models import db
from models.user import User
from models.expense import Expense, ExpenseCategory
from routes.auth import login_required, role_required
from services.audit_service import log_audit

expense_bp = Blueprint('expense', __name__, url_prefix='/expenses')

@expense_bp.route('/')
@login_required
def index():
    search_q = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    category_id = request.args.get('category_id', type=int)
    expense_type = request.args.get('expense_type', '').strip()
    payment_method = request.args.get('payment_method', '').strip()
    employee_id = request.args.get('employee_id', type=int)
    min_amount = request.args.get('min_amount', type=float)
    max_amount = request.args.get('max_amount', type=float)

    query = Expense.query.filter_by(is_deleted=False)

    if search_q:
        query = query.filter(
            (Expense.description.ilike(f'%{search_q}%')) |
            (Expense.vendor.ilike(f'%{search_q}%')) |
            (Expense.receipt_number.ilike(f'%{search_q}%')) |
            (Expense.location.ilike(f'%{search_q}%'))
        )

    if date_from:
        try:
            d_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Expense.expense_date >= d_from)
        except ValueError:
            pass

    if date_to:
        try:
            d_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Expense.expense_date <= d_to)
        except ValueError:
            pass

    if category_id:
        query = query.filter_by(category_id=category_id)

    if expense_type:
        query = query.filter_by(expense_type=expense_type)

    if payment_method:
        query = query.filter_by(payment_method=payment_method)

    if employee_id:
        query = query.filter_by(created_by=employee_id)

    if min_amount is not None:
        query = query.filter(Expense.amount >= min_amount)

    if max_amount is not None:
        query = query.filter(Expense.amount <= max_amount)

    expenses = query.order_by(Expense.expense_date.desc(), Expense.id.desc()).all()
    categories = ExpenseCategory.query.filter_by(is_active=True).order_by(ExpenseCategory.name.asc()).all()
    employees = User.query.filter_by(is_active=True).order_by(User.full_name.asc()).all()

    total_expense_sum = sum(e.amount for e in expenses)

    return render_template(
        'expenses/list.html',
        expenses=expenses,
        categories=categories,
        employees=employees,
        total_expense_sum=total_expense_sum,
        filters=request.args
    )

@expense_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        exp_date_str = request.form.get('expense_date', '').strip()
        category_id = request.form.get('category_id', type=int)
        description = request.form.get('description', '').strip()
        amount = float(request.form.get('amount', 0.0) or 0.0)
        payment_method = request.form.get('payment_method', 'Cash')
        vendor = request.form.get('vendor', '').strip()
        receipt_number = request.form.get('receipt_number', '').strip()
        location = request.form.get('location', '').strip()
        recurring = True if request.form.get('recurring') else False
        status = request.form.get('status', 'PAID')
        notes = request.form.get('notes', '').strip()

        if not category_id or not description or amount <= 0:
            flash('Category, Description, and a valid positive Amount are required.', 'danger')
            return redirect(url_for('expense.add'))

        category = ExpenseCategory.query.get(category_id)
        expense_type = category.default_type if category else 'BUSINESS'

        try:
            e_date = datetime.strptime(exp_date_str, '%Y-%m-%d').date()
        except ValueError:
            e_date = date.today()

        expense = Expense(
            expense_date=e_date,
            category_id=category_id,
            expense_type=expense_type,
            description=description,
            amount=amount,
            payment_method=payment_method,
            vendor=vendor,
            receipt_number=receipt_number,
            location=location,
            recurring=recurring,
            status=status,
            notes=notes,
            created_by=session['user_id']
        )
        db.session.add(expense)
        db.session.commit()

        log_audit('ADD_EXPENSE', table_name='expenses', record_id=expense.id, details=f"Added expense: {description} - ₹{amount:,.2f} ({category.name if category else ''})")
        flash(f'Expense of ₹{amount:,.2f} recorded successfully.', 'success')
        return redirect(url_for('expense.index'))

    categories = ExpenseCategory.query.filter_by(is_active=True).order_by(ExpenseCategory.name.asc()).all()
    return render_template('expenses/add.html', categories=categories, today_date=date.today().strftime('%Y-%m-%d'))

@expense_bp.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
@role_required(['OWNER'])
def edit(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.is_deleted:
        flash('Cannot edit a deleted expense.', 'danger')
        return redirect(url_for('expense.index'))

    if request.method == 'POST':
        exp_date_str = request.form.get('expense_date', '').strip()
        expense.category_id = request.form.get('category_id', expense.category_id, type=int)
        expense.description = request.form.get('description', expense.description).strip()
        expense.amount = float(request.form.get('amount', expense.amount) or 0.0)
        expense.payment_method = request.form.get('payment_method', expense.payment_method)
        expense.vendor = request.form.get('vendor', '').strip()
        expense.receipt_number = request.form.get('receipt_number', '').strip()
        expense.location = request.form.get('location', '').strip()
        expense.recurring = True if request.form.get('recurring') else False
        expense.status = request.form.get('status', 'PAID')
        expense.notes = request.form.get('notes', '').strip()

        if exp_date_str:
            try:
                expense.expense_date = datetime.strptime(exp_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        category = ExpenseCategory.query.get(expense.category_id)
        if category:
            expense.expense_type = category.default_type

        db.session.commit()
        log_audit('EDIT_EXPENSE', table_name='expenses', record_id=expense.id, details=f"Updated expense: {expense.description}")
        flash('Expense record updated successfully.', 'success')
        return redirect(url_for('expense.index'))

    categories = ExpenseCategory.query.filter_by(is_active=True).order_by(ExpenseCategory.name.asc()).all()
    return render_template('expenses/edit.html', expense=expense, categories=categories)

@expense_bp.route('/delete/<int:expense_id>', methods=['POST'])
@login_required
@role_required(['OWNER'])
def delete(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    expense.is_deleted = True
    expense.deleted_at = datetime.now()
    db.session.commit()

    log_audit('DELETE_EXPENSE', table_name='expenses', record_id=expense.id, details=f"Soft-deleted expense: {expense.description}")
    flash('Expense record deleted successfully.', 'info')
    return redirect(url_for('expense.index'))

@expense_bp.route('/categories')
@login_required
@role_required(['OWNER'])
def categories():
    cats = ExpenseCategory.query.filter_by(is_active=True).order_by(ExpenseCategory.name.asc()).all()
    return render_template('expenses/categories.html', categories=cats)

@expense_bp.route('/categories/add', methods=['POST'])
@login_required
@role_required(['OWNER'])
def add_category():
    name = request.form.get('name', '').strip()
    default_type = request.form.get('default_type', 'BUSINESS')
    description = request.form.get('description', '').strip()

    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('expense.categories'))

    existing = ExpenseCategory.query.filter_by(name=name).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.default_type = default_type
            existing.description = description
            db.session.commit()
            flash(f'Reactivated expense category "{name}".', 'success')
            return redirect(url_for('expense.categories'))
        flash(f'Expense category "{name}" already exists.', 'warning')
        return redirect(url_for('expense.categories'))

    cat = ExpenseCategory(name=name, default_type=default_type, description=description, is_active=True)
    db.session.add(cat)
    db.session.commit()

    log_audit('ADD_EXPENSE_CATEGORY', table_name='expense_categories', record_id=cat.id, details=f"Added expense category: {name}")
    flash(f'Expense category "{name}" added.', 'success')
    return redirect(url_for('expense.categories'))
