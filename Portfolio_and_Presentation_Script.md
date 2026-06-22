# Portfolio Outline & Week 14 Presentation Script
### Smart EV Route & Charging Optimizer for Malaysia

Team: **Radhi, Dhiyauddin, Ariff, Iqmal**  ·  Target length: **10-15 min** (script budgeted ~12.5 min)

---

# PART 1 — PORTFOLIO OUTLINE (Google Sites / GitHub)

Four sections, one per rubric requirement. Each section lists the page content and
which existing project file it draws from.

## Section (i) — Problem Illustration
*Goal: make the reader feel the problem before any maths.*

- **Hook**: the Hari Raya `balik kampung` scenario — Aisyah drives a BYD Atto 3
  (60 kWh) from Johor Bahru to Penang (~700 km) on the North-South Expressway.
- **Why it is hard**: limited DC chargers, unpredictable queues, range anxiety,
  congestion raising consumption, per-minute billing.
- **Why conventional navigation fails**: it optimises distance/time only and ignores
  battery state, charging taper, queues, and degradation.
- **Visuals**: corridor map (JB → Melaka → Seremban → KL → {Tapah | Ipoh} → Penang);
  a constraints table (battery, SoC, reserve, charger kW, queue, tariff).
- *Source file*: `Smart_EV_Optimizer_Scenario.docx`.

## Section (ii) — Algorithm Paradigm & Pseudocode
*Goal: show the three paradigms and the formal model.*

- **Problem formulation**: objective `min total time = drive + queue + charge`;
  state `(node, SoC)`; recurrence `T*(v,b)`; the strict `b ≥ b_min` safety constraint.
- **Three paradigms**: Greedy, Dynamic Programming, Modified Dijkstra / A*.
- **Pseudocode**: one clean block per algorithm, highlighting the shared pruning gate
  `is_safe()`.
- **Comparison table**: strengths/weaknesses across battery, queues, distance,
  optimality.
- *Source files*: `Mathematical_Formulation_and_Pseudocode.md`, `Algorithm_Comparison.md`.

## Section (iii) — Program Demo & Output Description
*Goal: prove it runs and explain what the output means.*

- **Architecture**: the OOP package (`vehicle`, `network`, `result`, `algorithms/`,
  `demo`) — one class per algorithm sharing `BaseSolver`.
- **How to run**: `cd EV_Optimizer && python3 main.py` (standard library only).
- **Annotated output**: the festive-peak run (Greedy 12h06m vs DP/A* 11h51m), the
  off-peak run, and the safety-check (INFEASIBLE) run.
- **Key observation to call out**: the optimal route *switches* from the Ipoh path
  (festive) to the shorter Tapah path (off-peak) once the 45-min queue clears.
- *Source files*: `EV_Optimizer/` package, screenshot of the console output.

## Section (iv) — Algorithm Analysis
*Goal: the rigorous "findings".*

- **Correctness**: induction / loop-invariant proof that DP is time-optimal and
  battery-safe; A* optimality via an admissible + consistent heuristic.
- **Time complexity**: best/average/worst for all three in terms of `V`, `E`, `S`.
- **Space complexity**: per algorithm.
- **Findings**: DP = benchmark, Greedy = fast baseline, A* = deployable optimum;
  DP and A* agree in every test, validating optimality.
- *Source file*: `Theoretical_Analysis.md`.

> **GitHub layout suggestion**
> ```
> /docs        -> the four .md/.docx write-ups (rendered on Google Sites)
> /EV_Optimizer -> the runnable package
> README.md    -> 1-paragraph overview + links to each section + run instructions
> ```

---

# PART 2 — SLIDE-BY-SLIDE PRESENTATION SCRIPT

**Speaking order & ownership**

| Speaker | Section | Slides | Budget |
|---|---|---|---|
| **Radhi** | (i) Problem Illustration | 1-3 | ~3:00 |
| **Dhiyauddin** | (ii) Paradigm & Pseudocode | 4-6 | ~3:15 |
| **Ariff** | (iii) Demo & Output | 7-9 | ~3:15 |
| **Iqmal** | (iv) Analysis & Close | 10-12 | ~3:00 |

