# Code Walkthrough — How the Optimizer Works
### Smart EV Route & Charging Optimizer for Malaysia

A plain-language explanation of the program flow, what each part does, and how it
fulfils the project objective. Use this for the report's "how it works" narrative.

---

## 1. The Big Picture

Everything in the package serves one goal: given a **start**, a **destination**, and a
**starting battery %**, find the route *and* the charging plan that minimise
**total elapsed time = driving + queueing + charging**, while never letting the battery
fall below the 15% safety reserve.

The three algorithms are simply three different *strategies* for searching that space of
decisions. They all share the same world model, so the comparison between them is fair.

**Dependency flow (top calls down; lower layers know nothing about higher ones):**

```
main.py  ->  demo.run_demo()  ->  three solver classes
                                      |
                                      +-- BaseSolver (shared logic)
                                      +-- Vehicle    (battery physics)
                                      +-- Network    (the map)
```

---

## 2. Layer 1 — The World Model (`vehicle.py`, `network.py`)

### Network = the map
`Network` holds two dictionaries:
- `edges`: each road leg stores `(distance_km, traffic_factor)`.
- `stations`: each charger stores `(power_kw, queue_min, tariff)`.

`build_sample_network()` builds the **festive** version (heavy traffic factors, long
queues — e.g. Tapah's 45-minute wait). `off_peak()` clones it with light traffic and
5-minute queues. That single swap is what makes the optimal route change between
Scenario 1 and Scenario 2.

### Vehicle = all the physics (one source of truth)
Keeping every formula here means no algorithm can diverge in its assumptions.

| Method | What it models |
|---|---|
| `edge_energy(d, f)` | `0.18 × distance × traffic_factor` — a congested leg drains more energy |
| `edge_drive_hours(d, f)` | `distance ÷ (90 ÷ traffic_factor)` — congestion slows the trip |
| `effective_power(rated, soc)` | the **charging taper**: full power below 80% SoC, then ramps toward zero near full |
| `charge_time_hours(...)` | integrates the taper in 0.25 kWh steps for an accurate charging time |
| `quantise_down(soc)` | snaps battery onto a 3 kWh (5%) grid, **always rounding down** so estimates stay conservative |

The taper is *why* the optimizer avoids charging past ~80% — the last 20% is the slowest
and (with per-minute billing) the most expensive energy of the trip.

---

## 3. Layer 2 — The Shared Brain (`algorithms/base.py`)

`BaseSolver` gives all three solvers two shared tools:

- **`freeflow_hours(dest)`** — a quick reverse Dijkstra estimating the *fastest possible*
  remaining driving time from every node to the destination (ignoring queues/charging).
  This is the **heuristic** A* uses and the "distance-to-go" signal Greedy uses.

- **`is_safe(soc_after_charge, energy_leg)`** — returns `True` only if
  `soc_after_charge − energy_leg ≥ reserve`. **This single line is the safety guarantee.**
  Every algorithm routes every candidate move through it, so an unsafe leg is discarded
  before it is ever considered. It is exactly why Scenario 3 (70% start) returns
  INFEASIBLE for all three: the first 215 km leg cannot pass this gate.

---

## 4. Layer 3 — The Three Strategies

### Greedy (`greedy.py`)
Walks forward one node at a time. At each node: if the destination is directly and safely
reachable, go. Otherwise score every reachable station by *(drive time + queue +
estimated time-to-go)*, pick the lowest, drive there, charge up to the 80% knee, repeat.
It never reconsiders past choices — fast, but short-sighted. Result: 4 stops, ~15 min
slower than optimal.

### Dynamic Programming (`dynamic_programming.py`)
Exhaustive and exact. Processes nodes in topological order, keeping a table
`T_best[(node, battery_level)]` = minimum time to reach that exact state. For every
reachable state it tries every charging amount and every onward road, prunes anything
failing `is_safe`, and records the best time plus a back-pointer. At the end it reads the
best entry at the destination and back-tracks to rebuild the plan. Considering *every*
combination makes it provably optimal — the benchmark.

### A* (`astar.py`)
Reaches the same optimum, but smarter. It searches a graph whose nodes are
`(city, battery-level)` states, using a priority queue ordered by
`elapsed time + heuristic`. Two move types: **charge** (jump to a higher battery level at
a station, paying queue + taper time) and **drive** (move to the next city, losing energy,
pruned by `is_safe`). Because the heuristic never overestimates, the first time it pops
the destination the answer is guaranteed optimal — so it settles far fewer states than DP.

---

## 5. Layer 4 — Orchestration (`demo.py`, `main.py`)

`main.py` builds one `Vehicle` and the two networks, then calls `run_demo` three times
(festive, off-peak, unsafe-start). `run_demo` instantiates all three solver classes with
the **same inputs**, calls `.solve()` on each, prints each result, and prints the summary
with the optimal time and Greedy's gap. Because the three classes share an identical
interface, the demo simply loops over them.

---

## 6. How This Achieves the Project Objective

The objective was to show EV routing is a genuine multi-constraint optimisation problem
and to solve it three ways and compare. The code delivers exactly that:

- **Every constraint is encoded as a concrete function** — battery capacity, reserve,
  non-linear charging taper, queues, congestion — not hand-waved.
- **Results are measurable and comparable** — DP and A* agree at 11h 51m
  (cross-validating optimality), Greedy is 2.1% worse (quantifying the cost of a myopic
  strategy), and the route switches Ipoh → Tapah off-peak (proving it responds to real
  conditions).
- **Safety is guaranteed** by one shared invariant, demonstrated by the INFEASIBLE case.

This maps directly onto the rubric: the **paradigm comparison** is embodied in the three
classes, the **correctness/complexity analysis** describes their behaviour, and the
**demo output** is the empirical proof.
