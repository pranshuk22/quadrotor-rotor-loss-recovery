# 8. Reproducibility

## Environment
- Python 3.12; dependencies pinned in `requirements.txt` (NumPy, SciPy, Matplotlib, python-control, CVXPY with Clarabel/SCS/OSQP, pytest).
- LaTeX report: built with Tectonic (`/opt/homebrew/bin/tectonic`); any TeX Live with `latexmk` also works.

```bash
cd rotor-failure-project
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run everything

```bash
.venv/bin/python -m pytest -q                          # 46 tests + 1 expected failure, ~20 s
.venv/bin/python experiments/v0_validation_report.py   # model vs papers
.venv/bin/python experiments/e1_equilibrium.py
.venv/bin/python experiments/e2_structure.py
.venv/bin/python experiments/e3_lqr.py
.venv/bin/python experiments/e4_delay_sweep.py         # several minutes, 8 processes
.venv/bin/python experiments/e5_first_certificate.py   # ~8 min, 8 processes
.venv/bin/python experiments/e6_koopman_prediction.py  # ~2.5 min
.venv/bin/python experiments/e7_mpc_closed_loop.py     # ~3 min, 8 processes
cp results/figures/*.png docs/report/figures/ && (cd docs/report && tectonic -X compile report.tex)
```

## Determinism
- Every random draw uses `numpy.random.default_rng(seed)` with a seed written in the script (E4 Monte Carlo seeds 0–39; E5 none; E6 seeds 11, 12, 13, 21; E7 seed 0 and the E6 training seed).
- Success criteria and thresholds are constants in `rotorfail/metrics.py`, fixed before the sweeps were run.
- Parallel runs (`ProcessPoolExecutor`) only distribute independent simulations; results do not depend on the number of workers.
- Small numerical differences can come from the LMI and QP solvers (Clarabel, SCS, OSQP versions); certificate values are reported to 2–3 digits.

## Where the numbers in documents come from
Every number quoted in `proposal/`, `progress/`, `docs/` and the report should be traceable to a file in `results/tables/`. If an experiment is re-run, update the documents and the report from the regenerated tables.
