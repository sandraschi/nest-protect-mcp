"""State management for Nest Protect MCP."""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, TypeVar, Generic, Callable, Awaitable
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class StateManager:
    """Thread-safe state manager with persistence."""
    _instance = None
    _state: Dict[str, Any] = {}
    _state_file: Path = Path("data/state.json")
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance._state = {}
            cls._instance._state_file.parent.mkdir(parents=True, exist_ok=True)
        return cls._instance
    
    async def initialize(self) -> None:
        """Initialize the state manager and load state from disk."""
        await self._load_state()
    
    async def _load_state(self) -> None:
        """Load state from file if it exists."""
        if not self._state_file.exists():
            self._state = {}
            return
            
        try:
            async with self._lock:
                with open(self._state_file, 'r') as f:
                    self._state = json.load(f)
            logger.info(f"Loaded state from {self._state_file}")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            self._state = {}
    
    async def _save_state(self) -> None:
        """Save current state to file."""
        try:
            async with self._lock:
                with open(self._state_file, 'w') as f:
                    json.dump(self._state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    async def get(self, key: str, default: T = None) -> T:
        """Get a value from the state."""
        async with self._lock:
            return self._state.get(key, default)
    
    async def set(self, key: str, value: Any, persist: bool = True) -> None:
        """Set a value in the state."""
        async with self._lock:
            self._state[key] = value
        if persist:
            await self._save_state()
    
    async def update(self, key: str, updater: Callable[[Any], Any], default: Any = None, persist: bool = True) -> Any:
        """Update a value using a function."""
        async with self._lock:
            current = self._state.get(key, default)
            updated = updater(current)
            self._state[key] = updated
            
        if persist:
            await self._save_state()
        return updated
    
    async def delete(self, key: str) -> None:
        """Delete a key from the state."""
        async with self._lock:
            if key in self._state:
                del self._state[key]
        await self._save_state()
    
    async def clear(self) -> None:
        """Clear all state."""
        async with self._lock:
            self._state.clear()
        await self._save_state()
    
    async def get_all(self) -> Dict[str, Any]:
        """Get all state."""
        async with self._lock:
            return self._state.copy()

# Global instance
state_manager = StateManager()

# FastAPI integration
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    logger.info("Initializing state manager...")
    await state_manager.initialize()
    
    # Store state manager in app state
    app.state.state_manager = state_manager
    
    try:
        yield
    finally:
        logger.info("Saving state before shutdown...")
        await state_manager._save_state()

def setup_state(app: FastAPI) -> None:
    """Set up state management for FastAPI app."""
    app.state.state_manager = state_manager
