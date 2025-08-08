
from typing import List, Dict, Tuple, Callable

def nearest_neighbor_order(home: Dict, stops: List[Dict], distance_fn: Callable) -> Tuple[List[Dict], float]:
    if not stops:
        return [], 0.0
    unvisited = stops[:]
    current = home
    route = []
    total = 0.0

    while unvisited:
        nxt = min(unvisited, key=lambda s: distance_fn(current, s))
        total += distance_fn(current, nxt)
        route.append(nxt)
        current = nxt
        unvisited.remove(nxt)
    # return to home not counted (walking trips often don't end at hotel in demo)
    return route, total
