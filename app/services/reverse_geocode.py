"""Reverse geocoding via OpenStreetMap Nominatim (usage policy: ≤1 req/s, valid User-Agent)."""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request

# https://operations.osmfoundation.org/policies/nominatim/
_USER_AGENT = "Fruger/1.0 (local ride demo; reverse geocode)"
_MIN_INTERVAL_S = 1.1

_cache: dict[str, str | None] = {}
_lock = threading.Lock()
_last_request_mono = 0.0


def coord_key(lat: float, lng: float) -> str:
    return f"{round(float(lat), 5)},{round(float(lng), 5)}"


def nominatim_reverse_display_name(lat: float, lng: float, *, timeout: float = 10.0) -> str | None:
    """Return Nominatim ``display_name`` or ``None`` on failure / empty result."""
    key = coord_key(lat, lng)
    with _lock:
        if key in _cache:
            return _cache[key]
        global _last_request_mono
        now = time.monotonic()
        wait = _MIN_INTERVAL_S - (now - _last_request_mono)
        if wait > 0:
            time.sleep(wait)
        url = (
            "https://nominatim.openstreetmap.org/reverse?"
            f"format=jsonv2&lat={float(lat)}&lon={float(lng)}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        label: str | None = None
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.load(resp)
            dn = data.get("display_name")
            if isinstance(dn, str) and dn.strip():
                label = dn.strip()
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
            label = None
        _cache[key] = label
        _last_request_mono = time.monotonic()
        return label


def batch_reverse_labels(points: list[tuple[float, float]]) -> dict[str, str | None]:
    """Resolve unique coordinate keys in order; each Nominatim miss is stored as ``None``."""
    out: dict[str, str | None] = {}
    seen: set[str] = set()
    for lat, lng in points:
        key = coord_key(lat, lng)
        if key in seen:
            continue
        seen.add(key)
        out[key] = nominatim_reverse_display_name(lat, lng)
    return out
