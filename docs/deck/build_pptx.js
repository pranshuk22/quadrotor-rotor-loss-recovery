// Builds docs/deck/final-presentation.pptx. Speaker notes are read from docs/deck/speaker-notes.md.
// Usage: NODE_PATH=<folder with pptxgenjs>/node_modules node docs/deck/build_pptx.js
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "../..");   // repository root
const FIG = path.join(ROOT, "docs/deck/figures");   // title rows removed by prepare_figures.py
const NOTES = path.join(ROOT, "docs/deck/speaker-notes.md");
const OUT = path.join(ROOT, "docs/deck/final-presentation.pptx");

const INK = "222222", BLUE = "1F4E79", GREY = "666666", RULE = "BBBBBB", HEAD = "E9EDF2";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                 // 13.333 x 7.5 in
pres.theme = { headFontFace: "Arial", bodyFontFace: "Arial" };
pres.title = "Fault-tolerant control of a quadrotor after complete rotor loss";

// ------------------------------------------------------------------ speaker notes ("## <slide id>" sections)
const NOTE = {};
fs.readFileSync(NOTES, "utf8").split(/^## /m).slice(1).forEach((sec) => {
  const i = sec.indexOf("\n");
  NOTE[sec.slice(0, i).trim()] = sec.slice(i + 1).replace(/\s+/g, " ").trim();
});
function notesFor(id) {
  if (!(id in NOTE)) throw new Error("no speaker notes for slide " + id);
  return NOTE[id];
}

pres.defineSlideMaster({
  title: "PLAIN",
  background: { color: "FFFFFF" },
  objects: [
    { line: { x: 0.6, y: 1.2, w: 12.13, h: 0, line: { color: RULE, width: 1 } } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.75, fontSize: 28, bold: true, color: BLUE, margin: 0, valign: "middle", align: "left" }, text: "" } },
    { text: { text: "EE650 final presentation", options: { x: 0.6, y: 7.05, w: 6, h: 0.3, fontSize: 10, color: GREY, margin: 0 } } },
  ],
  slideNumber: { x: 12.1, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: GREY, align: "right" },
});

// ------------------------------------------------------------------ helpers
const FIGSIZE = {
  "e1_rho_sweep.png": [1780, 1115], "e3_failed_lqr_nonlinear.png": [2159, 567],
  "e6_data_efficiency.png": [1098, 634], "e6_multistep_error.png": [2179, 1311], "e7_altitude.png": [1981, 645],
  "e8_altitude.png": [2181, 684], "e8_altitude_selected.png": [2181, 680], "e8_full_koopman.png": [1981, 645], "e8c_adaptive.png": [2173, 678],
  "e8d_spinup.png": [2179, 677], "e8f_ablations.png": [2179, 677],
};
function figure(slide, file, x, y, w) {
  const [W, H] = FIGSIZE[file];
  slide.addImage({ path: path.join(FIG, file), x, y, w, h: w * H / W, altText: file, objectName: file });
}
function bullets(slide, items, opts) {
  const runs = items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 8 } }));
  slide.addText(runs, Object.assign({ isTextBox: true, margin: 0, valign: "top", color: INK, fontSize: 18 }, opts));
}
function wide(slide, file, left, right, captions) {
  const [W, H] = FIGSIZE[file];
  const w = captions ? 9.6 : 11.0, x = captions ? 1.85 : 1.15;
  let y = 1.45;
  if (captions) {                                   // panel titles, as text above the two halves of the figure
    captions.forEach((c, i) => slide.addText(c, { x: x + i * w / 2, y: 1.4, w: w / 2, h: 0.35, fontSize: 14, bold: true, color: INK, align: "center", margin: 0 }));
    y = 1.8;
  }
  slide.addImage({ path: path.join(FIG, file), x, y, w, h: w * H / W, altText: file, objectName: file });
  const yb = y + w * H / W + 0.3;
  const fz = captions ? 14 : 15;
  bullets(slide, left, { x: 0.6, y: yb, w: 6.0, h: 6.95 - yb, fontSize: fz });
  bullets(slide, right, { x: 6.9, y: yb, w: 5.8, h: 6.95 - yb, fontSize: fz });
}
function note(slide, s, opts) {
  slide.addText(s, Object.assign({ isTextBox: true, margin: 0, valign: "top", color: GREY, fontSize: 12 }, opts));
}
function table(slide, rows, opts) {
  const o = opts || {};
  const fs_ = o.fontSize || 14;
  const data = rows.map((r, i) => r.map((t) => ({ text: t, options: { fontSize: fs_, color: INK, bold: i === 0, fill: i === 0 ? { color: HEAD } : undefined, valign: "middle", margin: [3, 6, 3, 6] } })));
  slide.addTable(data, Object.assign({ border: { type: "solid", pt: 0.5, color: RULE }, autoPage: false }, o));
}
function slide(id, title) {
  const s = pres.addSlide({ masterName: "PLAIN" });
  s.addText(title, { placeholder: "title" });
  s.addNotes(notesFor(id));
  return s;
}

