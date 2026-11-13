# Speaker notes

One section per slide, in slide order. `build_pptx.js` copies each section into the notes of the matching slide. The deck covers research question 1 (residual Koopman MPC) only.

## cover
Good morning. Our project is about a quadrotor that has lost one rotor completely, and about one question: can we keep the known physics model of the spinning drone and learn only its error from data, and does that give better predictions and better control than the physics model alone or a Koopman model of the full dynamics? I will go through the problem, the simulator and its validation, the first results, and then the further experiments we ran to test whether the learned residual is the right tool.

## timeline
First, the problem. A quadrotor has four thrusts that control exactly four things: height, roll, pitch and yaw. The propellers also twist the body with small reaction torques, which cancel in normal flight because two propellers spin each way. If one rotor stops, the remaining torques no longer cancel and the drone starts to spin. Mueller and D'Andrea showed that if we give up control of the heading and accept the spin, the three remaining rotors can still hold the drone in the air: it hovers like a spinning top, with its spin axis tilted about 16 degrees, and moves by tilting that axis. They called this the relaxed hover.

## problem
So why is there still a problem? A controller is only as good as its model. The Mueller and D'Andrea model captures the main spinning motion, but it misses real effects: in their flights the drone produced less thrust while spinning fast and spun 20 to 27 percent slower than predicted, and inertia and motor speed are never known exactly. A controller built on this model settles with a steady error. Our research question is whether a data-driven model of only the mismatch, on top of the physics model, predicts the failed drone better and gives a smaller steady error in MPC than the physics model alone or a Koopman model of the full dynamics. Koopman or EDMD methods describe the state with many nonlinear features and fit a linear model on them by least squares. We use them to learn the one-step error of the physics model, evaluated outside the MPC optimization so the problem stays a convex quadratic program. Residual Koopman models exist for healthy drones, but we did not find them for the spinning regime after complete rotor loss.

## model
We wrote our own simulator in Python: a six degree of freedom rigid body with quaternion attitude, the rotor gyroscopic terms from the paper, thrust limits and a first-order motor lag. The key state for the failed vehicle is the reduced attitude n, the vertical direction seen from the body, which is all that is controlled after the failure. For learning we also need truth plants, which are the same simulator with effects the design model does not have: thrust loss at high spin, inertia error and slower motors, and later air-relative thrust and drag. The vehicle parameters are those of Mueller and D'Andrea.

## validation
Before trusting any result we checked the simulator against published numbers. The two- and three-rotor-loss equilibria match every digit they published. The one-rotor-loss case matches within half a percent except the pitch rate, where we find that the paper's own values do not satisfy its own roll equation. Their more detailed 2016 model, which we implemented separately, agrees within 4 percent on five hover cases, and a second drone's formula is reproduced exactly. Against flight data, our spin-up time to 10 radians per second at the flight thrust is 0.65 seconds against 0.62 in flight. 123 automated tests check this and the physics; one expected failure keeps the published inconsistency visible.

## equilibrium
This is the equilibrium the failed vehicle must reach. With rotor 4 gone, the two side rotors produce equal thrust and the opposite rotor about half of it. The vehicle then spins at about 19.6 radians per second about an axis tilted 16 degrees. The plot shows how the equilibrium changes with the thrust ratio and reproduces the paper's figure.

## structure
Linearizing about the spinning equilibrium in body coordinates gives a linear time-invariant model with two undamped oscillations, a slow yaw mode and the altitude double integrator. It is fully controllable from the three rotors. Observability is the weak point: gyroscopes alone cannot see tilt or altitude, and a barometer reveals tilt only weakly because the equilibrium is tilted, about 2,700 times less visibly than with a tilt sensor once noise is included. In this work all controllers are given the exact state, which is a limitation.

## lqr
The failure-mode LQR at the spinning equilibrium uses the paper's weights with motor states and altitude added. On the full nonlinear model with motor lag and thrust limits it converges from a one-metre offset in about two seconds. The delay margin is only 18 milliseconds, less than half the healthy drone's 40 milliseconds: the spinning drone is much less forgiving, which makes a good model matter.

## part1
Now the approach: learn only the mismatch of the physics model, and use it inside MPC.

## koopman
We compare three predictors on the same data. The analytical model is the Mueller and D'Andrea linearization with no learning. Full-state EDMDc learns everything from data with 55 features. The residual model keeps the physics model and learns a one-step correction, clipped at the 99.5th percentile of the training errors. Training data are 40 episodes of 4 seconds from a truth plant A; we test on new episodes from plant A and from a different plant B.

