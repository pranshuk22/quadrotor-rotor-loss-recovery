# Literature Review: Complete Rotor Loss in Quadrotors

Organized by theme. "Read depth": **F** = full text read, **P** = partial / grep of full text, **A** = abstract or secondary description only. Per-paper notes are in `notes/`, and local PDFs (open-access only) are in `papers/`.

## A. Physics of complete rotor loss and the relaxed hover

| Paper | Depth | Key content | Relevance |
|---|---|---|---|
| Mueller & D'Andrea, ICRA 2014; IJRR 2016 "Relaxed hover solutions" | F (§1–5, per v3 notes) | Spinning equilibrium; reduced-attitude LTI model in a body-fixed frame; controllability conditions; LQR + cascaded position loop; motor lag 15 ms; hardware. Simulations start *at* hover attitude with no failure transient; spin-up done open-loop before the LQR is enabled. Lists estimation and mode transitions as future work | Model + baseline controller. Leaves the transition/delay question open → [notes/mueller-dandrea.md](notes/mueller-dandrea.md) |

## B. Linear / LPV controllers for the failed vehicle

| Paper | Depth | Key content | Relevance |
|---|---|---|---|
| Lanzon, Freddi & Longhi, JGCD 2014 | A | Robust feedback linearization; gives up yaw; H∞ loop shaping around a working point with zero roll/pitch and constant yaw rate | Linear baseline; must read |
| **Stephan, Schmitt & Fichter, JGCD 2018** (doi:10.2514/1.G003441) | A (via citations) | **LPV control with yaw rate as scheduling parameter**; aligns thrust axis; guarantees performance through the initial transient after actuator loss; outdoor flights | **Closest work to C2.** Paywalled; **must read** |
| Sun et al., T-RO 2020 (INDI, two opposing rotors; arXiv:2002.07837) | P | INDI handles aerodynamic uncertainty at > 8 m/s; LQR comparison fails in wind tunnel | Shows the limits of fixed-gain LQR → [notes/sun2020-indi.md](notes/sun2020-indi.md) |

## C. Large-disturbance / upset recovery (empirical)

| Paper | Depth | Key content | Relevance |
|---|---|---|---|
| Sun, Baert, Strack van Schijndel, de Visser, 2020 (arXiv:2002.09425) | P | QP allocation with an "undesirable angular velocity" constraint; attainable moment set; 200-run Monte Carlo; throw tests. States that FDD delay can leave the vehicle upside-down before FTC triggers, and that linear FTCs "could fail" from linearization violation/saturation | **Motivates C1 directly**; empirical only → [notes/sun2020-upset.md](notes/sun2020-upset.md) |
| Nan, Sun, Foehn, Scaramuzza, RA-L 2022 (arXiv:2109.12886) | P | NMPC with per-rotor thrust limits; recovers from flips; criticises linear/cascaded methods that ignore input constraints | Nonlinear upper reference; no delay analysis → [notes/nan2022-nmpc.md](notes/nan2022-nmpc.md) |

## D. Certified / guaranteed results for failed quadrotors

| Paper | Depth | Key content | Relevance |
|---|---|---|---|
| Simha, Vadgama & Raha 2017 (arXiv:1704.00327) | F (per v3 notes) | Geometric controller with an analytic ROA; fault assumed already detected; positive-thrust only in simulation | Certified regions exist, with **zero delay** → [notes/simha2017.md](notes/simha2017.md) |
| Al Lawati & Akhtar 2026 (arXiv:2609.23918) | P (assumptions checked in text) | Quasi-static feedback; path invariance; local exponential convergence. **"We assume ... a reliable FDI module and an instantaneous transition"** | Guarantees with **zero delay** → [notes/allawati2026.md](notes/allawati2026.md) |
| Fault-tolerant motion planning, Aerosp. Sci. Tech. 2024 (UNIST) | A | Backward-reachability-based planner after failure; closed-form trajectories trackable by the FTC | Post-engagement planning; not delay |

## E. Detection delay

| Paper | Depth | Key content | Relevance |
|---|---|---|---|
| Kulkarni, Sundararajan & Sundaram, Heli-quad (arXiv:2011.07529) | P | Variable-pitch cambered-propeller quad; **max tolerable FDI delay 180 ms found empirically** by simulation sweeps | Only quantitative delay-tolerance figure found; different vehicle → [notes/heliquad2020.md](notes/heliquad2020.md) |
| Multiple-model L1 adaptive FDD and recovery, IEEE 2025 (doc 11235993) | A | Detection in 30–130 ms with no missed detections; ~45 ms reported | Realistic τ range |
| Other FDD reports | A | ~0.1 s observation delay from FDD noted as degrading AFTC | Realistic τ range |

## F. General set-theoretic FTC methodology

| Work | Depth | Key content | Relevance |
|---|---|---|---|
| Stoican & Olaru, *Set-Theoretic FTC in Multisensor Systems*, Wiley 2013; Olaru, De Doná, Seron, Stoican 2010; Stoican et al. 2012 | A | Invariant/reachable sets for FDI and reconfiguration | **The general method is known.** Cite it as the foundation |
| Shin & Belcastro 2006 (performance analysis of FTC with detection delay, NASA) | A | Induced-norm bounds as a function of detection time | General delay analysis, not rotor loss |
| Hu & Lin 2001; Boyd et al. 1994 | n/a | Saturation-aware invariant ellipsoids; LMI toolbox | Core tools for C |

## G. Koopman (relevant only to the optional extension)

| Paper | Depth | Key content | Relevance |
|---|---|---|---|
| Todde, Martini, Rizzo & Valavanis, ICUAS 2026 | **F** | Residual MLP on an analytical Koopman lifted model; healthy trajectory tracking under ±30% parameter mismatch; residual applied as a measured disturbance outside the QP; **no failure, no guarantees**; future work: "structured uncertainty bounds ... formal robustness guarantees" | Does not overlap with v4 → [notes/todde2026.md](notes/todde2026.md) |
| Narayanan & Vaidya 2026 RK-MPC (arXiv:2604.04221); Bruder et al. IJRR 2025; Fu et al. 2025; SE(3) Koopman-MPC (Narayanan et al. 2023); Martini et al. ICUAS 2025 | A | Residual Koopman in other domains; Koopman MPC for healthy quadrotors | Background for the extension |

## H. Gap synthesis

1. **Every guarantee-bearing paper assumes the failure controller starts at t = 0** (Simha 2017; Al Lawati 2026), or starts its simulations at the equilibrium (Mueller & D'Andrea).
2. **Every delay-tolerance number is empirical** (Heli-quad 180 ms), and the upset-recovery papers name detection delay as a cause of failure without quantifying it (Sun 2020).
3. **Linear failure controllers are known to break under saturation and large upsets** (Sun 2020; Nan 2022; Sun T-RO 2020), but no one has certified *where* they work.
4. The set-theoretic FTC toolbox exists but has not been applied to the spinning, coordinate-switching rotor-loss problem.

→ v4 question: **a certified fault-detection-delay budget τ\*** (see `../proposal/proposal.md`).
