"""Reporting / demo harness: runs all three solvers and prints a comparison."""
from .algorithms import GreedySolver, DynamicProgrammingSolver, AStarSolver


def _fmt_hours(h):
    if h == float("inf"):
        return "INFEASIBLE"
    m = int(round(h * 60))
    return "{}h {:02d}m".format(m // 60, m % 60)


def print_result(res):
    print("\n" + "-" * 70)
    print("  ALGORITHM: " + res.algorithm)
    print("-" * 70)
    if not res.feasible:
        print("  Result: INFEASIBLE - no battery-safe route found.")
        return
    print("  Route        : " + " -> ".join(res.path))
    if res.stops:
        print("  Charging stops:")
        for s in res.stops:
            print("     * {:<9}  charge {:5.1f}% -> {:5.1f}%  (+{:4.1f} kWh)"
                  "   queue {:>2.0f}m  charge {:4.1f}m".format(
                      s.node, s.arrive_pct, s.depart_pct, s.added_kwh,
                      s.queue_min, s.charge_min))
    else:
        print("  Charging stops: none needed")
    print("  Time breakdown: drive {}  |  queue {}  |  charge {}".format(
        _fmt_hours(res.drive_h), _fmt_hours(res.queue_h), _fmt_hours(res.charge_h)))
    print("  TOTAL ELAPSED : {}  ({:.2f} h)".format(
        _fmt_hours(res.total_time_h), res.total_time_h))


def run_demo(vehicle, network, start="JB", dest="Penang",
             start_battery_pct=100.0, label=""):
    """Instantiate the three solver classes and compare their outputs."""
    print("=" * 70)
    print("  SMART EV ROUTE & CHARGING OPTIMIZER  -  " + label)
    print("=" * 70)
    print("  Vehicle      : {:.0f} kWh battery, {:.0f} kW max DC, {} kWh/km".format(
        vehicle.battery_cap_kwh, vehicle.max_dc_kw, vehicle.base_kwh_per_km))
    print("  Reserve floor: {:.0f}% ({:.1f} kWh)   | taper knee: {:.0f}% ({:.1f} kWh)".format(
        vehicle.reserve_frac * 100, vehicle.reserve_kwh,
        vehicle.knee_frac * 100, vehicle.knee_kwh))
    print("  Trip         : {} -> {},  start SoC = {:.0f}%".format(start, dest, start_battery_pct))

    # Identical constructor + identical solve() signature for all three classes.
    solvers = [
        GreedySolver(vehicle, network),
        DynamicProgrammingSolver(vehicle, network),
        AStarSolver(vehicle, network),
    ]
    results = [s.solve(start, dest, start_battery_pct) for s in solvers]
    for r in results:
        print_result(r)

    # summary
    print("\n" + "=" * 70)
    print("  SUMMARY  (lower total time is better)")
    print("=" * 70)
    print("  {:<26}{:<14}{:<9}{}".format("Algorithm", "Total time", "# stops", "Route"))
    for r in results:
        tt = _fmt_hours(r.total_time_h)
        n = len(r.stops) if r.feasible else "-"
        route = " -> ".join(r.path) if r.feasible else "INFEASIBLE"
        print("  {:<26}{:<14}{:<9}{}".format(r.algorithm, tt, str(n), route))

    feas = [r for r in results if r.feasible]
    if feas:
        best = min(feas, key=lambda r: r.total_time_h)
        print("\n  >> Optimal (benchmark) time: {} via {}.".format(
            _fmt_hours(best.total_time_h), best.algorithm))
        g = next((r for r in results if r.algorithm == "Greedy" and r.feasible), None)
        if g and g.total_time_h > best.total_time_h:
            gap = (g.total_time_h - best.total_time_h) * 60
            pct = 100 * (g.total_time_h / best.total_time_h - 1)
            print("  >> Greedy is {:.0f} min slower than the optimum "
                  "({:.1f}% worse) - the price of no look-ahead.".format(gap, pct))
    print()
    return results
