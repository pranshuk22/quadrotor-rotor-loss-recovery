#!/usr/bin/env bash
# Runs the tests and every experiment in dependency order, records the wall-clock time of each step, and copies the
# figures to the report and the paper. Usage (from the repository root, with the virtual environment created):
#   bash experiments/run_all.sh            # full run (hours on 8 cores)
#   bash experiments/run_all.sh --quick    # tests and the fast experiments only (v0, E1 to E3)
#   bash experiments/run_all.sh --report   # tests and every experiment the report uses (v0, E1 to E3, E6, E7, E8a to E8g)
# The ordering matters: E9c writes results/certificates/e9c_designs.npz (read by E9d), E9d writes results/tables/e9d_certified_delay.csv
# (read by E10a).
set -euo pipefail
PY=.venv/bin/python
LOG=results/run_all_times.txt
: > "$LOG"
step() {
  local t0=$(date +%s)
  echo ">> $*"
  "$@"
  local t1=$(date +%s)
  echo "$(( t1 - t0 )) s  $*" | tee -a "$LOG"
}
step $PY -m pytest -q
step $PY experiments/v0_validation_report.py
step $PY experiments/e1_equilibrium.py
step $PY experiments/e2_structure.py
step $PY experiments/e3_lqr.py
if [ "${1:-}" = "--report" ]; then
  step $PY experiments/e6_koopman_prediction.py
  step $PY experiments/e7_mpc_closed_loop.py
  step $PY experiments/e8_offset_free.py
  step $PY experiments/e8a_diag_state_capture.py
  step $PY experiments/e8_full_koopman_mpc.py
  step $PY experiments/e8c_adaptive_residual.py
  step $PY experiments/e8d_spinup_residual.py
  step $PY experiments/e8e_mpc_tuning.py
  step $PY experiments/e8f_ablations.py
  step $PY experiments/e8g_realistic_plant.py
elif [ "${1:-}" != "--quick" ]; then
  step $PY experiments/e4_delay_sweep.py
  step $PY experiments/e5_first_certificate.py
  step $PY experiments/e6_koopman_prediction.py
  step $PY experiments/e7_mpc_closed_loop.py
  step $PY experiments/e8_offset_free.py
  step $PY experiments/e8a_diag_state_capture.py
  step $PY experiments/e8_full_koopman_mpc.py
  step $PY experiments/e8c_adaptive_residual.py
  step $PY experiments/e8d_spinup_residual.py
  step $PY experiments/e8e_mpc_tuning.py
  step $PY experiments/e8f_ablations.py
  step $PY experiments/e8g_realistic_plant.py
  step $PY experiments/e9a_handover.py
  step $PY experiments/e9b_robust_certificate.py
  step $PY experiments/e9c_gain_synthesis.py
  step $PY experiments/e9d_certified_delay.py
  step $PY experiments/e10a_tightness.py
  step $PY experiments/e10b_trade_study.py
  step $PY experiments/e10c_mpc_certificate.py
fi
mkdir -p docs/report/figures
cp results/figures/*.png docs/report/figures/
if [ -d docs/paper ]; then mkdir -p docs/paper/figures && cp results/figures/*.png docs/paper/figures/; fi
echo "total: $(awk '{s+=$1} END {print s}' "$LOG") s"
