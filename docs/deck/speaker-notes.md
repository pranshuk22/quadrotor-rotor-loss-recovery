# Speaker notes

One section per slide id, in slide order. `build_pptx.js` copies each section into the notes of the matching slide.

## cover
Our project is about a quadrotor that has lost one of its rotors completely. A physics model of the drone in that state already exists. We ask whether it is worth keeping that model and learning only its error from data, and whether this gives better prediction and control than the physics model alone or than a model learned entirely from data.

## rotorloss
A quadrotor has four thrusts and exactly four things to control: height, roll, pitch and yaw. There is no spare actuator. The propellers also twist the body; with four rotors these twists cancel, but with three they don't, and the drone starts to spin. Mueller and D'Andrea showed that if you give up the heading and accept the spin, the three remaining rotors can still hold the drone in the air, spinning about a slightly tilted axis. They called this the relaxed hover. For their drone it is a spin of about 19.6 rad/s, a bit over three turns per second, with a tilt of 16 degrees. The table shows the thrusts: rotor 2, opposite the failed one, carries only half as much as rotors 1 and 3.

## question
The controller for this state is designed on the physics model. The model gets the equilibrium and the spin-up right, but it is not exact: in the real flights the propellers lost thrust at high spin rates and the drone spun 20 to 27 percent slower than predicted. A controller built on an imperfect model settles with a steady error, for example at the wrong height. Learning only the error of a physics model, a so-called residual Koopman model, has been used for healthy quadrotors and other robots, but we did not find it for a drone spinning after rotor loss. That is our research question.

## simulator
We wrote the simulator ourselves in Python. It is a full rigid-body model with quaternion attitude, the gyroscopic effect of the propellers, thrust limits and a 15 ms motor lag; it integrates at 1 ms and the controllers run every 5 ms. The parameters on the right are those of Mueller and D'Andrea. To have something to learn, we generate data on "truth plants": the same simulator with effects the design model does not have, such as thrust loss at high spin rate, wrong inertias and slower motors. Later we also add air-relative thrust and drag.

## validation
Before trusting the simulator we checked it against published results. The two- and three-rotor-loss equilibria match every printed digit. The one-rotor case agrees within half a percent except for the pitch rate, which is 6 percent lower; we found that the paper's own printed values do not satisfy its own roll equation, so we keep this as one expected test failure. The more detailed 2016 model, which we implemented separately, agrees within 4 percent on all five hover cases, and against the real flight our spin-up takes 0.65 seconds against 0.62.

## equilibrium
This is the state the controller has to hold. Rotors 1 and 3 carry equal thrust and rotor 2 carries half of it. The figure shows how the equilibrium changes with this thrust ratio; it reproduces the corresponding figure of the paper, with a minimum spin of 18.6 against their 19.0 rad/s.

## linear
In body axes the linearized model is time-invariant, even though the drone spins. It has seven states: three body rates, two tilt components, height and vertical speed. It has two undamped oscillations and the altitude double integrator, so it needs feedback, and it is controllable from the three remaining rotors. Observability depends on the sensors: gyroscopes alone see only three of the seven states, and with a barometer the tilt becomes observable only very weakly. In this work every controller gets the exact state, which is one of our limitations.

## lqr
The failure LQR uses the weights of Mueller and D'Andrea, extended with the motor states and the altitude. On the full nonlinear model, started one metre low with rate and tilt errors, it settles in about two seconds. One warning sign: it tolerates only 18 ms of input delay, against 40 ms for the healthy drone. The spinning drone is much less forgiving.

## predictors
We compare three predictors on the same data. The analytical one is the linearized physics model and uses no data. The full-state EDMDc model learns everything: it lifts the state into 55 features and fits a linear model on them. The residual model keeps the physics model and learns only its one-step error, clipped to the range seen in training. All of them are trained on 40 four-second episodes from plant A and tested on new episodes from plant A and from a different plant B.

## prediction
On plant A the residual model is the best predictor from 100 ms to one second. At one second its error is 0.64, against 0.91 for the full-state model and 7.09 for the physics model. Below 100 ms the full-state model is better, but it has four eigenvalues outside the unit circle, so its errors grow, and by two seconds it falls behind simply assuming nothing changes. Beyond two seconds, "no change" beats every model, which is why these predictors are used inside a feedback controller.