// 1 title
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText("Fault-tolerant control of a quadrotor after complete rotor loss", { x: 0.9, y: 2.0, w: 11.5, h: 1.5, fontSize: 36, bold: true, color: BLUE, margin: 0, valign: "top", objectName: "title" });
  s.addText("Residual Koopman model predictive control", { x: 0.9, y: 3.7, w: 11.5, h: 0.6, fontSize: 22, color: INK, margin: 0, objectName: "subtitle" });
  s.addText("Pranshu Kumar, Mudita Jain, Prashant Gupta, Aarush Singh Kushwaha", { x: 0.9, y: 5.3, w: 11.5, h: 0.4, fontSize: 16, color: INK, margin: 0, objectName: "team" });
  s.addText("EE650 Basics of Modern Control Systems, November 2026", { x: 0.9, y: 5.8, w: 11.5, h: 0.4, fontSize: 16, color: GREY, margin: 0, objectName: "course" });
  s.addNotes(notesFor("cover"));
}

// 2 motivation
{
  const s = slide("rotorloss", "A quadrotor that loses a rotor");
  bullets(s, [
    "Four thrusts control four quantities: height, roll, pitch and yaw. There is no spare actuator.",
    "The propellers also twist the body (reaction torque). With four rotors the torques cancel; with three they do not, and the drone spins about its vertical axis.",
    "Mueller and D'Andrea (2014): give up the heading and accept the spin. The three remaining rotors can still hold the drone up, with the spin axis tilted.",
    "This steady spinning state is called the relaxed hover.",
    "It can be controlled with a linear controller on a reduced model: the up direction in body axes plus altitude.",
  ], { x: 0.6, y: 1.6, w: 7.2, h: 5.2, fontSize: 18 });
  table(s, [
    ["Relaxed hover (rotor 4 lost)", "Value"],
    ["Spin rate", "19.6 rad/s"], ["Spin axis tilt", "16 degrees"], ["Thrust, rotors 1 and 3", "2.04 N"], ["Thrust, rotor 2", "1.02 N"],
    ["Thrust, rotor 4", "0 N"], ["Radius of the centre-of-mass orbit", "7 mm"],
  ], { x: 8.2, y: 1.7, w: 4.5, colW: [2.9, 1.6], rowH: 0.55, fontSize: 14 });
  note(s, "Values from our simulator for the vehicle of Mueller and D'Andrea.", { x: 8.2, y: 5.7, w: 4.5, h: 0.6, fontSize: 13 });
}

// 3 problem and question
{
  const s = slide("question", "Problem and research question");
  bullets(s, [
    "The controller is designed on the physics model of Mueller and D'Andrea. It gives the right equilibrium and spin-up time, but it is not exact.",
    "In their flights the thrust was lower than predicted at high spin rate and the spin was 20 to 27 percent slower. Inertia and motor speed are also uncertain.",
    "A controller built on the model then settles with a steady error.",
    "Residual Koopman MPC exists for healthy quadrotors (Todde et al., 2026) and other robots. We did not find it applied to the spinning regime after complete rotor loss.",
  ], { x: 0.6, y: 1.55, w: 12.1, h: 3.1, fontSize: 18 });
  s.addShape(pres.ShapeType.rect, { x: 0.6, y: 4.85, w: 12.1, h: 1.75, fill: { color: "F3F5F8" }, line: { color: BLUE, width: 1.25 } });
  s.addText("Research question. Can a Koopman (EDMD) model of only the error of the physics model, used inside MPC, predict and control the failed drone better than the physics model alone, or than a Koopman model of the full dynamics?",
    { x: 0.85, y: 4.95, w: 11.6, h: 1.55, fontSize: 20, bold: true, color: INK, margin: 0, valign: "middle", objectName: "question" });
}

