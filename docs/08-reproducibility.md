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
.venv/bin/python -m pytest -q          # 123 tests (122 pass, 1 expected failure), about 1 min
bash experiments/run_all.sh --report   # v0, E1 to E3, E6, E7, E8a to E8g; per-step times in results/run_all_times.txt
bash experiments/run_all.sh            # also the exploratory scripts (hours; E9e, E10a, E10b were never run)
cp results/figures/*.png docs/report/figures/ && (cd docs/report && tectonic -X compile report.tex)
```

Every script can also be run on its own, for example `.venv/bin/python experiments/e6_koopman_prediction.py`. What each script does is listed in `experiments/README.md`.

## Determinism
- Every random draw uses `numpy.random.default_rng(seed)` with a seed written in the script (E6 seeds 11, 12, 13, 21; E7 and E8 seed 0 and the E6 training seed; the seeds of E8c to E8g are in their script docstrings).
- Success criteria and thresholds are constants in `rotorfail/metrics.py`, fixed before the sweeps were run.
- Parallel runs (`ProcessPoolExecutor`) only distribute independent simulations; results do not depend on the number of workers.
- Small numerical differences can come from the QP solvers (OSQP and Clarabel versions); timing lines differ between machines.

## Where the numbers in documents come from
Every number quoted in `proposal/`, `progress/`, `docs/` and the report should be traceable to a file in `results/tables/`. If an experiment is re-run, update the documents and the report from the regenerated tables.
