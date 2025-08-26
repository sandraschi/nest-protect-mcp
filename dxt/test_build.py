import os
import sys
import tempfile
import shutil
from pathlib import Path

def test_dxt_build():
    """Test the DXT build process."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory(prefix="test_dxt_build_") as temp_dir:
        temp_dir = Path(temp_dir)
        print(f"Using temporary directory: {temp_dir}")
        
        # Create a simple package structure
        package_dir = temp_dir / "src" / "test_package"
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a simple __init__.py
        with open(package_dir / "__init__.py", "w") as f:
            f.write("""""Test package for DXT build."""\n""")
        
        # Create a simple cli.py
        with open(package_dir / "cli.py", "w") as f:
            f.write("""""Test package CLI."""
                   """\n\n"""
                   """def main():"""
                   """Main entry point."""
                   """    print(\"Test package\")"""
                   """\n\n"""
                   """if __name__ == \"__main__\":"""
                   """    main()""")
        
        # Create a simple pyproject.toml
        with open(temp_dir / "pyproject.toml", "w") as f:
            f.write("""[build-system]
requires = ["setuptools>=42.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "test-package"
version = "0.1.0"
description = "Test package for DXT build"
authors = [{name = "Test User", email = "test@example.com"}]
requires-python = ">=3.9"

[project.scripts]
test-package = "test_package.cli:main"
""")
        
        # Print the directory structure
        print("\nDirectory structure:")
        for root, dirs, files in os.walk(temp_dir):
            level = root.replace(str(temp_dir), '').count(os.sep)
            indent = ' ' * 4 * (level)
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                print(f"{subindent}{f}")
        
        print("\nTest setup complete!")
        return True

if __name__ == "__main__":
    test_dxt_build()
