"""Entry point for the Smart EV Route & Charging Optimizer demo.

Run from the EV_Optimizer/ directory:
    python3 main.py
"""
from ev_optimizer import Vehicle, build_sample_network, off_peak, run_demo


def main():
    vehicle = Vehicle()                       # default common-Malaysian-EV profile
    festive = build_sample_network()          # heavy traffic + long festive queues
    normal = off_peak(festive)                # light traffic + short queues

    # Scenario 1: festive 'balik kampung' peak
    run_demo(vehicle, festive, "JB", "Penang", 100.0,
             label="SCENARIO 1: FESTIVE PEAK (Hari Raya)")

    # Scenario 2: same trip off-peak (note the route may switch)
    print("\n")
    run_demo(vehicle, normal, "JB", "Penang", 100.0,
             label="SCENARIO 2: OFF-PEAK (normal day)")

    # Scenario 3: safety check - the first 215 km leg needs ~96% charge,
    # so a 70% start MUST be rejected by all three solvers.
    print("\n\n##### SCENARIO 3: SAFETY CHECK - departing with only 70% battery #####")
    print("##### (first 215 km leg needs ~96%; all solvers must report INFEASIBLE) #####")
    run_demo(vehicle, festive, "JB", "Penang", 70.0,
             label="SCENARIO 3: UNSAFE START (expect INFEASIBLE)")


if __name__ == "__main__":
    main()
