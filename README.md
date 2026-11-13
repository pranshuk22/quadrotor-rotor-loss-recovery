# Quadrotor Rotor-Loss Recovery

Fault-tolerant control of a quadrotor after the complete loss of one rotor. Course project for **EE650: Basics of Modern Control Systems** (simulation only).

After a rotor fails, a quadrotor can no longer hover level. Its only steady state is a constant spin about a tilted body axis, the *relaxed hover* of Mueller and D'Andrea. The physics model of this state is good but not exact. This project asks whether a Koopman (EDMDc) model of only the error of the physics model, used inside a convex MPC, predicts and controls the failed vehicle better than the physics model alone or a Koopman model of the full dynamics.

## Team

| Name | Roll number |
|---|---|
| Pranshu Kumar | 220799 |
| Mudita Jain | 220675 |
| Prashant Gupta | 220803 |
| Aarush Singh Kushwaha | 230019 |

## Key results

| Topic | Result |
|---|---|
| Model validation | Reproduces the published two-rotor and three-rotor-loss equilibria of Mueller and D'Andrea (ICRA 2014) to every digit, and five hover solutions of their IJRR 2016 model within 4%. At the thrust used in flight, the spin-up time is within about 4% of the flight data. |
| Prediction | On the training plant, the residual Koopman model has the lowest multi-step error from 100 ms to 1 s (normalized RMSE at 1 s: 0.64, against 0.91 for full-state EDMDc and 7.1 for the analytical model) and needs less data. It does not generalize to an unseen plant; online adaptation helps only partly. |
| Control | A residual-corrected MPC reduces a steady altitude error caused by model mismatch by one third (0.29 m to 0.19 m); the QP solver needs under 1 ms per step. An offset-free MPC (disturbance on all physical states) removes the error but fails the capture, while an LQR with integrator reduces it to at most 0.024 m and keeps the LQR's capture performance (the best trade-off tested), all without learning; an MPC on the full-state Koopman model is stable near the hover but fails the capture earlier. |

Full details are in the [detailed report](docs/report/report.pdf) and the [documentation](docs/README.md).

## Quick start

Requires Python 3.12.

```bash
git clone https://github.com/pranshuk22/quadrotor-rotor-loss-recovery.git
cd quadrotor-rotor-loss-recovery
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python -m pytest -q                          # 123 tests (122 pass, 1 expected failure), about 1 min
.venv/bin/python experiments/v0_validation_report.py   # model against published results
bash experiments/run_all.sh --report                   # every experiment the report uses
```

Each experiment script writes a table to `results/tables/` and figures to `results/figures/`; all random seeds are fixed in the scripts. What is in each folder and how the code fits together is explained in [`rotorfail/README.md`](rotorfail/README.md) (the Python package), [`experiments/README.md`](experiments/README.md) (the experiment scripts) and [`tests/README.md`](tests/README.md) (the tests).

| Script | Purpose | Runtime |
|---|---|---|
| `experiments/v0_validation_report.py` | Model against three papers and flight data | seconds |
| `experiments/e1_equilibrium.py` | Relaxed-hover equilibrium | seconds |
| `experiments/e2_structure.py` | Controllability and observability | seconds |
| `experiments/e3_lqr.py` | LQR designs and delay margins | about 15 s |
| `experiments/e6_koopman_prediction.py` | Analytical, full-state and residual EDMDc predictors | about 2.5 min |
| `experiments/e7_mpc_closed_loop.py` | LQR, analytical MPC and residual Koopman MPC | about 3 min |
| `experiments/e8_offset_free.py` (E8a) | Offset-free MPC variants and LQR with integrator | about 9 min |
| `experiments/e8_full_koopman_mpc.py` (E8b) | MPC on the full-state Koopman model | about 18 min |
| `experiments/e8c_adaptive_residual.py` | Online adaptation of the residual | about 25 min |
| `experiments/e8d_spinup_residual.py` | Residual trained on capture transients | about 15 min |
| `experiments/e8e_mpc_tuning.py` | MPC horizon and weights | about 1 h |
| `experiments/e8f_ablations.py` | Dictionary, ridge, sampling period, sensor noise | about 1.5 h |
| `experiments/e8g_realistic_plant.py` | Air-relative thrust and quadratic drag in the truth plant | about 12 min |

## Exploratory work not in the submission

The following experiments were explored while studying how long fault detection may take before recovery is no longer possible. They are in the repository but not in the final report, deck or paper. All outcomes are negative or inconclusive: **no certified detection-delay budget exists** for any configuration tested, and **the state at which the published strategy hands over from its open-loop spin-up to the failure controller cannot be contained in any ellipsoid centred at the relaxed hover**.

