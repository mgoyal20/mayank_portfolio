
from typing import List, Dict, Callable, Tuple
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def tsp_order(stops: List[Dict], distance_fn: Callable, start: Dict) -> Tuple[List[Dict], float]:
    # Solve a simple TSP path starting from 'start' visiting all 'stops' once.
    if not stops:
        return [], 0.0

    nodes = [start] + stops
    n = len(nodes)

    def distance_callback(from_index, to_index):
        a = nodes[from_index]
        b = nodes[to_index]
        return int(distance_fn(a, b) * 1000)

    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)
    transit_cb_index = routing.RegisterTransitCallback(lambda i,j: distance_callback(manager.IndexToNode(i), manager.IndexToNode(j)))
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb_index)
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(search_params)

    if solution:
        index = routing.Start(0)
        order = []
        total_m = 0
        while not routing.IsEnd(index):
            nidx = manager.IndexToNode(index)
            index2 = solution.Value(routing.NextVar(index))
            nidx2 = manager.IndexToNode(index2)
            total_m += distance_callback(nidx, nidx2)
            if nidx != 0:
                order.append(nodes[nidx])
            index = index2
        return order, total_m / 1000.0
    else:
        return stops, 0.0