## prediction
On held-out episodes from the training plant, the residual model is the best predictor from 100 milliseconds to one second: at one second its error is 0.64 against 0.91 for the full-state model and 7.09 for the physics model. Below 100 milliseconds the full-state model is better. The full-state model has four of its 55 eigenvalues just outside the unit circle, and by two seconds it falls behind a trivial no-change predictor, as we had hypothesised; beyond two seconds no-change beats every model.

## limits
Two more results, one good and one bad. Good: the residual model needs less data; with 10 episodes it beats the full-state model trained on 40. Bad: on the unseen plant B both learned models are worse than the physics model alone, and training on randomized plants helps on B only up to about 100 milliseconds and hurts on A. A model that sees only the current state cannot tell which vehicle it is on. So the residual is a calibration of one vehicle, not yet a general model.

## mpc
In closed loop we built a linear MPC on the physics model and the same MPC with the residual added as a measured disturbance. On the training plant the mismatch causes a steady altitude error of 29 centimetres for the LQR and the plain MPC; the residual reduces it to 19 centimetres, a third. On a held-out variant of plant B the correction pushes the wrong way and the error is 47 percent larger. The obvious baseline is integral action, which we test next.

## part2
We then ran a series of further experiments to see whether the learned residual is really the right tool: offset-free baselines, the third controller from our proposal, online adaptation, transient training data, tuning, ablations and a more realistic plant.

## offsetfree
Integral action beats the learned residual. An LQR with an integrator removes the steady error to at most 2.4 centimetres on all six plants and keeps the LQR's capture. An offset-free MPC with a disturbance on all physical states also removes the error completely, but it fails the capture even without any detection delay: in one diagnostic run its estimator attributes the fast transient to a constant disturbance. The first pre-registered design, with a three-dimensional thrust offset, did not remove the error because three disturbance states cannot absorb the mismatch of seven physical states. So the residual is not the best way to remove the steady error.

## fullstate
The third controller of our proposal plans with the full-state Koopman model. It is stable near the hover only because we recompute the lifted state from the measurement at every step; the model itself has unstable modes. Its steady errors are close to the residual MPC's, but the capture fails already at 10 milliseconds of delay on plant A, and from 20 milliseconds the runs diverge, because the lifted features leave the training range during capture by up to 350 standard deviations. It also needs 55 to 319 milliseconds per step against a 5 millisecond period, so it is an analysis result, not a real-time controller. The physics model is needed in the capture.

## adapt
To address the generalization failure we adapted the residual online by recursive least squares, with causal updates. On the unseen plant the prediction error halves, and the worst closed-loop case improves from plus 16 to plus 8 centimetres, better than the LQR's plus 11. But on the training plant it is no better than the fixed residual, and the covariance sits at its cap because near the hover most weights are not excited. Combined with offset-free MPC the bias is zero with or without the residual.

## transient
Next we trained the residual on capture transients, since the capture starts far from the equilibrium. Predictions of those transients improve by an order of magnitude, from 8.2 to 0.57 at 100 milliseconds. But the MPC built on it is a worse capture controller: it is not safe even at zero delay. We did not diagnose why. A longer MPC horizon from 10 to 80 steps changes nothing in the number of safe delays, a heavier attitude weight adds one delay, and no setting beats the LQR.

## ablations
Ablations: cubic features cut the long-horizon error on the unseen plant from 30.6 to 5.9 at three seconds but are worse on the training plant at 100 milliseconds. The ridge parameter and the sampling period, from 2 to 10 milliseconds, make no difference. Training on noisy measurements is harmful, with a closed-loop bias of 2.8 metres, because noisy regressors bias the fit; the clean-trained residual and the offset-free MPC tolerate noise. Finally, adding air-relative thrust and quadratic drag to the truth plant does not change any conclusion.

## hypotheses
Status of our hypotheses. H1, the full-state model being unstable, is supported for prediction and it is stable inside an MPC that re-lifts every step. H2, the residual predicts best, is supported from 100 milliseconds to one second, on the training plant only. H3, residual MPC removes the bias, is only partly supported: a third on the training plant, worse on one held-out plant, and integral action does better. H4, less data, is supported.

## summary
To summarize. A residual Koopman model is the most accurate predictor from 100 milliseconds to one second and needs little data, but only on the plant it was trained on. Inside MPC it cuts the steady bias by a third, but an integrator does better, and no learned variant improved the capture. Online adaptation, transient data, tuning and ablations did not change that, and the results hold on a more realistic plant. The limits are that everything is simulation with exact state measurement; next steps are grey-box estimation of the few uncertain physical parameters, an estimator for tilt and height, and hardware. Thank you; we are happy to take questions.

## references
Backup slide with the key references, in case of questions on sources. The full bibliography is in the report.
