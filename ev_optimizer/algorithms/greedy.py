"""Algorithm 1 - Greedy: fast, myopic, no backtracking."""
from .base import BaseSolver
from ..result import Result, ChargeStop


class GreedySolver(BaseSolver):
    name = "Greedy"

    def solve(self, start, dest, start_battery_pct) -> Result:
        v, net = self.v, self.net
        h = self.freeflow_hours(dest)
        b = start_battery_pct / 100.0 * v.battery_cap_kwh
        node, path, stops = start, [start], []
        drive_h = charge_h = queue_h = 0.0

        guard = 0
        while node != dest:
            guard += 1
            if guard > len(net.nodes()) * 3:                 # safety against loops
                return Result(self.name, False, path, stops, float("inf"),
                              drive_h, charge_h, queue_h)

            nbrs = net.neighbors(node)

            # 1) Direct dash to the destination if the battery allows it.
            if dest in nbrs:
                d, f = nbrs[dest]
                if self.is_safe(b, v.edge_energy(d, f)):
                    drive_h += v.edge_drive_hours(d, f)
                    b -= v.edge_energy(d, f)
                    path.append(dest); node = dest
                    break

            # 2) Next hops reachable WITHOUT breaching the reserve.
            reachable = []
            for nxt, (d, f) in nbrs.items():
                if self.is_safe(b, v.edge_energy(d, f)):
                    score = v.edge_drive_hours(d, f) + h.get(nxt, float("inf"))
                    if net.is_station(nxt):
                        score += net.station(nxt).queue_min / 60.0
                    reachable.append((score, nxt, d, f))

            if not reachable:                                # stranded - cannot recover
                return Result(self.name, False, path, stops, float("inf"),
                              drive_h, charge_h, queue_h)

            # 3) Greedy choice: smallest local score.
            reachable.sort(key=lambda x: x[0])
            _, nxt, d, f = reachable[0]
            drive_h += v.edge_drive_hours(d, f)
            b -= v.edge_energy(d, f)
            path.append(nxt); node = nxt

            # 4) Charge to the knee (dodge the slow, costly taper) if at a station.
            if node != dest and net.is_station(node):
                st = net.station(node)
                arrive = b
                target = min(v.knee_kwh, v.battery_cap_kwh)
                if target > b:
                    ct = v.charge_time_hours(st.power_kw, b, target)
                    charge_h += ct
                    queue_h += st.queue_min / 60.0
                    stops.append(ChargeStop(node, v.pct(arrive), v.pct(target),
                                            target - b, st.queue_min, ct * 60.0))
                    b = target

        total = drive_h + charge_h + queue_h
        return Result(self.name, node == dest, path, stops, total,
                      drive_h, charge_h, queue_h)
