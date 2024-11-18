import os
import sys
from pathlib import Path

def create_build_script():
    """
    Creates a build script that includes the full HunterApp class
    and handles resource paths correctly
    """
    # Read the original hunter.py file
    with open('hunter.py', 'r') as f:
        original_code = f.read()
    
    # Extract the HunterApp class and main function
    start_index = original_code.find('class HunterApp')
    end_index = original_code.find('if __name__ == "__main__":')
    hunter_app_code = original_code[start_index:end_index].strip()

    script_content = '''import os
import sys
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

''' + hunter_app_code + '''

def main():
    try:
        root = tk.Tk()
        app = HunterApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
'''

    # Modify the CSV loading line to use resource_path
    script_content = script_content.replace(
        "self.df = pd.read_csv('hunter_data.csv')",
        "self.df = pd.read_csv(resource_path('hunter_data.csv'))"
    )

    # Write the modified script to a new file
    with open('hunter_build.py', 'w', encoding='utf-8') as f:
        f.write(script_content)

def create_spec_file():
    """Creates a PyInstaller spec file with proper configuration"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['hunter_build.py'],
    pathex=[],
    binaries=[],
    datas=[('hunter_data.csv', '.')],
    hiddenimports=['pandas', 'tkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HunterApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Changed to False to hide console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

    with open('hunter.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

def main():
    # Verify files exist
    if not os.path.exists('hunter.py'):
        print("Error: hunter.py not found in current directory")
        return
    if not os.path.exists('hunter_data.csv'):
        print("Error: hunter_data.csv not found in current directory")
        return

    # Create build directory if it doesn't exist
    if not os.path.exists('build'):
        os.makedirs('build')

    # Create the modified Python script and spec file
    print("Creating build files...")
    create_build_script()
    create_spec_file()

    # Build command for PyInstaller
    build_command = 'pyinstaller --clean hunter.spec'
    
    print("\nBuilding executable...")
    result = os.system(build_command)
    
    if result == 0:
        print("\nBuild successful!")
        print("Your executable can be found in the 'dist' folder")
        
        # Verify the build
        exe_path = os.path.join('dist', 'HunterApp.exe')
        if os.path.exists(exe_path):
            print(f"\nExecutable size: {os.path.getsize(exe_path) / 1024 / 1024:.2f} MB")
        
        csv_path = os.path.join('dist', 'hunter_data.csv')
        if os.path.exists(csv_path):
            print("CSV file was successfully bundled")
        else:
            print("Warning: CSV file may not have been bundled correctly")
    else:
        print("\nBuild failed. Please check the error messages above.")

if __name__ == "__main__":
    main()