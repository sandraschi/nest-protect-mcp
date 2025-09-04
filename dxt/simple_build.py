"""
Simple build script that creates a basic DXT package without DXD validation.
"""

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime
import zipfile

def create_dxt_package():
    """Create a simple DXT package for testing."""
    print("Creating simple DXT package...")
    
    # Create a temporary directory
    temp_dir = Path("dist") / f"nest-protect-mcp-{int(datetime.utcnow().timestamp())}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Using temporary directory: {temp_dir}")
    
    # Create a simple manifest
    manifest = {
        "name": "nest-protect-mcp",
        "version": "0.1.0",
        "description": "Nest Protect MCP Server",
        "author": "Sandra Schiessl",
        "entry_point": "nest_protect_mcp.server:main",
        "python_version": "3.9",
        "dependencies": [
            "fastmcp==2.12.0",
            "pydantic>=1.10.0",
            "aiohttp>=3.8.0",
            "python-dotenv>=0.19.0",
            "toml>=0.10.2",
            "requests>=2.28.0"
        ],
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    # Write the manifest
    with open(temp_dir / "dxt_manifest.json", "w") as f:
        import json
        json.dump(manifest, f, indent=2)
    
    # Create a simple README
    with open(temp_dir / "README.md", "w") as f:
        f.write("# Nest Protect MCP Server\n\n"
               "This is a simple DXT package for the Nest Protect MCP server.\n")
    
    # Create the DXT package
    output_file = Path("dist") / "nest-protect-mcp-0.1.0.dxt"
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(temp_dir)
                zipf.write(file_path, arcname)
    
    print(f"\nSuccessfully created DXT package: {output_file}")
    print(f"Package size: {output_file.stat().st_size / (1024 * 1024):.2f} MB")
    
    # Clean up
    shutil.rmtree(temp_dir)
    
    return True

if __name__ == "__main__":
    print("Simple DXT Package Builder")
    print("=========================")
    
    if create_dxt_package():
        print("\n✅ Build completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Build failed!", file=sys.stderr)
        sys.exit(1)
