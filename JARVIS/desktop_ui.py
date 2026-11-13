"""Standalone desktop host for the requested JARVIS Command Deck HTML."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView


def main() -> int:
    html = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (
        Path.home() / "Desktop/UI_Logic/jarvis-ui-logic/jarvis-ui.html"
    )
    bridge = sys.argv[2] if len(sys.argv) > 2 else "ws://127.0.0.1:8875"
    app = QApplication(sys.argv[:1])
    app.setApplicationName("JARVIS Command Deck")
    app.setApplicationDisplayName("JARVIS Command Deck")
    view = QWebEngineView()
    view.setWindowTitle("JARVIS Command Deck")
    view.resize(1440, 900)
    view.setUrl(QUrl.fromUserInput(f"file://{html}?demo=0&bridge={bridge}"))
    view.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