| Script and table | What it did and what came out |
|---|---|
| `e4_delay_sweep.py`, `results/tables/e4_delay_sweep.md` | Probability of a safe recovery against detection delay for the published strategy: below 0.9 from 12 ms, below 0.5 from 19 ms |
| `e5_first_certificate.py`, `e5_first_certificate.md` | First saturation-aware LMI certificate (linear model): covers 22 % of the way to the state after a failure |
| `e9a_handover.py`, `e9a_handover.md` | State at the hand-over: far from the equilibrium; none of 1312 hand-over states inside the E5 ellipsoid |
| `e9b_robust_certificate.py`, `e9b_robust_certificate.md` | Quasi-LPV certificate over a range of spin rates: verified, but tiny once the nonlinear remainder is bounded; analytic ceiling below 1 |
| `e9c_gain_synthesis.py`, `e9c_gain_synthesis.md` | Capture-gain synthesis and hand-over thresholds: every synthesised gain rejected (closed-loop poles of 216 to 47,700 rad/s) |
| `e9d_certified_delay.py`, `e9d_run1_coverage_pinv.md` | Reachable hand-over sets and containment: the centre of the hand-over set is outside every certificate, so no certified delay budget; the coverage statistics of this run are invalid and were not re-run |
| `e10c_mpc_certificate.py`, `e10c_mpc_certificate.md` | Certificate for the residual-MPC loop: not certifiable; all 1000 nonlinear runs left the ellipsoid |

The scripts `e9e_early_handover.py` (confirmation on new seeds that a lower hand-over threshold extends the tolerated delay), `e10a_tightness.py`, `e10b_trade_study.py` and the corrected coverage re-run of `e9d_certified_delay.py` are pre-registered and committed but **were not run**. The finding of E9c that the published LQR with a hand-over threshold of 6 rad/s was safe up to 80 ms on seeds 1000 to 1039 is therefore unconfirmed. The supporting code is `rotorfail/lpv.py`, `rotorfail/reach.py`, `rotorfail/mpc_cert.py` and the robust and synthesis functions of `rotorfail/certify.py`. The last version of the report that contained this material is commit `b58ee00`.

## Repository layout

```
rotorfail/     Python package: dynamics, trim solvers, linear models, controllers,
               Koopman models, MPC (see rotorfail/README.md)
experiments/   One script per experiment, shared helpers, run_all.sh (see experiments/README.md)
tests/         Physics, published-result and unit tests (see tests/README.md)
results/       Generated tables and figures
docs/          Documentation, detailed report (LaTeX), short paper and slide deck
proposal/      Project proposal, novelty assessment and work plan
progress/      Status, task list and review reports
literature/    Literature review, search log and paper notes
history/       Earlier versions of the proposal
```

## Documentation

- [Detailed report](docs/report/report.pdf) (LaTeX source in `docs/report/`)
- [Slide deck](docs/deck/final-presentation.pdf) ([PPTX](docs/deck/final-presentation.pptx))
- [Short paper](docs/paper/paper.pdf)
- [Technical documentation](docs/README.md): model and equations, validation, methods, experiments, code reference and reproducibility
- [Project proposal](proposal/proposal.md)

## Main references

- M. W. Mueller and R. D'Andrea, "Stability and control of a quadrocopter despite the complete loss of one, two, or three propellers," ICRA 2014.
- M. W. Mueller and R. D'Andrea, "Relaxed hover solutions for multicopters," IJRR, 2016.
- M. Korda and I. Mezić, "Linear predictors for nonlinear dynamical systems: Koopman operator meets model predictive control," Automatica, 2018.
- E. Todde, S. Martini, A. Rizzo and K. P. Valavanis, "Residual Koopman-based model predictive control of quadrotors," ICUAS 2026.
- I. Schimperna, L. Bold and K. Worthmann, "Offset-free nonlinear MPC with Koopman-based surrogate models," arXiv:2504.10954, 2025.

The full bibliography is in [`docs/report/references.bib`](docs/report/references.bib).

## License

Code (`rotorfail/`, `experiments/`, `tests/`, `docs/deck/build_pptx.js`) is released under the [MIT License](LICENSE). Documentation, report, slides and other written material are released under [CC BY 4.0](LICENSE-docs). Paper PDFs are not included; see [`literature/papers/README.md`](literature/papers/README.md) for links.
