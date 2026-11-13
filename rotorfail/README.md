# `rotorfail`: the Python package

Simulator, models, controllers and learning code for a quadrotor that has lost one rotor (rotor 4). Everything is plain NumPy/SciPy; convex problems use CVXPY. Run the tests with `.venv/bin/python -m pytest -q` from the repository root.

## Conventions

- **Simulator state (17 entries):** position (3), velocity (3), quaternion (4, body to inertial, scalar first), body rates p, q, r (3), produced rotor thrusts (4). Index slices are in `dynamics.py` (`IDX_D`, `IDX_V`, `IDX_Q`, `IDX_W`, `IDX_F`). The inertial z axis points up.
- **Failed-vehicle design coordinates:** 7 states `[p, q, r, n_x, n_y, z, v_z]` with `n = R^T e3` (the "up" direction in body axes), plus 3 motor states for the thrusts of rotors 1 to 3. The relaxed hover is a fixed point in these coordinates, so the linearization is time-invariant. Learning and MPC use **deviations from the relaxed hover**.
- **Time:** the simulator runs at 1 ms; controllers are sampled with a zero-order hold (1 ms for the LQR, `TS = 5 ms` for the learning and MPC code).
- **Rotors:** 1 at +x, 2 at +y, 3 at -x, 4 at -y; rotor 4 is lost, rotor 2 is opposite to it. Thrust limits are 0.2 to 3.8 N; a command of 0 or less stops a motor.
- **Defaults are fixed:** `QuadParams` defaults, `truth_family("A"/"B")`, `TS`, `FailureMPC`, `FailureLQR`, `SpinUpThenLQR` and `DelaySupervisor` reproduce the published results; new options default to the old behaviour (tests check this).

## Modules

| Module | What it contains |
|---|---|
| `params.py` | `QuadParams` (all vehicle parameters, `prop_speeds`, `body_torque`, `thrust_efficiency`, optional air-relative thrust and quadratic drag), `DEFAULT`, `truth_family("A"/"B"/"A+"/"B+")` (plants with effects the design model lacks), `random_family` |
| `dynamics.py` | State layout, quaternion helpers, thrust saturation, the equations of motion (`deriv`), one RK4 step, `make_state`, `quat_from_n` |
| `equilibrium.py` | `relaxed_hover(p, rho)` (solves the equilibrium with rotor 4 lost), two- and one-rotor hovers, healthy hover thrust |
| `models.py` | Nonlinear design models (`healthy_f`, `failed_f`), numerical Jacobians, `healthy_linear`, `failed_linear`, `add_motor_lag` |
| `analysis.py` | Controllability and observability tests (rank, PBH, Gramians), delay margin |
| `control.py` | `HealthyLQR`, `FailureLQR` (with an internal motor-state filter), `SpinUpThenLQR` (the strategy of Mueller and D'Andrea: spin up on rotors 1 and 3, then the failure LQR), `DelaySupervisor` (healthy controller until the detection delay has passed), `CertifiedCaptureController` (exploratory) |
| `sim.py` | `simulate(...)`: fixed-step integration with a sampled controller; returns a `SimLog` |
| `metrics.py` | The success criterion (captured, safe), fixed before the experiments |
| `koopman.py` | `NominalModel` (discretized physics model), `Dictionary`, data generation (`generate`, `generate_capture`, `ExcitedLQR`), `FullEDMDc`, `ResidualEDMD`, `RLS` and `AdaptiveResidual` (online adaptation), `MeasurementNoise`, error evaluation |
| `mpc.py` | `FailureMPC` (CVXPY + OSQP; optional learned residual as a measured disturbance; weights and terminal-cost options), `LiftedKoopmanMPC` (MPC on the full-state Koopman model, re-lifted at every step) |
| `offset_free.py` | `OffsetFreeMPC` (disturbance estimator, target calculation, MPC on the estimate; thrust or state disturbance model) and `FailureLQRIntegral` (LQR with an integrator on the altitude) |
| `validation.py` | An independent implementation of the IJRR 2016 model, used only to validate the simulator |
| `plotting.py` | Shared figure style |

Exploratory modules (detection-delay certificates; not used by the report, see the README in the repository root): `certify.py` (saturation-aware LMI ellipsoids, robust version and gain synthesis), `lpv.py` (quasi-LPV model), `reach.py` (hand-over sets and ellipsoid containment), `mpc_cert.py` (certificate for the residual-MPC loop).

## Typical use

```python
from rotorfail.params import DEFAULT as P
from rotorfail.equilibrium import relaxed_hover
from rotorfail.control import FailureLQR
from rotorfail.dynamics import make_state
from rotorfail.sim import simulate

eq = relaxed_hover(P)
ctrl = FailureLQR(P, eq)
x0 = make_state(w=eq.w)                         # hover with the spin already built up
ctrl.reset(eq.f[:3])
log = simulate(x0, ctrl, P, 6.0, dt=1e-3, ctrl_period=1e-3, alive_fn=lambda t: [True, True, True, False])
```
