# Mathematical Formulation & Algorithm Design
### Smart EV Route & Charging Optimizer for Malaysia (JB → Penang)

This document formalises the EV route-and-charging problem and specifies the three solution
algorithms. It is written so that battery-infeasible paths — any path where the battery would drop
below the safety reserve (and certainly below 0%) — are **strictly pruned** at the point of state
transition.

---

## 0. Notation and Parameters

We model the North–South Expressway corridor as a **directed graph** `G = (V, E)`.

| Symbol | Meaning |
|---|---|
| `V` | Nodes: origin `o` (JB), destination `d` (Penang), and candidate charging stations `C ⊆ V` (Ayer Keroh, Seremban, Tapah, …) |
| `E` | Directed edges `(i, j)` representing a drivable leg between two nodes |
| `B` | Usable battery capacity in kWh (e.g. `B = 60.48`) |
| `b` | Battery energy (State of Charge) in kWh, `0 ≤ b ≤ B` |
| `b_min` | Safety reserve, `b_min = 0.15·B` (the no-stranding floor) |
| `D_ij` | Distance of edge `(i, j)` in km |
| `κ_ij` | Energy consumption rate on edge `(i,j)` in kWh/km (varies with terrain, traffic, A/C) |
| `e_ij` | Energy consumed on edge `(i,j)`: `e_ij = κ_ij · D_ij` |
| `t` | Clock time (time-of-day), needed because traffic and queues are time-dependent |
| `τ(i, j, t)` | Driving time on edge `(i,j)` when **departing** at time `t` (rises during festive peaks) |
| `P_i` | Rated charging power at station `i` (kW) |
| `P_veh` | Vehicle's max DC intake (kW), e.g. 80 |
| `P_eff(i, b)` | Effective charging power at station `i` when battery is at level `b` (captures the taper) |
| `ρ_i` | Charging tariff at station `i` (RM per minute) |
| `W_i(t)` | Expected queue wait at station `i` for a vehicle **arriving** at time `t` |
| `Δ_i` | Energy (kWh) added by charging at station `i` (a decision variable, `Δ_i ≥ 0`) |
| `T_start` | Departure time from the origin |

### Charging-power taper model
Effective power falls once the battery passes a "knee" SoC `b_knee` (≈ 80% of `B`):

```
P_eff(i, b) =  min(P_i, P_veh)                         if  b ≤ b_knee
               min(P_i, P_veh) · (B − b)/(B − b_knee)   if  b > b_knee
```

### Charging-duration function
Time to raise the battery from `b` to `b + Δ` at station `i` is the integral of the inverse power
(non-linear because of the taper):

```
                       b+Δ
   c(i, b, Δ)  =  ∫        1 / P_eff(i, x)  dx          (hours)
                       b
```

For a piecewise-linear taper this integral has a closed form; in implementation it is evaluated over
discretised SoC steps.

---

## 1. Objective Function (minimise total travel time)

A **solution** is a route `π = (v₀=o, v₁, …, v_k=d)` together with a charging plan `Δ = (Δ_{v₁}, …)`.
Let `a_m` be the arrival time at `v_m` and `t_m` the departure time. Total travel time is:

```
   minimise   T(π, Δ)  =   Σ      τ(v_m, v_{m+1}, t_m)          ← driving time
                          edges m
                                                                   ┌ queue wait
                        +  Σ     [ W_{v_m}(a_m)  +  c(v_m, b_m, Δ_{v_m}) ]
                        stations m                  └ charging duration
```

where the clock advances consistently:

```
   a_0  = T_start
   t_m  = a_m + W_{v_m}(a_m) + c(v_m, b_m, Δ_{v_m})      (depart after queue + charge)
   a_{m+1} = t_m + τ(v_m, v_{m+1}, t_m)
```

**Decision variables:** the sequence of nodes visited (the route) and the charge amount `Δ_i ≥ 0` at
each visited station.

### Constraints

