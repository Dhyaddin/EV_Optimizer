# Week 14 Presentation Script — Slide-by-Slide
### Smart EV Route & Charging Optimizer for Malaysia
**Course:** CCS4202 — Design and Analysis of Algorithms · **Team of four**
**Target length:** 15–20 minutes · **This script budgets ≈ 18:00 of speaking**, leaving buffer for Q&A.

---

## Speaker Roster & Ownership

| Speaker | Name | Section owned | Slides | Budget |
|---|---|---|---|---|
| **Speaker 1** | **Radhi** (Tengku Eymran Radhi Putra) | 1 · Introduction | 1–4 | ~3:45 |
| **Speaker 2** | **Dhiyauddin** (Muhammad Dhiyauddin) | 2 · Problem Illustration + 3 · Mathematical Formulation | 5–7 | ~4:30 |
| **Speaker 3** | **Ariff** (Ariff Danial) | 4 · Algorithm Paradigms + 5 · Pseudocode & Program Demo | 8–9 | ~4:30 |
| **Speaker 4** | **Iqmal** (Iqmal Iskandar) | 6 · Algorithm Analysis + 7 · Conclusion | 10–14 | ~5:15 |

**How to use this script.** Each handoff sentence is in **bold** — say it *verbatim* so transitions feel rehearsed (examiners reward smooth teamwork). Timing cues are in `(mm:ss)`. If you run long, cut the lines marked *[trim]*.

---

### SLIDE 1 — Title  ·  *Speaker 1 (Radhi)* + team intro  ·  `(0:45)`
**On slide:** project title "Smart EV Route & Charging Optimizer for Malaysia", the EV render, all four names.

> **Radhi:** "Assalamualaikum and good morning. Our project is the **Smart EV Route and Charging Optimizer for Malaysia** — turning one real Hari Raya road trip into a rigorous algorithms problem."
>
> *(Each member says one line — this signals teamwork from the first 20 seconds.)*
> **Radhi:** "I'm Radhi, I'll frame the problem."
> **Dhiyauddin:** "I'm Dhiyauddin, I'll cover the model and the maths."
> **Ariff:** "I'm Ariff, I'll show the three algorithms and the live demo."
> **Iqmal:** "I'm Iqmal, I'll prove they're correct and efficient, and close."
>
> **Radhi:** "Let's begin with what we'll walk you through."

---

### SLIDE 2 — Table of Contents  ·  *Speaker 1 (Radhi)*  ·  `(0:30)`
**On slide:** the 7 sections (Introduction → Conclusion).

> **Radhi:** "Our talk has seven parts. First I'll introduce EV routing in Malaysia and why it matters *now*. Dhiyauddin then illustrates the concrete problem and formalises it mathematically. Ariff presents the three algorithm paradigms, their pseudocode, and a working program demo. Iqmal closes with the algorithm analysis — correctness and complexity — and our conclusion. Think of it as: *motivation, model, methods, and proof.*"

---

### SLIDE 3 — Introduction  ·  *Speaker 1 (Radhi)*  ·  `(1:20)`
**On slide:** EV adoption drivers; uneven charging network; why traditional navigation falls short.

> **Radhi:** "EV adoption in Malaysia is climbing fast — pushed by fuel prices, government green incentives, expanding infrastructure, and a wave of more affordable models. But the charging network hasn't kept pace evenly. DC fast chargers cluster at highway rest-and-relax areas, queue times are unpredictable, and limited range still makes drivers anxious on long trips.
>
> Here's the core gap: traditional navigation optimises only **distance or time**. That's perfectly fine for a petrol car — refuelling is fast and everywhere. For an EV it *breaks down*, because a good EV route also has to reason about battery capacity, charger availability, how long charging actually takes, cost, and even battery health. That richer problem is exactly what we set out to solve."

---

### SLIDE 4 — Introduction: The Evidence  ·  *Speaker 1 (Radhi)*  ·  `(1:10)`
**On slide:** two news sources — 5,360 public chargers (end-Nov 2025); 94,165 EV units since 2018.

