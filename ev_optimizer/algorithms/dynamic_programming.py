"""Algorithm 2 - Dynamic Programming: exact optimum over a (node, SoC) grid."""
from collections import defaultdict

from .base import BaseSolver
from ..result import Result, ChargeStop


class DynamicProgrammingSolver(BaseSolver):
    name = "Dynamic Programming"

    def solve(self, start, dest, start_battery_pct) -> Result:
        v, net = self.v, self.net
        order = net.topological_order()
        levels = v.soc_levels()

        # T_best[(node, level)] = min elapsed hours; back = predecessor + energy added
        T_best = defaultdict(lambda: float("inf"))
        back = {}
        T_best[(start, v.quantise_down(start_battery_pct / 100.0 * v.battery_cap_kwh))] = 0.0

        for node in order:
            known = [(lvl, T_best[(node, lvl)]) for lvl in levels
                     if T_best[(node, lvl)] < float("inf")]
            for lvl, t_here in known:
                # charging targets (stations only); non-stations: "no charge".
                if net.is_station(node) and node != dest:
                    targets = [tl for tl in levels if tl >= lvl]
                else:
                    targets = [lvl]

                for tgt in targets:
                    if tgt > lvl:
                        st = net.station(node)
                        add_time = st.queue_min / 60.0 + v.charge_time_hours(st.power_kw, lvl, tgt)
                        added = tgt - lvl
                    else:
                        add_time, added = 0.0, 0.0

                    for nxt, (d, f) in net.neighbors(node).items():
                        e = v.edge_energy(d, f)
                        if not self.is_safe(tgt, e):          # *** STRICT PRUNE ***
                            continue
                        arrive_lvl = v.quantise_down(tgt - e)
                        new_t = t_here + add_time + v.edge_drive_hours(d, f)
                        if new_t < T_best[(nxt, arrive_lvl)]:
                            T_best[(nxt, arrive_lvl)] = new_t
                            back[(nxt, arrive_lvl)] = ((node, lvl), added)

        # best terminal state at the destination
        best_state, best_t = None, float("inf")
        for lvl in levels:
            if T_best[(dest, lvl)] < best_t:
                best_t, best_state = T_best[(dest, lvl)], (dest, lvl)

        if best_state is None:
            return Result(self.name, False, [start], [], float("inf"), 0, 0, 0)

        return self._reconstruct(best_state, back)

    def _reconstruct(self, goal_state, back):
        v, net = self.v, self.net
        states, s = [], goal_state
        while s is not None:
            states.append(s)
            prev = back.get(s)
            s = prev[0] if prev else None
        states.reverse()

        path = [st[0] for st in states]
        stops, drive_h, charge_h, queue_h = [], 0.0, 0.0, 0.0
        for i in range(1, len(states)):
            (node, lvl) = states[i]
            ((pnode, plvl), added) = back[(node, lvl)]
            d, f = net.neighbors(pnode)[node]
            drive_h += v.edge_drive_hours(d, f)
            if added > 1e-9:
                st = net.station(pnode)
                ct = v.charge_time_hours(st.power_kw, plvl, plvl + added)
                charge_h += ct
                queue_h += st.queue_min / 60.0
                stops.append(ChargeStop(pnode, v.pct(plvl), v.pct(plvl + added),
                                        added, st.queue_min, ct * 60.0))
        return Result(self.name, True, path, stops,
                      drive_h + charge_h + queue_h, drive_h, charge_h, queue_h)
