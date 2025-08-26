"""
Test script for DXT build process.

This script tests the DXT build process by creating a temporary directory,
copying the necessary files, and running the build script.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and return the output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
    else:
        print(result.stdout)
    return result.returncode == 0

def test_dxt_build():
    """Test the DXT build process."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory(prefix="test_dxt_build_") as temp_dir:
        temp_dir = Path(temp_dir)
        print(f"Using temporary directory: {temp_dir}")
        
        # Copy the dxt directory to the temp directory
        dxt_dir = temp_dir / "dxt"
        shutil.copytree("dxt", dxt_dir)
        
        # Copy pyproject.toml to the temp directory
        shutil.copy2("pyproject.toml", temp_dir / "pyproject.toml")
        
        # Create a simple test package
        src_dir = temp_dir / "src" / "nest_protect_mcp"
        src_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a simple __init__.py
        with open(src_dir / "__init__.py", "w") as f:
            f.write("""""Nest Protect MCP package."""\n""")
        
        # Create a simple cli.py
        with open(src_dir / "cli.py", "w") as f:
            f.write("""""Command-line interface for Nest Protect MCP."""
                   """\n\n"""
                   """def main():"""
                   """Main entry point."""
                   """    print("Nest Protect MCP")"""
                   """\n\n"""
                   """if __name__ == "__main__":"""
                   """    main()""")
        
        # Run the build script
        build_script = dxt_dir / "dxt_build.py"
        if not build_script.exists():
            print(f"Error: Build script not found: {build_script}", file=sys.stderr)
            return False
        
        # Run the build script
        success = run_command([sys.executable, str(build_script)], cwd=temp_dir)
        
        # Check if the package was created
        dist_dir = temp_dir / "dist"
        dxt_files = list(dist_dir.glob("*.dxt"))
        
        if not dxt_files:
            print("Error: No DXT package was created", file=sys.stderr)
            return False
        
        print(f"\nSuccess! Created DXT package: {dxt_files[0]}")
        return True

if __name__ == "__main__":
    if test_dxt_build():
        print("\nTest passed!")
        sys.exit(0)
    else:
        print("\nTest failed!", file=sys.stderr)
        sys.exit(1)
