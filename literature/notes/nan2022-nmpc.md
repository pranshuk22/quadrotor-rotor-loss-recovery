# Nan, Sun, Foehn & Scaramuzza (RA-L 2022): Nonlinear MPC for Quadrotor Fault-Tolerant Control

**arXiv:** 2109.12886  **Local PDF:** `../papers/Nan2022_NMPC_FTC_arXiv2109.12886.pdf`  **Read depth:** partial (abstract, intro; full text grepped for "delay")

## What it does
- NMPC on the full nonlinear dynamics of the damaged vehicle, with per-rotor thrust constraints.
- Recovers from extreme initial conditions (e.g. failure at the top of a flip). Simulation + real flights.
- Critique of prior work: methods "either rely on linear assumptions or resort to cascaded structures neglecting input constraints in the outer-loop".

## Delay
- "Delay" appears only for motor/thrust tracking and filter lag. There is **no fault-detection-delay analysis** and no certificate.

## Use in v4
- Supports the motivation (linear methods + constraints = the open issue).
- Nonlinear upper reference if an MPC comparison is added later (optional).
