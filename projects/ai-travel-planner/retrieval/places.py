from typing import List, Dict

SAMPLES = {
    "Las Vegas": [
        {"name":"Bellagio Fountains","lat":36.1126,"lng":-115.1767,"category":"landmarks","rating":4.7,"note":"Water show"},
        {"name":"The LINQ High Roller","lat":36.1186,"lng":-115.1716,"category":"views","rating":4.6,"note":"Observation wheel"},
        {"name":"Gordon Ramsay Burger","lat":36.1025,"lng":-115.1731,"category":"food","rating":4.5,"note":"Burger spot"},
        {"name":"The Venetian Canals","lat":36.1216,"lng":-115.1707,"category":"landmarks","rating":4.6,"note":"Gondolas"},
        {"name":"Red Rock Canyon","lat":36.1350,"lng":-115.4270,"category":"nature","rating":4.8,"note":"Desert park"},
        {"name":"Welcome to LV Sign","lat":36.0820,"lng":-115.1722,"category":"landmarks","rating":4.6,"note":"Photo stop"}
    ],
    "New York": [
        {"name":"Central Park","lat":40.7851,"lng":-73.9683,"category":"nature","rating":4.8},
        {"name":"Met Museum","lat":40.7794,"lng":-73.9632,"category":"museums","rating":4.8},
        {"name":"Times Square","lat":40.7580,"lng":-73.9855,"category":"landmarks","rating":4.5},
        {"name":"Brooklyn Bridge","lat":40.7061,"lng":-73.9969,"category":"landmarks","rating":4.7},
        {"name":"Katz's Deli","lat":40.7222,"lng":-73.9874,"category":"food","rating":4.5}
    ],
    "Tokyo": [
        {"name":"Senso-ji Temple","lat":35.7148,"lng":139.7967,"category":"landmarks","rating":4.7},
        {"name":"Shibuya Crossing","lat":35.6595,"lng":139.7005,"category":"landmarks","rating":4.6},
        {"name":"Meiji Jingu","lat":35.6764,"lng":139.6993,"category":"museums","rating":4.7},
        {"name":"Tokyo Skytree","lat":35.7100,"lng":139.8107,"category":"views","rating":4.7},
        {"name":"Ichiran Ramen","lat":35.6628,"lng":139.7036,"category":"food","rating":4.5}
    ],
    "Chicago": [
        {"name":"Millennium Park","lat":41.8826,"lng":-87.6226,"category":"landmarks","rating":4.7},
        {"name":"Art Institute","lat":41.8796,"lng":-87.6237,"category":"museums","rating":4.8},
        {"name":"Skydeck","lat":41.8789,"lng":-87.6359,"category":"views","rating":4.6},
        {"name":"Lou Malnati's","lat":41.8925,"lng":-87.6261,"category":"food","rating":4.5}
    ],
    "San Francisco": [
        {"name":"Golden Gate Bridge","lat":37.8199,"lng":-122.4783,"category":"landmarks","rating":4.8},
        {"name":"Alcatraz Island","lat":37.8267,"lng":-122.4230,"category":"museums","rating":4.7},
        {"name":"Ferry Building","lat":37.7955,"lng":-122.3937,"category":"food","rating":4.5},
        {"name":"Twin Peaks","lat":37.7544,"lng":-122.4477,"category":"views","rating":4.7}
    ]
}

def get_sample_pois(city: str, interests: list) -> List[Dict]:
    items = SAMPLES.get(city, [])
    if not interests:
        return items[:6]
    wanted = set(interests)
    filtered = [p for p in items if p["category"] in wanted]
    if len(filtered) < 3:
        extras = [p for p in items if p not in filtered]
        filtered.extend(extras[: (6 - len(filtered)) ])
    return filtered[:8]
PY
