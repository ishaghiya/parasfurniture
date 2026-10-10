import os
import subprocess
import sys

def build():
    print("Building standalone executable for Paras Furniture Management System...")
    
    # Check PyInstaller installation
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        "pyinstaller",
        "--name=ParasFurniture",
        "--onefile",
        "--add-data=templates;templates",
        "--add-data=static;static",
        "--add-data=config.py;.",
        "--add-data=database_setup.py;.",
        "app.py"
    ]

    print(f"Executing: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("\n============================================================")
    print("SUCCESS! Built standalone executable in dist/ParasFurniture.exe")
    print("============================================================")

if __name__ == '__main__':
    build()
