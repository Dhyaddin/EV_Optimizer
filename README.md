# 🔋 Smart EV Route & Charging Optimizer for Malaysia

> A **Design & Analysis of Algorithms** group project (CCS4202). We model a long‑distance
> electric‑vehicle journey across Peninsular Malaysia — **Johor Bahru → Penang during the
> Hari Raya *balik kampung* exodus** — as a multi‑objective, NP‑hard routing‑and‑charging
> problem, then design, implement and analyse **three algorithm paradigms**: **Greedy**,
> **Dynamic Programming**, and a **Modified Dijkstra / A\***.

**Team:** Radhi · Dhiyauddin · Ariff · Iqmal

**Run it:** `python3 main.py` (pure Python standard library — no installs)

---

## 📑 Online Portfolio Contents

This README **is** our portfolio. It follows the four required steps:

1. [Illustrate the Problem](#i-illustrate-the-problem)
2. [Algorithm Paradigm & Pseudocode](#ii-algorithm-paradigm--pseudocode)
3. [Program Demonstration & Output](#iii-program-demonstration--output)
4. [Algorithm Analysis](#iv-algorithm-analysis)

Deep‑dive documents are linked in each section for markers who want the full detail.

---

## i. Illustrate the Problem

**The scenario.** Aisyah must drive a **BYD Atto 3 (≈60 kWh)** from Johor Bahru to Penang
— about **700 km** — on the eve of Hari Raya, when the North–South Expressway carries
~2.3 million vehicles/day. Her real‑world range is only ~336 km, so she **must** charge at
least twice, but chargers are sparse, queues can hit 45 minutes, congestion drains the
battery faster, and charging is billed **per minute**.

**The road network we model:**

```
        JB ── Melaka ── Seremban ── KL ──┬── Tapah ──┐
                                         │           ├── Penang
                                         └── Ipoh ───┘
```

**Hard constraints the optimizer must respect:**

| Constraint | Value |
|---|---|
| Usable battery | 60 kWh |
| Real highway consumption | ~0.18 kWh/km (rises with congestion) |
| Max DC charging | 80 kW, tapering above 80% SoC |
| Safety reserve | never below **15% (9 kWh)** |
| Charging cost | billed per minute (RM 2.05–2.35/min) |
| Queues | up to 45 min at peak (e.g. Tapah) |

**Why conventional navigation fails.** Ordinary apps optimise **distance or time only**.
For an EV the *cost of a stop* also depends on battery level, the non‑linear charging
taper, the queue, and battery wear — so this is a **multi‑objective optimisation**, not a
shortest‑path lookup.

📄 *Full write‑up:* see Section 2 of `EV_Optimizer_Final_Report.pdf`

---

## ii. Algorithm Paradigm & Pseudocode

We solve the same problem three ways. **State** = `(current_node, battery_level)`.
**Objective** = minimise `total_time = driving + queue + charging`, subject to
`battery ≥ reserve` at every step.

### Comparison of the three paradigms

| | **Greedy** | **Dynamic Programming** | **A\* (state‑augmented)** |
|---|---|---|---|
| Idea | best local choice | optimal over all `(node,SoC)` states | cheapest‑frontier search + heuristic |
| Optimal? | ❌ no | ✅ yes (benchmark) | ✅ yes (deployable) |
| Speed | fastest | heaviest | fast |

### Pseudocode

**Shared safety gate (used by all three):**
```
is_safe(soc_after_charge, energy_leg):
    return (soc_after_charge − energy_leg) ≥ reserve   # also forbids < 0%
```

**Greedy**
```
node ← start; battery ← full
while node ≠ destination:
    if destination reachable safely: drive there; stop
    candidates ← reachable stations passing is_safe()
    if none: return INFEASIBLE
    next ← candidate minimising (drive + queue + time_to_go)
    drive to next; charge up to the 80% knee
```

**Dynamic Programming**
```
T_best[(start, full)] ← 0
for node in topological_order:
    for (level, time) in known states of node:
        for target ≥ level (charging), for each out‑edge:
            if not is_safe(target, edge_energy): continue      # PRUNE
            relax T_best[(next, arrival_level)]
answer ← min over levels of T_best[(destination, level)];  back‑track path
```

**A\* / Modified Dijkstra**
```
push (start, full) with priority = heuristic
while queue:
    pop state with lowest (elapsed + heuristic)
    if node = destination: return path            # first pop = optimal
    expand CHARGE moves (station → higher SoC band)
    expand DRIVE moves (edge, pruned by is_safe)
heuristic = free‑flow remaining driving time (admissible)
```

📄 *Full formulation & comparison:* `Mathematical_Formulation_and_Pseudocode.md`, `Algorithm_Comparison.md`

---

## iii. Program Demonstration & Output

**Architecture** — one class per algorithm, all sharing a common `BaseSolver`:

```
.
├── main.py                          # runs the three demo scenarios
└── ev_optimizer/
    ├── vehicle.py                   # battery + charging physics
    ├── network.py                   # map (roads + stations) + sample data
    ├── result.py                    # Result / ChargeStop dataclasses
    ├── demo.py                      # run_demo() reporting harness
    └── algorithms/
        ├── base.py                  # BaseSolver + is_safe() safety gate
        ├── greedy.py                # GreedySolver
        ├── dynamic_programming.py   # DynamicProgrammingSolver
        └── astar.py                 # AStarSolver
```

**How to run:** from the repository root, `python3 main.py`

**Output — Scenario 1 (festive peak):**

| Algorithm | Total time | Stops | Route |
|---|---|---|---|
| Greedy | 12h 06m | 4 | via Ipoh |
| **Dynamic Programming** | **11h 51m** | **3** | via Ipoh (optimal) |
| A* | 11h 51m | 3 | via Ipoh (optimal) |

**Output — Scenario 2 (off‑peak):**

| Algorithm | Total time | Stops | Route |
|---|---|---|---|
| Greedy | 9h 30m | 4 | via Tapah |
| **Dynamic Programming** | **9h 23m** | **3** | via Tapah (optimal) |
| A* | 9h 23m | 3 | via Tapah (optimal) |

**Output — Scenario 3 (70% start):** all three return **INFEASIBLE** (the first 215 km
leg alone needs ~96% charge).

**Describing the output — what it means:**
- **DP and A\* agree exactly** in every scenario → cross‑validates the optimal answer.
- **Greedy is 6–15 min slower** with an extra stop → the measurable cost of no look‑ahead.
- **The route changes** from Ipoh (festive) to the shorter Tapah (off‑peak) once the
  45‑min queue clears → the optimizer reacts to real conditions, not just distance.
- **INFEASIBLE, not a guess** → the shared `is_safe` gate refuses any unsafe trip.

📄 *Line‑by‑line explanation:* `Code_Walkthrough.md`

---

## iv. Algorithm Analysis

**Correctness (Dynamic Programming).** Proven by induction with a loop invariant: after
processing each node in topological order, `T_best[(node, level)]` holds the true optimum
for that state. It rests on **optimal substructure** (best route = best sub‑routes) and
**conservative rounding** (`quantise_down` never overstates battery, so a plan called safe
is genuinely safe). A\* is optimal because its free‑flow heuristic is **admissible &
consistent** — which is why DP and A\* return identical answers.

**Time complexity** (V nodes, E edges, S SoC levels):

| Algorithm | Best | Average | Worst |
|---|---|---|---|
| Greedy | O(V + E) | O(E log V) | O(E log V) |
| Dynamic Programming | Θ((V+E)·S²) | Θ((V+E)·S²) | Θ((V+E)·S²) |
| A* / Dijkstra | O((V+S)·log VS) | ≤ worst (heuristic‑pruned) | O((S·E + V·S²)·log VS) |

**Space complexity:**

| Algorithm | Space |
|---|---|
| Greedy | O(V + E) — no SoC grid |
| Dynamic Programming | O(V · S) — the state table |
| A* / Dijkstra | O(S·E + V·S²) — priority queue worst case |

**Key finding.** DP grows **quadratically with battery resolution S** (curse of
dimensionality); A\* matches DP's optimum but explores far fewer states on average.
**Recommendation:** DP = benchmark, Greedy = fast baseline, A\* = deployable engine.

📄 *Full proof & derivations:* `Theoretical_Analysis.md`

---

## 📂 Repository Map

| Path | Purpose |
|---|---|
| `main.py` | Entry point — runs the three demo scenarios |
| `ev_optimizer/` | The Python package (all solver classes) — Section iii |
| `Algorithm_Comparison.md` | Paradigm comparison — Section ii |
| `Mathematical_Formulation_and_Pseudocode.md` | Formulation & pseudocode — Section ii |
| `Code_Walkthrough.md` | How the code works — Section iii |
| `Theoretical_Analysis.md` | Correctness & complexity — Section iv |
| `Portfolio_and_Presentation_Script.md` | Presentation script |
| `EV_Optimizer_Final_Report.pdf` | The full consolidated report (scenario in Section 2) |
