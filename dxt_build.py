"""
DXT build script for Nest Protect MCP.

This script creates a DXT package for the Nest Protect MCP server,
including all dependencies and using Anthropic DXD for validation.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

# Constants
PACKAGE_NAME = "nest_protect_mcp"
DIST_DIR = Path("dist")
DIST_DIR.mkdir(exist_ok=True, parents=True)

# Dependencies from pyproject.toml
REQUIRED_DEPENDENCIES = [
    "fastmcp>=0.1.0",
    "pydantic>=1.9.0",
    "aiohttp>=3.8.0",
    "python-dotenv>=0.20.0",
    "toml>=0.10.2",
    "python-dateutil>=2.8.2",
]

def run_command(cmd: List[str], cwd: Optional[Path] = None) -> bool:
    """Run a shell command and return True if successful."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or Path.cwd(),
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}", file=sys.stderr)
        print(f"Error output: {e.stderr}", file=sys.stderr)
        return False

def validate_with_dxd(manifest_path: Path) -> bool:
    """Validate the package using Anthropic DXD."""
    print("Validating package with Anthropic DXD...")
    return run_command(["dxt", "validate", str(manifest_path)])

def install_dependencies(temp_dir: Path) -> bool:
    """Install package dependencies into the temporary directory."""
    print("Installing dependencies...")
    
    # Create a requirements.txt file
    requirements = temp_dir / "requirements.txt"
    with open(requirements, 'w', encoding='utf-8') as f:
        for dep in REQUIRED_DEPENDENCIES:
            f.write(f"{dep}\n")
    
    # Install dependencies to a lib directory
    lib_dir = temp_dir / "lib"
    lib_dir.mkdir(exist_ok=True)
    
    return run_command([
        sys.executable, "-m", "pip", "install",
        "--target", str(lib_dir),
        "--no-compile",
        "-r", str(requirements)
    ])

def copy_package_files(temp_dir: Path) -> bool:
    """Copy package files to the temporary directory."""
    print("Copying package files...")
    
    # Create package directory
    pkg_dir = temp_dir / PACKAGE_NAME
    pkg_dir.mkdir(exist_ok=True, parents=True)
    
    # Copy Python files from src
    src_dir = Path("src") / PACKAGE_NAME
    if not src_dir.exists():
        print(f"Error: Source directory not found: {src_dir}", file=sys.stderr)
        return False
    
    # Copy Python files
    for py_file in src_dir.glob("**/*.py"):
        rel_path = py_file.relative_to(src_dir.parent)
        dest_file = temp_dir / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(py_file, dest_file)
    
    # Copy config directory if it exists
    config_src = Path("config")
    if config_src.exists():
        shutil.copytree(config_src, temp_dir / "config", dirs_exist_ok=True)
    
    # Copy README and other docs
    for doc_file in ["README.md", "LICENSE", "CHANGELOG.md"]:
        if Path(doc_file).exists():
            shutil.copy2(doc_file, temp_dir / doc_file)
    
    return True

def create_dxt_package() -> bool:
    """Create the DXT package with all dependencies."""
    # Read version from pyproject.toml or use default
    version = "0.1.0"
    try:
        import tomli
        with open("pyproject.toml", "rb") as f:
            pyproject = tomli.load(f)
            version = pyproject.get("project", {}).get("version", version)
    except Exception as e:
        print(f"Warning: Could not read version from pyproject.toml: {e}")
    
    # Create temporary directory for packaging
    with tempfile.TemporaryDirectory(prefix=f"{PACKAGE_NAME}_build_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        
        # Set up package structure
        (temp_dir / PACKAGE_NAME).mkdir(exist_ok=True, parents=True)
        
        # Copy package files
        if not copy_package_files(temp_dir):
            return False
        
        # Install dependencies
        if not install_dependencies(temp_dir):
            return False
        
        # Copy dxt_manifest.json
        if not Path("dxt_manifest.json").exists():
            print("Error: dxt_manifest.json not found", file=sys.stderr)
            return False
        shutil.copy2("dxt_manifest.json", temp_dir / "dxt_manifest.json")
        
        # Validate with DXD
        if not validate_with_dxd(temp_dir / "dxt_manifest.json"):
            print("DXD validation failed", file=sys.stderr)
            return False
        
        # Create the DXT package
        output_file = DIST_DIR / f"{PACKAGE_NAME}-{version}.dxt"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if output_file.exists():
            output_file.unlink()
        
        # Create zip file
        print(f"Creating DXT package: {output_file}")
        shutil.make_archive(
            str(output_file.with_suffix('')),  # Remove .dxt extension
            'zip',
            root_dir=temp_dir
        )
        
        # Rename .zip to .dxt
        zip_file = output_file.with_suffix('.zip')
        if zip_file.exists():
            zip_file.rename(output_file)
        
        print(f"\nSuccessfully created DXT package: {output_file}")
        return True

def main() -> int:
    """Main entry point for the build script."""
    print(f"Building {PACKAGE_NAME} DXT package...")
    
    if not create_dxt_package():
        print("\nError: Failed to create DXT package", file=sys.stderr)
        return 1
    
    print("\nBuild completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