## limits
The residual model also needs much less data: with only 10 episodes it is already better than the full-state model trained on 40. But there is a catch. On plant B, which neither model has seen, both learned models are worse than the plain physics model, and training on randomly varied plants does not fix this. So the residual behaves like a calibration of one particular vehicle, not a general model of rotor failure.

## mpc
Now control. We use an MPC on the physics model with a 100 ms horizon, with and without the learned residual added as a known disturbance, so the problem stays a convex QP. On plant A the LQR and the plain MPC settle 29 cm too low; with the residual the error is 19 cm, a third less. On one variant of plant B, however, the residual makes it worse. We also test every controller on catching the drone after a failure: the failure is detected after a delay, the drone spins up on two rotors, and then the controller takes over. The LQR survives up to 10 ms of delay, both MPCs only zero delay.

## offsetfree
The obvious question is how this compares with the classical way of removing a steady error, which is integral action. An LQR with an integrator brings the error down to at most 2.4 cm on all six plants and still survives 10 ms of delay, like the plain LQR. An offset-free MPC, with one estimated disturbance per state, removes the error completely, but it loses the drone in the capture even with no delay. In a logged run its estimator read the fast motion after the failure as a constant disturbance. Our first offset-free design, with only three thrust disturbances for seven states, could not remove the error at all. So the integrator LQR is the best trade-off we found.

## fullstate
The third MPC uses no physics at all: it plans with the full-state Koopman model. Although that model has unstable modes, the loop is stable near the hover, because we recompute the lifted state from the measurement at every step, and its steady error is close to the residual MPC's. In the capture it is safe without delay, like the other MPCs, but from 20 ms of delay its runs diverge completely, because the drone leaves the range of the training data, by up to 350 standard deviations. It also needs 55 to 319 ms per step against a 5 ms period, so it is far too slow for real time.

## adapt
To tackle the generalization problem we let the residual keep learning in flight, with recursive least squares. On the unseen plant B this halves the prediction error, and it fixes the one plant where the residual MPC had been worse than the LQR: 8 cm instead of 16. But on plant A, where the original fit was already good, adaptation makes predictions worse, and near the hover most weights are not excited, so the covariance just sits at its cap. Adaptation helps partly, not fully.

## transient
The residual was trained near the hover, but the capture starts far from it. So we trained it on capture transients as well. Predictions of those transients improve dramatically, 0.57 against 8.2 at 100 ms. Surprisingly, the MPC built on this residual is worse: it is not safe even at zero delay, and we have not found the reason. We also checked whether the MPC settings were to blame. Horizons from 10 to 80 steps make no difference, a heavier tilt weight buys one extra delay step, and no setting beats the LQR.

## ablations
Finally, the robustness checks. Cubic features reduce the long-horizon error on plant B but cost accuracy on A, and the ridge parameter and sampling period make no difference. Sensor noise matters: training on noisy measurements is harmful, and the resulting MPC ends about 2.8 m from its set-point, while the residual trained on clean data and the offset-free MPC cope with noise. With air-relative thrust and drag added to the simulated drone, all conclusions stay the same.

## hypotheses
To summarize against our four hypotheses: H1, that the full-state Koopman model is unstable, holds for prediction, although an MPC that re-lifts at every step keeps it stable. H2 and H4, best prediction and less data, hold, but only on the plant the model was trained on. H3, that the residual MPC removes the steady error, holds only partly: it cuts the error by a third, it does not remove it, and integral action does better.

## conclusions
So, learning only the error of the physics model gives the best predictions from 100 ms to one second and needs little data, but only for the drone it was trained on. As a controller it reduces the steady error by a third, while a simple LQR with an integrator removes it almost completely and keeps the ability to catch the drone. Adaptation, transient training, MPC tuning and the other changes did not improve the capture. All of this is in simulation, with exact state measurement and one vehicle. The next steps would be to estimate the uncertain physical parameters directly, add a state estimator for tilt and height, and test on hardware. Thank you.

## references
Backup slide with the main references.
