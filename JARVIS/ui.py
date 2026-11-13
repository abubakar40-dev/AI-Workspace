"""
GUI entry point.

The interface is no longer built from Qt widgets. It is the operator's design
in ``assets/command_center/index.html``, shipped byte-for-byte and hosted in a
``QWebEngineView`` by :mod:`command_center`. The previous cockpit GUI --
``hud_widgets.py`` -- has been removed; ``hud_sensors.py`` stays because it is
the real telemetry source behind the gauges and the System row.

This module stays as the import path the rest of the app already uses
(``from ui import JarvisUI``) and re-exports the handful of helpers that were
part of the old public surface.
"""

from __future__ import annotations

from command_center import (          # noqa: F401  (re-exported on purpose)
    APP_VERSION,
    BASE_DIR,
    CommandCenter,
    JarvisUI,
    WEB_ENGINE_AVAILABLE,
    human_bytes,
)

#: The page the command center serves. Read-only by contract.
COMMAND_CENTER_HTML = BASE_DIR / "assets" / "command_center" / "index.html"

__all__ = [
    "APP_VERSION",
    "BASE_DIR",
    "COMMAND_CENTER_HTML",
    "CommandCenter",
    "JarvisUI",
    "WEB_ENGINE_AVAILABLE",
    "human_bytes",
]
