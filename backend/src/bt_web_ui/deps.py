"""Shared FastAPI dependency providers.

This module breaks the circular dependency between main.py and API routers.
The singletons are set by main.py lifespan and accessed by API modules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

    from bt_web_ui.services.device_store import DeviceStore
    from bt_web_ui.services.event_bus import EventBus

_device_store: DeviceStore | None = None
_event_bus: EventBus | None = None
_templates: Jinja2Templates | None = None


def get_device_store() -> DeviceStore:
    """Dependency: return the global DeviceStore instance."""
    assert _device_store is not None
    return _device_store


def set_device_store(store: DeviceStore) -> None:
    """Set the global DeviceStore instance (called by lifespan)."""
    global _device_store
    _device_store = store


def get_event_bus() -> EventBus:
    """Dependency: return the global EventBus instance."""
    assert _event_bus is not None
    return _event_bus


def set_event_bus(bus: EventBus) -> None:
    """Set the global EventBus instance (called by lifespan)."""
    global _event_bus
    _event_bus = bus


def get_templates() -> Jinja2Templates:
    """Dependency: return the Jinja2Templates instance."""
    assert _templates is not None
    return _templates


def set_templates(templates: Jinja2Templates) -> None:
    """Set the Jinja2Templates instance (called by lifespan)."""
    global _templates
    _templates = templates