// 4 simulator
{
  const s = slide("simulator", "Simulator and vehicle");
  bullets(s, [
    "6-DOF rigid body with quaternion attitude and the gyroscopic terms of the propellers",
    "Thrust per rotor 0.2 to 3.8 N; a motor can be stopped",
    "First-order motor lag, 15 ms",
    "RK4 integration; controllers sampled every 1 to 5 ms",
    "Truth plants for the learning data: the same simulator with effects the design model lacks (thrust loss at high spin rate, inertia error, slower motors; later also air-relative thrust and drag)",
  ], { x: 0.6, y: 1.6, w: 6.5, h: 5.2, fontSize: 18 });
  table(s, [
    ["Parameter", "Value"],
    ["Mass", "0.50 kg"], ["Arm length", "0.17 m"], ["Inertia Ixx = Iyy", "3.2e-3 kg m2"], ["Inertia Izz", "5.5e-3 kg m2"],
    ["Thrust coefficient", "6.41e-6 N s2/rad2"], ["Yaw torque per newton", "0.0169 m"], ["Yaw drag", "2.75e-3 N m s/rad"],
    ["Thrust range per rotor", "0.2 to 3.8 N"], ["Motor time constant", "15 ms"],
  ], { x: 7.5, y: 1.7, w: 5.2, colW: [2.7, 2.5], rowH: 0.47, fontSize: 14 });
  note(s, "Values from Mueller and D'Andrea, ICRA 2014, Sec. V-A.", { x: 7.5, y: 6.5, w: 5.2, h: 0.4 });
}

// 5 validation
{
  const s = slide("validation", "Validation of the simulator");
  table(s, [
    ["Source", "Compared", "Result"],
    ["Mueller and D'Andrea 2014", "Two- and three-rotor-loss equilibria", "all printed digits match"],
    ["Mueller and D'Andrea 2014", "One-rotor-loss equilibrium", "within 0.5 %, pitch rate 6 % lower *"],
    ["Mueller and D'Andrea 2016", "Detailed model, 5 hover cases (separate code)", "body rates within 4 %"],
    ["Sun et al. 2021", "Bebop 2, two rotors lost", "equals the paper's formula"],
    ["Flight data", "Spin-up to 10 rad/s at 2.95 N", "0.65 s, flight 0.62 s"],
  ], { x: 0.6, y: 1.6, w: 12.1, colW: [3.4, 5.0, 3.7], rowH: 0.58, fontSize: 16 });
  bullets(s, [
    "The test suite (123 tests, one expected failure) also checks conservation laws, closed-form solutions and the agreement of the two model implementations.",
    "* The values printed in the paper do not satisfy the paper's own roll equation; the other two cases match exactly.",
  ], { x: 0.6, y: 5.75, w: 12.1, h: 1.2, fontSize: 14 });
}

// 6 equilibrium
{
  const s = slide("equilibrium", "Relaxed-hover equilibrium");
  figure(s, "e1_rho_sweep.png", 0.6, 1.5, 7.6);
  bullets(s, [
    "Rotor 4 lost. Thrusts f1 = f3; f2 belongs to the rotor opposite the failed one. The ratio rho = f2/f1 is 0.5.",
    "Thrusts (2.04, 1.02, 2.04) N, spin 19.6 rad/s, axis tilted 16 degrees.",
    "Thrusts, yaw rate and the vertical axis component agree with the paper within 0.5 %; pitch rate and tilt are about 5 % lower.",
    "The figure reproduces Fig. 3 of the paper (minimum spin 18.6 against 19.0 rad/s).",
  ], { x: 8.5, y: 1.6, w: 4.2, h: 5.2, fontSize: 16 });
}

