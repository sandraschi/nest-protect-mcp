"""
Test script to verify Python imports and environment.
"""

import sys
import os

def test_imports():
    """Test importing required modules."""
    modules = [
        'toml',
        'pathlib',
        'shutil',
        'subprocess',
        'importlib.metadata',
        'typing',
        'datetime',
        'tempfile',
        'json'
    ]
    
    print("Testing imports...")
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
    
    print("\nPython version:", sys.version)
    print("Current working directory:", os.getcwd())
    print("Python executable:", sys.executable)

if __name__ == "__main__":
    test_imports()
