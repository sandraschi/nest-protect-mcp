"""
Simple test script to verify basic Python environment and imports.
"""

import sys
import os
from pathlib import Path

def main():
    print("=== Python Environment Test ===")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Try to import required modules
    print("\n=== Testing Imports ===")
    
    modules = [
        "toml",
        "pathlib",
        "shutil",
        "subprocess",
        "importlib.metadata"
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
    
    # Check if dxt_build.py exists
    print("\n=== Checking for dxt_build.py ===")
    dxt_build = Path("dxt_build.py")
    if dxt_build.exists():
        print(f"✅ Found {dxt_build}")
        
        # Try to read the file
        try:
            content = dxt_build.read_text(encoding='utf-8')
            print(f"✅ Successfully read {dxt_build} ({len(content)} bytes)")
        except Exception as e:
            print(f"❌ Error reading {dxt_build}: {e}")
    else:
        print(f"❌ {dxt_build} not found in {dxt_build.absolute().parent}")
    
    # Check if we can write to the current directory
    print("\n=== Testing File Permissions ===")
    test_file = Path("test_write.txt")
    try:
        with open(test_file, "w") as f:
            f.write("test")
        print(f"✅ Successfully wrote to {test_file}")
        test_file.unlink()  # Clean up
    except Exception as e:
        print(f"❌ Error writing to {test_file}: {e}")

if __name__ == "__main__":
    main()
