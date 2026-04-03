"""
State management for monitoring system.
Stores current health status locally and optionally in DynamoDB.
"""

import json
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class BaseStateManager:
    """Abstract base for state storage."""

    def save_state(self, state: Dict[str, Any]) -> None:
        """Save monitoring state."""
        raise NotImplementedError

    def load_state(self) -> Dict[str, Any]:
        """Load monitoring state."""
        raise NotImplementedError

    def get_last_update_time(self) -> Optional[datetime]:
        """Get timestamp of last state update."""
        raise NotImplementedError


class FileStateManager(BaseStateManager):
    """File-based state storage (default, simple option)."""

    def __init__(self, file_path: str = '/tmp/monitoring-state.json'):
        """
        Initialize file-based state manager.

        Args:
            file_path: Path to JSON state file
        """
        self.file_path = Path(file_path)
        self._lock = threading.Lock()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save_state(self, state: Dict[str, Any]) -> None:
        """Save state to JSON file."""
        with self._lock:
            data = {
                'timestamp': datetime.utcnow().isoformat(),
                'state': state
            }
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)

    def load_state(self) -> Dict[str, Any]:
        """Load state from JSON file."""
        with self._lock:
            if self.file_path.exists():
                try:
                    with open(self.file_path, 'r') as f:
                        data = json.load(f)
                        return data.get('state', {})
                except (json.JSONDecodeError, IOError):
                    return {}
            return {}

    def get_last_update_time(self) -> Optional[datetime]:
        """Get last update timestamp."""
        with self._lock:
            if self.file_path.exists():
                try:
                    with open(self.file_path, 'r') as f:
                        data = json.load(f)
                        timestamp_str = data.get('timestamp')
                        if timestamp_str:
                            return datetime.fromisoformat(timestamp_str)
                except (json.JSONDecodeError, IOError, ValueError):
                    return None
            return None


class InMemoryStateManager(BaseStateManager):
    """In-memory state storage (for testing)."""

    def __init__(self):
        """Initialize in-memory state manager."""
        self._state = {}
        self._last_update = None
        self._lock = threading.Lock()

    def save_state(self, state: Dict[str, Any]) -> None:
        """Save state to memory."""
        with self._lock:
            self._state = state
            self._last_update = datetime.utcnow()

    def load_state(self) -> Dict[str, Any]:
        """Load state from memory."""
        with self._lock:
            return self._state.copy()

    def get_last_update_time(self) -> Optional[datetime]:
        """Get last update timestamp."""
        with self._lock:
            return self._last_update
