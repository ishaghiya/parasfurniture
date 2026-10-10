from datetime import datetime, date, timedelta
from sqlalchemy import func, extract
from models import db
from models.user import User
from models.customer import Customer
from models.income import Bill, BillItem
from models.furniture import FurnitureCategory, FurnitureItem
from models.expense import Expense, ExpenseCategory

def parse_date_preset(preset, custom_start=None, custom_end=None):
    today = date.today()
    if preset == 'today':
        return today, today
    elif preset == 'yesterday':
        y = today - timedelta(days=1)
        return y, y
    elif preset == 'this_week':
        start = today - timedelta(days=today.weekday())
        return start, today
    elif preset == 'this_month':
        start = date(today.year, today.month, 1)
        return start, today
    elif preset == 'last_month':
        first_this_month = date(today.year, today.month, 1)
        last_day_prev_month = first_this_month - timedelta(days=1)
        first_day_prev_month = date(last_day_prev_month.year, last_day_prev_month.month, 1)
        return first_day_prev_month, last_day_prev_month
    elif preset == 'this_quarter':
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        start = date(today.year, quarter_month, 1)
        return start, today
    elif preset == 'this_year':
        return date(today.year, 1, 1), today
    elif preset == 'last_year':
        return date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)
    elif preset == 'custom' and custom_start and custom_end:
        try:
            d1 = datetime.strptime(custom_start, '%Y-%m-%d').date()
            d2 = datetime.strptime(custom_end, '%Y-%m-%d').date()
            return d1, d2
        except ValueError:
            pass
    return None, None