> **Radhi:** "This isn't hypothetical. As of end-November 2025, Malaysia had about **5,360 public EV charging bays** — well short of the 10,000 target, with the AC target now pushed to Q3 2026. Meanwhile EV adoption has grown to over **94,000 units since 2018**. So demand is racing ahead while charging supply lags and stays geographically uneven.
>
> That mismatch — many more EVs, not enough well-placed chargers — is precisely the pressure that makes *smart* routing valuable. **Dhiyauddin will now put a face to this problem and show you why it's genuinely hard.**"

---

### SLIDE 5 — Problem Illustration: Aisyah's Journey  ·  *Speaker 2 (Dhiyauddin)*  ·  `(1:30)`
**On slide:** JB→Penang corridor map; constraints (60.48 kWh usable, ~336 km range, 80 kW DC, 15% reserve).

> **Dhiyauddin:** "Thanks, Radhi. Meet Aisyah. On the eve of Hari Raya she must drive from **Johor Bahru to Penang** — about **700 kilometres** up the North–South Expressway — during the *balik kampung* exodus, the single most demanding annual stress-test of our road and charging network.
>
> Her car is a **BYD Atto 3 Extended Range**: usable battery **60.48 kilowatt-hours**, effective real-world range around **336 km**, maximum DC charging **80 kW**, and a hard rule — never let the battery fall below a **15% emergency reserve**. Do the arithmetic: keeping that reserve leaves only about **285 km of usable range between full charges**. A 700 km corridor therefore forces **at least two charging stops** — and *where* she stops is a non-trivial decision, because the chargers aren't evenly spaced."

---

### SLIDE 6 — Problem Illustration: Why It's Hard  ·  *Speaker 2 (Dhiyauddin)*  ·  `(1:15)`
**On slide:** "Why it is hard" (limited DC chargers, unpredictable queues, range anxiety, congestion, per-minute billing) vs "Why conventional navigation fails".

> **Dhiyauddin:** "Five things make this hard at once. DC chargers are **limited**. Queues are **unpredictable** — up to 45 minutes at a hotspot like Tapah during the peak. **Range anxiety** shrinks the safe operating window. **Congestion raises consumption**, so the battery drains faster exactly when you're stuck. And charging is billed **per minute**, so a slow charge is also an expensive one.
>
> Conventional navigation is blind to all of this: it only optimises distance and time, it ignores battery state, and it can't see the charging taper or the queue ahead. So this is not a shortest-path lookup — it's a **multi-objective, resource-constrained optimisation**. **To solve it properly, we first had to model it precisely — here's the formulation.**"

---

### SLIDE 7 — Mathematical Formulation  ·  *Speaker 2 (Dhiyauddin)*  ·  `(1:40)`
**On slide:** graph `G=(V,E)`; state `(node, SoC)`; objective; Bellman recurrence `T*`; safety constraint `b_j ≥ b_min`.

> **Dhiyauddin:** "We model the corridor as a **directed graph, G equals V and E**. The **vertices V** are cities and charging hubs — origin JB, destination Penang, and the candidate stations in between like Ayer Keroh, Seremban, Tapah, Ipoh. The **edges E** are the drivable road legs between them.
>
> The key idea is the **state**: a *pair* — which node you're at, and your **State-of-Charge**, your battery level. Our **objective** is to minimise total elapsed time — the sum of driving time, plus at each stop the queue wait and the charging duration. Formally that's a **Bellman recurrence**: the optimal time to reach a state is the best over all predecessor states of *their* optimal time plus queue, charge, and drive.
>
> And one rule dominates everything — the **safety constraint**, `b ≥ b_min`: the battery never drops below the 15% reserve, which of course also means never below zero. That's the one hard invariant every algorithm must obey. **Ariff will now show the three different ways we attacked this.**"

---

### SLIDE 8 — Algorithm Paradigms  ·  *Speaker 3 (Ariff)*  ·  `(1:30)`
**On slide:** three columns — Greedy · Dynamic Programming · Modified A* — with battery/queue/optimality rows.