// 7 linear model
{
  const s = slide("linear", "Linear model: controllability and observability");
  bullets(s, [
    "7 states (p, q, r, n_x, n_y, z, v_z) and 3 inputs; linear time-invariant in body axes.",
    "Open-loop modes: +-10.1j, +-19.6j, -0.51 and an altitude double integrator.",
    "Controllable from the three rotors: rank 7 of 7 (PBH test).",
    "With a barometer the tilt is observable only weakly: the smallest Gramian eigenvalue is about 2700 times smaller than with a tilt sensor.",
    "All controllers in this work use the exact state.",
  ], { x: 0.6, y: 1.6, w: 6.4, h: 5.2, fontSize: 20 });
  table(s, [
    ["Sensors", "Observable", "Missing"],
    ["Gyro", "3 / 7", "tilt, altitude"],
    ["Gyro + tilt", "5 / 7", "altitude"],
    ["Gyro + barometer", "7 / 7", "(weak)"],
    ["Gyro + tilt + barometer", "7 / 7", "none"],
  ], { x: 7.4, y: 1.7, w: 5.3, colW: [2.5, 1.4, 1.4], rowH: 0.75, fontSize: 16 });
  note(s, "Observable states out of 7. Gyroscopes alone cannot see tilt or height.", { x: 7.4, y: 5.7, w: 5.3, h: 0.6, fontSize: 14 });
}

// 8 lqr
{
  const s = slide("lqr", "LQR at the spinning equilibrium");
  figure(s, "e3_failed_lqr_nonlinear.png", 0.6, 1.5, 12.1);
  bullets(s, [
    "Nonlinear simulation, 1 m below the set-point with rate and tilt errors; motor lag and thrust limits included.",
    "Weights from Mueller and D'Andrea, extended by the motor states and altitude. Settling time 1.8 to 2.5 s.",
    "Input-delay margin 18 ms (healthy LQR: 40 ms); least-damped mode with damping ratio 0.19.",
  ], { x: 0.6, y: 5.0, w: 12.1, h: 1.9, fontSize: 18 });
}

// 9 predictors
{
  const s = slide("predictors", "The three predictors");
  table(s, [
    ["Predictor", "Model", "Uses data"],
    ["Analytical", "Linearization of the Mueller and D'Andrea model, discretized at 5 ms: x+ = A_d x + B_d u", "no"],
    ["Full-state EDMDc", "55 features of the state (constant, states, all pairwise products), linear model on the features", "yes, everything"],
    ["Residual EDMDc", "Analytical model plus a learned one-step correction, clipped at the 99.5th percentile of the training errors: x+ = A_d x + B_d u + clip(W' psi(x, u))", "yes, the error only"],
  ], { x: 0.6, y: 1.6, w: 12.1, colW: [2.4, 7.5, 2.2], rowH: 0.95, fontSize: 16 });
  bullets(s, [
    "Training data: 40 episodes of 4 s at 5 ms from truth plant A, failure LQR with random excitation of the commands.",
    "Test data: 10 new episodes from plant A and 10 from a different plant B.",
  ], { x: 0.6, y: 5.55, w: 12.1, h: 1.3, fontSize: 17 });
}

// 10 prediction
{
  const s = slide("prediction", "Multi-step prediction");
  figure(s, "e6_multistep_error.png", 0.6, 1.5, 7.9);
  note(s, "Normalized RMSE at a 1 s horizon, plant A:", { x: 8.8, y: 1.55, w: 3.9, h: 0.4, fontSize: 14 });
  table(s, [
    ["Predictor", "Error"],
    ["Residual EDMDc", "0.64"], ["Full-state EDMDc", "0.91"], ["No change", "2.38"], ["Analytical", "7.09"],
  ], { x: 8.8, y: 2.0, w: 3.9, colW: [2.6, 1.3], rowH: 0.42, fontSize: 15 });
  bullets(s, [
    "Below 100 ms the full-state model is better.",
    "It has 4 of 55 eigenvalues outside the unit circle and falls behind 'no change' by 2 s.",
    "Beyond about 2 s 'no change' beats every model.",
  ], { x: 8.8, y: 4.4, w: 3.9, h: 2.5, fontSize: 15 });
}

