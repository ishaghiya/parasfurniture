import os
from flask import Flask, render_template, session, redirect, url_for
from config import Config
from models import db
from database_setup import init_db

# Import Blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.income import income_bp
from routes.expense import expense_bp
from routes.customers import customers_bp
from routes.furniture import furniture_bp
from routes.reports import reports_bp
from routes.users import users_bp
from routes.backup import backup_bp
from routes.settings import settings_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(furniture_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(settings_bp)

    # Create Database tables and default records on first run
    init_db(app)

    # Context processors & Filters
    @app.template_filter('inr')
    def inr_format(val):
        try:
            return f"₹{float(val):,.2f}"
        except (ValueError, TypeError):
            return "₹0.00"

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('base.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return "Internal Server Error", 500

    return app

app = create_app()

if __name__ == '__main__':
    # Local only desktop server
    app.run(host='127.0.0.1', port=5000, debug=True)