> **Ariff:** "Thanks, Dhiyauddin. We deliberately solved the *same* problem three ways, because comparing paradigms is the heart of an algorithms project.
>
> **Greedy** makes the best *local* choice at each step with no look-ahead — it only reacts to the battery when it's already low, and it commits to a station before it truly knows the wait. It's fast, but it can be sub-optimal and can even fail feasibility. Its best role is a fast baseline or fallback.
>
> **Dynamic Programming** exploits **optimal substructure** over `(node, SoC)` states — SoC is an *explicit* state dimension, and queues fold into the transitions. It's **globally optimal** within the discretisation grid, so we use it as our offline benchmark.
>
> **Modified A\*** is a cheapest-frontier graph search over SoC-augmented states, guided by a heuristic. It's **optimal when the heuristic is admissible**, and it explores far fewer states — so it's our **deployable, real-time engine**. **Let's look at the pseudocode and actually run it.**"

---

### SLIDE 9 — Algorithm Pseudocode & Program Demo  ·  *Speaker 3 (Ariff)*  ·  `(3:00)`
**On slide:** the three pseudocode blocks (see companion doc) with the shared `is_safe()` gate boxed; then the terminal output of `python3 main.py`.

> **Ariff:** "First, the shared idea that makes all three *safe*. Before **every** move, one gate runs — `is_safe`: it checks that battery on arrival, after any charging, stays at or above the reserve. If it doesn't, that path is **pruned instantly** and never explored. One line, shared by all three algorithms — that's why *none* of them can ever return a route that strands the driver.
>
> *(Point at each block briefly.)* **Greedy** loops: drive toward the goal, and when you can't reach it safely, pick the reachable station that minimises drive-plus-queue-plus-time-to-go, then charge up to the fast-band knee. **DP** relaxes every `(node, SoC)` state in topological order and back-tracks the optimum. **A\*** pops the lowest `elapsed + heuristic` state, expanding charge-moves and drive-moves until it first pops the destination.
>
> Now the demo. *(Run, or show the captured output.)* **Scenario 1, festive peak:** Greedy finishes in **12 hours 6 minutes with four stops**; DP and A\* both find **11 hours 51 minutes with only three** — via Ipoh. **Scenario 2, a normal day:** same trip, but the optimal route *switches to Tapah* — 9 hours 23 minutes — because the 45-minute festive queue is gone. And **Scenario 3**, starting at only 70% charge: all three correctly return **INFEASIBLE** rather than a dangerous plan, because the first leg alone would need ~96%. **Iqmal will now prove why the optimal answer is trustworthy — and how efficient each method is.**"

*[trim]* If short on time, describe Scenario 1 + Scenario 3 only and skip the off-peak switch narration (it reappears in the Conclusion).

---

### SLIDE 10 — Algorithm Analysis: Proof of Correctness  ·  *Speaker 4 (Iqmal)*  ·  `(1:30)`
**On slide:** three cards — Conservative Quantisation · Optimal Substructure · Loop Invariant `I(k)`; plus the A* admissibility note.

> **Iqmal:** "Thanks, Ariff. Running correctly once is not a proof — so we proved it. Three pillars.
>
> **One, conservative quantisation.** We round battery *down* to the grid: `quantise_down(x) = ⌊x/Δ⌋·Δ ≤ x`. The stored charge never *overstates* the true charge, so any plan we call safe is *genuinely* safe.
>
> **Two, optimal substructure.** The prefix of an optimal plan is itself optimal — if a cheaper prefix existed, we could substitute it and beat the supposed optimum, a contradiction.
>
> **Three, a loop invariant.** After processing node `u_k` in topological order, our table holds the true optimum for every state up to `k`. Base case is trivial; the inductive step follows from optimal substructure because all predecessors are already finalised in DAG order; the state space is finite, so termination gives a truly optimal, feasible plan.
>
> And as a complement, **A\*'s free-flow heuristic is admissible and consistent**, so its first pop of the destination is optimal — which is exactly why DP and A\* agree in every single test."

---

### SLIDE 11 — Algorithm Analysis: Time Complexity  ·  *Speaker 4 (Iqmal)*  ·  `(1:20)`
**On slide:** best/average/worst table for `V`, `E`, `S` (SoC levels).

