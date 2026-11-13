# Recoverable set computation for post-fault/failure quadrotors based on sum of squares (SOS)

**Record:** HAL hal-01348150 (the entry cited as Qi et al. 2016 in `proposal/novelty-and-claims.md` and in the report bibliography as `qi2016recoverable`).  **Read depth:** abstract (as returned by a search); the HAL page returned an access-denied page to the fetch tool, so the full text was not read.

## What the abstract says
- A method to compute the **recoverable set** for different faulty conditions with sum-of-squares programming; the recoverable set is an invariant set of initial states that can be driven to the equilibrium while respecting propeller faults, failures and rotating-speed limits.
- Feasible equilibria (relaxed hover solutions) are computed first, for different faulty cases; simulations on the nonlinear quadrotor dynamics illustrate the approach.

## Use in this project
- Closest existing work to a certified capture set; it does not (in the abstract) consider the detection delay or the spin-up hand-over. Our capture sets are LMI (quadratic, saturation-aware) rather than SOS.
- Cited with the wording "according to its abstract"; its scope (single or multiple rotors, polynomial degree, size of the set) is not verified.