```
(C1) Battery dynamics:   b_{m+1} = b_m + Δ_{v_m} − e_{v_m, v_{m+1}}
(C2) Reserve floor:      b_m ≥ b_min            for every node m        ← no-stranding
(C3) Physical capacity:  0 ≤ b_m + Δ_{v_m} ≤ B  at every station
(C4) Start condition:    b_0 = B,  depart at T_start
(C5) Reach goal:         v_k = d
```

> **Feasibility / pruning rule.** A leg `(i → j)` is *feasible* only if, after charging,
> `b_i + Δ_i − e_ij ≥ b_min`. Any transition that violates this (in particular any that would send the
> battery below 0%) is **discarded immediately** and never enters the search frontier or DP table.

The objective generalises to a **weighted multi-objective** form
`J = w_T·T + w_C·Cost + w_D·Degradation` by adding cost `Σ ρ_i · 60 · c(i,·)` and a degradation
penalty (rising with peak SoC and charging power); the pseudocode below keeps time as the primary
metric and notes where the other terms attach.

---

## 2. State Representation & Recurrence Relations

### State
A search/DP **state** is the pair:

```
   s = (v, b)        v = current node,   b = battery level on arrival (kWh)
```

Because `b` is continuous, it is **discretised** into `S` levels (e.g. 5% steps → 21 levels). We write
`b ∈ {β₀, β₁, …, β_{S−1}}`.

### Value function
Define the optimal-substructure value:

```
   T*(v, b) = the minimum elapsed travel time to reach node v
              arriving with battery level (at least) b
```

### Recurrence (Bellman equation)
Stations on the northbound corridor form a natural ordering, so `G` is a DAG and the recurrence is
well-defined:

```
   T*(o, B) = 0                                              (base case: start full at origin)

   T*(j, b_j) =        min            {  T*(i, b_i)
                 (i,b_i,Δ) feasible
                                         + W_i( arrival_time(i, b_i) )      ← queue
                                         + c(i, b_i, Δ)                     ← charge
                                         + τ( i, j, depart_time(i,b_i,Δ) )  ← drive
                                      }

   subject to   b_j = b_i + Δ − e_ij ,   b_j ≥ b_min ,   b_i + Δ ≤ B ,   Δ ≥ 0
```

The optimal plan is recovered by storing, with each `T*(j, b_j)`, the predecessor `(i, b_i, Δ)` that
achieved the minimum, then **back-tracking** from the best `T*(d, ·)`.

### Dominance (used to prune labels in graph search)
Label `L₁ = (v, b₁, T₁)` **dominates** `L₂ = (v, b₂, T₂)` iff:

```
   b₁ ≥ b₂   AND   T₁ ≤ T₂        (at least as much battery, no later, same node)
```

Dominated labels can never lead to a better solution and are discarded — the key efficiency lever for
the resource-constrained search.

---

## 3. Pseudocode for the Three Algorithms

All three share the helper predicates below.

```
function FEASIBLE_LEG(b_after_charge, e_ij):
    # strictly prune battery-negative / reserve-violating transitions
    b_arrive = b_after_charge − e_ij
    return (b_arrive ≥ b_min)          # b_min ≥ 0, so this also forbids b < 0

function DRIVE(i, j, depart_t, b_after_charge):
    e_ij     = κ(i,j) · D(i,j)
    b_arrive = b_after_charge − e_ij
    a_j      = depart_t + τ(i, j, depart_t)
    return (b_arrive, a_j)

function CHARGE_TIME(i, b, Δ):           # non-linear taper integral
    return ∫_b^{b+Δ} 1 / P_eff(i, x) dx
```

---

### 3.1 Dynamic Programming (exact, stage-based over discretised SoC)

