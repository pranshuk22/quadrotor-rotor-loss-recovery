# Rotondo, Ponsart, Nejjari, Theilliol & Puig: virtual-actuator FTC for LPV systems with saturating actuators and FDI delays

**Venue:** 3rd Conference on Control and Fault-Tolerant Systems (SYSTOL), 2016, pp. 831-837. Preprints: UPC repository (recercat.cat handle 2072/280645) and HAL (hal-01348187). The LTI predecessor appeared in Annual Reviews in Control 39 (2015) 68-80.  **Read depth:** abstract and a search-result summary only; the full text could not be retrieved in this session (certificate error on the UPC host, HTTP 403 on core.ac.uk). **No technical statement below goes beyond the abstract.**

## What the abstract says
- Fault-tolerant control for LPV systems subject to actuator saturation and fault detection and isolation (FDI) delays.
- A virtual actuator reconfigures the faulty plant (not the controller) and keeps the closed loop stable while avoiding saturation.
- A separate design step gives a nominal output-feedback controller that **maximises the tolerated delay between fault occurrence and isolation**, as the solution of a finite set of LMIs.
- The LTI paper states that if the state at the fault-isolation time lies in a region defined by a Lyapunov-function level, the trajectory converges despite the faults of a predefined set.

## Use in this project
- **Overlap with RQ2:** a general (LPV, saturation, FDI delay) LMI formulation of a tolerated detection delay exists. Our contribution is therefore not the idea of an LMI delay budget but its instantiation for complete rotor loss with the open-loop spin-up hand-over, and the measured result that the published strategy's hand-over state cannot be certified (E9a to E9d).
- Cited in the report as related work with the wording "according to its abstract". Must be read in full before any stronger statement.