*Timing cues are in (mm:ss). To trim to 10 min, cut the italicised "deep-dive"
lines on slides 6 and 11. Each handoff sentence is written in **bold** — say it
verbatim so transitions feel rehearsed.*

---

### SLIDE 1 — Title  ·  *Radhi*  ·  (0:30)
**On slide**: project title, the JB→Penang map silhouette, four names + matric IDs.

> "Assalamualaikum and good morning. We're Radhi, Dhiyauddin, Ariff and Iqmal, and
> our project is the **Smart EV Route & Charging Optimizer for Malaysia**. Imagine
> it's the eve of Hari Raya, you drive an EV, and you need to get from Johor Bahru to
> Penang — 700 kilometres — without getting stranded. That single journey is the
> problem we turned into an algorithms project."

---

### SLIDE 2 — Problem Illustration  ·  *Radhi*  ·  (1:15)
**On slide**: the corridor map; the constraints table (60 kWh battery, 15% reserve,
charger kW, queue minutes); a "range anxiety" icon.

> "Meet Aisyah. She drives a BYD Atto 3 — about 60 kilowatt-hours, a real-world range
> near 336 km. But the trip is 700 km, so she *must* charge at least twice. Now layer
> on the festive reality: only a handful of DC chargers on the expressway, queues that
> can hit 45 minutes, congestion that drains the battery faster, and charging that's
> billed per minute. Every one of these is a constraint our optimizer has to respect."

---

### SLIDE 3 — Why Conventional Navigation Fails  ·  *Radhi*  ·  (1:15)
**On slide**: split image — Google-Maps-style "shortest path" vs our multi-factor view.

> "Here's the critical insight. A normal navigation app optimises one thing: distance
> or time. For a petrol car that's fine — refuelling is fast and everywhere. For an EV
> it breaks down, because the *cost of a stop* depends on your battery level, the
> charging taper, the queue, and even long-term battery wear. So this isn't a shortest-
> path lookup; it's a multi-objective optimisation. **And to solve it properly, we
> first had to model it mathematically — Dhiyauddin will take you through that.**"

---

### SLIDE 4 — Formulation: Objective & State  ·  *Dhiyauddin*  ·  (1:15)
**On slide**: `min T = Σ drive + Σ(queue + charge)`; state `(node, SoC)`; recurrence
`T*(v,b)`; constraint `SoC ≥ b_min`.

> "Thanks, Radhi. We model the corridor as a graph: nodes are cities and charging
> hubs, edges are road legs. The state we track is a pair — *which node you're at* and
> *how much battery you have*. Our objective is to minimise total elapsed time: driving
> plus queueing plus charging. And the one hard rule, our safety constraint, is that
> the battery never drops below a 15% reserve — which also means never below zero."

---

### SLIDE 5 — Three Algorithm Paradigms  ·  *Dhiyauddin*  ·  (1:00)
**On slide**: three columns — Greedy / Dynamic Programming / A* — with a one-line idea
each.

> "We deliberately attacked it three ways. **Greedy** — make the best local choice at
> each stop, fast but short-sighted. **Dynamic Programming** — build the optimum from
> sub-solutions over every battery level, exact but heavy. And **Modified A\*** — a
> shortest-path search on an augmented `(node, battery)` graph, guided by a heuristic.
> Comparing paradigms is the heart of the project."

---

### SLIDE 6 — Pseudocode & the Safety Invariant  ·  *Dhiyauddin*  ·  (1:00)
**On slide**: short pseudocode for A*; the line `if not is_safe(...) : prune` boxed.

> "Across all three, one line does the safety work: `is_safe`. Before any move, we
> check that arrival battery stays above the reserve — if not, that path is pruned
> instantly and never explored. *That single shared gate is why none of our algorithms
> can ever return a route that strands the driver.* **Now that you've seen the logic,
> Ariff will show it actually running.**"

---

### SLIDE 7 — Program Architecture  ·  *Ariff*  ·  (1:00)
**On slide**: the package tree (`vehicle`, `network`, `result`, `algorithms/`,
`demo`); "one class per algorithm, shared `BaseSolver`".

