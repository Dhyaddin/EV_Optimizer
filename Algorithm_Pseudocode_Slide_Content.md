# Pseudocode Slide Content — The Three Algorithms
### Smart EV Route & Charging Optimizer for Malaysia
**Fulfils project requirement 1(g)(ii): Algorithm Paradigm & Pseudocode**
**Course:** CCS4202 — Design and Analysis of Algorithms

> This document gives **slide-ready pseudocode** for the three paradigms we compare — **Greedy**,
> **Dynamic Programming**, and **Graph Search (Dijkstra / Modified A\*)**. Every block is written in
> the vocabulary of an advanced algorithms class (graph `G=(V,E)`, Bellman recurrence, optimal
> substructure, topological/DAG order, edge relaxation, label dominance, admissible & consistent
> heuristic) and explicitly shows the four EV-specific behaviours the rubric asks for:
>
> 1. **Graph model** — vertices `V` = cities / charging hubs, edges `E` = road legs.
> 2. **SoC decay** — battery State-of-Charge drops across distance *and* traffic.
> 3. **Hard pruning** — any transition that would drive `SoC ≤ 0%` (or below the reserve) before
>    reaching a charger is *cut at the point of transition* and never explored.
> 4. **Weighted costs** — station **queue wait** time and **charging speed (kW)** enter the cost.

---

## 0. Shared Data Model & Notation  *(put this on the slide before the three algorithms)*

```
GRAPH            G = (V, E)                     directed graph of the NSE corridor
  V  (vertices)  = { o } ∪ C ∪ { d }           o = origin (JB), d = destination (Penang),
                                               C = charging hubs (Ayer Keroh, Seremban, Tapah, Ipoh, …)
  E  (edges)     = { (i, j) }                   a drivable road leg from vertex i to vertex j

BATTERY / STATE OF CHARGE (SoC)
  B              usable capacity (kWh)          e.g. 60.48
  b              current SoC (kWh), 0 ≤ b ≤ B
  b_min          safety reserve = 0.15 · B      the no-stranding floor (≈ 9 kWh); note b_min ≥ 0
  S              number of discretised SoC bands (e.g. 5% steps → 21 levels)

EDGE / ENERGY / TIME (all can be time-of-day dependent)
  D_ij           length of edge (i,j) in km
  κ_ij(t)        consumption rate (kWh/km) — RISES with congestion/terrain/AC at clock time t
  e_ij(t)        energy drawn on the leg      e_ij(t) = κ_ij(t) · D_ij      ← SoC decay term
  τ_ij(t)        driving time on (i,j) departing at t (rises during festive peaks)

CHARGING (this is where kW and queues become cost weights)
  P_i            rated charger power at hub i (kW)
  P_veh          vehicle max DC intake (kW), e.g. 80
  b_knee         taper knee ≈ 0.80 · B         above the knee, effective power falls
  P_eff(i,b)     EFFECTIVE charging power (kW) at hub i, SoC b  — models the taper
  W_i(t)         expected QUEUE wait at hub i for arrival time t   ← cost weight (time-dependent)
  ρ_i            tariff (RM per minute)         optional money term for multi-objective cost
```

### Shared primitives (called by all three algorithms)

```
# ---- 1. SoC DECAY: how much battery a leg consumes, given live traffic ----
function ENERGY_ON_LEG(i, j, t):
    return κ(i, j, t) · D(i, j)                 # higher traffic ⇒ higher κ ⇒ faster SoC drop

# ---- 2. CHARGING SPEED (kW) as a cost weight: effective power tapers past the knee ----
function P_EFF(i, b):
    P = min(P_i, P_veh)                          # limited by the slower of charger and vehicle
    if b ≤ b_knee:  return P
    else:           return P · (B − b) / (B − b_knee)   # taper: power collapses near full

# ---- 3. CHARGE DURATION: integral of inverse power (non-linear because of the taper) ----
function CHARGE_TIME(i, b, Δ):                   # time to add Δ kWh starting from SoC b
    return ∫_b^{b+Δ}  1 / P_EFF(i, x)  dx        # ⇒ charging to 100% is slow & (per-minute) costly

# ---- 4. THE PRUNING GATE (shared safety invariant) ----
function IS_SAFE(b_after_charge, e_leg):
    b_arrive = b_after_charge − e_leg
    #   b_arrive < 0      ⇒ car is STRANDED mid-leg  → prune
    #   b_arrive < b_min  ⇒ reserve breached (stricter, subsumes the < 0 case) → prune
    return (b_arrive ≥ b_min)                    # returns FALSE ⇒ caller discards this transition

# ---- 5. Conservative quantisation: round SoC DOWN to a grid band (never overstate charge) ----
function QUANTISE_DOWN(b):
    return ⌊ b / Δ_band ⌋ · Δ_band               # ⌊x⌋ rounding ⇒ a plan called "safe" is truly safe
```

