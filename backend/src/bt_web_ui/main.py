"""FastAPI application entry point for Bluetooth Web UI."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from bt_web_ui.api import BluetoothError
from bt_web_ui.config import get_settings
from bt_web_ui.deps import (
    get_device_store,
    get_event_bus,
    get_templates,
    set_device_store,
    set_event_bus,
    set_templates,
)
from bt_web_ui.services.device_store import DeviceStore
from bt_web_ui.services.event_bus import EventBus

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)

# Re-export for backward compatibility with tests
__all__ = ["app", "create_app", "get_device_store", "get_event_bus", "get_templates"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle."""
    settings = get_settings()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Initialize device store
    store = DeviceStore(settings.db_path)
    await store.init_db()
    set_device_store(store)

    # Initialize event bus
    bus = EventBus()
    set_event_bus(bus)

    # Initialize templates
    template_dir = Path(__file__).parent / "templates"
    set_templates(Jinja2Templates(directory=str(template_dir)))

    # Initialize BlueZ manager
    from bt_web_ui.api.adapter import set_bluetooth_manager
    from bt_web_ui.services.bluetooth import BlueZManager

    adapter_name = settings.adapter or "hci0"
    bt_manager = BlueZManager(bus, adapter_name=adapter_name)
    try:
        await bt_manager.startup()
    except Exception:
        logger.warning(
            "BlueZManager failed to start - Bluetooth features will be unavailable",
            exc_info=True,
        )
    set_bluetooth_manager(bt_manager)

    logger.info(
        "Bluetooth Web UI started on %s:%d (db: %s)",
        settings.host,
        settings.port,
        settings.db_path,
    )

    yield

    # Shutdown
    await bt_manager.shutdown()
    await store.close()
    logger.info("Bluetooth Web UI shut down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Bluetooth Web UI",
        description="Web-based interface for managing Bluetooth device pairing and connections",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Mount static files
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Register error handler for BluetoothError
    @app.exception_handler(BluetoothError)
    async def bluetooth_error_handler(
        request: Request,
        exc: BluetoothError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_code, "message": exc.error_message},
        )

    # Register error handler for Pydantic validation errors (contract format)
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = exc.errors()
        messages = [
            f"{'.'.join(str(loc) for loc in e.get('loc', []))}: {e.get('msg', '')}" for e in errors
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "; ".join(messages),
            },
        )

    # Import and include routers (deferred to avoid circular imports)
    from bt_web_ui.api.adapter import router as adapter_router
    from bt_web_ui.api.devices import router as devices_router
    from bt_web_ui.api.settings import router as settings_router
    from bt_web_ui.api.websocket import router as websocket_router

    app.include_router(adapter_router)
    app.include_router(devices_router)
    app.include_router(websocket_router)
    app.include_router(settings_router)

    return app


app = create_app()
