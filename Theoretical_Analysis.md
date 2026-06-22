# Theoretical Analysis
### Smart EV Route & Charging Optimizer for Malaysia

This section provides the formal "Analysis and Findings" for the three implemented
solvers (`GreedySolver`, `DynamicProgrammingSolver`, `AStarSolver`). It contains
(1) a proof of correctness for our primary optimal algorithm, (2) a best/average/
worst-case time-complexity analysis of all three, and (3) a space-complexity
analysis. The analysis refers directly to the implemented code and its variables.

---

## 0. Notation and Model Parameters

| Symbol | Meaning |
|---|---|
| `V` | number of nodes (cities / charging hubs) in the network |
| `E` | number of directed edges (road legs); note `Σ_v outdeg(v) = E` |
| `B` | usable battery capacity (kWh) |
| `Δ` | SoC discretisation step (`soc_step_kwh`, = 3 kWh in our build) |
| `S` | number of discrete SoC levels, `S = ⌊B / Δ⌋ + 1` (= 21 in our build) |
| `b_min` | reserve floor in kWh (`reserve_kwh`, = 0.15·B) |
| `P` | integration steps in `charge_time_hours` (`= B / 0.25`); a constant w.r.t. `V, E` |

A **state** is the pair `(node, SoC-level)`, drawn from a space of size `V·S`.
The corridor graph is a **directed acyclic graph (DAG)**: every road leg advances
northbound, so no cycles exist. (This DAG property is what the Dynamic Programming
solver relies on; see §1.4 for the general-graph case.)

The optimisation minimises **total elapsed time** = driving + queue + charging time,
subject to the hard safety constraint that the battery never falls below `b_min`
(and hence never below 0%). Throughout, the single feasibility gate is
`BaseSolver.is_safe(soc_after_charge, e_leg) ≡ (soc_after_charge − e_leg ≥ b_min)`.

---

## 1. Proof of Correctness — Dynamic Programming (Primary Optimal Algorithm)

We prove that `DynamicProgrammingSolver` returns a **time-optimal, battery-feasible**
plan, optimal up to the SoC discretisation `Δ`. Dynamic Programming is chosen as the
primary algorithm for the formal proof because its correctness follows cleanly from
the optimal-substructure property of the DAG; §1.5 gives the complementary optimality
argument for A*.

### 1.1 Definitions

For a node `v` and a discrete level `b ∈ {0, Δ, 2Δ, …, B}`, define the **true optimum**

```
  OPT(v, b) = the minimum total elapsed time of any battery-feasible partial plan
              that starts at `start` (full), ends at v, and arrives with quantised
              SoC exactly b;     OPT(v, b) = +∞ if no such feasible plan exists.
```

A *partial plan* is a sequence of drive legs and (at stations) charge actions in
which **every** intermediate arrival SoC is ≥ `b_min`. Let `T_best[(v,b)]` be the
table the algorithm fills, and let `u_0, u_1, …, u_{n}` be the nodes in topological
order (`u_0 = start`).

### 1.2 Two structural lemmas

**Lemma 1 (Conservative quantisation).** `quantise_down(x) = ⌊x/Δ⌋·Δ ≤ x`. Hence the
level stored for a state never *overstates* the real battery. Consequently, any leg
the algorithm accepts as feasible (`is_safe` true on the quantised level) is feasible
on the *true* (≥) battery as well. *No infeasible plan is ever reported feasible.*

**Lemma 2 (Optimal substructure).** Consider an optimal feasible plan `π*` reaching
`(u_k, b)`. Let its last transition leave some predecessor state `(u_j, b_j)` (a drive
leg `u_j → u_k`, possibly preceded by a charge at `u_j`), with `j < k` because the
graph is a DAG. Then the prefix of `π*` up to `(u_j, b_j)` is itself an optimal plan
for `(u_j, b_j)`. *Proof:* the total time is the sum of the prefix time and the
(fixed) transition time `queue + charge + drive`; if a cheaper prefix to `(u_j,b_j)`
existed, substituting it would yield a cheaper plan to `(u_k,b)`, contradicting the
optimality of `π*`. ∎

### 1.3 Loop invariant and induction

> **Invariant `I(k)`.** Immediately after the outer loop has finished processing
> topological node `u_k`, for every node `u_i` with `i ≤ k` and every level `b`,
> `T_best[(u_i, b)] = OPT(u_i, b)`.

