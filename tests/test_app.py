import unittest
import os
from datetime import date
from app import create_app
from models import db
from models.user import User
from models.customer import Customer
from models.income import Bill, BillItem
from models.expense import ExpenseCategory, Expense
from services.dashboard_service import get_dashboard_analytics
from services.backup_service import create_database_backup

class ParasFurnitureTestCase(unittest.TestCase):
    def setUp(self):
        os.environ['SECRET_KEY'] = 'test_secret_key'
        test_db_path = os.path.join(os.path.dirname(__file__), 'test_database.db')
        os.environ['DATABASE_URL'] = f"sqlite:///{test_db_path}"
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{test_db_path}"
        self.client = self.app.test_client()

    def tearDown(self):
        test_db_path = os.path.join(os.path.dirname(__file__), 'test_database.db')
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except Exception:
                pass

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_01_default_owner_login_and_forced_password_change(self):
        """Test default owner account admin/Admin@123 login and forced password reset."""
        response = self.login('admin', 'Admin@123')
        self.assertIn(b'Security Update Required', response.data)

        # Submit password change
        change_resp = self.client.post('/change-password-forced', data=dict(
            new_password='NewAdminPass@123',
            confirm_password='NewAdminPass@123'
        ), follow_redirects=True)
        self.assertIn(b'Dashboard', change_resp.data)

    def test_02_employee_login_and_rbac_restrictions(self):
        """Test employee account restricted permissions."""
        self.login('rahul', 'Rahul@123')
        
        # Access Dashboard - OK
        dash_resp = self.client.get('/dashboard')
        self.assertEqual(dash_resp.status_code, 200)

        # Employee attempting owner-only routes should be restricted (redirected with error)
        users_resp = self.client.get('/users', follow_redirects=True)
        self.assertIn(b'Access denied', users_resp.data)

        backup_resp = self.client.get('/backup', follow_redirects=True)
        self.assertIn(b'Access denied', backup_resp.data)

    def test_03_bill_financial_calculations(self):
        """Test multi-item bill math and payment status determination."""
        with self.app.app_context():
            cust = Customer.query.first()
            user = User.query.first()

            bill = Bill(
                bill_number='TEST-BILL-999',
                bill_date=date.today(),
                customer_id=cust.id,
                discount=500.0,
                tax=200.0,
                amount_received=2500.0,
                created_by=user.id
            )
            db.session.add(bill)
            db.session.flush()

            # Item 1: Qty 2 @ 1000 = 2000
            item1 = BillItem(bill_id=bill.id, item_name='Test Sofa', quantity=2, unit_price=1000.0)
            item1.calculate_total()
            db.session.add(item1)

            # Item 2: Qty 1 @ 1500 = 1500
            item2 = BillItem(bill_id=bill.id, item_name='Test Table', quantity=1, unit_price=1500.0)
            item2.calculate_total()
            db.session.add(item2)

            # Subtotal = 2000 + 1500 = 3500
            bill.subtotal = item1.total_amount + item2.total_amount
            # Final Bill Amount = 3500 - 500 + 200 = 3200
            # Pending Amount = 3200 - 2500 = 700
            bill.calculate_totals()

            self.assertEqual(bill.subtotal, 3500.0)
            self.assertEqual(bill.total_amount, 3200.0)
            self.assertEqual(bill.pending_amount, 700.0)
            self.assertEqual(bill.payment_status, 'PARTIALLY_PAID')

            # Clean up test bill
            db.session.delete(item1)
            db.session.delete(item2)
            db.session.delete(bill)
            db.session.commit()

    def test_04_dashboard_cross_filtering_api(self):
        """Test central dashboard analytics service query."""
        with self.app.app_context():
            analytics = get_dashboard_analytics({'date_preset': 'this_year'})
            self.assertIn('kpis', analytics)
            self.assertIn('charts', analytics)
            self.assertIn('total_income', analytics['kpis'])
            self.assertIn('total_expense', analytics['kpis'])
            self.assertIn('net_profit', analytics['kpis'])

    def test_05_backup_creation(self):
        """Test database backup service."""
        b_path, b_name = create_database_backup()
        self.assertTrue(os.path.exists(b_path))
        self.assertTrue(b_name.endswith('.db'))

if __name__ == '__main__':
    unittest.main()
