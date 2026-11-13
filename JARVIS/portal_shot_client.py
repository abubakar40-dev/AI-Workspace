#!/usr/bin/env python3
"""XDG Screenshot portal client -- one request, one JSON line on stdout.

Invoked by ``screen_capture`` with a Python that has PyGObject (the project
venv does not, the system ``python3`` does):

    python3 portal_shot_client.py [--interactive] [--timeout SECONDS]

Why a subprocess: the portal answers with the ``Response`` signal of the
request object it hands back, which needs a GLib main loop. Keeping that
in a short-lived child process means the main app never blocks on D-Bus
and a hung portal can always be killed.

Output: exactly one JSON object on stdout
    {"ok": bool, "code": int|None, "uri": str|None, "error": str|None}
Diagnostics go to stderr so stdout stays parseable.

Portal response codes: 0 = success, 1 = cancelled, 2 = failed/denied.
"""

from __future__ import annotations

import json
import sys

DEFAULT_TIMEOUT = 20.0


def _result(ok=False, code=None, uri=None, error=None) -> None:
    print(json.dumps({"ok": ok, "code": code, "uri": uri, "error": error}))


def main(argv: list[str]) -> int:
    interactive = "--interactive" in argv
    timeout = DEFAULT_TIMEOUT
    if "--timeout" in argv:
        try:
            timeout = float(argv[argv.index("--timeout") + 1])
        except (ValueError, IndexError):
            timeout = DEFAULT_TIMEOUT

    try:
        import gi
        gi.require_version("Gio", "2.0")
        from gi.repository import Gio, GLib
    except Exception as exc:  # no PyGObject in this interpreter
        _result(error=f"PyGObject unavailable: {exc}")
        return 2

    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        proxy = Gio.DBusProxy.new_sync(
            bus, Gio.DBusProxyFlags.NONE, None,
            "org.freedesktop.portal.Desktop",
            "/org/freedesktop/portal/desktop",
            "org.freedesktop.portal.Screenshot",
            None,
        )
        options = GLib.Variant(
            "(sa{sv})", ("", {"interactive": GLib.Variant("b", interactive)})
        )
        handle, = proxy.call_sync(
            "Screenshot", options, Gio.DBusCallFlags.NONE, 30000, None
        )
    except Exception as exc:
        _result(error=f"portal Screenshot call failed: {exc}")
        return 3

    state = {"done": False}
    loop = GLib.MainLoop()

    def on_response(*args):
        # PyGObject delivers g-signal as (proxy, sender, signal, params).
        if len(args) < 2:
            return
        signal, params = args[-2], args[-1]
        if signal != "Response" or state["done"]:
            return
        try:
            code, details = params.unpack()
        except Exception:
            code, details = 2, {}
        uri = details.get("uri")
        state["done"] = True
        if code == 0 and uri:
            _result(ok=True, code=code, uri=uri)
        else:
            reason = (details.get("error") or details.get("message")
                      or f"portal response code {code}")
            _result(code=code, error=str(reason))
        loop.quit()

    try:
        request = Gio.DBusProxy.new_sync(
            bus, Gio.DBusProxyFlags.NONE, None,
            "org.freedesktop.portal.Desktop",
            handle,
            "org.freedesktop.portal.Request",
            None,
        )
        request.connect("g-signal", on_response)
    except Exception as exc:
        _result(error=f"could not watch portal response: {exc}")
        return 4

    # Safety net: never hang the caller for longer than asked.
    GLib.timeout_add(int(max(1.0, timeout) * 1000),
                     lambda: (loop.quit(), False)[1])
    loop.run()

    if not state["done"]:
        _result(code=None,
                error=("portal did not answer in time (the capture UI may "
                       "still be waiting for a click)" if interactive
                       else "portal timed out"))
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
