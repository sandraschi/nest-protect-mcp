import os
import sys
import subprocess
from pathlib import Path

def main():
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Run the build script
    print("Running DXT build script...")
    result = subprocess.run(
        [sys.executable, "dxt/dxt_build.py"],
        capture_output=True,
        text=True
    )
    
    # Print the output
    print("\n=== STDOUT ===")
    print(result.stdout)
    
    if result.stderr:
        print("\n=== STDERR ===")
        print(result.stderr)
    
    # Check if the build was successful
    dist_dir = Path("dist")
    dxt_files = list(dist_dir.glob("*.dxt"))
    
    if dxt_files:
        print("\n✅ DXT package created successfully!")
        print(f"Package: {dxt_files[0]}")
    else:
        print("\n❌ Failed to create DXT package")

if __name__ == "__main__":
    main()