```
ALGORITHM DP_EV_OPTIMIZER(G, B, b_min, T_start)
    # Stations are topologically ordered along the corridor: o = u_0, u_1, ..., u_n = d
    # T_best[v][b] = min elapsed time to reach node v with battery level b
    # BACK[v][b]   = (prev_node, prev_b, Δ) achieving that minimum

    initialise T_best[v][b] ← +∞   for all nodes v, all SoC levels b
    initialise BACK[v][b]   ← NULL

    T_best[o][ quantise(B) ] ← 0          # start: full battery at origin, time 0

    for each node i in topological order (o → d):
        for each SoC level b_i with T_best[i][b_i] < +∞:

            arrival_t = T_start + T_best[i][b_i]

            # ----- enumerate charging decisions at station i (Δ = 0 allowed) -----
            for each target level b_charged in { b_i, ..., quantise(B) }  with b_charged ≥ b_i:
                Δ = b_charged − b_i
                if i ∈ C:                       # only stations can charge
                    wait = W_i(arrival_t)
                    ct   = CHARGE_TIME(i, b_i, Δ)
                else:
                    if Δ > 0: continue          # cannot charge at a non-station node
                    wait = 0 ; ct = 0
                depart_t = arrival_t + wait + ct
                time_at_i = T_best[i][b_i] + wait + ct

                # ----- expand to each outgoing leg -----
                for each edge (i, j) in E:
                    if NOT FEASIBLE_LEG(b_charged, e(i,j)):   # PRUNE battery < b_min
                        continue
                    (b_j, a_j) = DRIVE(i, j, depart_t, b_charged)
                    b_j_q      = quantise(b_j)                # snap to grid (round DOWN = conservative)
                    new_time   = time_at_i + τ(i, j, depart_t)

                    if new_time < T_best[j][b_j_q]:
                        T_best[j][b_j_q] = new_time
                        BACK[j][b_j_q]   = (i, b_i, Δ)

    # ----- extract optimal plan -----
    b* = argmin over b of T_best[d][b]
    if T_best[d][b*] = +∞: return INFEASIBLE
    return RECONSTRUCT(BACK, d, b*)          # back-track predecessors to o
```

**Complexity:** `O(|V| · S² · deg)` time and `O(|V| · S)` memory, where `S` = number of SoC levels and
`deg` = average out-degree. Globally optimal up to the SoC discretisation; finer grids cost more (the
curse of dimensionality).

---

### 3.2 Greedy Approach (fast heuristic, no backtracking)

```
ALGORITHM GREEDY_EV(G, B, b_min, T_start, start=o, goal=d)
    current  = start
    b        = B                      # start full
    clock    = T_start
    route    = [start]

    while current ≠ goal:

        # Case 1: can we reach the goal directly on current charge?
        if EDGE(current, goal) exists AND FEASIBLE_LEG(b, e(current, goal)):
            (b, clock) = DRIVE_AND_ADVANCE(current, goal, clock, b)
            route.append(goal) ; current = goal
            break

        # Case 2: find the set of stations reachable WITHOUT dropping below reserve
        reachable = { s ∈ C : EDGE(current,s) AND FEASIBLE_LEG(b, e(current,s)) }
        if reachable = ∅:
            return INFEASIBLE          # stranded: no station in range → prune this run

        # Greedy choice: pick the station minimising a local score.
        # SCORE blends imminent wait + detour time (swap for ρ_s to be cost-greedy).
        next_stn = argmin_{s ∈ reachable} [ τ(current, s, clock)
                                            + W_s( clock + τ(current,s,clock) )
                                            + h(s, goal) ]     # h = freeflow time s→goal

        # drive to chosen station
        (b, clock) = DRIVE_AND_ADVANCE(current, next_stn, clock, b)
        route.append(next_stn) ; current = next_stn

        # Greedy charging rule: charge just enough to reach the NEXT hop + reserve,
        # but never beyond the fast band (cap at b_knee to dodge the slow, costly taper).
        need      = required_energy_to_next_hop(current, goal) + b_min
        target    = min( max(need, b), b_knee )      # never below current, never past the knee
        Δ         = max(0, target − b)
        clock    += W_current(clock) + CHARGE_TIME(current, b, Δ)
        b         = b + Δ

    return route, clock − T_start      # (plan, total time)  — NOT guaranteed optimal
```

