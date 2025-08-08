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

def _hash_key(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]

def _cache_read(name: str):
    p = CACHE_DIR / name
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return None
    return None

def _cache_write(name: str, data):
    try:
        (CACHE_DIR / name).write_text(json.dumps(data))
    except Exception:
        pass

def get_live_pois(city: str, interests: list, limit: int = 25) -> List[Dict]:
    if not API_KEY:
        return []
    key = _hash_key({"textsearch": True, "city": city, "interests": interests, "limit": limit})
    cache_name = f"places_{key}.json"
    cached = _cache_read(cache_name)
    if cached is not None:
        return cached

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

    # de-dupe by place_id or name
    dedup = {}
    for r_ in results:
        k = r_.get("place_id") or r_["name"]
        if k not in dedup:
            dedup[k] = r_
    results = list(dedup.values())[:limit]
    _cache_write(cache_name, results)
    return results

def get_place_details_bulk(place_ids: List[str]) -> Dict[str, Dict]:
    """
    Fetch Place Details (opening hours) for many IDs with simple caching.
    Returns mapping: place_id -> {"opening_hours": {...}} when available.
    """
    out: Dict[str, Dict] = {}
    if not API_KEY or not place_ids:
        return out

    for pid in place_ids:
        cache_name = f"details_{pid}.json"
        cached = _cache_read(cache_name)
        if cached is not None:
            out[pid] = cached
            continue

        url = "https://maps.googleapis.com/maps/api/place/details/json"
        # fields kept minimal to reduce cost/size
        params = {
            "place_id": pid,
            "fields": "opening_hours",  # can add 'name,formatted_address' if needed
            "key": API_KEY
        }
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json().get("result", {})
            to_store = {"opening_hours": data.get("opening_hours")}
            _cache_write(cache_name, to_store)
            out[pid] = to_store
        time.sleep(0.12)
    return out

def get_nearby_food(lat: float, lng: float, limit: int = 5) -> List[Dict]:
    if not API_KEY:
        return []
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 1200,
        "type": "restaurant",
        "key": API_KEY,
        "opennow": False
    }
    r = requests.get(url, params=params, timeout=15)
    if r.status_code != 200:
        return []
    data = r.json()
    out = []
    for it in data.get("results", []):
        out.append({
            "name": it.get("name"),
            "lat": it.get("geometry",{}).get("location",{}).get("lat"),
            "lng": it.get("geometry",{}).get("location",{}).get("lng"),
            "category": "food",
            "rating": it.get("rating", 0),
            "price_level": it.get("price_level"),
            "place_id": it.get("place_id"),
            "address": it.get("vicinity")
        })
    out = [x for x in out if x.get("lat") and x.get("lng")]
    out.sort(key=lambda x: x.get("rating", 0), reverse=True)
    return out[:limit]
