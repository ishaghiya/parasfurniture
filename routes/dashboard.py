from flask import Blueprint, render_template, request, jsonify, session
from models import db
from models.customer import Customer
from models.furniture import FurnitureCategory, FurnitureItem
from models.expense import ExpenseCategory
from models.user import User
from routes.auth import login_required
from services.dashboard_service import get_dashboard_analytics

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    customers = Customer.query.filter_by(is_deleted=False).order_by(Customer.name.asc()).all()
    furniture_cats = FurnitureCategory.query.filter_by(is_active=True).order_by(FurnitureCategory.name.asc()).all()
    furniture_items = FurnitureItem.query.filter_by(is_active=True).order_by(FurnitureItem.name.asc()).all()
    expense_cats = ExpenseCategory.query.filter_by(is_active=True).order_by(ExpenseCategory.name.asc()).all()
    employees = User.query.filter_by(is_active=True).order_by(User.full_name.asc()).all()

    cities = db.session.query(Customer.city).filter(Customer.is_deleted==False, Customer.city.isnot(None)).distinct().all()
    city_list = sorted([c[0] for c in cities if c[0]])

    return render_template(
        'dashboard.html',
        customers=customers,
        furniture_cats=furniture_cats,
        furniture_items=furniture_items,
        expense_cats=expense_cats,
        employees=employees,
        city_list=city_list
    )

@dashboard_bp.route('/api/dashboard/data', methods=['GET', 'POST'])
@login_required
def dashboard_data():
    if request.method == 'POST':
        filters = request.get_json() or {}
    else:
        filters = request.args.to_dict()

    data = get_dashboard_analytics(filters)
    return jsonify(data)
