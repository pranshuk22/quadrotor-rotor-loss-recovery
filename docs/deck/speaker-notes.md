# Speaker notes

One section per slide id, in slide order. `build_pptx.js` copies each section into the notes of the matching slide.

## cover
Our project is about a quadrotor that has lost one rotor. The question is whether we can keep the physics model of the spinning drone and learn only its error from data, and whether that predicts and controls better than the alternatives.

## rotorloss
A quadrotor has four thrusts and four things to control, so it has no spare actuator. The propellers also twist the body. With four rotors the twists cancel. With three they don't, and the drone starts to spin. Mueller and D'Andrea showed that if you accept the spin and give up the heading, the three rotors can still hold the drone up, with the spin axis tilted. That is the relaxed hover. For their drone it is about 19.6 rad/s with a 16 degree tilt. A linear controller on a reduced model can hold it.

## question
The controller is designed on their physics model. It is good, but it misses things. In their flights the thrust dropped at high spin rate, and the drone spun 20 to 27 percent slower than predicted. Inertia and motor speed are not known exactly either. So a controller based on the model ends up with a steady error. Our question is whether a Koopman model of only the error of the physics model, used inside MPC, does better than the physics model alone or than a Koopman model of everything. The residual is computed outside the optimization and added as a known disturbance, so the MPC stays a convex QP. Residual Koopman MPC exists for healthy quadrotors, but we did not find it for this case.

## simulator
We wrote the simulator ourselves in Python: rigid body with quaternion attitude, the gyroscopic terms, thrust limits, motor lag of 15 ms. For the learning data we use truth plants, which are the same simulator with effects the design model does not have: thrust loss at high spin rate, an inertia error, slower motors. Later we also add air-relative thrust and drag. The parameters are the ones from the Mueller and D'Andrea paper.

## validation
We checked the simulator against published numbers. The two- and three-rotor-loss equilibria match every digit. The one-rotor case is within half a percent except the pitch rate. There the paper's own numbers do not satisfy its own roll equation, so we keep one expected test failure. Their more detailed 2016 model, which we implemented separately, agrees within 4 percent on five hover cases. Against the flight data, our spin-up to 10 rad/s takes 0.65 seconds and the flight took 0.62.

## equilibrium
This is the equilibrium the controller has to hold. The two side rotors have equal thrust and the opposite rotor has about half. The figure shows how it changes with the thrust ratio, and it reproduces the paper's figure.

## linear
Linearizing in body axes gives a linear time-invariant model with seven states. It is controllable from the three rotors. Observability depends on the sensors. Gyros alone see three of the seven states, and a barometer makes the rest observable only weakly. We give all controllers the exact state, which is a limitation.

## lqr
The failure LQR uses the paper's weights with motor states and altitude added. On the nonlinear model it settles in about two seconds. The input-delay margin is only 18 ms, compared with 40 ms for the healthy drone.

## predictors
We compare three predictors on the same data. The analytical one is the linearization, with no data. The full-state EDMDc learns everything with 55 features. The residual model keeps the physics and learns only a one-step correction, which is clipped at the 99.5th percentile of the training errors. We train on 40 episodes from plant A and test on new episodes from A and from a different plant B.

## prediction
On plant A the residual model is the best predictor from 100 ms to 1 s. At one second its error is 0.64, against 0.91 for the full-state model and 7.09 for the analytical model. Below 100 ms the full-state model is better. It has four eigenvalues outside the unit circle and falls behind a no-change predictor by about two seconds. Beyond that, no-change beats everything.

## limits
The residual model needs less data: with 10 episodes it beats the full-state model trained on 40. But on plant B both learned models are worse than the analytical model. Training on randomized plants helps on B only up to about 100 ms and hurts on A. So the residual is a calibration for one vehicle.

## mpc
In closed loop we use an MPC on the physics model, with and without the residual. On plant A the LQR and the plain MPC settle 29 cm low, and the residual MPC 19 cm, which is a third less. On one variant of plant B the residual makes it worse, 0.164 m against 0.112 for the LQR. The solver itself takes 0.7 ms per step.

## offsetfree
Next we tried the obvious classical alternatives. An LQR with an integrator removes the error on all six plants, to at most 2.4 cm, and keeps the capture of the LQR. An offset-free MPC with a disturbance on every physical state also removes it, but it fails the capture even without delay. In one diagnostic run its estimator treats the fast transient as a constant disturbance. The first design, with a three-dimensional thrust offset, leaves an error because three disturbance states cannot absorb the mismatch of seven.

## fullstate
The third controller in our proposal plans with the full-state Koopman model. It is stable near the hover because we recompute the lifted state from the measurement at every step. The steady error is similar to the residual MPC. Capture already fails at 10 ms of delay on plant A, and the runs diverge from 20 ms, because the features leave the training range during capture. It also needs 55 to 319 ms per step, so it is not real-time.

## adapt
To deal with generalization we adapted the residual online with recursive least squares. On plant B the prediction error is about halved, and the worst closed-loop case goes from +0.164 to +0.084 m. On plant A it is not better than the fixed residual. The covariance sits at its cap because most weights are not excited near the hover.

## transient
We trained the residual on capture transients, since the capture starts far from the equilibrium. Predictions of those transients improve a lot: 0.57 against 8.2 at 100 ms. But the MPC built on it is not safe even at zero delay. We did not find out why. Changing the MPC horizon from 10 to 80 steps changes nothing, a heavier attitude weight gives one more safe delay, and no setting beats the LQR.

## ablations
Cubic features reduce the long-horizon error on plant B but are worse on A. The ridge parameter and the sampling period do not matter. Noisy training data are harmful, with a closed-loop bias of 2.8 m. The clean-trained residual and the offset-free MPC tolerate noise. With air-relative thrust and drag in the truth plant, the conclusions do not change.

## hypotheses
H1 and H4 are supported. H2 is supported on the training plant only. H3 is only partly supported: a third less error on the training plant, worse on one held-out plant, and integral action does better.

## conclusions
The residual Koopman model is the best predictor from 100 ms to 1 s and needs little data, on the plant it was trained on. In MPC it reduces the steady error by about a third, but an integrator does better and keeps the capture. Adaptation, transient data, tuning and the ablations did not improve the capture. The limits are that it is all simulation, with exact state measurement. Next we would estimate the uncertain physical parameters directly, add a state estimator, and test on hardware.

## references
Backup slide with the main references.
