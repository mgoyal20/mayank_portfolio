import os, time, requests, json, hashlib
from typing import List, Dict
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parents[1] / "data"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY") or os.environ.get("GOOGLE_MAPS_API_KEY")

INTEREST_TO_QUERY = {
    "landmarks": {"keyword": "landmark OR sightseeing OR historic site"},
    "museums": {"type": "museum"},
    "nature": {"keyword": "park OR garden OR nature"},
    "food": {"type": "restaurant"},
    "views": {"keyword": "observation deck OR viewpoint OR skyline"},
    "nightlife": {"type": "bar"}
}

def _cache_path(kind: str, city: str, interests: list, limit: int) -> Path:
    key = json.dumps({"kind":kind,"city":city,"interests":interests,"limit":limit}, sort_keys=True)
    h = hashlib.sha256(key.encode()).hexdigest()[:16]
    return CACHE_DIR / f"places_{h}.json"

def get_live_pois(city: str, interests: list, limit: int = 25) -> List[Dict]:
    if not API_KEY:
        return []

    cache_file = _cache_path("textsearch", city, interests, limit)
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text())
        except Exception:
            pass

    results: List[Dict] = []
    interests = interests or list(INTEREST_TO_QUERY.keys())
    for interest in interests:
        params = {"query": f"best {interest} in {city}", "key": API_KEY}
        params.update(INTEREST_TO_QUERY.get(interest, {}))
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            continue
        data = r.json()
        for item in data.get("results", []):
            poi = {
                "name": item.get("name"),
                "lat": item.get("geometry",{}).get("location",{}).get("lat"),
                "lng": item.get("geometry",{}).get("location",{}).get("lng"),
                "category": interest,
                "rating": item.get("rating", 0),
                "price_level": item.get("price_level"),
                "place_id": item.get("place_id"),
                "address": item.get("formatted_address"),
                "open_now": item.get("opening_hours",{}).get("open_now") if item.get("opening_hours") else None
            }
            if poi["name"] and poi["lat"] and poi["lng"]:
                results.append(poi)
        time.sleep(0.2)

    # dedupe
    dedup = {}
    for r in results:
        k = r.get("place_id") or r["name"]
        if k not in dedup:
            dedup[k] = r
    results = list(dedup.values())[:limit]

    try:
        cache_file.write_text(json.dumps(results))
    except Exception:
        pass
    return results
