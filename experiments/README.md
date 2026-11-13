# Experiments

One script per experiment. Each script writes a markdown table to `results/tables/` and figures to `results/figures/`, uses fixed random seeds, and starts with a docstring that states the question and, for the later experiments, **the choices fixed before the first run** (pre-registration). Run everything the report uses with

```bash
bash experiments/run_all.sh --report     # tests and v0, E1 to E3, E6, E7, E8a to E8g; times in results/run_all_times.txt
bash experiments/run_all.sh --quick      # tests and the fast scripts only
bash experiments/run_all.sh              # also the exploratory scripts (hours)
```

The parallel scripts use 8 worker processes (one BLAS thread each). Runtimes are for an 8-core laptop without power throttling.

## Experiments of the report

| ID | Script | Question | Runtime |
|---|---|---|---|
| V0 | `v0_validation_report.py` | Does the model match published numbers and flight data? | seconds |
| E1 | `e1_equilibrium.py` | Relaxed hover against the paper; thrust-ratio sweep | seconds |
| E2 | `e2_structure.py` | Eigenvalues, controllability, observability by sensor set | seconds |
| E3 | `e3_lqr.py` | LQR designs, delay margins, nonlinear check | about 15 s |
| E6 | `e6_koopman_prediction.py` | Analytical vs full-state vs residual EDMDc: multi-step error, data efficiency, held-out plant | about 2.5 min |
| E7 | `e7_mpc_closed_loop.py` | LQR vs analytical MPC vs residual Koopman MPC: steady altitude error, capture | about 3 min |
| E8a | `e8_offset_free.py` | Offset-free MPC variants and LQR with integrator against the residual MPC | about 9 min |
| E8a diag. | `e8a_diag_state_capture.py` | One diagnostic run: why the state-model offset-free MPC fails the capture | seconds |
| E8b | `e8_full_koopman_mpc.py` | MPC on the full-state Koopman model | about 18 min |
| E8c | `e8c_adaptive_residual.py` | Online adaptation of the residual by RLS | about 25 min |
| E8d | `e8d_spinup_residual.py` | Residual trained on capture transients | about 15 min |
| E8e | `e8e_mpc_tuning.py` | MPC horizon and weights for the capture | about 1 h |
| E8f | `e8f_ablations.py` | Dictionary degree, ridge, sampling period, sensor noise | about 1.5 h |
| E8g | `e8g_realistic_plant.py` | Air-relative thrust and quadratic drag in the truth plant (plants A+ and B+) | about 12 min |

## Helpers

- `shared.py`: builds a controller from a picklable spec, and runs the steady-error and capture protocols on any truth plant (used by E8c to E8g).
- `run_all.sh`: runs the tests and the experiments in dependency order and logs the time of each step.
- `audit_numbers.py`: lists the numbers of a `.tex` file that cannot be found in `results/` (`.venv/bin/python experiments/audit_numbers.py FILE.tex`).

## Exploratory scripts (not in the report)

`e4_delay_sweep.py`, `e5_first_certificate.py`, `e9a_handover.py`, `e9b_robust_certificate.py`, `e9c_gain_synthesis.py`, `e9d_certified_delay.py` and `e10c_mpc_certificate.py` were run; `e9e_early_handover.py`, `e10a_tightness.py` and `e10b_trade_study.py` are pre-registered but were not run. Their outcomes are summarised in the "Exploratory work not in the submission" section of the root README. `e9d_certified_delay.py` and `e10a_tightness.py` read `results/certificates/e9c_designs.npz` (written by E9c) and the E9d table.

## Reading a result

Every table in `results/tables/` begins with a sentence describing the set-up; the details and the fixed choices are in the docstring of the script with the same name. A first run that had to be changed is kept next to the final table under a name containing `run1`.
