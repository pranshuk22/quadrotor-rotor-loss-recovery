# Quadrotor Rotor-Loss Recovery

Fault-tolerant control of a quadrotor after the complete loss of one rotor. Course project for **EE650: Basics of Modern Control Systems** (simulation only).

After a rotor fails, a quadrotor can no longer hover level. Its only steady state is a constant spin about a tilted body axis, the *relaxed hover* of Mueller and D'Andrea. This project studies how to recover the vehicle into that state reliably:

- **Physics-informed learning for control.** Keep the known model of the spinning vehicle and learn only its mismatch with a Koopman (EDMDc) model. Then use the corrected linear predictor inside a convex MPC.
- **Detection delay.** A fault detector needs time to notice the failure. We study how long detection may take before recovery can no longer be guaranteed, and work towards certifying that limit with Lyapunov and LMI methods.

## Team

| Name | Roll number |
|---|---|
| Pranshu Kumar | 220799 |
| Mudita Jain | 220675 |
| Prashant Gupta | 220803 |
| Aarush Singh Kushwaha | 230019 |

## Key results so far

| Topic | Result |
|---|---|
| Model validation | Reproduces the published two-rotor and three-rotor-loss equilibria of Mueller and D'Andrea (ICRA 2014) to every digit, and five hover solutions of their IJRR 2016 model within 4%. At the thrust used in flight, the spin-up time is within about 4% of the flight data. |
| Prediction | On the training plant, the residual Koopman model has the lowest multi-step error from 100 ms on (normalized RMSE at 1 s: 0.64, against 0.91 for full-state EDMDc and 7.1 for the analytical model) and needs less data. It does not yet generalize to an unseen plant. |
| Control | A residual-corrected MPC reduces a steady altitude error caused by model mismatch by one third (0.29 m to 0.19 m); the QP solver needs under 1 ms per step. |
| Detection delay | In simulation, the published recovery strategy recovers safely with probability above 0.9 only for detection delays up to about 12 ms, and below 0.5 beyond about 19 ms (40 random starts per delay). Fast detectors need 30 to 130 ms. |
| Certification | A first saturation-aware LMI certificate covers 22% of the way from the spinning equilibrium to the state just after a failure in hover; in simulation, every start up to 70% of the way recovers. |

Full details are in the [progress report](docs/report/report.pdf) and the [documentation](docs/README.md).

## Quick start

Requires Python 3.12.

```bash
git clone https://github.com/pranshuk22/quadrotor-rotor-loss-recovery.git
cd quadrotor-rotor-loss-recovery
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python -m pytest -q                          # 46 tests, about 20 s
.venv/bin/python experiments/v0_validation_report.py   # model against published results
.venv/bin/python experiments/e1_equilibrium.py         # relaxed-hover equilibrium
```

| Script | Purpose | Runtime |
|---|---|---|
| `experiments/v0_validation_report.py` | Model against three papers and flight data | seconds |
| `experiments/e1_equilibrium.py` | Relaxed-hover equilibrium | seconds |
| `experiments/e2_structure.py` | Controllability and observability | seconds |
| `experiments/e3_lqr.py` | LQR designs and delay margins | about 15 s |
| `experiments/e4_delay_sweep.py` | Effect of detection delay, Monte Carlo | several minutes |
| `experiments/e5_first_certificate.py` | First LMI certificate against simulation | about 8 min |
| `experiments/e6_koopman_prediction.py` | Analytical, full-state and residual EDMDc predictors | about 2.5 min |
| `experiments/e7_mpc_closed_loop.py` | LQR, analytical MPC and residual Koopman MPC | about 3 min |

Each script writes a table to `results/tables/` and figures to `results/figures/`. All random seeds are fixed.

## Repository layout

```
rotorfail/     Python package: dynamics, trim solvers, linear models, controllers,
               LMI certificates, Koopman models, MPC, validation model
experiments/   One script per experiment (V0, E1 to E7)
tests/         Physics, published-result and unit tests
results/       Generated tables and figures
docs/          Documentation, progress report (LaTeX) and slide deck
proposal/      Project proposal, novelty assessment and work plan
progress/      Status, task list and review reports
literature/    Literature review, search log and paper notes
history/       Earlier versions of the proposal
```

## Documentation

- [Progress report](docs/report/report.pdf) (LaTeX source in `docs/report/`)
- [Slide deck](docs/deck/progress-review.pdf) ([PPTX](docs/deck/progress-review.pptx))
- [Technical documentation](docs/README.md): model and equations, validation, methods, experiments, code reference and reproducibility
- [Project proposal](proposal/proposal.md)

## Main references

- M. W. Mueller and R. D'Andrea, "Stability and control of a quadrocopter despite the complete loss of one, two, or three propellers," ICRA 2014.
- M. W. Mueller and R. D'Andrea, "Relaxed hover solutions for multicopters," IJRR, 2016.
- M. Korda and I. Mezić, "Linear predictors for nonlinear dynamical systems: Koopman operator meets model predictive control," Automatica, 2018.
- E. Todde, S. Martini, A. Rizzo and K. P. Valavanis, "Residual Koopman-based model predictive control of quadrotors," ICUAS 2026.
- T. Hu and Z. Lin, *Control Systems with Actuator Saturation*, Birkhäuser, 2001.

The full bibliography is in [`docs/report/references.bib`](docs/report/references.bib).

## License

Code (`rotorfail/`, `experiments/`, `tests/`, `docs/deck/build_pptx.js`) is released under the [MIT License](LICENSE). Documentation, report, slides and other written material are released under [CC BY 4.0](LICENSE-docs). Paper PDFs are not included; see [`literature/papers/README.md`](literature/papers/README.md) for links.