**Complexity:** `O(|V| · |C|)` — essentially linear. Extremely fast, but myopic: it can route into a
peak-hour queue or, worse, into a dead-end where no station is reachable (it then reports
`INFEASIBLE`). Best used as a baseline or real-time fallback.

---

### 3.3 Dijkstra's / A\* on the State-Augmented Graph (deployable optimum)

Search the graph of states `(node, SoC-band)`. Dijkstra uses `priority = elapsed time`; **A\*** adds an
admissible heuristic `h` that lower-bounds remaining time (so it never over-estimates and stays
optimal).

```
ALGORITHM ASTAR_EV(G, B, b_min, T_start, start=o, goal=d)
    # state = (node, b_band).  g = elapsed travel time so far.
    start_state = (start, quantise(B))
    g[start_state] = 0
    PQ = min-priority-queue keyed by f = g + h
    PUSH(PQ, start_state, priority = 0 + H(start, goal))
    BACK = {}                      # for path reconstruction
    CLOSED = ∅

    while PQ not empty:
        (v, b) = POP_MIN(PQ)
        if v = goal: return RECONSTRUCT(BACK, (v,b))      # first pop of goal = optimal (admissible h)
        if (v,b) ∈ CLOSED: continue
        add (v,b) to CLOSED
        arrival_t = T_start + g[(v,b)]

        # ---- successor type A: CHARGING self-transitions (only at stations) ----
        if v ∈ C:
            for each higher band b' in { b+step, ..., quantise(B) }:
                Δ    = b' − b
                wait = W_v(arrival_t)
                ct   = CHARGE_TIME(v, b, Δ)
                g_new = g[(v,b)] + wait + ct
                RELAX( (v, b'), g_new, parent=(v,b), action=CHARGE(Δ) )

        # ---- successor type B: DRIVING edges ----
        depart_t = arrival_t                       # (already includes any charge done to reach (v,b))
        for each edge (v, j) in E:
            if NOT FEASIBLE_LEG(b, e(v,j)):        # PRUNE: would breach reserve / go below 0%
                continue
            (b_j, a_j) = DRIVE(v, j, depart_t, b)
            b_j_band   = quantise(b_j)             # round DOWN — conservative on battery
            g_new      = g[(v,b)] + τ(v, j, depart_t)
            RELAX( (j, b_j_band), g_new, parent=(v,b), action=DRIVE(v,j) )

    return INFEASIBLE

# ---- relaxation with dominance/standard check ----
function RELAX(state, g_new, parent, action):
    if g_new < g.get(state, +∞):
        g[state]   = g_new
        BACK[state] = (parent, action)
        PUSH(PQ, state, priority = g_new + H(node_of(state), goal))

# ---- admissible heuristic: free-flow driving time ignoring charging & queues ----
function H(v, goal):
    return  freeflow_driving_time(v, goal)         # never overestimates → A* stays optimal
                                                   # (set H ≡ 0 to recover plain Dijkstra)
```

**Complexity:** Dijkstra `O(E_aug + V_aug · log V_aug)` over the augmented state graph
(`V_aug = |V|·S`). A\* explores far fewer states in practice thanks to `H`, and remains optimal as long
as `H` is admissible. This is the recommended real-time engine for the optimiser.

---

## 4. How the Three Connect (suggested experimental framing)

| Role | Algorithm | Guarantee | Use in the project |
|---|---|---|---|
| **Benchmark (ground truth)** | Dynamic Programming | Globally optimal (within discretisation) | Measure how close the others get |
| **Lower-bound baseline** | Greedy | None (myopic) | Fast reference; exposes the cost of no look-ahead |
| **Deployable solver** | A\* (state-augmented) | Optimal for modelled cost (admissible `H`) | The engine you would actually ship |

Across all three, the **same pruning invariant** guarantees safety: a state is created only when
`b_arrive ≥ b_min ≥ 0`, so no returned route ever lets the battery fall below 0% — battery-infeasible
paths are eliminated at the moment of transition, never explored, and never reconstructed.