> "Thanks, Dhiyauddin. We built this as a clean Python package — pure standard library,
> no dependencies. Each algorithm is its own class inheriting a common `BaseSolver`, so
> they take identical inputs and are fully interchangeable. All the battery physics
> lives in one `Vehicle` class, so the three algorithms can't disagree on assumptions."

---

### SLIDE 8 — Live Demo  ·  *Ariff*  ·  (1:30)
**On slide**: terminal output of `python3 main.py` (festive + off-peak summaries).

> "Let's run it. Scenario one — festive peak. Watch the summary: Greedy finishes in
> **12 hours 6 minutes** with four stops; Dynamic Programming and A* both find **11
> hours 51 minutes** with only three. Now scenario two — a normal day. Same trip, but
> look — the optimal route *changes*: it now goes via Tapah instead of Ipoh, because
> the 45-minute festive queue is gone. The optimizer is reacting to live conditions,
> not just distance."

---

### SLIDE 9 — Output Description & Insight  ·  *Ariff*  ·  (0:45)
**On slide**: side-by-side route diagrams (festive via Ipoh vs off-peak via Tapah);
the INFEASIBLE safety-check line.

> "Two things to take away. First, Greedy isn't wrong — it's just *worse*, and our
> output quantifies exactly how much: 15 minutes and an extra stop. Second, when we
> start with too little charge, all three correctly return INFEASIBLE rather than a
> dangerous plan. **Iqmal will now prove, formally, why our optimal algorithm is
> trustworthy.**"

---

### SLIDE 10 — Proof of Correctness  ·  *Iqmal*  ·  (1:00)
**On slide**: the loop invariant `I(k)`; "optimal substructure + conservative
quantisation".

> "Thanks, Ariff. Running correctly once isn't a proof — so we proved it. Using
> induction with a loop invariant, we show that after processing each node, our DP
> table holds the true optimum for every battery level. It rests on two properties:
> *optimal substructure* — the best route is built from best sub-routes — and
> *conservative rounding*, which guarantees we never *overstate* the battery, so a
> plan we call safe is genuinely safe."

---

### SLIDE 11 — Complexity Analysis  ·  *Iqmal*  ·  (1:15)
**On slide**: the best/avg/worst table for V, E, S.

> "On efficiency: Greedy is near-linear, `O(E log V)` — cheap but sub-optimal. Dynamic
> Programming is a tight `theta of (V+E) times S-squared`, where S is the number of
> battery levels — provably optimal, but it scales *quadratically* with battery
> resolution, the classic curse of dimensionality. A* has the same worst case but, with
> our admissible heuristic, explores far fewer states on average. *In space, Greedy is
> the lightest; DP needs the full node-by-battery table.*"

---

### SLIDE 12 — Findings & Conclusion  ·  *Iqmal*  ·  (0:45)
**On slide**: "DP = benchmark · Greedy = baseline · A* = deployable"; thank-you + Q&A.

> "So our findings: use Dynamic Programming as the gold-standard benchmark, Greedy as a
> fast baseline, and A* as the deployable engine — it's optimal *and* fast. The clincher
> is that DP and A* agreed on the exact same answer in every test, cross-validating our
> optimality claim. We turned one Hari Raya road trip into a rigorous, NP-hard
> optimisation problem — and solved it three ways. Thank you. We're happy to take
> questions."

---

## Delivery Tips (max out the presentation rubric)

- **Critical thinking signals**: each speaker states a *trade-off*, not just a fact
  (Greedy fast-but-worse; DP optimal-but-heavy; A* best-of-both). Examiners reward this.
- **One insight per section**: range-anxiety framing (Radhi), the shared pruning gate
  (Dhiyauddin), the route-switch under changing queues (Ariff), DP=A* cross-validation
  (Iqmal).
- **Transitions**: the bold handoff sentences hand the next speaker their cue —
  rehearse the seam, not just your own part.
- **Clock discipline**: practise to 12:30; that leaves slack to land inside 10-15 even
  if Q&A starts early. If running long, drop the italicised deep-dive lines.
- **Demo safety net**: pre-capture the console output as an image on slides 8-9 in case
  the live run fails — never debug live.
