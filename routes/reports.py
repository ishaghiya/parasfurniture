from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db
from models.income import Bill, BillItem
from models.expense import Expense, ExpenseCategory
from models.customer import Customer
from models.furniture import FurnitureCategory, FurnitureItem
from routes.auth import login_required, role_required
from services.export_service import export_to_csv, export_to_excel, export_to_pdf

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def index():
    report_type = request.args.get('report_type', 'income')
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    export_fmt = request.args.get('export', '').strip()

    # Parse date filters
    d_from, d_to = None, None
    if date_from:
        try:
            d_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            pass
    if date_to:
        try:
            d_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            pass

    # 1. Income Report
    if report_type == 'income':
        q = Bill.query.filter_by(is_deleted=False)
        if d_from: q = q.filter(Bill.bill_date >= d_from)
        if d_to: q = q.filter(Bill.bill_date <= d_to)
        bills = q.order_by(Bill.bill_date.desc()).all()

        if export_fmt:
            data = [{
                'Bill Number': b.bill_number,
                'Bill Date': b.bill_date.strftime('%d-%m-%Y'),
                'Customer': b.customer.name if b.customer else '',
                'Contact': b.customer.phone if b.customer else '',
                'Location': b.customer.location or b.customer.city if b.customer else '',
                'Bill Amount (₹)': b.total_amount,
                'Amount Received (₹)': b.amount_received,
                'Pending Amount (₹)': b.pending_amount,
                'Payment Status': b.payment_status,
                'Payment Method': b.payment_method
            } for b in bills]

            if export_fmt == 'excel':
                return export_to_excel(data, f"Income_Report_{date.today().strftime('%Y%m%d')}")
            elif export_fmt == 'csv':
                return export_to_csv(data, f"Income_Report_{date.today().strftime('%Y%m%d')}")
            elif export_fmt == 'pdf':
                headers = ['Bill #', 'Date', 'Customer', 'Location', 'Amount', 'Received', 'Pending', 'Status']
                rows = [[b.bill_number, b.bill_date.strftime('%d-%m-%Y'), b.customer.name if b.customer else '', b.customer.location or b.customer.city if b.customer else '', f"₹{b.total_amount:,.2f}", f"₹{b.amount_received:,.2f}", f"₹{b.pending_amount:,.2f}", b.payment_status] for b in bills]
                return export_to_pdf("Income Report", headers, rows, f"Income_Report_{date.today().strftime('%Y%m%d')}")

        return render_template('reports/list.html', report_type=report_type, bills=bills, date_from=date_from, date_to=date_to)

    # 2. Expense Report
    elif report_type == 'expense':
        q = Expense.query.filter_by(is_deleted=False)
        if d_from: q = q.filter(Expense.expense_date >= d_from)
        if d_to: q = q.filter(Expense.expense_date <= d_to)
        expenses = q.order_by(Expense.expense_date.desc()).all()

        if export_fmt:
            data = [{
                'Expense Date': e.expense_date.strftime('%d-%m-%Y'),
                'Category': e.category.name if e.category else '',
                'Expense Type': e.expense_type,
                'Description': e.description,
                'Amount (₹)': e.amount,
                'Vendor': e.vendor or '',
                'Payment Method': e.payment_method
            } for e in expenses]

            if export_fmt == 'excel':
                return export_to_excel(data, f"Expense_Report_{date.today().strftime('%Y%m%d')}")
            elif export_fmt == 'csv':
                return export_to_csv(data, f"Expense_Report_{date.today().strftime('%Y%m%d')}")
            elif export_fmt == 'pdf':
                headers = ['Date', 'Category', 'Type', 'Description', 'Amount', 'Vendor', 'Method']
                rows = [[e.expense_date.strftime('%d-%m-%Y'), e.category.name if e.category else '', e.expense_type, e.description, f"₹{e.amount:,.2f}", e.vendor or '', e.payment_method] for e in expenses]
                return export_to_pdf("Expense Report", headers, rows, f"Expense_Report_{date.today().strftime('%Y%m%d')}")

        return render_template('reports/list.html', report_type=report_type, expenses=expenses, date_from=date_from, date_to=date_to)

    # 3. Profit & Loss Report
    elif report_type == 'profit':
        q_b = Bill.query.filter_by(is_deleted=False)
        q_e = Expense.query.filter_by(is_deleted=False)
        if d_from:
            q_b = q_b.filter(Bill.bill_date >= d_from)
            q_e = q_e.filter(Expense.expense_date >= d_from)
        if d_to:
            q_b = q_b.filter(Bill.bill_date <= d_to)
            q_e = q_e.filter(Expense.expense_date <= d_to)

        tot_income = sum(b.total_amount for b in q_b.all())
        tot_expense = sum(e.amount for e in q_e.all())
        net_profit = tot_income - tot_expense
        margin = (net_profit / tot_income * 100) if tot_income > 0 else 0.0

        summary = {
            'total_income': tot_income,
            'total_expense': tot_expense,
            'net_profit': net_profit,
            'profit_margin': margin
        }

        if export_fmt:
            data = [{
                'Metric': 'Total Income', 'Amount (₹)': tot_income
            }, {
                'Metric': 'Total Expense', 'Amount (₹)': tot_expense
            }, {
                'Metric': 'Net Profit', 'Amount (₹)': net_profit
            }, {
                'Metric': 'Profit Margin (%)', 'Amount (₹)': f"{margin:.2f}%"
            }]
            if export_fmt == 'excel':
                return export_to_excel(data, f"Profit_Report_{date.today().strftime('%Y%m%d')}")
            elif export_fmt == 'csv':
                return export_to_csv(data, f"Profit_Report_{date.today().strftime('%Y%m%d')}")

        return render_template('reports/list.html', report_type=report_type, profit_summary=summary, date_from=date_from, date_to=date_to)

    # 4. Customer Report
    elif report_type == 'customer':
        customers = Customer.query.filter_by(is_deleted=False).all()
        cust_report = []
        for c in customers:
            active_bills = [b for b in c.bills if not b.is_deleted]
            if d_from: active_bills = [b for b in active_bills if b.bill_date >= d_from]
            if d_to: active_bills = [b for b in active_bills if b.bill_date <= d_to]
            if not active_bills and (d_from or d_to): continue

            tot_spent = sum(b.total_amount for b in active_bills)
            tot_paid = sum(b.amount_received for b in active_bills)
            tot_pending = sum(b.pending_amount for b in active_bills)
            cust_report.append({
                'Customer Name': c.name,
                'Phone': c.phone,
                'City': c.city or '',
                'Location': c.location or c.city or '',
                'Total Bills': len(active_bills),
                'Total Revenue (₹)': tot_spent,
                'Amount Paid (₹)': tot_paid,
                'Amount Pending (₹)': tot_pending
            })
        cust_report.sort(key=lambda x: x['Total Revenue (₹)'], reverse=True)

        if export_fmt:
            if export_fmt == 'excel':
                return export_to_excel(cust_report, f"Customer_Report_{date.today().strftime('%Y%m%d')}")
            elif export_fmt == 'csv':
                return export_to_csv(cust_report, f"Customer_Report_{date.today().strftime('%Y%m%d')}")

        return render_template('reports/list.html', report_type=report_type, cust_report=cust_report, date_from=date_from, date_to=date_to)

    # 5. Item Report
    elif report_type == 'item':
        b_items_query = BillItem.query.join(Bill).filter(Bill.is_deleted==False)
        if d_from: b_items_query = b_items_query.filter(Bill.bill_date >= d_from)
        if d_to: b_items_query = b_items_query.filter(Bill.bill_date <= d_to)
        
        b_items = b_items_query.all()
        item_summary = {}
        for bi in b_items:
            iname = bi.item_name
            cat_name = bi.furniture_item.category.name if (bi.furniture_item and bi.furniture_item.category) else 'Other'
            if iname not in item_summary:
                item_summary[iname] = {'item_name': iname, 'category': cat_name, 'units_sold': 0, 'total_revenue': 0.0}
            item_summary[iname]['units_sold'] += bi.quantity
            item_summary[iname]['total_revenue'] += bi.total_amount

        sorted_items = sorted(item_summary.values(), key=lambda x: x['total_revenue'], reverse=True)

        if export_fmt:
            if export_fmt == 'excel':
                return export_to_excel(sorted_items, f"Item_Report_{date.today().strftime('%Y%m%d')}")
            elif export_fmt == 'csv':
                return export_to_csv(sorted_items, f"Item_Report_{date.today().strftime('%Y%m%d')}")

        return render_template('reports/list.html', report_type=report_type, item_report=sorted_items, date_from=date_from, date_to=date_to)

    return render_template('reports/list.html', report_type='income')