> **Why the gate matters (say this on the slide):** `IS_SAFE` is the *single* line that guarantees
> feasibility. A state/label is **created only when `b_arrive ≥ b_min ≥ 0`**, so a battery-infeasible
> path — including any path that would hit `SoC ≤ 0%` before the next charger — is eliminated at the
> moment of transition, never entering the frontier, the DP table, or the reconstructed route.

---

## 1. GREEDY  —  *design paradigm: local optimisation, no look-ahead*

**Idea:** at each vertex take the best-looking *local* move; commit immediately; never revisit.
Fast baseline / real-time fallback. **Not** guaranteed optimal; may report `INFEASIBLE`.

```
ALGORITHM GREEDY_EV(G, B, b_min, T_start):
    current ← o                                  # start at origin vertex
    b       ← B                                  # start full
    clock   ← T_start
    route   ← [ o ]

    while current ≠ d:

        # (A) Can we finish NOW without breaching the reserve? — SoC-aware direct check
        if EDGE(current, d) exists AND IS_SAFE(b, ENERGY_ON_LEG(current, d, clock)):
            drive current → d; update b, clock          # b −= e_leg ; clock += τ
            route.append(d); current ← d
            break

        # (B) Which charging hubs are reachable WITHOUT the battery hitting 0%/reserve?
        reachable ← { s ∈ C : EDGE(current,s) AND IS_SAFE(b, ENERGY_ON_LEG(current,s,clock)) }
        if reachable = ∅:
            return INFEASIBLE                    # PRUNE whole run: stranded, no safe charger

        # (C) GREEDY CHOICE — weight the local score by queue wait + drive + distance-to-go
        next ← argmin_{s ∈ reachable} [ τ(current, s, clock)                    # drive time
                                      + W_s( clock + τ(current, s, clock) )     # QUEUE weight
                                      + h(s, d) ]                               # free-flow s→d
        drive current → next; update b, clock
        route.append(next); current ← next

        # (D) GREEDY CHARGING RULE — charge just enough for the next hop + reserve,
        #     but cap at the knee to avoid the slow, per-minute-expensive taper (kW-aware)
        need   ← energy_to_next_hop(current, d, clock) + b_min
        target ← min( max(need, b), b_knee )
        Δ      ← max(0, target − b)
        clock  ← clock + W_current(clock) + CHARGE_TIME(current, b, Δ)   # QUEUE + kW-taper cost
        b      ← b + Δ

    return (route, clock − T_start)              # total time — NOT guaranteed optimal
```

**Complexity:** time `O(|V| + |E|)` per run, `O(E log V)` if the reachable-set uses a priority
structure; space `O(V + E)` — **independent of `S`** (it never enumerates SoC bands).
**Weakness to name aloud:** myopic — it can pick a hub that is closest *now* but sits behind the worst
festive queue, or drive into a dead-end where no charger is reachable.

---

## 2. DYNAMIC PROGRAMMING  —  *paradigm: optimal substructure over `(vertex, SoC)` states*

**Idea:** treat charging hubs as **stages** in topological (DAG) order along the corridor and each
`(vertex, SoC-band)` as a **state**. Fill a value table bottom-up via the **Bellman recurrence**, then
back-track. **Globally optimal** within the SoC discretisation → our benchmark.

