"""Shared pytest fixtures for Bluetooth Web UI tests."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from typing import TYPE_CHECKING

from bt_web_ui.models.device import AdapterState
from bt_web_ui.services.device_store import DeviceStore
from bt_web_ui.services.event_bus import EventBus

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@pytest_asyncio.fixture
async def device_store(tmp_path: Path) -> AsyncIterator[DeviceStore]:
    """Provide an in-memory SQLite device store for testing."""
    store = DeviceStore(tmp_path / "test.db")
    await store.init_db()
    yield store
    await store.close()


@pytest.fixture
def event_bus() -> EventBus:
    """Provide a fresh event bus for testing."""
    return EventBus()


@pytest.fixture
def mock_bluetooth_manager() -> MagicMock:
    """Provide a mock BlueZ manager for testing.

    Returns a MagicMock that simulates BlueZManager behavior.
    All D-Bus calls return reasonable defaults.
    """
    manager = MagicMock()
    manager.get_adapter_state = AsyncMock(
        return_value=AdapterState(
            address="AA:BB:CC:DD:EE:FF",
            name="hci0",
            powered=True,
            discovering=False,
            discoverable=False,
        )
    )
    manager.start_discovery = AsyncMock()
    manager.stop_discovery = AsyncMock()
    manager.pair_device = AsyncMock()
    manager.connect_device = AsyncMock()
    manager.disconnect_device = AsyncMock()
    manager.trust_device = AsyncMock()
    manager.untrust_device = AsyncMock()
    manager.remove_device = AsyncMock()
    manager.get_device_state = AsyncMock(
        return_value={
            "name": "Test Device",
            "alias": None,
            "paired": False,
            "connected": False,
            "trusted": False,
            "rssi": None,
            "icon": None,
            "device_type": None,
        }
    )
    manager.get_all_device_states = AsyncMock(return_value={})
    manager.is_scanning = False
    return manager


@pytest_asyncio.fixture
async def test_client(
    device_store: DeviceStore,
    event_bus: EventBus,
    mock_bluetooth_manager: MagicMock,
) -> AsyncIterator[AsyncClient]:
    """Provide an async HTTP test client with mocked dependencies."""
    # Import main first to avoid circular import (main.create_app imports adapter.router)
    from bt_web_ui.api.adapter import get_bluetooth_manager
    from bt_web_ui.main import (
        create_app,
        get_device_store,
        get_event_bus,
    )

    app = create_app()

    # Override dependencies
    app.dependency_overrides[get_device_store] = lambda: device_store
    app.dependency_overrides[get_event_bus] = lambda: event_bus
    app.dependency_overrides[get_bluetooth_manager] = lambda: mock_bluetooth_manager

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
