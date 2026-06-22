"""The Malaysian road/charging network and sample-data factories."""
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Station:
    power_kw: float      # rated charger power (kW)
    queue_min: float     # expected queue wait (minutes)
    tariff: float        # charging tariff (RM per minute)


class Network:
    """A directed graph of nodes (cities/hubs) with charging stations on some."""

    def __init__(self, edges, stations):
        # edges:    {node: {neighbour: (distance_km, traffic_factor)}}
        # stations: {node: Station}
        self.edges = edges
        self.stations = stations

    def neighbors(self, node):
        return self.edges.get(node, {})

    def is_station(self, node):
        return node in self.stations

    def station(self, node):
        return self.stations[node]

    def nodes(self):
        return list(self.edges.keys())

    def topological_order(self):
        """Kahn-style topological sort (the corridor graph is a DAG)."""
        indeg = defaultdict(int)
        for u in self.edges:
            for v in self.edges[u]:
                indeg[v] += 1
        queue = [n for n in self.edges if indeg[n] == 0]
        order = []
        while queue:
            n = queue.pop()
            order.append(n)
            for v in self.edges.get(n, {}):
                indeg[v] -= 1
                if indeg[v] == 0:
                    queue.append(v)
        return order


def build_sample_network() -> Network:
    """Festive 'balik kampung' peak: heavy traffic factors and long queues.

        JB -> Melaka -> Seremban -> KL --(Tapah)--> Penang
                                       \\          /
                                        `-> Ipoh -'
    Two ways from KL to Penang make ROUTE choice (not just charging) matter.
    """
    edges = {
        "JB":       {"Melaka": (215, 1.25)},
        "Melaka":   {"Seremban": (90, 1.15)},
        "Seremban": {"KL": (65, 1.30)},
        "KL":       {"Tapah": (150, 1.10), "Ipoh": (205, 1.05)},
        "Tapah":    {"Penang": (190, 1.10), "Ipoh": (60, 1.05)},
        "Ipoh":     {"Penang": (160, 1.05)},
        "Penang":   {},
    }
    stations = {
        "Melaka":   Station(90,  20, 2.20),   # Ayer Keroh, 2 nozzles
        "Seremban": Station(60,  10, 2.05),
        "KL":       Station(120, 25, 2.35),   # powerful but busy
        "Tapah":    Station(100, 45, 2.35),   # fast charger, LONG festive queue
        "Ipoh":     Station(60,  15, 2.10),
    }
    return Network(edges, stations)


def off_peak(network: Network) -> Network:
    """Return a light-traffic, short-queue copy of a network (a normal day)."""
    import copy
    edges = {u: {v: (d, 1.02) for v, (d, _f) in nbrs.items()}
             for u, nbrs in network.edges.items()}
    stations = {n: Station(s.power_kw, 5, s.tariff) for n, s in network.stations.items()}
    return Network(edges, stations)
