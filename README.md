# Smart EV Route & Charging Optimizer for Malaysia

A Design & Analysis of Algorithms group project (CCS4202). We model a long-distance
electric-vehicle journey across Peninsular Malaysia — Johor Bahru to Penang during the
Hari Raya *balik kampung* exodus — as a multi-objective, NP-hard routing-and-charging
problem, then design, implement and analyse **three algorithm paradigms** to solve it:
**Greedy**, **Dynamic Programming**, and a **Modified Dijkstra / A\*** search.

**Team:** Radhi · Dhiyauddin · Ariff · Iqmal

---

## TL;DR

A driver with a ~60 kWh EV (real range ~336 km) must cross ~700 km with a strict 15%
battery reserve, sparse highway chargers, per-minute billing, a non-linear charging
taper, and unpredictable festive queues. Conventional "shortest path" navigation
ignores all of this. Our optimizer jointly chooses **which stations to stop at** and
**how much to charge**, minimising total time (driving + queue + charging) while never
letting the battery drop below the reserve.

```bash
cd EV_Optimizer
python3 main.py        # pure standard library, no dependencies
```

---

## Repository Index

### Final report (start here)
| File | What it is |
|---|---|
| `EV_Optimizer_Final_Report.pdf` | The consolidated, submission-ready report (11 pages) |
| `EV_Optimizer_Final_Report.docx` | Editable Word version of the same report |

### Section write-ups (portfolio sources)
| File | Portfolio section |
|---|---|
| `Smart_EV_Optimizer_Scenario.docx` | (i) Problem Illustration — the JB→Penang scenario & constraints |
| `Algorithm_Comparison.md` | (ii) Paradigm comparison — Greedy vs DP vs A\* |
| `Mathematical_Formulation_and_Pseudocode.md` | (ii) Objective function, recurrence, pseudocode |
| `Theoretical_Analysis.md` | (iv) Correctness proof, time & space complexity |
| `Portfolio_and_Presentation_Script.md` | Portfolio outline + Week 14 slide-by-slide script |

### Program (Section iii — Demo)
```
EV_Optimizer/
├── main.py                          # runs the three demo scenarios
├── README.md                        # package-level docs
└── ev_optimizer/
    ├── vehicle.py                   # Vehicle: battery + charging physics
    ├── network.py                   # Network/Station + sample Malaysian map
    ├── result.py                    # Result / ChargeStop dataclasses
    ├── demo.py                      # run_demo() reporting harness
    └── algorithms/
        ├── base.py                  # BaseSolver (abstract) + shared safety gate
        ├── greedy.py                # GreedySolver
        ├── dynamic_programming.py   # DynamicProgrammingSolver
        └── astar.py                 # AStarSolver
```

---

## Key Results

| Scenario | Greedy | Dynamic Programming | A\* | Insight |
|---|---|---|---|---|
| Festive peak | 12h 06m (4 stops) | **11h 51m (3 stops)** | 11h 51m | DP & A\* agree → optimal |
| Off-peak | 9h 30m (4 stops) | **9h 23m (3 stops)** | 9h 23m | Route switches Ipoh → Tapah |
| 70% start | INFEASIBLE | INFEASIBLE | INFEASIBLE | Strict reserve pruning works |

- **DP = optimal benchmark**, **Greedy = fast baseline**, **A\* = deployable optimum**.
- DP and A\* return identical answers in every test, cross-validating optimality.
- The optimal route changes with conditions (it avoids Tapah's 45-min festive queue),
  proving the optimizer reacts to live data, not just distance.

## Complexity (V nodes, E edges, S SoC levels)

| Algorithm | Time (worst) | Space |
|---|---|---|
| Greedy | O(E log V) | O(V + E) |
| Dynamic Programming | Θ((V+E)·S²) | O(V·S) |
| A\* / Dijkstra (augmented) | O((S·E + V·S²)·log VS) | O(S·E + V·S²) |

---

## Design highlights

- **One class per algorithm**, all inheriting a shared `BaseSolver` with an identical
  `solve(start, dest, start_battery_pct)` interface — fully interchangeable.
- **Single source of physics**: all battery/charging maths lives in `Vehicle`.
- **One safety invariant**: every transition passes `is_safe()`, so no returned route
  can ever take the battery below the 15% reserve (or 0%).

> *Note:* The folder also contains course-provided materials (lecture `Topic*` slides,
> the Cormen *Introduction to Algorithms* text, and the project brief) which are
> reference inputs, not project deliverables.
