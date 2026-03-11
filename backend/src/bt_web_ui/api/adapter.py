"""Adapter and scan API endpoints."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates  # noqa: TC002

from bt_web_ui.api import AdapterUnavailableError
from bt_web_ui.deps import get_device_store, get_templates
from bt_web_ui.models.device import (
    AdapterState,
    PowerRequest,
    ScanResponse,
)
from bt_web_ui.services.bluetooth import BlueZManager  # noqa: TC001
from bt_web_ui.services.device_store import DeviceStore  # noqa: TC001

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level singleton set by main.py lifespan
_bluetooth_manager: BlueZManager | None = None


def get_bluetooth_manager() -> BlueZManager:
    """Dependency: return the global BlueZManager instance."""
    if _bluetooth_manager is None:
        raise AdapterUnavailableError("BlueZManager not initialized")
    return _bluetooth_manager


def set_bluetooth_manager(manager: BlueZManager) -> None:
    """Called from main.py lifespan to set the global BlueZManager instance."""
    global _bluetooth_manager
    _bluetooth_manager = manager


# --- JSON API endpoints ---


@router.get("/api/adapter", response_model=AdapterState)
async def get_adapter(
    bt: Annotated[BlueZManager, Depends(get_bluetooth_manager)],
) -> AdapterState:
    """Return the current Bluetooth adapter state."""
    state = await bt.get_adapter_state()
    logger.debug("Adapter state: powered=%s discovering=%s", state.powered, state.discovering)
    return state


@router.post("/api/adapter/power", response_model=AdapterState)
async def set_adapter_power(
    body: PowerRequest,
    bt: Annotated[BlueZManager, Depends(get_bluetooth_manager)],
) -> AdapterState:
    """Toggle adapter power on or off."""
    logger.info("Setting adapter power to %s", body.powered)
    return await bt.set_powered(body.powered)


@router.post("/api/scan/start", response_model=ScanResponse)
async def start_scan(
    bt: Annotated[BlueZManager, Depends(get_bluetooth_manager)],
    store: Annotated[DeviceStore, Depends(get_device_store)],
    duration: int = 10,
) -> ScanResponse:
    """Start Bluetooth discovery scan."""
    logger.info("Starting scan for %d seconds", duration)
    await bt.start_discovery(duration_seconds=duration)
    return ScanResponse(status="scanning", duration_seconds=duration)


@router.post("/api/scan/stop", response_model=ScanResponse)
async def stop_scan(
    bt: Annotated[BlueZManager, Depends(get_bluetooth_manager)],
) -> ScanResponse:
    """Stop Bluetooth discovery scan."""
    logger.info("Stopping scan")
    await bt.stop_discovery()
    return ScanResponse(status="stopped")


# --- HTML page endpoint ---


@router.get("/")
async def index_page(
    request: Request,
    bt: Annotated[BlueZManager, Depends(get_bluetooth_manager)],
    store: Annotated[DeviceStore, Depends(get_device_store)],
    templates: Annotated[Jinja2Templates, Depends(get_templates)],
) -> object:
    """Serve the main index page with adapter state and device summary."""
    try:
        adapter = await bt.get_adapter_state()
    except Exception:
        adapter = None

    devices = await store.get_all_devices()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "adapter": adapter,
            "device_count": len(devices),
            "is_scanning": bt.is_scanning,
        },
    )
