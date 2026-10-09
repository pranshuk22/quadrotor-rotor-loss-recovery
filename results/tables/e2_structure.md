# E2: Structural analysis

Models are numerical Jacobians of the exact nonlinear equations (see `rotorfail/models.py`).

## Healthy quadrotor at hover

States (12): x, y, z, vx, vy, vz, phi, theta, psi, p, q, r; inputs: f1, f2, f3, f4

**Open-loop eigenvalues:** -0.506, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000

**Controllability:** rank [B AB ... A^11B] = 12 / 12 (columns normalized before the SVD).

PBH test, min singular value of [λI − A, B̃] per mode (scaled; > 0 means controllable):

| Mode λ | σ_min | Controllable |
|---|---|---|
| 0.000 | 3.76e-02 | yes |
| -0.506 | 3.72e-02 | yes |

Controllability Gramian W(1.0 s): λ_min = 1.05e+00, λ_max = 3.44e+04, condition number = 3.27e+04.

**Observability by sensor set:**

| Sensor set | rank O | Unobservable states | λ_min W_o(1 s) | cond W_o |
|---|---|---|---|---|
| S1 gyro (p,q,r) | 3 / 12 | x, y, z, vx, vy, vz, phi, theta, psi | 0 (unobs.) | ∞ |
| S2 gyro + position | 11 / 12 | psi | 0 (unobs.) | ∞ |
| S3 gyro + position + magnetometer (psi) | 12 / 12 | none | 4.8e-03 | 1.3e+03 |
| S4 gyro + attitude (phi,theta,psi) | 6 / 12 | x, y, z, vx, vy, vz | 0 (unobs.) | ∞ |

## Failed quadrotor (rotor 4 lost) at the relaxed hover, ρ = 0.5

States (7): p, q, r, n_x, n_y, z, v_z; inputs: f1, f2, f3

**Open-loop eigenvalues:** -0.506, 0.000, 0.000, -0.000 ± 10.099j, -0.000 ± 19.559j

**Controllability:** rank [B AB ... A^6B] = 7 / 7 (columns normalized before the SVD).

PBH test, min singular value of [λI − A, B̃] per mode (scaled; > 0 means controllable):

| Mode λ | σ_min | Controllable |
|---|---|---|
| 0.000 | 1.97e-02 | yes |
| -0.506 | 1.61e-02 | yes |
| -0.000 ± 10.099j | 2.75e-01 | yes |
| -0.000 ± 19.559j | 1.73e-02 | yes |

Controllability Gramian W(1.0 s): λ_min = 5.44e-01, λ_max = 4.12e+03, condition number = 7.58e+03.

**Observability by sensor set:**

| Sensor set | rank O | Unobservable states | λ_min W_o(1 s) | cond W_o |
|---|---|---|---|---|
| F1 gyro (p,q,r) | 3 / 7 | n_x, n_y, z, v_z | 0 (unobs.) | ∞ |
| F2 gyro + tilt estimate (n_x,n_y) | 5 / 7 | z, v_z | 0 (unobs.) | ∞ |
| F3 gyro + altitude (baro) | 7 / 7 | none | 2.4e-05 | 5.6e+04 |
| F4 gyro + tilt + altitude | 7 / 7 | none | 6.6e-02 | 2.0e+01 |

## Notes

- Healthy model: the classic result. Gyro + position leaves yaw ψ unobservable at hover (heading enters the translational dynamics only at second order), so a heading sensor is needed.
- Failed model: the rate dynamics do not depend on n, so gyro-only leaves the reduced attitude and the altitude unobservable.
- Failed model, F3: because the relaxed hover is *tilted* (n̄_y ≠ 0), vertical acceleration depends on tilt to first order (∂v̇_z/∂n_y ≠ 0). This coupling does not exist at a level hover, and it makes the full reduced attitude observable from gyro + barometer alone (F3). The Gramian columns show how weak this observability is compared with a direct tilt measurement (F4): it is a structural property, not a practical estimator design. It is a candidate for the observability part of the project (to be checked against the estimation literature).
- Controllability of the reduced attitude from three rotors reproduces Mueller & D'Andrea (not a contribution).
