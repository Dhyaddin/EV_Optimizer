"""Algorithm 3 - Modified Dijkstra / A* on the state-augmented graph."""
import heapq
from collections import defaultdict

from .base import BaseSolver
from ..result import Result, ChargeStop


class AStarSolver(BaseSolver):
    name = "A* (state-augmented)"

    def solve(self, start, dest, start_battery_pct) -> Result:
        v, net = self.v, self.net
        h = self.freeflow_hours(dest)
        start_state = (start, v.quantise_down(start_battery_pct / 100.0 * v.battery_cap_kwh))

        g = defaultdict(lambda: float("inf"))
        g[start_state] = 0.0
        back, closed = {}, set()
        pq = [(h.get(start, 0.0), 0.0, start_state)]   # (f = g + heuristic, g, state)

        while pq:
            f, gcur, (node, lvl) = heapq.heappop(pq)
            if (node, lvl) in closed:
                continue
            if node == dest:                            # first pop of goal = optimal
                return self._reconstruct(back, (node, lvl))
            closed.add((node, lvl))

            # successor type A: CHARGE (stations only) -> higher SoC band
            if net.is_station(node) and node != dest:
                st = net.station(node)
                for tgt in self._levels_up(lvl):
                    add_time = st.queue_min / 60.0 + v.charge_time_hours(st.power_kw, lvl, tgt)
                    ns, ng = (node, tgt), gcur + add_time
                    if ng < g[ns]:
                        g[ns] = ng
                        back[ns] = ((node, lvl), tgt - lvl)
                        heapq.heappush(pq, (ng + h.get(node, 0.0), ng, ns))

            # successor type B: DRIVE -> next node, lower SoC
            for nxt, (d, fct) in net.neighbors(node).items():
                e = v.edge_energy(d, fct)
                if not self.is_safe(lvl, e):            # *** STRICT PRUNE ***
                    continue
                arrive_lvl = v.quantise_down(lvl - e)
                ns, ng = (nxt, arrive_lvl), gcur + v.edge_drive_hours(d, fct)
                if ng < g[ns]:
                    g[ns] = ng
                    back[ns] = ((node, lvl), 0.0)
                    heapq.heappush(pq, (ng + h.get(nxt, 0.0), ng, ns))

        return Result(self.name, False, [start], [], float("inf"), 0, 0, 0)

    def _levels_up(self, lvl):
        v = self.v
        n_steps = int((v.battery_cap_kwh - lvl) / v.soc_step_kwh)
        return [round(lvl + k * v.soc_step_kwh, 6) for k in range(1, n_steps + 1)]

    def _reconstruct(self, back, goal_state):
        v, net = self.v, self.net
        states, s = [], goal_state
        while s is not None:
            states.append(s)
            prev = back.get(s)
            s = prev[0] if prev else None
        states.reverse()

        path = []
        for st in states:                               # collapse charge self-loops
            if not path or path[-1] != st[0]:
                path.append(st[0])

        stops, drive_h, charge_h, queue_h = [], 0.0, 0.0, 0.0
        for i in range(1, len(states)):
            (node, lvl) = states[i]
            ((pnode, plvl), added) = back[(node, lvl)]
            if node == pnode and added > 1e-9:          # charging transition
                st = net.station(pnode)
                ct = v.charge_time_hours(st.power_kw, plvl, plvl + added)
                charge_h += ct
                queue_h += st.queue_min / 60.0
                stops.append(ChargeStop(pnode, v.pct(plvl), v.pct(plvl + added),
                                        added, st.queue_min, ct * 60.0))
            elif node != pnode:                         # driving transition
                d, f = net.neighbors(pnode)[node]
                drive_h += v.edge_drive_hours(d, f)
        return Result(self.name, True, path, stops,
                      drive_h + charge_h + queue_h, drive_h, charge_h, queue_h)
