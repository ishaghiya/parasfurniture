import os
import shutil
from datetime import datetime
from config import BASE_DIR

DB_PATH = os.path.join(BASE_DIR, 'database.db')
BACKUP_FOLDER = os.path.join(BASE_DIR, 'backups')

def create_database_backup():
    """
    Creates a timestamped backup copy of database.db.
    Returns (backup_filepath, backup_filename).
    """
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"paras_furniture_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_FOLDER, backup_filename)

    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, backup_path)
        return backup_path, backup_filename
    else:
        raise FileNotFoundError("Database file database.db does not exist yet.")

def restore_database_from_file(uploaded_file_path):
    """
    1. Creates automatic safety backup of existing DB.
    2. Overwrites database.db with uploaded_file_path.
    """
    if not os.path.exists(uploaded_file_path):
        raise FileNotFoundError("Uploaded backup file not found.")

    # Step 1: Automatic pre-restore backup
    create_database_backup()

    # Step 2: Overwrite database.db
    shutil.copy2(uploaded_file_path, DB_PATH)
    return True
