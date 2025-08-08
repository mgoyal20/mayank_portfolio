
import math

def haversine_km(a, b) -> float:
    # a, b can be dicts with lat/lng or tuple(lat, lng)
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
