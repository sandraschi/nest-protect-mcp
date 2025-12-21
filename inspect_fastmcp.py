import importlib
import pkgutil


def print_module_structure(module_name, level=0):
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        print("  " * level + f"❌ Could not import {module_name}: {e}")
        return

    print(
        "  " * level
        + f"📦 {module_name} (version: {getattr(module, '__version__', 'not specified')})"
    )

    # List all attributes that don't start with underscore
    attrs = [attr for attr in dir(module) if not attr.startswith("_")]
    if attrs:
        print("  " * level + "  ├── Attributes/Classes:")
        for attr in attrs:
            obj = getattr(module, attr)
            if callable(obj):
                print("  " * (level + 1) + f"🔹 {attr}()")
            else:
                print("  " * (level + 1) + f"📎 {attr} = {obj}")

    # Try to find submodules
    try:
        module_path = module.__path__
    except AttributeError:
        module_path = None

    if module_path:
        print("  " * level + "  └── Submodules:")
        for _, name, is_pkg in pkgutil.iter_modules(module_path, module_name + "."):
            if is_pkg:
                print("  " * (level + 1) + f"📦 {name}")
            else:
                print("  " * (level + 1) + f"📄 {name}")


if __name__ == "__main__":
    print("🔍 Inspecting FastMCP package structure...\n")
    print_module_structure("fastmcp")

    # Also try to import specific submodules
    for submodule in ["server", "client", "core"]:
        try:
            module = importlib.import_module(f"fastmcp.{submodule}")
            print(f"\n✅ Successfully imported fastmcp.{submodule}")
        except (ImportError, ModuleNotFoundError) as e:
            print(f"\n❌ Could not import fastmcp.{submodule}: {e}")