```
ALGORITHM DP_EV_OPTIMIZER(G, B, b_min, T_start):
    # T_best[v][b] = min elapsed time to reach vertex v with SoC band b
    # BACK[v][b]   = (prev_vertex, prev_band, Δ) that achieved it  (for reconstruction)

    for all v ∈ V, all bands b:  T_best[v][b] ← +∞ ;  BACK[v][b] ← NULL
    T_best[o][ QUANTISE_DOWN(B) ] ← 0            # base case: full battery at origin, time 0

    for each vertex i ∈ V in TOPOLOGICAL ORDER (o → d):        # DAG order along the NSE
        for each SoC band b_i with T_best[i][b_i] < +∞:

            arrival_t ← T_start + T_best[i][b_i]

            # ---- enumerate the CHARGING decision at hub i (Δ = 0 is allowed) ----
            for each target band b_c ≥ b_i  up to  QUANTISE_DOWN(B):
                Δ ← b_c − b_i
                if i ∈ C:                        # only real hubs can charge
                    wait ← W_i(arrival_t)                       # QUEUE cost weight
                    ct   ← CHARGE_TIME(i, b_i, Δ)              # kW-taper charge cost
                else:
                    if Δ > 0: continue           # cannot charge at a non-hub vertex
                    wait ← 0 ; ct ← 0
                depart_t  ← arrival_t + wait + ct
                time_at_i ← T_best[i][b_i] + wait + ct

                # ---- RELAX every outgoing road edge (i, j) ∈ E ----
                for each edge (i, j) ∈ E:
                    e_leg ← ENERGY_ON_LEG(i, j, depart_t)      # SoC decay w/ live traffic
                    if NOT IS_SAFE(b_c, e_leg):  continue      # PRUNE: SoC would hit 0%/reserve
                    b_j  ← QUANTISE_DOWN(b_c − e_leg)          # arrival SoC, rounded DOWN
                    cost ← time_at_i + τ(i, j, depart_t)       # + drive time
                    if cost < T_best[j][b_j]:                  # standard DP relaxation
                        T_best[j][b_j] ← cost
                        BACK[j][b_j]   ← (i, b_i, Δ)

    # ---- extract optimal plan ----
    b* ← argmin_b  T_best[d][b]
    if T_best[d][b*] = +∞:  return INFEASIBLE
    return RECONSTRUCT(BACK, d, b*)              # back-track predecessors o ← … ← d
```

**Bellman recurrence (state-transition form for the slide):**

```
T*(o, B) = 0
T*(j, b_j) =   min      { T*(i, b_i) + W_i(arrival) + CHARGE_TIME(i,b_i,Δ) + τ(i,j,depart) }
            (i,b_i,Δ)
   subject to   b_j = b_i + Δ − e_ij ,   b_j ≥ b_min ,   b_i + Δ ≤ B ,   Δ ≥ 0
```

**Complexity:** time `Θ((|V|+|E|)·S²)` — the `S²` (charge-from-band × arrive-at-band) is the **curse of
dimensionality**, growing quadratically with battery resolution; space `O(|V|·S)` for the value +
back-pointer tables. **Optimal** up to the SoC grid.

---

## 3. GRAPH SEARCH — Dijkstra / Modified A\*  —  *paradigm: cheapest-frontier search on an augmented graph*

**Idea:** search the graph of **augmented states** `(vertex, SoC-band)`. Charging becomes a
self-transition to a *higher* SoC band; driving becomes an edge to another vertex. Priority = elapsed
time (`Dijkstra`) plus an **admissible heuristic** `H` (`A*`). First pop of the destination is optimal.

```
ALGORITHM ASTAR_EV(G, B, b_min, T_start):
    start ← (o, QUANTISE_DOWN(B))
    g[start] ← 0                                 # g = best-known elapsed time to a state
    PQ ← min-priority-queue keyed by  f = g + H  # A*: H = admissible lower bound on remaining time
    PUSH(PQ, start, f = 0 + H(o, d))
    BACK ← { } ; CLOSED ← ∅

    while PQ not empty:
        (v, b) ← POP_MIN(PQ)
        if v = d:  return RECONSTRUCT(BACK, (v,b))    # first pop of goal = OPTIMAL (admissible H)
        if (v,b) ∈ CLOSED:  continue
        CLOSED ← CLOSED ∪ {(v,b)}
        arrival_t ← T_start + g[(v,b)]

        # ---- successor type A: CHARGING self-transitions (only at hubs) ----
        if v ∈ C:
            for each higher band b' ∈ { b+step, …, QUANTISE_DOWN(B) }:
                Δ     ← b' − b
                g_new ← g[(v,b)] + W_v(arrival_t) + CHARGE_TIME(v, b, Δ)   # QUEUE + kW-taper cost
                RELAX( (v, b'), g_new, parent=(v,b), action = CHARGE(Δ) )

        # ---- successor type B: DRIVING edges (i,j) ∈ E ----
        for each edge (v, j) ∈ E:
            e_leg ← ENERGY_ON_LEG(v, j, arrival_t)   # SoC decay with live traffic
            if NOT IS_SAFE(b, e_leg):  continue      # PRUNE: would breach reserve / hit SoC ≤ 0%
            b_j   ← QUANTISE_DOWN(b − e_leg)         # round DOWN — conservative on battery
            g_new ← g[(v,b)] + τ(v, j, arrival_t)    # + drive time
            RELAX( (j, b_j), g_new, parent=(v,b), action = DRIVE(v,j) )

    return INFEASIBLE

# ---- relaxation with label check (add dominance test for extra pruning) ----
function RELAX(state, g_new, parent, action):
    if g_new < g.get(state, +∞):
        g[state]    ← g_new
        BACK[state] ← (parent, action)
        PUSH(PQ, state, priority = g_new + H(vertex_of(state), d))

# ---- admissible & consistent heuristic: free-flow driving time, ignoring charge & queues ----
function H(v, d):
    return FREEFLOW_DRIVE_TIME(v, d)             # never overestimates ⇒ A* stays optimal
                                                 # set H ≡ 0 to recover plain Dijkstra
```

