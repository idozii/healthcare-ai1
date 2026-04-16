from functools import lru_cache
from urllib.parse import quote
from urllib.request import Request, urlopen
import json


KNOWN_LOCATIONS = {
    "sydney": (-33.8688, 151.2093),
    "sydney cbd": (-33.8688, 151.2093),
    "melbourne": (-37.8136, 144.9631),
    "brisbane": (-27.4698, 153.0251),
    "perth": (-31.9523, 115.8613),
    "ho chi minh city": (10.8231, 106.6297),
    "hcm": (10.8231, 106.6297),
    "hanoi": (21.0278, 105.8342),
    "da nang": (16.0544, 108.2022),
    "singapore": (1.3521, 103.8198),
    "north kansas": (39.0997, -94.5786),
    "kansas": (39.0997, -94.5786),
    "kansas city": (39.0997, -94.5786),
    "topeka": (39.0473, -95.6752),
    "junction city": (39.0286, -96.8314),
    "emporia": (38.4039, -96.1817),
    "new york": (40.7128, -74.0060),
    "nyc": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437),
    "la": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298),
    "houston": (29.7604, -95.3698),
    "phoenix": (33.4484, -112.0740),
}


def _try_parse_lat_lon(value: str):
    parts = [x.strip() for x in value.split(",")]
    if len(parts) != 2:
        return None
    try:
        lat = float(parts[0])
        lon = float(parts[1])
    except ValueError:
        return None

    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None


@lru_cache(maxsize=256)
def _geocode_cached(raw: str, timeout: float):
    key = raw.lower()

    parsed = _try_parse_lat_lon(raw)
    if parsed is not None:
        return {
            "lat": parsed[0],
            "lon": parsed[1],
            "source": "parsed",
            "query": raw,
        }

    if key in KNOWN_LOCATIONS:
        lat, lon = KNOWN_LOCATIONS[key]
        note = None
        if key in {"kansas"}:
            note = "State-level input is ambiguous; using Kansas City metro as an approximate center. Use city or ZIP for better distance accuracy."
        return {
            "lat": lat,
            "lon": lon,
            "source": "known_map",
            "query": raw,
            "note": note,
        }

    # Best-effort online fallback (OpenStreetMap Nominatim)
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={quote(raw)}&format=json&limit=1"
        req = Request(url, headers={"User-Agent": "healthcare-ai/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        if payload:
            lat = float(payload[0]["lat"])
            lon = float(payload[0]["lon"])
            return {
                "lat": lat,
                "lon": lon,
                "source": "nominatim",
                "query": raw,
            }
    except Exception:
        return None

    return None


def geocode_location(location_text: str, timeout: float = 3.0):
    if not location_text or not location_text.strip():
        return None

    raw = location_text.strip()
    # Normalize timeout precision to improve cache hit-rate.
    timeout_key = round(float(timeout), 1)
    result = _geocode_cached(raw, timeout_key)
    return dict(result) if result is not None else None
