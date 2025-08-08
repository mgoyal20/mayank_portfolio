cat > projects/ai-travel-planner/routing/matrix.py << 'PY'
import os, math, json, hashlib, requests, time
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parents[1] / "data"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

GMAPS_KEY = os.environ.get("GOOGLE_PLACES_API_KEY") or os.environ.get("GOOGLE_MAPS_API_KEY")

def haversine_km(a, b) -> float:
    if isinstance(a, dict):
        lat1, lon1 = a["lat"], a["lng"]
    else:
        lat1, lon1 = a
    if isinstance(b, dict):
        lat2, lon2 = b["lat"], b["lng"]
    else:
        lat2, lon2 = b
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    h = (math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2)
    return 2 * R * math.asin(math.sqrt(h))

def _cache_key(orig, dest, mode):
    key = json.dumps({"o":orig, "d":dest, "m":mode}, sort_keys=True)
    return hashlib.sha256(key.encode()).hexdigest()[:16]

def _cache_file():
    return CACHE_DIR / "distance_cache.json"

def _load_cache():
    p = _cache_file()
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}
    return {}

def _save_cache(cache):
    try:
        _cache_file().write_text(json.dumps(cache))
    except Exception:
        pass

def distance_km(a, b, mode="walking") -> float:
    # Use Google Distance Matrix if key present, else haversine fallback
    if not GMAPS_KEY:
        return haversine_km(a, b)

    cache = _load_cache()
    ck = _cache_key(a, b, mode)
    if ck in cache:
        return cache[ck]

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{a['lat']},{a['lng']}",
        "destinations": f"{b['lat']},{b['lng']}",
        "mode": mode,
        "key": GMAPS_KEY
    }
    r = requests.get(url, params=params, timeout=15)
    if r.status_code != 200:
        return haversine_km(a, b)
    data = r.json()
    try:
        meters = data["rows"][0]["elements"][0]["distance"]["value"]
        km = meters / 1000.0
    except Exception:
        km = haversine_km(a, b)

    cache[ck] = km
    _save_cache(cache)
    time.sleep(0.05)
    return km
PY
