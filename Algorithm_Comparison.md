# Comparative Analysis of Three Algorithm Paradigms
### Smart EV Route & Charging Optimizer for Malaysia (JB → Penang)

This analysis compares **three algorithm design techniques** for solving the EV route-and-charging
problem defined in our scenario: a driver crossing Peninsular Malaysia on the North–South
Expressway (NSE) during the Hari Raya exodus, who must jointly decide **which charging stations to
stop at** and **how much to charge at each**, while balancing range safety, total trip time,
charging cost, and battery degradation.

The three chosen paradigms are:

1. **Dynamic Programming (DP)** — exact, state-based optimisation.
2. **Greedy Approach** — fast, locally-optimal heuristic.
3. **Graph Search (Dijkstra's / A\*)** — shortest-path search on a weighted graph.

---

## 1. Conceptual Approach (per paradigm)

### Dynamic Programming
DP treats the journey as a sequence of **stages** (candidate charging stations along the NSE:
Ayer Keroh, Seremban, Tapah, Gunung Semanggol, …) and a **state** at each stage defined by
`(station, State-of-Charge)`. It builds an optimal solution from the bottom up: for every reachable
`(station, SoC)` state it records the minimum weighted cost (time + money + degradation) to arrive
there, then extends each state forward by enumerating *how much to charge* and *which station to
visit next*. Because SoC is continuous, it is **discretised** (e.g. in 5% steps). The optimal plan
is recovered by back-tracking the stored decisions. DP naturally captures the **non-linear charging
taper** and the **carry-over of battery state** between legs — the property that breaks naive
shortest-path methods.

### Greedy Approach
The greedy method makes the **best-looking local decision at each step** with no look-ahead.
Starting in JB, it drives until SoC approaches the 15% reserve, then commits to the *nearest
reachable* (or *cheapest-per-minute*, or *fastest*) charger, charges by a fixed rule (e.g. "charge to
80%"), and repeats. Charging-station allocation is reactive: the choice is made only when the battery
is low, using whatever single criterion the heuristic prioritises. It never revisits or reconsiders
earlier decisions.

### Graph Search (Dijkstra's / A\*)
The corridor is modelled as a weighted graph `G = (V, E)`: nodes are the origin, destination, and
charging stations; edges carry a **cost** (travel time, or a weighted blend of time + energy + queue +
cost). Dijkstra's expands the lowest-cost frontier node until it reaches Penang; **A\*** adds an
admissible **heuristic** (e.g. straight-line distance / remaining time to Penang) to steer the search
and expand far fewer nodes. To handle the battery, the graph is **augmented** so each node becomes
`(station, SoC-band)` — turning charging decisions into edges between SoC levels of the same station.

---

## 2 & 3. Strengths and Weaknesses — Comparison Table

| Dimension | **Dynamic Programming** | **Greedy Approach** | **Graph Search (Dijkstra's / A\*)** |
|---|---|---|---|
| **Core idea** | Optimal substructure over `(station, SoC)` states; build solution bottom-up and back-track | Best local choice at each step; no look-ahead or backtracking | Expand cheapest frontier on a weighted graph; A\* uses a heuristic to focus search |
| **Handles battery drop / SoC carry-over** | **Excellent** — SoC is an explicit state dimension; the taper and reserve constraint are modelled exactly | **Weak** — only reacts when SoC is low; cannot plan a deliberate partial charge for a future leg | **Good** — only if the graph is *state-augmented* with SoC bands; on a plain graph it ignores battery |
| **Handles queues (time-dependent)** | **Strong** — queue/wait cost can be folded into each state-transition; supports rolling-horizon updates | **Poor** — picks a station before knowing the queue; easily routes into the worst festive bottleneck | **Moderate** — needs time-dependent edge weights; classic Dijkstra assumes static costs |
| **Handles distance / travel time** | Strong (stage cost) but distance is only one of several modelled terms | Strong for pure distance/time, which is exactly what it tends to over-prioritise | **Excellent** — this is the native strength of shortest-path search |
| **Multi-objective (time + cost + degradation)** | **Best fit** — weighted cost or Pareto front handled cleanly across states | Hard — collapses to a single greedy criterion; trade-offs are ignored | Workable via a weighted edge cost, but a single scalar weight is less expressive than DP states |
| **Solution quality** | **Globally optimal** (within the SoC discretisation) | **Sub-optimal**, sometimes badly so (can even fail to reach a feasible plan) | **Optimal for the modelled cost**; A\* optimal if the heuristic is admissible |
| **Time complexity** | High — roughly `O(N · S² · K)` for N stations, S SoC levels, K charge choices; grows with finer discretisation | **Very low** — `O(N)`; essentially linear in stations visited | Dijkstra `O(E + V log V)`; A\* usually far fewer expansions, but worst-case still exponential on the augmented graph |
| **Memory / overhead** | **Heavy** — must store the full state table; the "curse of dimensionality" bites as SoC resolution rises | **Negligible** — keeps only current state | Moderate — priority queue + visited set over the (possibly large) augmented node set |
| **Adapts to live/dynamic data** | Good via re-solving on a rolling horizon, but each re-solve is costly | **Excellent for speed** — trivially cheap to recompute, ideal as a fast fallback | Good — A\* re-plans quickly; well suited to live re-routing with updated edge weights |
| **Implementation difficulty** | High — state design, discretisation, taper modelling | **Low** — simplest to build and explain | Moderate — standard libraries exist, but the SoC augmentation adds real complexity |
| **Best role in our system** | The **gold-standard offline planner / benchmark** the others are measured against | A **fast baseline** and real-time fallback when compute or data is limited | The **practical real-time engine**, especially A\* on a state-augmented graph |

---

## Key Takeaways

- **No single paradigm wins on every axis.** DP gives provably optimal plans but is computationally
  heavy and scales poorly as SoC discretisation tightens. Greedy is almost free and great as a
  baseline, but its lack of look-ahead makes it unreliable for the multi-variable EV problem — it is
  exactly the behaviour a naive navigation app exhibits. Graph search (A\*) is the strongest
  *practical* compromise, *provided* the graph is augmented with battery state.

- **The right comparison strategy for the report:** use **DP as the optimal benchmark**, **Greedy as
  the lower-bound baseline**, and **A\* as the deployable solution**, then quantify the trade-off
  between solution quality and runtime across the three. This directly demonstrates the
  *time-vs-optimality* tension that an advanced algorithms project is meant to analyse.

- **Why this matters for EVs specifically:** the battery's SoC is a *carried state* and the charging
  taper makes cost *non-linear* — two features that plain Dijkstra ignores, that Greedy mishandles,
  and that DP captures exactly. That gap is the entire reason the EV problem is harder than ordinary
  routing.
