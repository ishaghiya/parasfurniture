from models import db
from models.user import User
from models.customer import Customer
from models.furniture import FurnitureCategory, FurnitureItem
from models.expense import ExpenseCategory
from models.settings import Setting
from services.audit_service import log_audit

DEFAULT_FURNITURE_CATEGORIES = [
    ("Sofa", "Living room sofas, recliners, L-shaped & leatherette sofas"),
    ("Bed", "King size, queen size, storage beds & wooden cots"),
    ("Dining Table", "Wooden, glass-top, 4-seater & 6-seater dining tables"),
    ("Dining Chair", "Dining seating chairs & wooden cushioned chairs"),
    ("Office Table", "Executive tables, workstation desks & computer tables"),
    ("Office Chair", "Ergonomic, mesh & revolving office chairs"),
    ("Wardrobe", "2-door, 3-door, sliding & modular wooden wardrobes"),
    ("Cabinet", "Storage cabinets, shoe racks & crockery units"),
    ("TV Unit", "Wall-mounted & floor standing TV entertainment consoles"),
    ("Side Table", "Bedside tables & accent side tables"),
    ("Center Table", "Coffee tables, glass tables & wooden tea tables"),
    ("Study Table", "Kids & adult study tables with drawers"),
    ("Bookshelf", "Wooden book racks & display shelves"),
    ("Modular Furniture", "Custom modular setups & office partitions"),
    ("Kitchen Furniture", "Modular kitchen cabinets, trolleys & pantry racks"),
    ("Custom Furniture", "Bespoke handcrafted furniture per client specs"),
    ("Wooden Furniture", "Teak, Sheesham & solid wood handcrafted items"),
    ("Other", "Miscellaneous furniture accessories & decor items")
]

DEFAULT_EXPENSE_CATEGORIES = [
    # WORKER EXPENSES
    ("Worker Salary", "WORKER", "Regular monthly salaries for workshop staff"),
    ("Labour Charges", "WORKER", "Daily wage labour charges and piece-rate payments"),
    ("Overtime", "WORKER", "Overtime payouts for weekend/evening shifts"),
    ("Contractor Payment", "WORKER", "Payments made to specialized sub-contractors"),
    
    # OFFICE EXPENSES
    ("Stationery", "OFFICE", "Paper, pens, registers, bill books"),
    ("Printing", "OFFICE", "Printing costs, cartridges & banners"),
    ("Internet", "OFFICE", "Broadband and Wi-Fi connection bills"),
    ("Telephone", "OFFICE", "Mobile recharge and landline bills"),
    ("Office Supplies", "OFFICE", "General office supplies and cleaning items"),
    
    # FOOD / STAFF
    ("Tea", "FOOD", "Daily tea & coffee for workers and office staff"),
    ("Snacks", "FOOD", "Daily/weekly staff snacks"),
    ("Lunch", "FOOD", "Staff lunch and hospitality expenses"),
    ("Drinking Water", "FOOD", "Water jar delivery and RO maintenance"),
    
    # FACTORY / WORKSHOP
    ("Electricity", "FACTORY", "Factory power bills & commercial meter charges"),
    ("Water", "FACTORY", "Commercial water supply charges"),
    ("Maintenance", "FACTORY", "Factory building & workshop repair"),
    ("Tools", "FACTORY", "Hand tools, saw blades, drill bits & cutters"),
    ("Machinery Repair", "FACTORY", "Woodworking machine servicing and parts replacement"),
    ("Cleaning", "FACTORY", "Sawdust cleaning & waste disposal"),
    ("Safety Equipment", "FACTORY", "Gloves, masks, safety goggles & helmets"),
    
    # MATERIAL
    ("Wood", "MATERIAL", "Teak, Sheesham, Pine & hardwood logs/planks"),
    ("Plywood", "MATERIAL", "Commercial, marine & BWP plywood sheets"),
    ("MDF", "MATERIAL", "Medium-density fibreboard sheets"),
    ("Laminate", "MATERIAL", "Sunmica, veneer & decorative laminates"),
    ("Hardware", "MATERIAL", "Hinges, handles, slides, locks & screws"),
    ("Glue", "MATERIAL", "Wood adhesive, Fevicol & synthetic resins"),
    ("Paint", "MATERIAL", "Wood paint, primers & thinners"),
    ("Polish", "MATERIAL", "PU polish, touch-up & lacquer finish"),
    ("Fabric", "MATERIAL", "Upholstery fabric, velvet & leatherette"),
    ("Foam", "MATERIAL", "High-density foam sheets for sofas and cushions"),
    
    # TRANSPORT
    ("Fuel", "TRANSPORT", "Diesel & petrol for delivery vehicles"),
    ("Delivery", "TRANSPORT", "Local client furniture transport & loading"),
    ("Vehicle Repair", "TRANSPORT", "Tempo/truck servicing & tyre repairs"),
    ("Transportation Charges", "TRANSPORT", "Inter-city freight & log transport"),
    
    # BUSINESS
    ("Rent", "BUSINESS", "Showroom & factory workshop monthly rent"),
    ("Advertising", "BUSINESS", "Local newspaper ads, hoardings & pamphlet distribution"),
    ("Marketing", "BUSINESS", "Social media ads & business promotion"),
    ("Software", "BUSINESS", "Software licenses & subscriptions"),
    ("Professional Fees", "BUSINESS", "CA fees, audit fees & legal counsel"),
    ("Bank Charges", "BUSINESS", "POS machine fees, cheque bounce fees & interest"),
    ("Taxes", "BUSINESS", "Property tax, commercial levies"),
    
    # OTHER
    ("Miscellaneous", "OTHER", "Uncategorized small business expenses")
]

