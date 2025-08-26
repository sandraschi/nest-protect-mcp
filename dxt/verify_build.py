"""
Verify the DXT build process with minimal dependencies.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and print the output."""
    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {cwd or os.getcwd()}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        
        print("\n=== STDOUT ===")
        print(result.stdout)
        
        if result.stderr:
            print("\n=== STDERR ===")
            print(result.stderr)
            
        print(f"\nExit code: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    """Main entry point."""
    # Print Python info
    print("=== Python Info ===")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if we can find the build script
    script_path = Path("dxt_build.py")
    if not script_path.exists():
        print(f"Error: {script_path} not found in current directory")
        return 1
    
    # Try to run the build script with Python
    print("\n=== Running DXT Build Script ===")
    success = run_command([sys.executable, "dxt_build.py"])
    
    if not success:
        print("\n=== Build Failed ===")
        print("Trying to run with Python's verbose flag...")
        success = run_command([sys.executable, "-v", "dxt_build.py"])
    
    # Check for output files
    print("\n=== Checking for Output Files ===")
    dist_dir = Path("dist")
    if dist_dir.exists():
        print(f"Contents of {dist_dir}:")
        for f in dist_dir.iterdir():
            print(f"  - {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    else:
        print(f"Directory {dist_dir} does not exist")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
