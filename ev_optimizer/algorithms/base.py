"""Abstract base class shared by all three solvers.

Every concrete solver inherits the SAME constructor (vehicle, network) and the
SAME public method `solve(start, dest, start_battery_pct) -> Result`, so they
are fully interchangeable.
"""
import heapq
from abc import ABC, abstractmethod
from collections import defaultdict

from ..result import Result


class BaseSolver(ABC):
    name = "Base"

    def __init__(self, vehicle, network):
        self.v = vehicle
        self.net = network

    @abstractmethod
    def solve(self, start, dest, start_battery_pct) -> Result:
        """Return the optimal/-ish path, charging stops and total elapsed time."""
        raise NotImplementedError

    # ---- shared helper: admissible A*/greedy heuristic ----
    def freeflow_hours(self, dest):
        """Lower-bound remaining driving time to `dest`, ignoring charging/queues.

        Computed by reverse Dijkstra on free-flow driving time. It never
        overestimates the true remaining time, so it is an admissible heuristic.
        """
        dist = {n: float("inf") for n in self.net.edges}
        dist[dest] = 0.0
        rev = defaultdict(list)
        for u, nbrs in self.net.edges.items():
            for v, (d, _f) in nbrs.items():
                rev[v].append((u, d))
        pq = [(0.0, dest)]
        while pq:
            cost, node = heapq.heappop(pq)
            if cost > dist[node]:
                continue
            for u, d in rev[node]:
                nc = cost + d / self.v.avg_speed_kmh
                if nc < dist[u]:
                    dist[u] = nc
                    heapq.heappush(pq, (nc, u))
        return dist

    # ---- shared feasibility gate: the single battery-safety invariant ----
    def is_safe(self, soc_after_charge_kwh, energy_leg_kwh):
        """A leg is admissible only if arrival SoC stays at/above the reserve.

        Because reserve_kwh >= 0, this also forbids the battery dropping below 0%.
        Every solver routes ALL of its transitions through this one gate.
        """
        return (soc_after_charge_kwh - energy_leg_kwh) >= self.v.reserve_kwh
