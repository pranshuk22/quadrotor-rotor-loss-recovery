# Novelty Assessment and Claim Boundaries (v5: both research questions)

Date of searches: 2026-10-09/10. The full query list is in `../literature/search-log.md`, and per-paper notes are in `../literature/notes/`. The v4-only version is in `../history/v4-novelty-and-claims.md`.

## 1. How the topic evolved

| Version | Core idea | Outcome |
|---|---|---|
| v1 (proposal PDF, presented) | Residual Koopman (EDMDc) on top of the Mueller–D'Andrea spin model, for MPC | **Kept as RQ1** |
| v2 | Same, re-framed around the "region of validity" of the linear predictor | Merged into RQ1 hypotheses |
| v3 | Certified recoverable set (LMI) for relaxed-hover LQR + delay map + observability | A local certificate cannot contain hover onset → refined into v4 |
| v4 | Certified fault-detection-delay budget τ\*, capture set robust over the spin-up yaw rate | **Kept as RQ2** |
| **v5 (current)** | RQ1 + RQ2 in one proposal: residual Koopman MPC is a capture controller; τ\* is the yardstick, and the LMI layer supplies the guarantees residual-Koopman work lacks | n/a |

## 2. RQ1 (residual Koopman MPC): what exists, do not claim

| Area | Prior work found | Implication |
|---|---|---|
| Complete-rotor-loss physics/control | Mueller & D'Andrea 2014; Nan et al. 2022 NMPC (arXiv 2109.12886); INDI FTC (arXiv 2002.07837) | Strong non-learning baselines |
| RL for rotor failure | arXiv 2109.10488, 2002.11564, 2503.02649 | Learned *policies*, not learned MPC prediction models |
| Koopman for quadrotors | SE(3) Koopman-MPC (Narayanan et al. 2023); Martini et al. analytical Koopman MPC (ICUAS 2025); Deep Koopman MPC (arXiv 2508.13795) | Koopman MPC for quadrotors is established |
| Koopman FTC | Bakhtiaridoust et al. 2024 (IET CTA); IEEE 10773232; Koopman FDI (J. Intell. Robot. Syst. 2024) | **Loss of effectiveness only**; all rotors still active |
| Residual Koopman MPC | Todde et al. ICUAS 2026 (healthy quadrotor, read in full); RK-MPC quadrupeds (arXiv 2604.04221); vehicle dynamics (Fu et al. 2025); soft arm (Bruder et al. 2025) | **The residual-Koopman pattern is not new** |
| Nominal + learned residual MPC | GP-MPC (arXiv 2102.05773); Neural-MPC (arXiv 2203.07747) | Baselines to mention |

## 3. RQ2 (delay budget): what exists, do not claim

| Topic | Prior work | Consequence |
|---|---|---|
| Relaxed hover, controllability, LQR at the spinning equilibrium | Mueller & D'Andrea 2014/2016 | Reproduced, not claimed |
| Linear robust control at a spinning working point | Lanzon, Freddi & Longhi, JGCD 2014 | Linear baseline; full text not yet read |
| **LPV control scheduled on yaw rate** | **Stephan, Schmitt & Fichter, JGCD 2018** | **Scheduling on r is not ours.** We use the LPV structure for certification under saturation and detection delay. **Must read** |
| Recovery from arbitrary attitude/rates | Sun et al. 2020; Nan et al. 2022 | Empirical only; linear controllers' failure region not quantified |
| Certified regions for failed quadrotors | Simha et al. 2017; Al Lawati & Akhtar 2026 | **Assume zero detection delay** |
| Detection-delay tolerance | Heli-quad (180 ms, empirical, different vehicle) | Only empirical numbers exist |
| Measured detector delays | Multiple-model L1 FDD (IEEE 2025): 30–130 ms | Realistic τ range |
| Set-theoretic FTC | Stoican & Olaru 2013; Shin & Belcastro 2006 | General method known; credit it |

## 4. Claims and estimated certainty (judgment from the searches, not measurements)

| Claim | Wording to use | Est. chance unpublished | Main risk |
|---|---|---|---|
| **RQ1-a** Residual Koopman model built on the M&D spinning-equilibrium model, in the complete-loss regime | "We did not find residual Koopman modeling applied to the complete-rotor-loss, spinning-equilibrium regime" | ~85–90% | Paywalled work; the pattern itself is known |
| **RQ1-b** Comparison of analytical / full-state / residual predictors and MPCs for the failed vehicle, incl. full-state EDMDc instability in this regime | "A controlled comparison in the failed regime" | ~85% | Low novelty per se; value is in the measured results |
| **RQ2-C1** Certified maximum τ\* for complete rotor loss | "To our knowledge, the first certified maximum tolerable detection delay for complete rotor loss that accounts for thrust saturation and the drift of the undetected phase; it extends stability analyses with a fixed detection delay (Başak 2015, 2018)" | ~50–60% | Başak & Prempain (ECC 2015) certify stability for a given delay in a linear model; Stephan 2018 and Qi 2016 unread |
| **RQ2-C2** Saturation-aware capture set robust over spin-up yaw rate | "A saturation-aware invariant ellipsoid for the relaxed-hover controller, robust over the spin-up yaw rate, used as the capture target of a detection-delay budget" | ~45–55% | LPV synthesis on the yaw rate (Stephan 2018) and SOS recoverable sets at the relaxed hover (Qi et al. 2016) exist |
| **RQ2-C3** τ\* trade study, incl. healthy-controller and capture-controller dependence (LQR vs analytical MPC vs residual-Koopman MPC) | n/a | ~80% | Could be seen as a parameter sweep |
| **Link** Capture certificate for the residual-Koopman MPC loop, using a bound on the true plant mismatch and an MPC terminal-set argument | "Capture guarantees for a residual-Koopman controller of the failed vehicle" | ~70% | d_max is not a bound on the true mismatch; the constrained MPC needs more than the Hu–Lin conditions; may be very conservative |

## 5. What the first results already say (presentation 1)

- RQ1: from 100 ms on, the residual predictor beats the analytical and full-state predictors on the training mismatch family (E6). It **does not generalize** to an unseen family, and **static** training on randomized vehicles helps there only up to about 100 ms while hurting on the training family. That is a limitation to report and a reason for online adaptation.
- RQ1: residual-Koopman MPC cuts the steady altitude bias by 32% on the training family and on 5 of 6 test plants, but increases it by 47% on one held-out variant (E7).
- RQ2: in simulation, the published recovery strategy is safe with probability above 0.9 only up to about 12 ms of detection delay, and below 0.5 beyond 19 ms (E4, flight spin-up thrust). The LTI certificate covers 22% of the way to hover onset (E5); the LQR fails only at spin rates ≤ 4.8 rad/s.

## 6. Must-do checks before the final report

1. Read **Stephan, Schmitt & Fichter (JGCD 2018)** and **Lanzon, Freddi & Longhi (JGCD 2014)**.
2. Done: "Lee et al. 2024" is correct (Lee, Kim, Kim & Bang, ICCAS 2024), and the RK-MPC "unstable within seconds" statement is verified (about 5 s).
3. Re-run the searches in `../literature/search-log.md` before submission.
4. Done: the 30 to 130 ms detector range is from Strack van Schijndel, Sun & de Visser (arXiv:2102.06439); the multiple-model L1 paper (Yang et al., RA-L 2026) reports about 45 ms. Independent novelty check: `../progress/novelty-check.md`.
5. Wording rule: "not found in our search", never "first ever" without the qualifier.
