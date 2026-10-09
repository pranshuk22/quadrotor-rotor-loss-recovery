# Kulkarni, Sundararajan & Sundaram: Heli-quad Design for Full-Attitude Fault-Tolerant Control under Complete Failure of an Actuator

**arXiv:** 2011.07529 (v3, 2024)  **Local PDF:** `../papers/Heliquad2020_arXiv2011.07529.pdf`  **Read depth:** partial (abstract + FDI-delay section)

## What it does
- Variable-pitch quad with cambered-airfoil propellers, which keeps **yaw authority** after an actuator fails (so there is no relaxed hover; a different vehicle class).
- Outer position loop, PD attitude loop, and neural-network reconfigurable allocation; SIMSCAPE software-in-the-loop simulation.
- **"From the empirical result, the maximum tolerable delay in FDI is 180 msec."** Found by simulation sweeps over the delay: during the delay, thrust imbalance causes roll and torque imbalance causes spin.

## Use in v4
- The only quantitative delay-tolerance figure found. It is **empirical** and for a **different vehicle**.
- Gives the order of magnitude for H2 (τ\* ~ tens to hundreds of ms).
