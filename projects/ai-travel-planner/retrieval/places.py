
from typing import List, Dict

# Minimal curated samples for a few cities to run key-free
SAMPLES = {
    "Las Vegas": [
        {"name":"Bellagio Fountains","lat":36.1126,"lng":-115.1767,"category":"landmarks","rating":4.7,"note":"Iconic water show"},
        {"name":"The LINQ High Roller","lat":36.1186,"lng":-115.1716,"category":"views","rating":4.6,"note":"Observation wheel"},
        {"name":"Gordon Ramsay Burger","lat":36.1025,"lng":-115.1731,"category":"food","rating":4.5,"note":"Popular burger spot"},
        {"name":"The Venetian Canals","lat":36.1216,"lng":-115.1707,"category":"landmarks","rating":4.6,"note":"Indoor gondolas"},
        {"name":"Red Rock Canyon Visitor Center","lat":36.1350,"lng":-115.4270,"category":"nature","rating":4.8,"note":"Scenic desert park"},
        {"name":"Welcome to Fabulous Las Vegas Sign","lat":36.0820,"lng":-115.1722,"category":"landmarks","rating":4.6,"note":"Photo stop"},
    ],
    "New York": [
        {"name":"Central Park","lat":40.7851,"lng":-73.9683,"category":"nature","rating":4.8,"note":"Strolls and views"},
        {"name":"Metropolitan Museum of Art","lat":40.7794,"lng":-73.9632,"category":"museums","rating":4.8,"note":"World-class art"},
        {"name":"Times Square","lat":40.7580,"lng":-73.9855,"category":"landmarks","rating":4.5,"note":"Bright and busy"},
        {"name":"Brooklyn Bridge","lat":40.7061,"lng":-73.9969,"category":"landmarks","rating":4.7,"note":"Great skyline views"},
        {"name":"Katz's Delicatessen","lat":40.7222,"lng":-73.9874,"category":"food","rating":4.5,"note":"Classic pastrami"}
    ],
    "Tokyo": [
        {"name":"Senso-ji Temple","lat":35.7148,"lng":139.7967,"category":"landmarks","rating":4.7,"note":"Historic temple"},
        {"name":"Shibuya Crossing","lat":35.6595,"lng":139.7005,"category":"landmarks","rating":4.6,"note":"Iconic scramble"},
        {"name":"Meiji Jingu","lat":35.6764,"lng":139.6993,"category":"museums","rating":4.7,"note":"Shrine & forest"},
        {"name":"Tokyo Skytree","lat":35.7100,"lng":139.8107,"category":"views","rating":4.7,"note":"Observation tower"},
        {"name":"Ichiran Ramen","lat":35.6628,"lng":139.7036,"category":"food","rating":4.5,"note":"Solo ramen booths"}
    ],
    "Chicago": [
        {"name":"Millennium Park","lat":41.8826,"lng":-87.6226,"category":"landmarks","rating":4.7,"note":"The Bean"},
        {"name":"Art Institute of Chicago","lat":41.8796,"lng":-87.6237,"category":"museums","rating":4.8,"note":"Huge collection"},
        {"name":"Willis Tower Skydeck","lat":41.8789,"lng":-87.6359,"category":"views","rating":4.6,"note":"Glass ledge"},
        {"name":"Lou Malnati's Pizzeria","lat":41.8925,"lng":-87.6261,"category":"food","rating":4.5,"note":"Deep-dish staple"}
    ],
    "San Francisco": [
        {"name":"Golden Gate Bridge","lat":37.8199,"lng":-122.4783,"category":"landmarks","rating":4.8,"note":"Iconic span"},
        {"name":"Alcatraz Island","lat":37.8267,"lng":-122.4230,"category":"museums","rating":4.7,"note":"Former prison tour"},
        {"name":"Ferry Building Marketplace","lat":37.7955,"lng":-122.3937,"category":"food","rating":4.5,"note":"Great eats"},
        {"name":"Twin Peaks","lat":37.7544,"lng":-122.4477,"category":"views","rating":4.7,"note":"City panorama"}
    ]
}

def get_sample_pois(city: str, interests: list) -> List[Dict]:
    items = SAMPLES.get(city, [])
    if not interests: 
        return items[:6]
    interests_set = set(interests)
    filtered = [p for p in items if p["category"] in interests_set]
    # if user filters too hard, backfill with any items
    if len(filtered) < 3:
        extras = [p for p in items if p not in filtered]
        filtered.extend(extras[: (6 - len(filtered)) ])
    # cap length
    return filtered[:8]
