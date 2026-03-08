import os
import subprocess
import sys
from pathlib import Path


def main():
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)

    # Run the build script
    print("Running DXT build script...")
    result = subprocess.run(
        [sys.executable, "mcpb/mcpb_build.py"], capture_output=True, text=True
    )

    # Print the output
    print("\n=== STDOUT ===")
    print(result.stdout)

    if result.stderr:
        print("\n=== STDERR ===")
        print(result.stderr)

    # Check if the build was successful
    dist_dir = Path("dist")
    mcpb_files = list(dist_dir.glob("*.mcpb"))

    if mcpb_files:
        print("\n✅ MCPB package created successfully!")
        print(f"Package: {mcpb_files[0]}")
    else:
        print("\n❌ Failed to create MCPB package")


if __name__ == "__main__":
    main()