DEFAULT_SETTINGS = {
    'company_name': 'Paras Furniture',
    'company_address': 'GIDC Industrial Estate, Near Highway',
    'company_city': 'Ahmedabad',
    'company_state': 'Gujarat',
    'company_phone': '+91 98765 43210',
    'company_email': 'contact@parasfurniture.com',
    'currency': 'INR',
    'currency_symbol': '₹',
    'date_format': 'DD-MM-YYYY',
    'timezone': 'Asia/Kolkata',
    'inactivity_timeout': '30'
}

def init_db(app):
    with app.app_context():
        db.create_all()

        # 1. Initialize Default Owner Account
        owner = User.query.filter_by(username='admin').first()
        if not owner:
            owner = User(
                username='admin',
                role='OWNER',
                full_name='Paras Furniture Owner',
                must_change_password=True,
                is_active=True
            )
            owner.set_password('Admin@123')
            db.session.add(owner)
            db.session.commit()
            print("Default owner account 'admin' created with password 'Admin@123'. Must change on first login.")

        # 2. Seed Furniture Categories
        for cat_name, desc in DEFAULT_FURNITURE_CATEGORIES:
            cat = FurnitureCategory.query.filter_by(name=cat_name).first()
            if not cat:
                cat = FurnitureCategory(name=cat_name, description=desc, is_active=True)
                db.session.add(cat)
        db.session.commit()

        # 3. Seed Expense Categories
        for exp_name, default_type, desc in DEFAULT_EXPENSE_CATEGORIES:
            exp_cat = ExpenseCategory.query.filter_by(name=exp_name).first()
            if not exp_cat:
                exp_cat = ExpenseCategory(name=exp_name, default_type=default_type, description=desc, is_active=True)
                db.session.add(exp_cat)
        db.session.commit()

        # 4. Seed Default System Settings
        for key, val in DEFAULT_SETTINGS.items():
            if not Setting.query.filter_by(key=key).first():
                db.session.add(Setting(key=key, value=val))
        db.session.commit()

        print("Database schema and default records initialized successfully!")
