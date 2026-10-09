# E3: LQR designs

| Controller | Model | Weights | Slowest closed-loop poles | Input-delay margin |
|---|---|---|---|---|
| Healthy LQR | 12-state hover | Bryson: 0.5 m, 1 m/s, 0.2 rad, 2 rad/s; 0.5 N per rotor | -1.72 ± 1.02j, -1.89, -1.94 ± 1.56j, -3.52, -13.39 ± 2.20j | 40 ms |
| Failure LQR (M&D weights) | 7-state reduced attitude + altitude + 3 motor states | 1 on p,q; 20 on n; 0 on r and motor states; 4 on z, 1 on v_z; 1 N⁻² | -1.09, -2.01 ± 1.04j, -3.80 ± 19.68j, -54.57 ± 22.87j, -57.58 ± 37.92j, -66.62 | 18 ms |
| Failure LQR, no motor model | 7-state | same, no motor states | -1.09, -2.01 ± 1.04j, -3.83 ± 19.66j, -53.51, -70.06 | 18 ms |

Closed loop of the no-motor-model design with the true 15 ms motor lag: max Re(λ) = -1.10 (stable). Mueller & D'Andrea report that motor dynamics strongly affect this system and include them in the design; we do the same.

Delay margin: largest pure input delay that keeps the linear closed loop stable (exact ZOH discretization at 1 ms with a delay line).

## Nonlinear check, failed vehicle

Start: relaxed hover + Δω = (1, −1, −3) rad/s, Δn = (0.08, −0.05, ·), 1 m below the set-point; rotor 4 off; motor lag and thrust limits active.

After 6 s: |n − n̄| = 1.6e-04, |ω − ω̄| = 1.2e-02 rad/s, z = -0.000 m.

## Nonlinear check, healthy vehicle

Start: (0.5, −0.3, −0.5) m offset, Euler (0.25, −0.2, 0.4) rad.
After 5 s: |position| = 2.5e-04 m.