> **Iqmal:** "On time. Let `V` be nodes, `E` edges, and `S` the number of battery levels. **Greedy** is near-linear — `O(E log V)` — cheap, because it never enumerates SoC levels at all. **Dynamic Programming** is a tight **Theta of (V plus E) times S-squared**: its edge-relaxation work sums to `S² · E`, so it grows **quadratically with battery resolution** — the classic *curse of dimensionality*. **A\* / Dijkstra** on the augmented graph is `O((V+S) log VS)` at best and, pruned by the heuristic, stays at or below the DP worst case on average. So there's a genuine spectrum: cheap-but-myopic, exact-but-heavy, and near-optimal-but-efficient."

---

### SLIDE 12 — Algorithm Analysis: Space Complexity  ·  *Speaker 4 (Iqmal)*  ·  `(0:55)`
**On slide:** space table — Greedy `O(V+E)`, DP `O(V·S)`, A* `O(SE + VS²)`.

> **Iqmal:** "Space tells the same story. **Greedy** needs only `O(V + E)` — a path and a frontier, no SoC grid, independent of `S`. **DP** needs `O(V · S)` for the value and back-pointer tables over `(node, level)` states. **A\*** can reach `O(SE + VS²)` in the worst case for its state maps and priority queue. The pattern is consistent: the more battery states you track, the more optimal you get — and the more memory you pay."

---

### SLIDE 13 — Conclusion  ·  *Speaker 4 (Iqmal)*  ·  `(1:10)`
**On slide:** "DP = benchmark · Greedy = baseline · A* = deployable"; validated-by-evidence line.

> **Iqmal:** "So, to conclude: long-distance EV travel in Malaysia is *not* a shortest-path lookup. It's a **multi-objective, resource-constrained, NP-hard** problem, shaped by a finite non-linearly-rechargeable battery, sparse capacity-limited chargers, per-minute billing, and stochastic queues.
>
> Our recommendation is to use each paradigm for what it's best at: **Dynamic Programming as the provably-optimal benchmark**, **Greedy as a fast baseline that exposes the real cost of no look-ahead**, and **A\* as the deployable engine — optimal yet efficient**. And it's validated by evidence: **DP and A\* agree across every scenario**, confirming optimality, while the festive-to-off-peak route switch proves the optimizer genuinely responds to real-world conditions."

---

### SLIDE 14 — Thank You / Q&A  ·  *All four*  ·  `(0:20)`
**On slide:** "Thank You".

> **Iqmal:** "We turned one Hari Raya road trip into a rigorous optimisation problem — and solved it three ways. Thank you."
> **All:** "We're happy to take your questions."

---

## Timing Summary

| Slides | Speaker | Section time | Running total |
|---|---|---|---|
| 1–4 | Speaker 1 · Radhi | 3:45 | 3:45 |
| 5–7 | Speaker 2 · Dhiyauddin | 4:25 | 8:10 |
| 8–9 | Speaker 3 · Ariff | 4:30 | 12:40 |
| 10–14 | Speaker 4 · Iqmal | 5:15 | 17:55 |

**Total ≈ 17:55** — comfortably inside the 15–20 min window with room for Q&A. To land at ~15:00, cut every *[trim]* line and tighten Slide 9's demo narration; to stretch toward 20:00, add ~30s of Q&A buffer per section.

---

## Delivery Notes — mapped to the "Excellent (5)" presentation tier

- **Teamwork & collaboration (5):** four contiguous, evenly-timed sections (~4–5 min each); every member speaks a substantive part; the title slide has all four introduce themselves; each **bold** handoff sentence hands the next speaker their cue — *rehearse the seams*.
- **Content mastery & critical thinking (5):** every section states a **trade-off**, not just a fact — Greedy fast-but-myopic, DP optimal-but-heavy, A\* best-of-both. One sharp insight per owner: range-anxiety framing (Radhi), the shared pruning gate (Dhiyauddin/Ariff), the queue-driven route switch (Ariff), the DP=A\* cross-validation (Iqmal).
- **Time management (5):** practise to ~17:30 so you comfortably land inside 15–20 even if Q&A starts early; use the *[trim]* markers as your release valve.
- **Delivery & clarity (5):** speak the numbers precisely (60.48 kWh, 15% reserve, 11h51m vs 12h06m); pause on the boxed `is_safe()` line; point, don't read, the pseudocode.
- **Demo safety net:** pre-capture the `python3 main.py` console output as an image on Slide 9 — never debug live.