**Optional label dominance (the key efficiency lever):** label `L₁=(v,b₁,g₁)` **dominates**
`L₂=(v,b₂,g₂)` iff `b₁ ≥ b₂ AND g₁ ≤ g₂` (as much battery, no later). Dominated labels are discarded.

**Complexity:** Dijkstra `O(E_aug + V_aug·log V_aug)` with `V_aug = |V|·S`; A\* expands far fewer states
thanks to `H`. Worst case `O((S·E + V·S²)·log VS)`; space `O(S·E + V·S²)`. **Optimal** whenever `H` is
admissible — the reason DP and A\* return identical answers in every scenario. **Recommended
deployable engine.**

---

## 4. How the three connect  *(one-line summary row for the slide)*

| Role | Algorithm | Optimality | EV-specific handling |
|---|---|---|---|
| Fast baseline / fallback | **Greedy** | None (myopic) | reacts to SoC only when low; queue in local score |
| Offline benchmark (ground truth) | **Dynamic Programming** | Globally optimal (within grid) | SoC is an explicit state dim; taper + queue in transitions |
| Deployable real-time engine | **Dijkstra / A\*** | Optimal if `H` admissible | SoC-augmented states; charge = self-edge; queue/kW in `g` |

---

## 5. Slide-layout suggestion (Slide 9 "Algorithm Pseudocode" is a section divider — expand it to 3–4 slides)

- **Slide 9a — Shared model & the safety gate:** the `G=(V,E)` + SoC notation box and the boxed
  `IS_SAFE` / `ENERGY_ON_LEG` primitives. *This is the "everything shares one pruning rule" slide.*
- **Slide 9b — Greedy:** the Greedy block; highlight the greedy-choice line and the "charge to the
  knee" rule.
- **Slide 9c — Dynamic Programming:** the DP block + the Bellman recurrence box; highlight the
  `IS_SAFE` prune and the relaxation line.
- **Slide 9d — Dijkstra / A\*:** the A\* block; highlight `f = g + H`, the two successor types
  (CHARGE / DRIVE), and "first pop of goal = optimal".

On each block, **colour the same three tokens** so the audience tracks them across all three:
`ENERGY_ON_LEG` (SoC decay), `IS_SAFE` (pruning), and `W_i(...) / CHARGE_TIME(...)` (queue + kW cost).

---

## 6. Requirement 1(g)(ii) coverage map  *(for the report appendix / marker)*

| Rubric-required behaviour | Where it appears in the pseudocode |
|---|---|
| Vertices `V` = cities/charging hubs, edges `E` = roads | §0 data model; every algorithm iterates `V` and relaxes `(i,j) ∈ E` |
| SoC drops across distance **and** traffic | `ENERGY_ON_LEG` uses `κ_ij(t)·D_ij` with traffic-dependent `κ`; applied in all three |
| Prune / break path if `SoC ≤ 0%` before a charger | `IS_SAFE` (`b_arrive ≥ b_min ≥ 0`) gates every drive transition in all three; Greedy also returns `INFEASIBLE` when `reachable = ∅` |
| Cost weight for station **queue wait** | `W_i(t)` in Greedy's score, DP's transition, and A\*'s `g_new` |
| Cost weight for **charging speed (kW)** | `P_EFF` taper feeds `CHARGE_TIME`, added to cost in all three; Greedy caps at `b_knee` to dodge the slow band |

**Advanced-algorithms vocabulary demonstrated:** directed graph `G=(V,E)`, DAG / topological order,
Bellman optimality recurrence, optimal substructure, edge relaxation, state-space augmentation,
label dominance, admissible & consistent heuristic, `A*` = Dijkstra with `H`, curse of dimensionality,
conservative quantisation, loop-invariant correctness.