**Base case `I(0)`.** Before any relaxation, `T_best[(start, b_0)] = 0` where `b_0`
is the quantised start SoC, and `+∞` elsewhere. The only zero-length feasible plan
is "stay at start", so `OPT(start, b_0) = 0` and `OPT(start, b≠b_0)=∞`. Thus `I(0)`
holds. (Processing `u_0` only *emits* transitions to successors; it does not change
`start`'s own entries.)

**Inductive step.** Assume `I(k−1)`. Because the nodes are processed in topological
order, **every predecessor** `u_j` (`j < k`) of `u_k` has already been fully
processed, and at that time the algorithm enumerated *all* charge targets
`tgt ≥ b_j` (stations) and *all* out-edges, relaxing each resulting successor:

```
  candidate(u_k, b') = T_best[(u_j,b_j)] + queue(u_j) + charge(u_j, b_j→tgt) + drive(u_j,u_k)
  where b' = quantise_down(tgt − e(u_j,u_k)),  admitted only if is_safe(tgt, e) .
```

Fix any level `b` with `OPT(u_k, b) < ∞`, realised by an optimal plan `π*`. By
Lemma 2 its prefix is optimal for the predecessor state `(u_j, b_j)`, and by `I(k−1)`
that prefix value equals `T_best[(u_j,b_j)]`. The transition of `π*` is one of the
enumerated `(tgt, edge)` combinations and passed `is_safe` (it is feasible). Therefore
the algorithm computed a candidate equal to `OPT(u_k, b)` and, via `if new_t <
T_best[...]`, stored `T_best[(u_k,b)] ≤ OPT(u_k,b)`.

Conversely, **every** value the algorithm writes into `T_best[(u_k,b)]` corresponds
to a concrete feasible plan (each relaxed transition passed `is_safe`, and by `I(k−1)`
its predecessor value is achievable), so `T_best[(u_k,b)] ≥ OPT(u_k,b)`. Combining,
`T_best[(u_k,b)] = OPT(u_k,b)`. Levels of `u_k` with `OPT = ∞` are never relaxed and
stay `+∞`. Hence `I(k)` holds. ∎

**Termination.** The state space `V·S` is finite; each state enumerates at most `S`
targets and `outdeg` edges, each doing `O(P)` bounded work, so the algorithm halts.

### 1.4 Conclusion

By induction `I(n)` holds, so `T_best[(dest, b)] = OPT(dest, b)` for every level `b`.
The solver returns `min_b T_best[(dest,b)]`, which equals `min_b OPT(dest,b)` — the
minimum elapsed time over **all** feasible plans reaching the destination at any
final SoC. By Lemma 1 the reconstructed plan is feasible on the true battery. Thus
the algorithm is correct: it returns a battery-safe, time-optimal plan, optimal up
to the discretisation `Δ` (as `Δ → 0`, `OPT` over the grid converges to the true
continuous optimum). `∎`

> **Assumption.** This proof uses the topological ordering, valid because the
> network is a DAG. For a general graph with cycles, the same value function is
> instead computed by the label-correcting search of §1.5 (A* / Dijkstra), whose
> optimality does not require acyclicity.

### 1.5 Complementary optimality of A* (state-augmented)

`AStarSolver` searches the state graph with priority `f = g + h`, where `g` is elapsed
time and `h` is the **free-flow remaining driving time** computed by reverse Dijkstra.

**Admissibility.** `h(v)` ignores queueing and charging and uses the maximum legal
speed, so `h(v) ≤` true remaining time for any feasible continuation; it never
overestimates.

**Consistency (monotonicity).** For any drive edge `u→v`, `h(u) ≤ drive(u,v) + h(v)`
because `h` is itself a shortest free-flow time (it satisfies the triangle
inequality); charge/self-edges have `h` unchanged and non-negative cost. With a
consistent heuristic, the first time A* pops a state it has its optimal `g`, and in
particular the first pop of any `(dest, ·)` state is time-optimal. Setting `h ≡ 0`
reduces the procedure to Dijkstra, which remains optimal. The identical `is_safe`
gate guarantees feasibility, exactly as in DP — which is why DP and A* return the
same optimum in every test scenario. `∎`

---

## 2. Time-Complexity Analysis (Best / Average / Worst)

We express bounds in `V`, `E`, and the SoC resolution `S`. The charge-time
integration factor `P` is a constant with respect to graph size and is folded into
the constants (noted where it matters).

### 2.1 Greedy

The solver computes the free-flow heuristic once (a reverse Dijkstra,
`O(E + V log V)`), then performs a single forward descent. The descent runs at most
`O(V)` hops; each hop scans the current node's out-edges and sorts the reachable set,
costing `O(outdeg · log outdeg)`. Summed over the path this is at most `O(E log V)`.
Greedy never revisits or backtracks, so its cost is essentially data-insensitive.

| Case | Bound | Reason |
|---|---|---|
| **Best** | `O(V + E)` | destination directly reachable; descent ends in a few hops; heuristic scan is linear when the heap stays small |
| **Average** | `O(E log V)` | a handful of charging hops, each sorting a small candidate set; dominated by the one-time heuristic `O(E + V log V)` |
| **Worst** | `O(E log V)` | long path visiting many nodes, each sorting its neighbours |

Greedy is the cheapest paradigm: **independent of `S`** (it never enumerates SoC
levels — it uses the fixed "charge to the knee" rule), and near-linear in graph size.

### 2.2 Dynamic Programming

The triple enumeration is: for each node (`V`), for each known SoC level (`S`), for
each charge target (`S`), relax each out-edge (`outdeg`). The edge-relaxation work
therefore totals

```
  Σ_v [ S · S · outdeg(v) ]  =  S² · Σ_v outdeg(v)  =  S² · E .
```

In addition, the charge-time integration is evaluated once per `(node, level, target)`
triple, contributing `O(V · S² · P)`. Hence the overall bound is

```
  T_DP  =  O( S² · E  +  S² · V · P )  =  O( S² · (V + E) )      (P constant).
```

Because the DP **exhaustively** fills every reachable state, the bound is *tight* and
data-insensitive — pruning of infeasible states only lowers the constant:

| Case | Bound | Reason |
|---|---|---|
| **Best** | `Θ((V + E)·S²)` | even favourable data still visits the reachable `(node, level)` grid |
| **Average** | `Θ((V + E)·S²)` | same; feasibility pruning trims constants, not the order |
| **Worst** | `Θ((V + E)·S²)` | full grid enumerated |

The key mathematical insight: cost grows **quadratically in the SoC resolution**
`S = ⌊B/Δ⌋ + 1`. Halving `Δ` (doubling `S`) quadruples the running time — the
classic "curse of dimensionality" of the continuous battery state.

### 2.3 Modified Dijkstra / A* (state-augmented)

The augmented graph has `V_aug = V·S` states. Each state has up to `outdeg` driving
successors and up to `S` charging (self-loop) successors, so the number of augmented
edges is

```
  E_aug  =  Σ_{(v,level)} ( outdeg(v) + S )  =  S·E  +  V·S² .
```

With a binary-heap implementation, Dijkstra/A* costs `O(E_aug · log V_aug)`:

| Case | Bound | Reason |
|---|---|---|
| **Best** | `O((V + S) · log(V·S))` | a (near-)perfect heuristic expands essentially only the states on the optimal path |
| **Average** | between best and worst | the consistent free-flow heuristic prunes large regions; far fewer than `V·S` expansions in practice |
| **Worst** | `O((S·E + V·S²) · log(V·S))` | uninformative heuristic (`h ≡ 0`, i.e. plain Dijkstra) settles every state |

A* shares the DP's dependence on `S` (the augmented state space is the same `V·S`),
but its **average** behaviour is typically far better because the admissible
heuristic steers the search toward the goal and the closed-set settles each state
at most once.

### 2.4 Summary table

| Algorithm | Best | Average | Worst |
|---|---|---|---|
| **Greedy** | `O(V + E)` | `O(E log V)` | `O(E log V)` |
| **Dynamic Programming** | `Θ((V+E)·S²)` | `Θ((V+E)·S²)` | `Θ((V+E)·S²)` |
| **A\* / Dijkstra (augmented)** | `O((V+S)·log(VS))` | ≤ worst (heuristic-pruned) | `O((S·E + V·S²)·log(VS))` |

(`S = ⌊B/Δ⌋ + 1` SoC levels; in our build `S = 21`, a constant, so practical runtime
collapses to the graph terms — but the table shows how resolution drives cost.)

---

## 3. Space-Complexity Analysis

| Algorithm | Space | Explanation |
|---|---|---|
| **Greedy** | `O(V + E)` | stores the path (`O(V)`), the visited frontier, and the heuristic distance map (`O(V)`); the adjacency input is `O(V+E)`. No SoC grid is materialised, so memory is **independent of `S`**. |
| **Dynamic Programming** | `O(V · S)` | the value table `T_best` and the back-pointer table each hold one entry per `(node, level)` state: `V·S` entries. This is the dominant cost and the practical limiter as `S` grows. |
| **A\* / Dijkstra (augmented)** | `O(S·E + V·S²)` worst | the `g`-map, closed set and back-pointers are `O(V·S)`, but the priority queue can hold up to `O(E_aug) = O(S·E + V·S²)` entries in the worst case; with the consistent heuristic the live frontier is usually much smaller. |

### Practical reading for the report

* **Greedy** — cheapest in time *and* space, independent of `S`, but sub-optimal
  (see the proof's contrast: it lacks the optimal-substructure guarantee). Ideal as a
  fast baseline / real-time fallback.
* **Dynamic Programming** — provably optimal with a *tight, predictable* `Θ((V+E)S²)`
  time and `O(V·S)` space; the right choice for an offline benchmark, but its cost
  scales quadratically with battery resolution.
* **A\*** — same worst-case order as DP but, thanks to the admissible/consistent
  free-flow heuristic, far better average-case expansion, while retaining optimality.
  This combination of optimality and practical speed is why A* is the deployable
  engine.
