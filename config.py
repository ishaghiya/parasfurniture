import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'paras_furniture_super_secret_offline_key_2026_gujarat'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload & export directories
    EXPORT_DIR = os.path.join(BASE_DIR, 'exports')
    BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    
    # Inactivity timeout (minutes)
    SESSION_INACTIVITY_TIMEOUT = 30
    
    # Indian Business Defaults
    CURRENCY = 'INR'
    CURRENCY_SYMBOL = '₹'
    DATE_FORMAT = '%d-%m-%Y'
    TIMEZONE = 'Asia/Kolkata'
    DEFAULT_STATE = 'Gujarat'
