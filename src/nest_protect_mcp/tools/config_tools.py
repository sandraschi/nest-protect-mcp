"""Configuration tools for Nest Protect MCP."""

import os
import json
import toml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from ..tools import tool
from ..config import Config, load_config, save_config

@tool(name="get_config", description="Get current configuration", parameters={"section": {"type": "string", "description": "Specific section to retrieve (optional)", "required": False}}, examples=["get_config()", "get_config('nest')"])
async def get_config(section: Optional[str] = None) -> Dict[str, Any]:
    """Get current configuration or a specific section."""
    from ..server import app
    
    try:
        config = app.state.config.dict()
        if section:
            return {"status": "success", "config": {section: config.get(section, {})}}
        return {"status": "success", "config": config}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get config: {str(e)}"}

@tool(name="update_config", description="Update configuration values", parameters={"updates": {"type": "object", "description": "Dictionary of configuration updates", "required": True}, "save_to_file": {"type": "boolean", "description": "Whether to save changes to config file", "default": True}}, examples=["update_config({'nest': {'client_id': 'new-id', 'client_secret': 'new-secret'}})"])
async def update_config(updates: Dict[str, Any], save_to_file: bool = True) -> Dict[str, Any]:
    """Update configuration values."""
    from ..server import app
    
    try:
        # Get current config as dict
        current_config = app.state.config.dict()
        
        # Apply updates
        for section, values in updates.items():
            if section in current_config and isinstance(current_config[section], dict) and isinstance(values, dict):
                current_config[section].update(values)
            else:
                current_config[section] = values
        
        # Update config object
        app.state.config = Config(**current_config)
        
        # Save to file if requested
        if save_to_file:
            config_path = Path("config/default.toml")
            if not config_path.exists():
                config_path.parent.mkdir(parents=True, exist_ok=True)
                
            with open(config_path, 'w') as f:
                toml.dump(current_config, f)
        
        return {"status": "success", "message": "Configuration updated", "saved_to_file": save_to_file}
    except Exception as e:
        return {"status": "error", "message": f"Failed to update config: {str(e)}"}

@tool(name="reset_config", description="Reset configuration to defaults", parameters={"confirm": {"type": "boolean", "description": "Must be set to True to confirm reset", "default": False}}, examples=["reset_config(confirm=True)"])
async def reset_config(confirm: bool = False) -> Dict[str, Any]:
    """Reset configuration to default values."""
    if not confirm:
        return {"status": "error", "message": "Confirmation required. Set confirm=True to reset configuration."}
    
    try:
        from ..server import app
        from ..config import default_config
        
        # Reset to defaults
        app.state.config = default_config()
        
        # Save to file
        config_path = Path("config/default.toml")
        if config_path.exists():
            config_path.unlink()
        
        return {"status": "success", "message": "Configuration reset to defaults"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to reset config: {str(e)}"}

@tool(name="export_config", description="Export current configuration to a file", parameters={"file_path": {"type": "string", "description": "Path to save the config file", "default": "config/exported_config.toml"}, "format": {"type": "string", "description": "Export format (toml, json)", "enum": ["toml", "json"], "default": "toml"}}, examples=["export_config()", "export_config('backup/config_backup.json', 'json')"])
async def export_config(file_path: str = "config/exported_config.toml", format: str = "toml") -> Dict[str, Any]:
    """Export current configuration to a file."""
    from ..server import app
    
    try:
        config_data = app.state.config.dict()
        export_path = Path(file_path)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == "json":
            with open(export_path, 'w') as f:
                json.dump(config_data, f, indent=2)
        else:  # Default to TOML
            with open(export_path, 'w') as f:
                toml.dump(config_data, f)
        
        return {"status": "success", "message": f"Configuration exported to {file_path}", "format": format}
    except Exception as e:
        return {"status": "error", "message": f"Failed to export config: {str(e)}"}

@tool(name="import_config", description="Import configuration from a file", parameters={"file_path": {"type": "string", "description": "Path to the config file to import", "required": True}, "merge": {"type": "boolean", "description": "Merge with existing config (True) or replace (False)", "default": True}}, examples=["import_config('backup/config_backup.toml')", "import_config('config/custom.json', merge=False)"])
async def import_config(file_path: str, merge: bool = True) -> Dict[str, Any]:
    """Import configuration from a file."""
    from ..server import app
    
    try:
        import_path = Path(file_path)
        if not import_path.exists():
            return {"status": "error", "message": f"File not found: {file_path}"}
        
        # Load the imported config
        if file_path.lower().endswith('.json'):
            with open(import_path, 'r') as f:
                imported_config = json.load(f)
        else:  # Assume TOML for other extensions
            with open(import_path, 'r') as f:
                imported_config = toml.load(f)
        
        # Get current config
        current_config = app.state.config.dict()
        
        # Merge or replace
        if merge:
            # Deep merge dictionaries
            def deep_merge(d1, d2):
                for k, v in d2.items():
                    if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                        deep_merge(d1[k], v)
                    else:
                        d1[k] = v
                return d1
            
            updated_config = deep_merge(current_config, imported_config)
        else:
            updated_config = imported_config
        
        # Update config
        app.state.config = Config(**updated_config)
        
        # Save to default config file
        config_path = Path("config/default.toml")
        with open(config_path, 'w') as f:
            toml.dump(updated_config, f)
        
        return {"status": "success", "message": f"Configuration imported from {file_path}", "merged": merge}
    except Exception as e:
        return {"status": "error", "message": f"Failed to import config: {str(e)}"}
