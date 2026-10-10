# Paras Furniture Management System

A complete, production-grade **100% offline desktop business management & financial analytics software** custom built for **Paras Furniture**.

Designed for single-computer offline operation with **zero internet dependency**, cloud storage, or external API calls. All financial records and database files remain safely stored on the local machine.

---

## 🌟 Key Features

1. **Role-Based Access Control (RBAC)**:
   - **Owner Role**: Full system privileges (Income, Expenses, Customers, Master Furniture & Expense Categories, Financial Reports, PDF/Excel Exports, User Management, DB Backup & Restore).
   - **Employee Role**: Restrictive entry privileges (Add bills, Add expenses, Search & View records; no record deletion or backup permissions).
2. **First-Login Security**:
   - Default owner account (`admin` / `Admin@123`) with mandatory forced password change on first launch.
   - Werkzeug password hashing & audit logging.
3. **Client Bill / Income Module**:
   - Manual entry of external pre-generated bills.
   - **Multi-Item Bills**: Add multiple furniture items per bill with automatic line item total, subtotal, tax, discount, total bill amount, amount received, and pending balance calculations.
   - Automatic status calculation: `PAID`, `PARTIALLY_PAID`, `PENDING`, `OVERDUE`.
   - Advanced multi-criteria search & filtering (Bill #, Client, Phone, City, Category, Payment Status, Payment Method).
4. **Expense Management Module**:
   - Manually record raw materials (Wood, Plywood, MDF, Hardware, Polish), worker salaries, daily wages, transport, fuel, electricity, office rent, tea/snacks, and taxes.
   - Custom expense categories & recurring monthly flag.
5. **Interactive Dashboard & Dynamic Cross-Filtering**:
   - 8 Financial KPI Cards (Total Income, Total Expense, Net Profit, Pending Amount, Amount Received, Number of Bills, Unique Clients, Margin %).
   - 9 Dynamic Chart.js charts updating simultaneously on any date preset or filter selection (Income vs Expense, Monthly Profit, Furniture Revenue, Units Sold per Item, Revenue by Location/City, Revenue by Customer, Expense Breakdown, Payment Status, Payment Method).
   - Furniture-specific analytics (Most Sold Item, Top Revenue Location, Top Customer, Avg Bill Value).
6. **Reporting & Exports**:
   - Instant export of Income, Expense, Profit/Loss, Customer, and Furniture Item reports to **Excel (.xlsx)**, **CSV**, and **PDF**.
7. **Offline Database Safety & Audit Trail**:
   - One-click SQLite database backup and safety restore (with auto pre-restore safety backup).
   - Complete audit trail tracking user actions, edits, and deletions.

---

## 🔑 Default Accounts

| Role | Username | Default Password | Notes |
| :--- | :--- | :--- | :--- |
| **Owner** | `admin` | `Admin@123` | Mandatory password change on first login |
| **Employee** | `rahul` | `Rahul@123` | Entry-level permissions |

---

## 🚀 How to Run the Software

### Quick Start (Windows)
Double-click `run.bat` in the project directory.

The application will:
1. Initialize the SQLite database `database.db` automatically if missing.
2. Seed initial default master categories & admin accounts.
3. Launch the local web server at `http://127.0.0.1:5000`.
4. Automatically open your default web browser to the login screen.

---

## 🛠️ Technology Stack
- **Backend**: Python, Flask, SQLAlchemy (SQLite ORM)
- **Database**: SQLite3 (`database.db`)
- **Frontend**: HTML5, Vanilla CSS3 (Custom Paras Furniture teak/slate theme), Bootstrap 5 (bundled locally), Chart.js (bundled locally)
- **Exports**: Pandas, OpenPyXL, ReportLab
- **Security**: Werkzeug Security, CSRF Protection, Role-Based Access Control

---

## 📦 Packaging as Windows Executable (.exe)

To package the application so non-technical users do not need Python installed:

```bash
python build_exe.py
```

The resulting standalone executable will be created inside `dist/ParasFurniture.exe`.
