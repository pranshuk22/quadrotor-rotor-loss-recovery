# 7. Code Reference (`rotorfail/`)

| Module | Main contents |
|---|---|
| `params.py` | `QuadParams` (frozen dataclass: all vehicle parameters, `prop_speeds`, `body_torque`, `thrust_efficiency`, `I_B`, `I_T`, `weight`); `DEFAULT`; `G`; `truth_family("A"/"B")`; `random_family(rng)` |
| `dynamics.py` | State layout (`IDX_D`, `IDX_V`, `IDX_Q`, `IDX_W`, `IDX_F`, 17 entries); quaternion helpers (`quat_to_rot`, `euler_to_quat`, `rot_to_euler`, `quat_mult`, `quat_from_n`); `saturate`; `body_rate_derivative(w, f, p)`; `deriv(x, f_cmd, p, alive, motor_lag)`; `rk4_step`; `make_state`; `reduced_attitude` |
| `equilibrium.py` | `relaxed_hover(p, rho)` → `RelaxedHover(rho, f, w, n, prop_speeds, orbit_radius)`; `two_rotor_hover(p)`, `single_rotor_hover(p)` → `HoverSolution`; `healthy_hover_thrust(p)` |
| `models.py` | `LinearModel(A, B, x_trim, u_trim, states, inputs)`; `jacobians` (central differences); `healthy_f`, `healthy_linear`; `failed_f`, `failed_linear`; `add_motor_lag`; `select_states` |
| `analysis.py` | `ctrb`, `obsv`, `rank`, `scaled_rank`, `pbh_controllability`, `pbh_observability`, `finite_gramian`, `gramian_summary`, `delay_margin` |
| `control.py` | `lqr`; `healthy_weights`, `HealthyLQR`; `failure_weights`, `FailureLQR` (internal motor-state filter, `reset`); `SpinUpThenLQR`; `DelaySupervisor` |
| `certify.py` | `invariant_ellipsoid(A, B, K, ubar, direction, decay, box)` (Hu–Lin LMIs, CVXPY); `slice_ellipse`; `contains`; `semi_axes` |
| `metrics.py` | Success criterion constants; `Outcome`; `evaluate(log, eq)` |
| `sim.py` | `simulate(x0, controller, p, T, dt, ctrl_period, alive_fn, ...)` → `SimLog(t, x, u, n)` |
| `koopman.py` | `TS`; `NominalModel`; `Dictionary`; `ridge`; `Dataset`; `ExcitedLQR`; `initial_state`; `generate`; `FullEDMDc`; `ResidualEDMD`; `nominal_rollout`; `multistep_errors` |
| `mpc.py` | `FailureMPC(p, eq, horizon, residual)` (CVXPY + OSQP, measured-disturbance residual) |
| `validation.py` | `GeneralMulticopter` (independent implementation of the IJRR 2016 model); `ijrr_speeds`; `IJRR_CASES` |
| `plotting.py` | Figure style (validated categorical palette, thin marks) |

## Controller interface
Every controller is a callable `controller(t, x) -> np.ndarray(4)` of thrust commands, where x is the 17-entry simulator state. A command ≤ 0 stops a motor, and commands are otherwise clipped to [f_min, f_max] by the plant. Controllers that keep internal state (FailureLQR, FailureMPC, SpinUpThenLQR) provide `reset(f_now)`. A supervisor may also provide `alive(t) -> bool[4]`; `simulate` uses it to know which rotors produce thrust.

## Conventions
- State deviations are taken from the relaxed-hover trim (`base.x_trim`) for the failed vehicle and from hover for the healthy one.
- Reduced attitude n = Rᵀe₃; n_z is recovered from (n_x, n_y) in the linear models.
- Rotor 4 (index 3) is the failed rotor.
- All random generators are `numpy.random.default_rng(seed)` with explicit seeds.