// 11 limits
{
  const s = slide("limits", "Data efficiency and generalization");
  s.addText("Error at 0.5 s against the number of training episodes", { x: 0.6, y: 1.4, w: 7.3, h: 0.35, fontSize: 14, bold: true, color: INK, align: "center", margin: 0 });
  figure(s, "e6_data_efficiency.png", 0.6, 1.85, 7.3);
  bullets(s, [
    "With 10 episodes the residual model (0.42) is better than the full-state model trained on 40 (0.48), at 0.5 s.",
    "On the unseen plant B both learned models are worse than the analytical model.",
    "Training on randomized plants helps on B only up to about 100 ms and makes A worse.",
    "The residual works as a calibration of one vehicle, not as a general model.",
  ], { x: 8.2, y: 1.6, w: 4.5, h: 5.2, fontSize: 17 });
}

// 12 mpc
{
  const s = slide("mpc", "MPC with the residual");
  wide(s, "e7_altitude.png", [
    "Horizon 20 steps of 5 ms, DARE terminal cost, thrust limits, OSQP.",
    "Plant A: steady altitude error 0.29 m (LQR) and 0.19 m (residual MPC), a reduction of 32 %.",
  ], [
    "Plant B without its thrust loss: the residual MPC is worse than the LQR (+0.164 against +0.112 m).",
    "QP solver 0.7 ms per step; 4.4 ms including the CVXPY layer.",
  ]);
}

// 13 offset-free
{
  const s = slide("offsetfree", "Offset-free MPC and integral action");
  figure(s, "e8_altitude_selected.png", 1.15, 1.45, 11.0);
  table(s, [
    ["Controller", "Bias, plant A", "Capture"],
    ["LQR", "-0.285 m", "safe to 10 ms"],
    ["Residual MPC", "-0.193 m", "safe at 0 ms"],
    ["Offset-free MPC, state model", "0.000 m", "fails at 0 ms"],
    ["LQR + integrator", "at most 0.024 m", "safe to 10 ms"],
  ], { x: 0.6, y: 5.15, w: 6.2, colW: [2.8, 1.8, 1.6], rowH: 0.34, fontSize: 12 });
  bullets(s, [
    "The LQR with an integrator removes the steady error on all six plants and keeps the capture of the LQR.",
    "The state-model offset-free MPC also removes the error but fails the capture: its estimator treats the fast transient as a constant disturbance.",
    "An offset-free MPC with a thrust-offset model (3 disturbance states for 7 physical states) leaves an error of -0.239 m.",
  ], { x: 7.1, y: 5.1, w: 5.6, h: 1.85, fontSize: 12 });
}

// 14 full-state koopman MPC
{
  const s = slide("fullstate", "MPC on the full-state Koopman model");
  wide(s, "e8_full_koopman.png", [
    "Steady error on plant A: -0.186 m (residual MPC -0.193, LQR -0.285).",
    "Stable near the hover only because the lifted state is recomputed from the measurement at every step; 4 of the 55 modes are unstable.",
  ], [
    "Capture fails already at 10 ms of delay on plant A and the runs diverge from 20 ms. The features leave the training range during capture (up to 350 standard deviations).",
    "55 to 319 ms per MPC step against a 5 ms period: an analysis result, not a real-time controller.",
  ]);
}

// 15 adaptation
{
  const s = slide("adapt", "Online adaptation of the residual");
  wide(s, "e8c_adaptive.png", [
    "Recursive least squares on the 91 x 7 residual weights, forgetting factor 0.995, causal update.",
    "Unseen plant B: prediction error about halved (100 ms: 2.8 against 5.9).",
  ], [
    "Worst closed-loop plant: +0.084 m (offline residual +0.164, LQR +0.112).",
    "Plant A: no better than the fixed residual (0.5 s error 1.30 against 0.30).",
    "The covariance trace sits at its cap: near the hover most weights are not excited.",
  ], ["Covariance trace of the adaptive residual", "Steady altitude error by plant"]);
}

// 16 transient and tuning
{
  const s = slide("transient", "Transient training and MPC tuning");
  wide(s, "e8d_spinup.png", [
    "Residual trained on capture transients (40 episodes): error on held-out transients at 100 ms 0.57, against 8.2 for the near-trim residual.",
    "The MPC built on it is not safe even at 0 ms delay.",
  ], [
    "MPC horizon 10 to 80 steps: no change in the number of safe delays. Heavier attitude weight: one more safe delay. No setting is better than the LQR.",
    "Horizon 80 needs 84 to 123 ms per step.",
  ], ["Held-out near-trim data", "Held-out capture transients"]);
}

