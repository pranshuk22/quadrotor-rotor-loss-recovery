# EE650 Course Project: Quadrotor Recovery After Complete Rotor Loss

**Proposal (v5):** *Fault-Tolerant Control Under Complete Rotor Loss via Physics-Informed Residual Koopman MPC, with Certified Fault-Detection-Delay Budgets*

- **RQ1 (the presented proposal PDF):** does a residual EDMDc model built on the Mueller–D'Andrea spinning-equilibrium model predict, and control via MPC, better than the analytical model or a full-state Koopman model?
- **RQ2 (added):** a real fault detector needs 30–130 ms to notice a dead rotor. What is the **largest detection delay τ\* with guaranteed recovery**, certified with Lyapunov/LMI tools, and how do the RQ1 controllers change it?

## Results so far (progress presentation 1)

- Simulator and equilibrium **validated** against Mueller & D'Andrea (ICRA 2014): thrusts, spin rate and n_z within 0.5%.
- Structural analysis: both models controllable. After the failure, **gyro + barometer makes the tilt observable**, but only weakly.
- **Empirical delay tolerance of the published recovery strategy ≈ 10 ms** (SAFE in 20/20 runs at 0 ms, 6/20 at 20 ms, 0/20 at 50 ms), against 30–130 ms for real detectors. Cause: the idle thrust of the opposite rotor gives an uncancellable roll acceleration ≥ 10.6 rad/s² during the undetected phase.
- **First saturation-aware LMI certificate**: covers 22% of the way to the hover-onset state, against 70% recovered in nonlinear simulation → an r-robust (LPV) certificate is needed (next phase).
- **RQ1, prediction:** residual EDMDc gives the lowest multi-step error on the training mismatch family (1 s: 0.42 vs full-state 0.70 vs analytical 5.1). Full-state EDMDc has eigenvalues outside the unit circle and falls behind the no-change predictor between 2 and 3 s, as the proposal predicted. Neither learned model generalizes to an unseen mismatch family.
- **RQ1, control:** residual-Koopman MPC cuts the steady altitude bias under mismatch by about 32% (QP ≈ 5 ms).

**Validation:** 45 automated tests (physics invariants + published numbers) and a validation report against 3 papers (ICRA 2014, IJRR 2016, Sun T-RO 2020 Bebop 2) plus their flight data: `results/tables/validation_report.md`. Honest status and caveats: `progress/status.md`.

**Deliverables:** progress report `docs/report/report.pdf` (LaTeX) and slide deck (link in `docs/deck/README.md`). Technical documentation: `docs/README.md`.

Details: `progress/presentation-1-plan.md`, tables in `results/tables/`, figures in `results/figures/`.

## Folder guide

```
rotor-failure-project/
├── README.md
├── docs/              DETAILED DOCS (01–08) · report/ (LaTeX report + PDF) · deck/ (slide deck link + sources)
├── proposal/          proposal.md · novelty-and-claims.md · work-plan.md
├── progress/          status.md (done / not done, setup, validation) · presentation-1-plan.md · task-list.md
├── rotorfail/         Python package
│   ├── params.py        vehicle parameters (M&D 2014 Hummingbird)
│   ├── dynamics.py      nonlinear 6-DOF model, saturation, motor lag, RK4
│   ├── equilibrium.py   healthy hover + relaxed hover (closed form + root find)
│   ├── models.py        healthy (12-state) and failed (7-state) linear models
│   ├── analysis.py      controllability / observability / PBH / Gramians / delay margin
│   ├── control.py       healthy LQR, failure LQR, M&D spin-up strategy, delay supervisor
│   ├── certify.py       saturation-aware invariant ellipsoids (Hu–Lin LMIs, CVXPY)
│   ├── koopman.py       data generation, nominal discrete model, full-state and residual EDMDc
│   ├── mpc.py           linear MPC (OSQP), analytical or residual-Koopman corrected
│   ├── validation.py    independent implementation of the IJRR 2016 general model (cross-check)
│   ├── metrics.py       recovery success criterion (fixed before the sweeps)
│   ├── sim.py           fixed-step simulation with a ZOH controller
│   └── plotting.py      figure style
├── experiments/       v0_validation_report · e1_equilibrium · e2_structure · e3_lqr · e4_delay_sweep · e5_first_certificate · e6_koopman_prediction · e7_mpc_closed_loop
├── results/           tables/ (markdown + csv) · figures/ (png)
├── tests/             test_physics.py · test_paper_validation.py · test_core.py · test_koopman_mpc.py (45 tests)
├── literature/        literature-review.md · search-log.md · notes/ · papers/
└── history/           v1–v4 of the proposal + CHANGELOG
```

## How to run

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q                         # 45 tests, ~20 s
.venv/bin/python experiments/v0_validation_report.py  # seconds: model vs papers
.venv/bin/python experiments/e1_equilibrium.py        # seconds
.venv/bin/python experiments/e2_structure.py          # seconds
.venv/bin/python experiments/e3_lqr.py                # ~15 s
.venv/bin/python experiments/e4_delay_sweep.py        # ~5 min on 8 cores (add --plot-only to redraw from CSV)
.venv/bin/python experiments/e5_first_certificate.py  # ~8 min on 8 cores
.venv/bin/python experiments/e6_koopman_prediction.py # ~2.5 min
.venv/bin/python experiments/e7_mpc_closed_loop.py    # ~3 min on 8 cores
```

## Next
See `progress/task-list.md`. RQ1: full-state Koopman MPC, offset-free MPC baseline, online residual adaptation. RQ2: read Stephan et al. 2018 (novelty gate), then the r-robust capture certificate.

## License
Code (`rotorfail/`, `experiments/`, `tests/`, `docs/deck/build_pptx.js`): MIT, see `LICENSE`. Documentation, report, slides and other written material: CC BY 4.0, see `LICENSE-docs`. Paper PDFs are not included; see `literature/papers/README.md` for links.
