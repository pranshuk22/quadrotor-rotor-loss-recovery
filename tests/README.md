# Tests

Run all tests from the repository root with `.venv/bin/python -m pytest -q` (123 tests: 122 pass, 1 is an expected failure that documents an inconsistency in a published case; about 1 minute).

| File | Tests | What it checks |
|---|---|---|
| `test_physics.py` | 13 | The simulator against results derived by hand: conservation laws, closed-form solutions, gyroscopic terms, yaw decoupling |
| `test_paper_validation.py` | 20 | The simulator against numbers published by Mueller and D'Andrea (ICRA 2014, IJRR 2016) and Sun et al. (T-RO); the expected failure is the published one-rotor roll equation |
| `test_core.py` | 10 | Equilibria, linearization against finite differences, controllers, sanity of the first certificate |
| `test_koopman_mpc.py` | 7 | Data generation, nominal model, EDMDc fits, MPC; the options of the MPC classes default to the published behaviour |
| `test_offset_free.py` | 11 | Offset-free MPC and the LQR with integrator: target and estimator equations, removal of constant offsets, regression test on a nonlinear plant |
| `test_adaptive.py` | 9 | RLS convergence and tracking, bounded covariance, causality of the adaptive residual, dictionary sizes, sampling-period paths, sensor noise |
| `test_truth_effects.py` | 5 | With the optional air-relative thrust and drag switched off the dynamics are bit-identical to the original code (random states, nominal plant and families A and B); with them on they match `rotorfail/validation.py` |
| `test_lpv.py`, `test_certify_robust.py`, `test_reach.py`, `test_mpc_cert.py` | 8, 8, 28, 4 | Exploratory code (quasi-LPV model, robust certificate and gain synthesis, reachable sets and ellipsoid containment, certificate of the residual-MPC loop), against small systems with known answers |

Tests that need CVXPY solve small problems only. Tests never write to `results/`.