// 17 ablations and realistic plant
{
  const s = slide("ablations", "Ablations and a more realistic plant");
  wide(s, "e8f_ablations.png", [
    "Cubic features: 3 s error on plant B 5.9 against 30.6, but worse on A at 100 ms.",
    "Ridge parameter (1e-6 to 0.1) and sampling period (2, 5, 10 ms): no effect.",
  ], [
    "Noisy measurements in the training data are harmful: bias +2.8 m in closed loop. The clean-trained residual and the offset-free MPC tolerate noise.",
    "Air-relative thrust and drag (plants A+ and B+) leave the conclusions unchanged.",
    "Steady bias: LQR -0.412 m, residual MPC -0.273 m, offset-free MPC 0.000 m.",
  ], ["Dictionary degree, test plant A", "Dictionary degree, test plant B"]);
}

// 18 hypotheses
{
  const s = slide("hypotheses", "Hypotheses");
  table(s, [
    ["", "Hypothesis", "Result"],
    ["H1", "Full-state Koopman model unstable, loses to 'no change' at long horizons", "Supported for prediction (4 of 55 eigenvalues outside the unit circle); stable inside an MPC that re-lifts every step"],
    ["H2", "Residual model predicts best", "Supported from 100 ms to 1 s, on the training plant only"],
    ["H3", "Residual MPC removes the steady bias", "Partly: -32 % on the training plant, worse on one held-out plant; integral action does better"],
    ["H4", "Residual model needs less data", "Supported: 10 episodes beat 40"],
  ], { x: 0.6, y: 1.6, w: 12.1, colW: [0.8, 4.7, 6.6], rowH: 0.95, fontSize: 17 });
}

// 19 conclusions
{
  const s = slide("conclusions", "Conclusions");
  bullets(s, [
    "The residual Koopman model is the best predictor from 100 ms to 1 s and needs little data, on the plant it was trained on.",
    "Inside MPC it reduces the steady error by about a third. An LQR with an integrator removes it almost completely and keeps the capture, so it is the better solution for the bias.",
    "Adaptation, transient training data, MPC tuning and the other ablations did not improve the capture. The results hold on a plant with air-relative thrust and drag.",
    "Limits: simulation only, exact state measurement, one vehicle.",
    "Next: grey-box estimation of the uncertain physical parameters, a state estimator for tilt and height, hardware tests.",
  ], { x: 0.6, y: 1.6, w: 12.1, h: 5.2, fontSize: 20 });
}

// 20 references
{
  const s = slide("references", "References");
  const refs = [
    "M. W. Mueller, R. D'Andrea. Stability and control of a quadrocopter despite the complete loss of one, two, or three propellers. ICRA 2014.",
    "M. W. Mueller, R. D'Andrea. Relaxed hover solutions for multicopters. IJRR 35(8), 2016.",
    "S. Sun, X. Wang, Q. Chu, C. de Visser. Incremental nonlinear fault-tolerant control of a quadrotor with complete loss of two opposing rotors. IEEE T-RO 37(1), 2021.",
    "M. Korda, I. Mezic. Linear predictors for nonlinear dynamical systems: Koopman operator meets model predictive control. Automatica 93, 2018.",
    "M. O. Williams, I. G. Kevrekidis, C. W. Rowley. A data-driven approximation of the Koopman operator: extending dynamic mode decomposition. J. Nonlinear Sci. 25, 2015.",
    "E. Todde, S. Martini, A. Rizzo, K. P. Valavanis. Residual Koopman-based model predictive control of quadrotors. ICUAS 2026.",
    "D. Bruder, D. Bombara, R. J. Wood. A Koopman-based residual modeling approach for the control of a soft robot arm. IJRR 44(3), 2025.",
    "I. Schimperna, L. Bold, K. Worthmann. Offset-free nonlinear MPC with Koopman-based surrogate models. arXiv:2504.10954, 2025.",
    "B. Stellato et al. OSQP: an operator splitting solver for quadratic programs. Math. Prog. Comp. 12, 2020.",
  ];
  bullets(s, refs, { x: 0.6, y: 1.5, w: 12.1, h: 5.3, fontSize: 15 });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  console.log("wrote", OUT);
})();
