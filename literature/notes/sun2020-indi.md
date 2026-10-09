# Sun, Wang, Chu & de Visser (T-RO 2020): Incremental Nonlinear Fault-Tolerant Control of a Quadrotor with Complete Loss of Two Opposing Rotors

**arXiv:** 2002.07837  **Local PDF:** `../papers/Sun2020_INDI_TwoRotors_arXiv2002.07837.pdf`  **Read depth:** abstract + grep

## What it does
- INDI controller for loss of two opposing rotors in high-speed flight (> 8 m/s); also generalizes to single-rotor loss.
- Analyses the internal dynamics and redefines the control output to stabilize them.
- Wind-tunnel flight tests. **An LQR from the literature (M&D-style) is compared and degrades in windy/high-speed conditions.**

## Use in v4
- Evidence that fixed-gain LQR at the equilibrium has a limited operating region. v4 quantifies that region (the capture set) instead of only observing it.
