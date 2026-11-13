# connectivity.py
#
# Lightweight online/offline check used to decide whether to even attempt
# the cloud providers (Gemini, Groq, OpenRouter) or skip straight to the
# local Ollama model. Avoids burning several seconds of timeouts per
# provider when there's genuinely no network -- checked once and cached
# briefly rather than on every single call.

import socket
import time

_last_check_time = 0.0
_last_check_result = True
_CACHE_SECONDS = 5  # re-check at most every 5s so a connection that drops
                     # mid-session is noticed reasonably quickly


def is_online(force: bool = False) -> bool:
    global _last_check_time, _last_check_result

    now = time.time()
    if not force and (now - _last_check_time) < _CACHE_SECONDS:
        return _last_check_result

    # A DNS-level connect to a well-known, extremely reliable host/port is
    # cheap and fast (typically <100ms when online, fails fast when not) --
    # far cheaper than waiting out an HTTP request timeout against Gemini/
    # Groq/OpenRouter one by one.
    hosts = [("8.8.8.8", 53), ("1.1.1.1", 53)]
    online = False
    for host, port in hosts:
        try:
            socket.setdefaulttimeout(1.5)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.close()
            online = True
            break
        except Exception:
            continue

    _last_check_time = now
    _last_check_result = online
    return online


if __name__ == "__main__":
    print("Online:", is_online(force=True))
