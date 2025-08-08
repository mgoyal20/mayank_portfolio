from typing import List, Dict, Callable, Tuple
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def tsp_order(stops: List[Dict], distance_fn: Callable, start: Dict) -> Tuple[List[Dict], float]:
    if not stops:
        return [], 0.0
    nodes = [start] + stops
    n = len(nodes)

    def distance_callback(from_index, to_index):
        a = nodes[from_index]
        b = nodes[to_index]
        return int(distance_fn(a, b) * 1000)  # meters

    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)
    cb = routing.RegisterTransitCallback(lambda i,j: distance_callback(manager.IndexToNode(i), manager.IndexToNode(j)))
    routing.SetArcCostEvaluatorOfAllVehicles(cb)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    sol = routing.SolveWithParameters(params)
    if not sol:
        return stops, 0.0

    index = routing.Start(0)
    order, total_m = [], 0
    while not routing.IsEnd(index):
        nidx = manager.IndexToNode(index)
        next_index = sol.Value(routing.NextVar(index))
        nidx2 = manager.IndexToNode(next_index)
        total_m += distance_callback(nidx, nidx2)
        if nidx != 0:
            order.append(nodes[nidx])
        index = next_index
    return order, total_m / 1000.0
