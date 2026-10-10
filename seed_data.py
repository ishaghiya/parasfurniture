import random
from datetime import datetime, date, timedelta
from app import create_app
from models import db
from models.user import User
from models.customer import Customer
from models.furniture import FurnitureCategory, FurnitureItem
from models.income import Bill, BillItem
from models.expense import ExpenseCategory, Expense
from models.settings import Setting

def seed_demo_data():
    app = create_app()
    with app.app_context():
        print("Seeding realistic Paras Furniture demo dataset...")

        # 1. Ensure Employee user 'rahul'
        employee = User.query.filter_by(username='rahul').first()
        if not employee:
            employee = User(
                username='rahul',
                full_name='Rahul Patel (Sales)',
                role='EMPLOYEE',
                must_change_password=False,
                is_active=True
            )
            employee.set_password('Rahul@123')
            db.session.add(employee)
            db.session.commit()
            print("Created employee user 'rahul' with password 'Rahul@123'.")

        owner = User.query.filter_by(username='admin').first()

        # 2. Seed Realistic Customers
        customers_info = [
            ("ABC Interiors", "9876543210", "abc@interiors.com", "Near Commerce Six Roads, Navrangpura", "Ahmedabad", "Gujarat", "380009", "Navrangpura", "Interior Designer", "24ABCDE1234F1Z5"),
            ("Shree Developers", "9825012345", "contact@shreedevelopers.com", "SG Highway, Opp YMCA", "Ahmedabad", "Gujarat", "380015", "SG Highway", "Builder", "24AAAAA5555B1Z1"),
            ("Patel Residence", "9898011223", "patel.residence@gmail.com", "Bunglow #42, Sterling City, Bopal", "Ahmedabad", "Gujarat", "380058", "Bopal", "Individual", ""),
            ("Royal Furnishings", "9727099887", "info@royalfurnishings.in", "Ring Road, Near Textile Market", "Surat", "Gujarat", "395002", "Ring Road", "Business", "24ROYAL7777C1Z9"),
            ("Mehta Architects", "9426011122", "designs@mehtaarchitects.com", "Alkapuri Main Road", "Vadodara", "Gujarat", "390007", "Alkapuri", "Architect", "24MEHTA8888D1Z2"),
            ("Galaxy Builders", "9879033445", "projects@galaxybuilders.com", "Kudasan, Near PDEU", "Gandhinagar", "Gujarat", "382421", "Kudasan", "Builder", "24GALAXY9999E1Z4"),
            ("Shah Residence", "9824088776", "shah.family@yahoo.com", "Race Course Road", "Rajkot", "Gujarat", "360001", "Race Course", "Individual", ""),
            ("Vraj Interior Design Studio", "9909012345", "design@vrajstudio.in", "Satellite Road", "Ahmedabad", "Gujarat", "380015", "Satellite", "Interior Designer", "24VRAJ1111F1Z6")
        ]

        customer_objs = []
        for name, phone, email, addr, city, state, pin, loc, ctype, gst in customers_info:
            c = Customer.query.filter_by(phone=phone).first()
            if not c:
                c = Customer(
                    name=name, phone=phone, email=email, address=addr,
                    city=city, state=state, pincode=pin, location=loc,
                    customer_type=ctype, gst_number=gst
                )
                db.session.add(c)
                db.session.flush()
            customer_objs.append(c)
        db.session.commit()

        # 3. Seed Furniture Master Catalog Items
        furniture_catalog_data = [
            ("Sofa", ["L-Shape 6-Seater Leatherette Sofa", "3+2 Recline Fabric Sofa", "Chesterfield 3-Seater Velvet Sofa"]),
            ("Bed", ["King Size Teak Wood Bed with Hydraulic Storage", "Queen Size Modern Cot", "Poster Bed with Carved Legs"]),
            ("Dining Table", ["6-Seater Solid Teak Dining Table", "4-Seater Glass Top Dining Table", "Marble Top 8-Seater Dining Set"]),
            ("Dining Chair", ["Cushioned Teak Dining Chair", "Ergonomic Wooden Chair"]),
            ("Office Table", ["Executive Boss Table 6ft", "Computer Workstation Desk"]),
            ("Office Chair", ["High Back Mesh Executive Chair", "Ergonomic Office Revolving Chair"]),
            ("Wardrobe", ["3-Door Sliding Teak Wardrobe", "4-Door Wooden Cupboard with Mirror"]),
            ("TV Unit", ["Wall Mounted Modular TV Console", "Floor Standing Wooden Entertainment Cabinet"])
        ]

        furniture_items_pool = []
        for cat_name, item_names in furniture_catalog_data:
            cat = FurnitureCategory.query.filter_by(name=cat_name).first()
            if cat:
                for iname in item_names:
                    fi = FurnitureItem.query.filter_by(name=iname).first()
                    if not fi:
                        fi = FurnitureItem(name=iname, category_id=cat.id, is_active=True)
                        db.session.add(fi)
                        db.session.flush()
                    furniture_items_pool.append((fi, cat))
        db.session.commit()

        # 4. Generate Demo Bills (Income) across the past 12 months
        if Bill.query.count() < 5:
            today = date.today()
            payment_methods = ['Cash', 'UPI', 'Bank Transfer', 'Cheque', 'Card']
            
            bill_counter = 1001

            for month_offset in range(12, -1, -1):
                # Generate 2 to 4 bills per month
                num_bills_this_month = random.randint(2, 4)
                for _ in range(num_bills_this_month):
                    b_date = today - timedelta(days=month_offset * 30 + random.randint(1, 25))
                    cust = random.choice(customer_objs)
                    creator = random.choice([owner, employee])

                    bill_no = f"PF-{bill_counter}"
                    bill_counter += 1

                    bill = Bill(
                        bill_number=bill_no,
                        bill_date=b_date,
                        due_date=b_date + timedelta(days=30),
                        customer_id=cust.id,
                        discount=random.choice([0, 1000, 2000, 5000]),
                        tax=random.choice([0, 1800, 3600, 5400]),
                        payment_method=random.choice(payment_methods),
                        reference_number=f"BILL-REF-{random.randint(100,999)}",
                        created_by=creator.id
                    )
                    db.session.add(bill)
                    db.session.flush()

                    # Add 1 to 3 items per bill
                    items_count = random.randint(1, 3)
                    subtotal = 0.0
                    for _ in range(items_count):
                        fi, cat = random.choice(furniture_items_pool)
                        qty = random.randint(1, 3)
                        price = random.choice([12000, 25000, 45000, 65000, 85000, 120000])
                        
                        b_item = BillItem(
                            bill_id=bill.id,
                            item_id=fi.id,
                            item_name=fi.name,
                            quantity=qty,
                            unit_price=price,
                            material=random.choice(["Teak Wood", "Sheesham Wood", "Commercial Plywood & Sunmica", "Velvet Fabric"]),
                            dimensions="Standard Specs"
                        )
                        item_total = b_item.calculate_total()
                        subtotal += item_total
                        db.session.add(b_item)

                    bill.subtotal = subtotal
                    final_amt = max(0.0, subtotal - bill.discount + bill.tax)

                    # Random payment completion status
                    status_rand = random.random()
                    if status_rand < 0.65:
                        bill.amount_received = final_amt # PAID
                    elif status_rand < 0.85:
                        bill.amount_received = round(final_amt * 0.5, 2) # PARTIALLY PAID
                    else:
                        bill.amount_received = 0.0 # PENDING or OVERDUE

                    bill.calculate_totals()

            db.session.commit()
            print("Generated realistic client bill records with multi-item entries!")

        # 5. Generate Demo Expenses across the past 12 months
        if Expense.query.count() < 10:
            exp_cats = ExpenseCategory.query.all()
            today = date.today()

            for month_offset in range(12, -1, -1):
                # Generate 4 to 8 expenses per month
                for _ in range(random.randint(4, 8)):
                    e_date = today - timedelta(days=month_offset * 30 + random.randint(1, 28))
                    cat = random.choice(exp_cats)
                    creator = random.choice([owner, employee])

                    amount = random.choice([500, 1200, 3500, 8500, 15000, 25000, 45000, 60000])

                    exp = Expense(
                        expense_date=e_date,
                        category_id=cat.id,
                        expense_type=cat.default_type,
                        description=f"{cat.name} payout for workshop operations",
                        amount=amount,
                        payment_method=random.choice(['Cash', 'UPI', 'Bank Transfer', 'Cheque']),
                        vendor=random.choice(["Gujarat Timber Traders", "Sardar Patel Hardware", "Ahmedabad Power Corp", "Workshop Worker Shift", "Surat Transport Co"]),
                        location="Ahmedabad Workshop",
                        created_by=creator.id
                    )
                    db.session.add(exp)

            db.session.commit()
            print("Generated realistic business expense dataset!")

        print("Demo data seeding completed successfully!")

if __name__ == '__main__':
    seed_demo_data()
