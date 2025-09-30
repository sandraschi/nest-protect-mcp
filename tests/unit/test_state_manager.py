"""
Unit tests for state manager functionality.
"""
import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, AsyncMock

from nest_protect_mcp.state_manager import StateManager, state_manager


class TestStateManager:
    """Test StateManager class."""

    @pytest.fixture
    def temp_state_file(self):
        """Create a temporary state file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test_key": "test_value"}, f)
            temp_file = f.name
        yield temp_file
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)

    @pytest.fixture
    def state_manager_instance(self, temp_state_file):
        """Create a StateManager instance with a temporary state file."""
        # Create a new instance for each test
        manager = StateManager.__new__(StateManager)
        manager._state = {}
        manager._state_file = Path(temp_state_file)
        manager._lock = asyncio.Lock()
        manager._initialized = False
        return manager

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """Test that StateManager follows singleton pattern."""
        manager1 = StateManager()
        manager2 = StateManager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_initialization(self, state_manager_instance):
        """Test state manager initialization."""
        assert not state_manager_instance._initialized

        await state_manager_instance.initialize()

        assert state_manager_instance._initialized
        assert state_manager_instance._state == {"test_key": "test_value"}

    @pytest.mark.asyncio
    async def test_initialization_no_file(self):
        """Test initialization when no state file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "nonexistent.json"
            manager = StateManager.__new__(StateManager)
            manager._state = {}
            manager._state_file = state_file
            manager._lock = asyncio.Lock()
            manager._initialized = False

            await manager.initialize()

            assert manager._initialized
            assert manager._state == {}

    @pytest.mark.asyncio
    async def test_load_state_corrupted_file(self):
        """Test loading corrupted state file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name

        try:
            manager = StateManager.__new__(StateManager)
            manager._state = {}
            manager._state_file = Path(temp_file)
            manager._lock = asyncio.Lock()
            manager._initialized = False

            # Should handle corrupted file gracefully
            await manager.initialize()

            assert manager._initialized
            assert manager._state == {}
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_get_set_operations(self, state_manager_instance):
        """Test basic get/set operations."""
        await state_manager_instance.initialize()

        # Test set operation
        await state_manager_instance.set("test_key2", "test_value2")
        assert await state_manager_instance.get("test_key2") == "test_value2"

        # Test get with default
        assert await state_manager_instance.get("nonexistent", "default") == "default"

        # Test get without default
        assert await state_manager_instance.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_update_operation(self, state_manager_instance):
        """Test update operation."""
        await state_manager_instance.initialize()

        # Set initial value
        await state_manager_instance.set("counter", 0)

        # Update using function
        result = await state_manager_instance.update("counter", lambda x: x + 1)
        assert result == 1
        assert await state_manager_instance.get("counter") == 1

        # Update with default
        result = await state_manager_instance.update("new_counter", lambda x: x + 1, 0)
        assert result == 1

    @pytest.mark.asyncio
    async def test_delete_operation(self, state_manager_instance):
        """Test delete operation."""
        await state_manager_instance.initialize()

        # Set and then delete
        await state_manager_instance.set("temp_key", "temp_value")
        assert await state_manager_instance.get("temp_key") == "temp_value"

        await state_manager_instance.delete("temp_key")
        assert await state_manager_instance.get("temp_key") is None

    @pytest.mark.asyncio
    async def test_clear_operation(self, state_manager_instance):
        """Test clear operation."""
        await state_manager_instance.initialize()

        # Set multiple values
        await state_manager_instance.set("key1", "value1")
        await state_manager_instance.set("key2", "value2")

        assert len(await state_manager_instance.get_all()) == 3  # Including loaded test_key

        await state_manager_instance.clear()
        assert len(await state_manager_instance.get_all()) == 0

    @pytest.mark.asyncio
    async def test_get_all_operation(self, state_manager_instance):
        """Test get_all operation."""
        await state_manager_instance.initialize()

        all_state = await state_manager_instance.get_all()
        assert isinstance(all_state, dict)
        assert "test_key" in all_state

    @pytest.mark.asyncio
    async def test_persistence_disabled(self, state_manager_instance):
        """Test operations with persistence disabled."""
        await state_manager_instance.initialize()

        # Set without persistence
        await state_manager_instance.set("temp_key", "temp_value", persist=False)

        # Value should be set in memory
        assert await state_manager_instance.get("temp_key") == "temp_value"

        # But file should not be updated (this is hard to test directly without mocking file operations)

    @pytest.mark.asyncio
    async def test_concurrent_access(self, state_manager_instance):
        """Test thread safety of state manager."""
        await state_manager_instance.initialize()

        async def increment_counter():
            for _ in range(100):
                await state_manager_instance.update("counter", lambda x: (x or 0) + 1, 0)

        # Run multiple concurrent operations
        tasks = [increment_counter() for _ in range(5)]
        await asyncio.gather(*tasks)

        # Should have exactly 500 increments
        assert await state_manager_instance.get("counter") == 500

    @pytest.mark.asyncio
    async def test_state_file_creation(self):
        """Test that state file is created when saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            state_file = Path(temp_dir) / "state.json"
            manager = StateManager.__new__(StateManager)
            manager._state = {"test": "data"}
            manager._state_file = state_file
            manager._lock = asyncio.Lock()
            manager._initialized = True

            await manager._save_state()

            assert state_file.exists()
            with open(state_file, 'r') as f:
                saved_data = json.load(f)
            assert saved_data == {"test": "data"}

    @pytest.mark.asyncio
    async def test_save_state_error_handling(self, state_manager_instance):
        """Test error handling in save_state."""
        await state_manager_instance.initialize()

        # Mock a file system error
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            # Should not raise an exception, just log it
            await state_manager_instance.set("test_key", "test_value")


class TestGlobalStateManager:
    """Test the global state_manager instance."""

    @pytest.mark.asyncio
    async def test_global_instance(self):
        """Test that global state_manager is accessible."""
        assert state_manager is not None
        assert isinstance(state_manager, StateManager)

    @pytest.mark.asyncio
    async def test_global_instance_operations(self):
        """Test operations on global state manager."""
        # Clear any existing state
        await state_manager.clear()

        # Test basic operations
        await state_manager.set("global_test", "global_value")
        assert await state_manager.get("global_test") == "global_value"

        # Clean up
        await state_manager.delete("global_test")


class TestAppStateLegacy:
    """Test legacy AppState compatibility layer."""

    def test_app_state_creation(self):
        """Test AppState creation."""
        from nest_protect_mcp.state_manager import AppState

        app_state = AppState()
        assert app_state.config is None
        assert app_state.access_token is None
        assert app_state.refresh_token is None

    def test_app_state_with_config(self):
        """Test AppState with configuration."""
        from nest_protect_mcp.state_manager import AppState

        config = {"test": "config"}
        app_state = AppState(config=config)
        assert app_state.config == config

    def test_initialize_app_state(self):
        """Test initialize_app_state function."""
        from nest_protect_mcp.state_manager import initialize_app_state, get_app_state, _app_state

        # Clear any existing state
        _app_state = None

        initialize_app_state({"test": "config"})
        app_state = get_app_state()

        assert app_state is not None
        assert app_state.config == {"test": "config"}

    def test_get_app_state_auto_init(self):
        """Test get_app_state auto-initialization."""
        from nest_protect_mcp.state_manager import get_app_state, _app_state

        # Clear any existing state
        _app_state = None

        app_state = get_app_state()
        assert app_state is not None
        assert app_state.config is None
