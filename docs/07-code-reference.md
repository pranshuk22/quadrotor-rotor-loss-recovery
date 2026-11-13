# 7. Code Reference (`rotorfail/`)

| Module | Main contents |
|---|---|
| `params.py` | `QuadParams` (frozen dataclass: all vehicle parameters, `prop_speeds`, `body_torque`, `thrust_efficiency`, `I_B`, `I_T`, `weight`); `DEFAULT`; `G`; `truth_family("A"/"B")`; `random_family(rng)`; `air_relative`, `quad_drag`, `effective_thrust` and `truth_family('A+'/'B+')` (optional IJRR effects, off by default) |
| `dynamics.py` | State layout (`IDX_D`, `IDX_V`, `IDX_Q`, `IDX_W`, `IDX_F`, 17 entries); quaternion helpers (`quat_to_rot`, `euler_to_quat`, `rot_to_euler`, `quat_mult`, `quat_from_n`); `saturate`; `body_rate_derivative(w, f, p)`; `deriv(x, f_cmd, p, alive, motor_lag)`; `rk4_step`; `make_state`; `reduced_attitude` |
| `equilibrium.py` | `relaxed_hover(p, rho)` → `RelaxedHover(rho, f, w, n, prop_speeds, orbit_radius)`; `two_rotor_hover(p)`, `single_rotor_hover(p)` → `HoverSolution`; `healthy_hover_thrust(p)` |
| `models.py` | `LinearModel(A, B, x_trim, u_trim, states, inputs)`; `jacobians` (central differences); `healthy_f`, `healthy_linear`; `failed_f`, `failed_linear`; `add_motor_lag`; `select_states` |
| `analysis.py` | `ctrb`, `obsv`, `rank`, `scaled_rank`, `pbh_controllability`, `pbh_observability`, `finite_gramian`, `gramian_summary`, `delay_margin` |
| `control.py` | `lqr`; `healthy_weights`, `HealthyLQR`; `failure_weights`, `FailureLQR` (internal motor-state filter, `reset`); `SpinUpThenLQR`; `DelaySupervisor`; `CertifiedCaptureController` (FailureLQR with a replaced gain, the 'redesigned capture' of E9c) |
| `certify.py` (exploratory) | `invariant_ellipsoid(A, B, K, ubar, direction, decay, box)` (Hu–Lin LMIs, CVXPY); `slice_ellipse`; `contains`; `semi_axes`; `robust_invariant_ellipsoid` (LPV closed loop: common Q over the parameter vertices, all saturation patterns, scaled coordinates, box and disc self-consistency, optional remainder S-procedure); `verify_robust` (solver-independent eigenvalue check); `synthesize_gain` and `verify_design` (Hu-Lin design LMIs with a gain-size bound) |
| `metrics.py` | Success criterion constants; `Outcome`; `evaluate(log, eq)` |
| `sim.py` | `simulate(x0, controller, p, T, dt, ctrl_period, alive_fn, ...)` → `SimLog(t, x, u, n)` |
| `koopman.py` | `TS`; `NominalModel`; `Dictionary`; `ridge`; `Dataset`; `ExcitedLQR`; `initial_state`; `generate`; `FullEDMDc`; `ResidualEDMD`; `nominal_rollout`; `multistep_errors`; `Dictionary(degree)`; `RLS`, `AdaptiveResidual` (online adaptation, E8c); `generate_capture` (capture transients, E8d); `MeasurementNoise`, `noisy_measurement`, `generate(noise=...)` (E8f); `ResidualEDMD.fit(weighting, degree)` |
| `mpc.py` | `FailureMPC(p, eq, horizon, residual)` (CVXPY + OSQP, measured-disturbance residual); `LiftedKoopmanMPC(p, eq, model, horizon)` (MPC on a `FullEDMDc` lifted model, re-lifted each step, DARE terminal cost with checks in `.dare`); `FailureMPC(weights, terminal)` options (published defaults reproduce the earlier controller exactly) |
| `offset_free.py` | `OffsetFreeMPC(p, eq, horizon, residual, disturbance="thrust"/"state")` (Kalman filter, target calculation, MPC on the estimate); `FailureLQRIntegral` (failure LQR with integrator on altitude); `thrust_offset_matrix`, `detectability_rank` |
| `validation.py` | `GeneralMulticopter` (independent implementation of the IJRR 2016 model); `ijrr_speeds`; `IJRR_CASES` |
| `lpv.py` (exploratory) | `QuasiLPV(p, eq)`: 10-state quasi-LPV closed-loop model with scheduling parameters (r, n_z), `A(r, n_z)` affine, closed-form `remainder`, `f_nonlinear`, `vertices`; `frozen_check`, `remainder_sup` |
| `reach.py` (exploratory) | `ChainSpec`, `run_chain` (the E4 chain stopped at the hand-over), `chain_jacobian`, `hand_over_set`, `sample_x0`, `coverage`; `UndetectedLTI` (affine LTI model of the undetected phase), `command_ranges`; `max_beta` (S-procedure LMI), `max_beta_exact` (trust region), `centre_scaling` |
| `mpc_cert.py` (exploratory) | `unconstrained_law` (closed form of the unconstrained finite-horizon MPC), `horizon_gains`, `unconstrained_region`, `design_ellipsoid`, `verify_design`, `mismatch_margin` (E10c) |
| `plotting.py` | Figure style (validated categorical palette, thin marks) |

## Controller interface
Every controller is a callable `controller(t, x) -> np.ndarray(4)` of thrust commands, where x is the 17-entry simulator state. A command ≤ 0 stops a motor, and commands are otherwise clipped to [f_min, f_max] by the plant. Controllers that keep internal state (FailureLQR, FailureMPC, SpinUpThenLQR) provide `reset(f_now)`. A supervisor may also provide `alive(t) -> bool[4]`; `simulate` uses it to know which rotors produce thrust.

## Conventions
- State deviations are taken from the relaxed-hover trim (`base.x_trim`) for the failed vehicle and from hover for the healthy one.
- Reduced attitude n = Rᵀe₃; n_z is recovered from (n_x, n_y) in the linear models.
- Rotor 4 (index 3) is the failed rotor.
- All random generators are `numpy.random.default_rng(seed)` with explicit seeds.
