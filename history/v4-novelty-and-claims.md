# Novelty Assessment and Claim Boundaries (v4)

Date of searches: 2026-10-09. The full query list is in `../literature/search-log.md`, and per-paper notes are in `../literature/notes/`.

## 1. How the topic was narrowed

| Version | Core idea | Why it was dropped or narrowed |
|---|---|---|
| v1 (proposal PDF) | Residual Koopman (EDMDc) on top of the Mueller–D'Andrea spin model, for MPC | Mainly an ML contribution; weak fit for EE650; the residual-Koopman pattern already exists (Todde 2026, RK-MPC, Bruder 2025) |
| v2 | Same, re-framed around the "region of validity" of the linear predictor | Same course-fit problem |
| v3 | Certified recoverable set (LMI ellipsoid) for relaxed-hover LQR + detection-delay map + observability | Good course fit, but **a local certificate at r_eq cannot contain hover-onset states** (yaw rate 0 vs ~20 rad/s), so the headline would have missed the main scenario. Claims were also spread over four separate items |
| **v4 (this)** | **Certified fault-detection-delay budget τ\***, enabled by a **capture set that is robust over the spin-up yaw rate** | Single headline question; fixes the v3 locality gap; every tool is a course tool |

## 2. What exists (do not claim)

| Topic | Prior work | Consequence |
|---|---|---|
| Relaxed hover, controllability, LQR at the spinning equilibrium | Mueller & D'Andrea 2014/2016 | Model and baseline controller. Controllability is reproduced, not claimed |
| Linear robust control at a spinning working point | Lanzon, Freddi & Longhi, JGCD 2014 (feedback linearization + H∞ loop shaping) | Another linear baseline; no saturation ROA, no detection delay (abstract-level check; full text paywalled) |
| **LPV control scheduled on yaw rate**, covering the "initial transient after actuator loss" | **Stephan, Schmitt & Fichter, JGCD 2018** | **Scheduling on r is not ours.** We use the LPV structure for *analysis/certification under saturation and detection delay*. **Must read the full paper** to confirm it reports no saturation-aware ROA or delay analysis |
| Recovery from arbitrary attitude/rates | Sun et al. 2020 (QP allocation, Monte Carlo + flight); Nan et al. 2022 (NMPC, Monte Carlo + flight) | Empirical only. Both note that linear controllers break under saturation or large upsets but **do not quantify where** |
| Certified regions for failed quadrotors | Simha et al. 2017 (geometric controller, analytic ROA, fault assumed already detected); Al Lawati & Akhtar 2026 (path invariance; **assumes reliable FDI and instantaneous transition**) | Certificates exist, but **all assume zero detection delay** |
| Detection-delay tolerance | Heli-quad 2020: 180 ms, **empirical** sweep, different vehicle (variable-pitch). Sun et al. 2020 mention FDD delay as a cause of upsets | Only empirical numbers exist |
| Measured detector delays | Multiple-model L1 adaptive FDD (IEEE 2025): 30–130 ms; other detectors ~45 ms; ~0.1 s FDD observation delay noted elsewhere | Supplies the **realistic τ range** our τ\* is compared against |
| Set-theoretic FTC (invariance + reachability for FDI/reconfiguration) | Stoican & Olaru 2013 (book); Seron, De Doná, Olaru; Shin & Belcastro 2006 (performance with detection delay) | **The general method is not new.** We apply it to a structurally hard case: the post-failure equilibrium is a spinning state in different coordinates, reached through a large parameter transient |
| Post-failure motion planning with backward reachability | Aerospace Sci. & Tech. 2024 (UNIST), "Fault tolerant motion planning for a quadrotor subject to complete rotor failure" | Plans *after* the FTC is engaged; not about detection delay |
| Residual Koopman MPC for quadrotors | Todde et al. ICUAS 2026 (read in full) | Healthy flight only, no failure, no guarantees; affects only the optional extension |

## 3. Claims and estimated certainty

These are judgment estimates from the searches, not measurements.

| Claim | Wording to use | Est. chance unpublished | Main risk |
|---|---|---|---|
| **C1** Certified τ\* for complete rotor loss | "To our knowledge, the first certified (rather than simulated) bound on the tolerable fault-detection delay for a quadrotor with complete single-rotor loss" | **~75–80%** | Something similar in paywalled FTC/aerospace venues; Stephan 2018 not yet read |
| **C2** Saturation-aware capture set robust over spin-up yaw rate | "A saturation-aware invariant capture set for the relaxed-hover controller that remains valid from hover onset" | **~55–65%** | Stephan 2018 may contain stability-region analysis; standard LMI techniques make it look routine |
| **C3** τ\* trade study, in particular the effect of the *healthy* controller | "How healthy-mode tuning, thrust margin, motor lag and sampling trade against the delay budget" | ~80% for the healthy-controller dependence | Low risk; possibly seen as a parameter sweep |
| C4 Tightness vs Monte Carlo | Validation, not claimed as novel | n/a | n/a |
| C5 Failure-aware healthy-controller tuning (stretch) | "Tuning the healthy controller to enlarge the delay budget" | ~80% | Stretch; only if time allows |

**Overall for a course project:** the question is new, the answer is useful (a detector specification), and the methods are squarely EE650. The main defensibility risk is the "known tools" criticism, which is answered by the problem structure (switched coordinates + spin-up transient + saturation) and the design insight (C3).

## 4. Must-do checks before submission

1. **Read Stephan, Schmitt & Fichter (JGCD 2018)** via the IIT Kanpur library (AIAA). If it already gives a saturation-aware region of attraction over r, narrow C2 to "used for delay certification" and keep C1/C3.
2. **Read Lanzon, Freddi & Longhi (JGCD 2014).** Check whether they analyse any switching or detection delay.
3. **Re-run the core searches** in `../literature/search-log.md` the week before submission, adding "dwell time" and "switching delay" variants.
4. Get the full text of the multiple-model L1 FDD paper (IEEE 11235993) to cite exact detector-delay numbers.
5. Wording rule: always "not found in our search", never "first ever" without the qualifier.