def get_dashboard_analytics(filters):
    """
    filters can contain:
    - date_preset, custom_start, custom_end
    - location / city
    - customer_id
    - furniture_category_id
    - furniture_item_id
    - payment_status
    - payment_method
    - expense_category_id
    - employee_id
    """
    preset = filters.get('date_preset', 'this_year')
    d_start, d_end = parse_date_preset(preset, filters.get('custom_start'), filters.get('custom_end'))

    # Base bill query
    bill_query = Bill.query.filter(Bill.is_deleted == False)
    if d_start and d_end:
        bill_query = bill_query.filter(Bill.bill_date >= d_start, Bill.bill_date <= d_end)

    # Base expense query
    expense_query = Expense.query.filter(Expense.is_deleted == False)
    if d_start and d_end:
        expense_query = expense_query.filter(Expense.expense_date >= d_start, Expense.expense_date <= d_end)

    # Additional filters for bills
    location = filters.get('location', '').strip()
    if location:
        bill_query = bill_query.join(Customer).filter(
            (Customer.location.ilike(f'%{location}%')) | (Customer.city.ilike(f'%{location}%'))
        )
        expense_query = expense_query.filter(Expense.location.ilike(f'%{location}%'))

    customer_id = filters.get('customer_id')
    if customer_id and str(customer_id).isdigit():
        bill_query = bill_query.filter(Bill.customer_id == int(customer_id))

    furniture_cat_id = filters.get('furniture_category_id')
    if furniture_cat_id and str(furniture_cat_id).isdigit():
        bill_query = bill_query.join(BillItem).join(FurnitureItem).filter(FurnitureItem.category_id == int(furniture_cat_id)).distinct()

    furniture_item_id = filters.get('furniture_item_id')
    if furniture_item_id and str(furniture_item_id).isdigit():
        bill_query = bill_query.join(BillItem).filter(BillItem.item_id == int(furniture_item_id)).distinct()

    p_status = filters.get('payment_status')
    if p_status:
        bill_query = bill_query.filter(Bill.payment_status == p_status)

    p_method = filters.get('payment_method')
    if p_method:
        bill_query = bill_query.filter(Bill.payment_method == p_method)
        expense_query = expense_query.filter(Expense.payment_method == p_method)

    expense_cat_id = filters.get('expense_category_id')
    if expense_cat_id and str(expense_cat_id).isdigit():
        expense_query = expense_query.filter(Expense.category_id == int(expense_cat_id))

    emp_id = filters.get('employee_id')
    if emp_id and str(emp_id).isdigit():
        bill_query = bill_query.filter(Bill.created_by == int(emp_id))
        expense_query = expense_query.filter(Expense.created_by == int(emp_id))

    # Execute Bill KPI calculations
    matched_bills = bill_query.all()
    total_income = sum(b.total_amount for b in matched_bills)
    amount_received = sum(b.amount_received for b in matched_bills)
    pending_amount = sum(b.pending_amount for b in matched_bills)
    num_bills = len(matched_bills)
    unique_customers = len(set(b.customer_id for b in matched_bills))

    # Execute Expense KPI calculations
    matched_expenses = expense_query.all()
    total_expense = sum(e.amount for e in matched_expenses)

    net_profit = total_income - total_expense
    profit_margin = (net_profit / total_income * 100) if total_income > 0 else 0.0
    avg_bill_value = (total_income / num_bills) if num_bills > 0 else 0.0

    # Collect Furniture Units Sold
    matched_bill_ids = [b.id for b in matched_bills]
    if matched_bill_ids:
        b_items = BillItem.query.filter(BillItem.bill_id.in_(matched_bill_ids)).all()
        total_units_sold = sum(bi.quantity for bi in b_items)
    else:
        b_items = []
        total_units_sold = 0

    # Build Charts Data

    # Chart 1 & 2: Monthly Income, Expense & Profit Trend
    months_map = {}
    for b in matched_bills:
        m_key = b.bill_date.strftime('%b %Y')
        m_sort = b.bill_date.strftime('%Y-%m')
        if m_sort not in months_map:
            months_map[m_sort] = {'label': m_key, 'income': 0.0, 'expense': 0.0}
        months_map[m_sort]['income'] += b.total_amount

    for e in matched_expenses:
        m_key = e.expense_date.strftime('%b %Y')
        m_sort = e.expense_date.strftime('%Y-%m')
        if m_sort not in months_map:
            months_map[m_sort] = {'label': m_key, 'income': 0.0, 'expense': 0.0}
        months_map[m_sort]['expense'] += e.amount

    sorted_months = sorted(months_map.keys())
    chart_months_labels = [months_map[k]['label'] for k in sorted_months]
    chart_income_series = [round(months_map[k]['income'], 2) for k in sorted_months]
    chart_expense_series = [round(months_map[k]['expense'], 2) for k in sorted_months]
    chart_profit_series = [round(months_map[k]['income'] - months_map[k]['expense'], 2) for k in sorted_months]

    # Chart 3 & 4: Furniture Revenue & Quantity Sold per Item
    item_rev_map = {}
    item_qty_map = {}
    for bi in b_items:
        iname = bi.item_name
        item_rev_map[iname] = item_rev_map.get(iname, 0.0) + bi.total_amount
        item_qty_map[iname] = item_qty_map.get(iname, 0) + bi.quantity

    sorted_by_rev = sorted(item_rev_map.items(), key=lambda x: x[1], reverse=True)[:10]
    chart_items_labels = [x[0] for x in sorted_by_rev]
    chart_items_revenue = [round(x[1], 2) for x in sorted_by_rev]
    chart_items_qty = [item_qty_map.get(x[0], 0) for x in sorted_by_rev]

    most_sold_item = max(item_qty_map.items(), key=lambda x: x[1])[0] if item_qty_map else 'N/A'
    highest_rev_item = sorted_by_rev[0][0] if sorted_by_rev else 'N/A'

    # Chart 5: Revenue by Location
    location_map = {}
    for b in matched_bills:
        loc = (b.customer.location or b.customer.city or 'Unknown') if b.customer else 'Unknown'
        location_map[loc] = location_map.get(loc, 0.0) + b.total_amount

    sorted_locs = sorted(location_map.items(), key=lambda x: x[1], reverse=True)[:8]
    chart_loc_labels = [x[0] for x in sorted_locs]
    chart_loc_revenue = [round(x[1], 2) for x in sorted_locs]
    top_location = sorted_locs[0][0] if sorted_locs else 'N/A'

    # Chart 6: Revenue by Customer
    cust_map = {}
    for b in matched_bills:
        cname = b.customer.name if b.customer else 'Unknown'
        cust_map[cname] = cust_map.get(cname, 0.0) + b.total_amount

    sorted_custs = sorted(cust_map.items(), key=lambda x: x[1], reverse=True)[:8]
    chart_cust_labels = [x[0] for x in sorted_custs]
    chart_cust_revenue = [round(x[1], 2) for x in sorted_custs]
    top_customer = sorted_custs[0][0] if sorted_custs else 'N/A'

    # Chart 7: Expense Category Distribution
    exp_cat_map = {}
    for e in matched_expenses:
        cname = e.category.name if e.category else 'Other'
        exp_cat_map[cname] = exp_cat_map.get(cname, 0.0) + e.amount

    sorted_exp_cats = sorted(exp_cat_map.items(), key=lambda x: x[1], reverse=True)[:10]
    chart_exp_cat_labels = [x[0] for x in sorted_exp_cats]
    chart_exp_cat_values = [round(x[1], 2) for x in sorted_exp_cats]
    highest_exp_category = sorted_exp_cats[0][0] if sorted_exp_cats else 'N/A'

    # Chart 8: Payment Status Breakdown
    p_status_map = {'PAID': 0, 'PARTIALLY_PAID': 0, 'PENDING': 0, 'OVERDUE': 0}
    for b in matched_bills:
        st = b.payment_status or 'PENDING'
        p_status_map[st] = p_status_map.get(st, 0) + 1

    # Chart 9: Payment Method Distribution
    p_method_map = {}
    for b in matched_bills:
        pm = b.payment_method or 'Cash'
        p_method_map[pm] = p_method_map.get(pm, 0.0) + b.total_amount

    return {
        'kpis': {
            'total_income': round(total_income, 2),
            'total_expense': round(total_expense, 2),
            'net_profit': round(net_profit, 2),
            'num_bills': num_bills,
            'num_customers': unique_customers,
            'amount_received': round(amount_received, 2),
            'pending_amount': round(pending_amount, 2),
            'profit_margin': round(profit_margin, 1),
            'avg_bill_value': round(avg_bill_value, 2),
            'total_units_sold': total_units_sold,
            'most_sold_item': most_sold_item,
            'highest_rev_item': highest_rev_item,
            'top_customer': top_customer,
            'top_location': top_location,
            'highest_exp_category': highest_exp_category
        },
        'charts': {
            'months': chart_months_labels,
            'income_series': chart_income_series,
            'expense_series': chart_expense_series,
            'profit_series': chart_profit_series,
            'items_labels': chart_items_labels,
            'items_revenue': chart_items_revenue,
            'items_qty': chart_items_qty,
            'location_labels': chart_loc_labels,
            'location_revenue': chart_loc_revenue,
            'customer_labels': chart_cust_labels,
            'customer_revenue': chart_cust_revenue,
            'exp_cat_labels': chart_exp_cat_labels,
            'exp_cat_values': chart_exp_cat_values,
            'payment_status': p_status_map,
            'payment_method': {
                'labels': list(p_method_map.keys()),
                'values': [round(v, 2) for v in p_method_map.values()]
            }
        }
    }
