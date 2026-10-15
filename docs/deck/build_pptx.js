// Builds docs/deck/progress-review.pptx. Speaker notes are read from docs/deck/speaker-notes.md.
// Usage: NODE_PATH=<folder with pptxgenjs>/node_modules node docs/deck/build_pptx.js
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "../..");   // repository root
const FIG = path.join(ROOT, "results/figures");
const NOTES = path.join(ROOT, "docs/deck/speaker-notes.md");
const OUT = path.join(ROOT, "docs/deck/progress-review.pptx");

// pptxgenjs writes Office's default color scheme into the theme; replace it with ours.
async function applyTheme(file, theme) {
  const JSZip = require(require.resolve("jszip", { paths: [require.resolve("pptxgenjs")] }));
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const part = "ppt/theme/theme1.xml";
  const xml = await zip.file(part).async("string");
  const slots = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"];
  const scheme = `<a:clrScheme name="${theme.name}">` +
    slots.map((k) => `<a:${k}><a:srgbClr val="${theme.colors[k]}"/></a:${k}>`).join("") + "</a:clrScheme>";
  const out = xml.replace(/<a:clrScheme\b[\s\S]*?<\/a:clrScheme>/, scheme);
  if (out === xml) throw new Error("no color scheme found in " + part);
  zip.file(part, out);
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

const THEME = {
  name: "Rotor Loss Recovery",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1E2433", lt1: "FFFFFF", dk2: "16233F", lt2: "F2F4F8",
    accent1: "2A62C4", accent2: "B9531C", accent3: "A9C4F0",
    accent4: "E8EFFB", accent5: "FBEDE5", accent6: "5B6472",
    hlink: "2A62C4", folHlink: "6A4FB0",
  },
};
const HEX = THEME.colors;   // for hex-only options (borders)

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                 // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Rotor Loss Recovery: Progress Review";
const C = pres.SchemeColor;

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

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: 0.6, y: 0.32, w: 9.0, h: 0.36, fontSize: 12, bold: true, color: C.accent1, charSpacing: 1, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.66, w: 12.1, h: 0.78, fontSize: 30, bold: true, color: C.text2, margin: 0, valign: "top", align: "left" }, text: "" } },
    { text: { text: "EE650 · Progress review", options: { x: 0.6, y: 7.0, w: 8.0, h: 0.3, fontSize: 10, color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: 12.1, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
});
pres.defineSlideMaster({
  title: "DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: 0.8, y: 1.9, w: 11.5, h: 0.4, fontSize: 14, bold: true, color: C.accent3, charSpacing: 1, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.45, w: 11.7, h: 1.9, fontSize: 40, bold: true, color: C.background1, margin: 0, valign: "top", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.45, w: 11.5, h: 1.0, fontSize: 20, color: C.accent3, margin: 0, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "DARK_CONTENT",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: 0.6, y: 0.32, w: 9.0, h: 0.36, fontSize: 12, bold: true, color: C.accent3, charSpacing: 1, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.66, w: 12.1, h: 0.78, fontSize: 30, bold: true, color: C.background1, margin: 0, valign: "top", align: "left" }, text: "" } },
  ],
});

// ------------------------------------------------------------------ helpers
const FIGSIZE = {
  "e1_rho_sweep.png": [1780, 1185], "e3_failed_lqr_nonlinear.png": [2159, 637],
  "e6_data_efficiency.png": [1098, 700],
  "e6_multistep_error.png": [2179, 1381], "e7_altitude.png": [1981, 715],
};
function figure(slide, file, x, y, w, alt) {
  const [W, H] = FIGSIZE[file];
  const h = w * H / W;
  slide.addImage({ path: path.join(FIG, file), x, y, w, h, altText: alt, objectName: file });
  return h;
}
function text(slide, runs, opts) {
  slide.addText(runs, Object.assign({ isTextBox: true, margin: 0, valign: "top", color: C.text1, fontSize: 16 }, opts));
}
function card(slide, runs, opts) {
  slide.addText(runs, Object.assign({
    isTextBox: true, shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.08, fill: { color: C.background2 },
    line: { color: C.background2 }, margin: 12, valign: "top", color: C.text1, fontSize: 16,
  }, opts));
}
function stat(slide, value, label, x, y, w, color) {
  text(slide, [
    { text: value, options: { fontSize: 36, bold: true, color: color || C.text2, breakLine: true } },
    { text: label, options: { fontSize: 13, color: C.accent6 } },
  ], { x, y, w, h: 1.1, objectName: `stat ${value}` });
}
function table(slide, rows, opts) {
  const cell = (t, o) => ({ text: t, options: Object.assign({ fontSize: 14, color: C.text1, valign: "middle", margin: [3, 6, 3, 6] }, o || {}) });
  const data = rows.map((r, i) => r.map((t) => (typeof t === "string"
    ? cell(t, i === 0 ? { bold: true, fill: { color: C.accent4 } } : {})
    : cell(t.text, Object.assign(i === 0 ? { bold: true, fill: { color: C.accent4 } } : {}, t.options)))));
  slide.addTable(data, Object.assign({ border: { type: "solid", pt: 0.75, color: "D5D9E0" }, autoPage: false }, opts));
}
function eyebrow(slide, s, orange) {
  slide.addText(orange ? [{ text: s, options: { color: C.accent2 } }] : s, { placeholder: "eyebrow" });
}
function content(section, id, eb, title, orange) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  eyebrow(s, eb, orange);
  s.addText(title, { placeholder: "title" });
  s.addNotes(notesFor(id));
  return s;
}

// ================================================================== slides
const S1 = "Problem and aim", S2 = "Foundation", S3 = "Learning the mismatch", S5 = "Plan and summary";

// 1 cover
pres.addSection({ title: S1 });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: S1 });
  s.addText("EE650 · BASICS OF MODERN CONTROL SYSTEMS · PROGRESS REVIEW", { placeholder: "eyebrow" });
  s.addText("Fault-tolerant control of a quadrotor after complete rotor loss", { placeholder: "title" });
  s.addText("Physics-informed residual Koopman model predictive control", { placeholder: "body" });
  text(s, "Pranshu Kumar · Mudita Jain · Prashant Gupta · Aarush Singh Kushwaha", { x: 0.8, y: 6.4, w: 8.4, h: 0.4, fontSize: 16, color: C.accent3, objectName: "team" });
  text(s, "October 2026", { x: 9.5, y: 6.4, w: 3.0, h: 0.4, fontSize: 16, color: C.accent3, align: "right", objectName: "date" });
  s.addNotes(notesFor("cover"));
}

// 2 timeline: what happens when a rotor fails
{
  const s = content(S1, "timeline", "THE PROBLEM", "What happens when a rotor fails");
  text(s, "A quadrotor uses its four thrusts to control four things: height, roll, pitch and yaw. With one rotor gone, the twisting (reaction) torques of the propellers no longer cancel, so the drone cannot avoid spinning.",
    { x: 0.6, y: 1.65, w: 12.1, h: 0.9, fontSize: 17, objectName: "intro" });
  const steps = [
    ["Healthy flight", "Four rotors, normal controller", C.background2],
    ["Rotor fails", "One thrust lost; yaw torque no longer balanced", C.accent5],
    ["Drone spins up", "Spin rate grows towards ≈ 19 rad/s", C.background2],
    ["Failure controller", "Holds the spin axis and the height", C.background2],
    ["Relaxed hover", "Steady spin, axis tilted 16°", C.accent4],
  ];
  const w = 2.1, gap = 0.4, y = 2.75;
  steps.forEach(([h, b, fill], i) => {
    const x = 0.6 + i * (w + gap);
    card(s, [
      { text: h, options: { fontSize: 18, bold: true, color: C.text2, breakLine: true } },
      { text: b, options: { fontSize: 14, color: C.accent6, paraSpaceBefore: 6 } },
    ], { x, y, w, h: 1.7, fill: { color: fill }, line: { color: fill }, objectName: `step ${i + 1}` });
    if (i < steps.length - 1) {
      s.addShape(pres.shapes.RIGHT_ARROW, { x: x + w + 0.06, y: y + 0.7, w: gap - 0.12, h: 0.3, fill: { color: C.accent6 }, line: { color: C.accent6 }, objectName: `arrow ${i + 1}` });
    }
  });
  card(s, [
    { text: "Giving up yaw keeps the drone flying.", options: { fontSize: 20, bold: true, color: C.text2, breakLine: true } },
    { text: "It hovers like a spinning top and moves by tilting its spin axis. Mueller & D'Andrea (2014) derived this \"relaxed hover\", showed that it is controllable and flew it.", options: { fontSize: 16, paraSpaceBefore: 8 } },
  ], { x: 0.6, y: 4.85, w: 12.1, h: 1.35, objectName: "relaxed hover statement" });
}

// 3 problem statement and research question
{
  const s = content(S1, "problem", "PROBLEM STATEMENT", "The physics model is good, but not perfect");
  card(s, [
    { text: "WHAT THE CONTROLLER RELIES ON", options: { fontSize: 13, bold: true, color: C.accent1, breakLine: true } },
    { text: "The spinning-drone model of Mueller & D'Andrea: correct equilibrium, linear about the spin, spin-up time matched in flight.", options: { fontSize: 16, paraSpaceBefore: 8 } },
  ], { x: 0.6, y: 1.7, w: 5.9, h: 1.65, fill: { color: C.accent4 }, line: { color: C.accent4 }, objectName: "relies card" });
  card(s, [
    { text: "WHAT THE MODEL MISSES", options: { fontSize: 13, bold: true, color: C.accent2, breakLine: true } },
    { text: "In flight: less thrust while spinning fast, and a spin about 20–27% slower than predicted. Also inertia errors and motor speed. A controller built on it settles with a steady error.", options: { fontSize: 16, paraSpaceBefore: 8 } },
  ], { x: 6.8, y: 1.7, w: 5.9, h: 1.65, fill: { color: C.accent5 }, line: { color: C.accent5 }, objectName: "misses card" });
  card(s, [
    { text: "RESEARCH QUESTION", options: { fontSize: 13, bold: true, color: C.accent1, breakLine: true } },
    { text: "Can a data-driven model of only the mismatch, built on top of the physics model, predict the failed drone more accurately and give a smaller steady error in MPC than the physics model alone or a Koopman model of the full dynamics?", options: { fontSize: 19, bold: true, color: C.text2, paraSpaceBefore: 8 } },
  ], { x: 0.6, y: 3.6, w: 12.1, h: 1.7, objectName: "question card" });
  text(s, [
    { text: "Koopman / EDMD: ", options: { bold: true } },
    { text: "describe the state by many nonlinear features (here all pairwise products) and fit a linear model on them by least squares. We use the same tools to learn the one-step error of the physics model; it is evaluated outside the MPC optimization, so the MPC stays a convex quadratic program (QP). " },
    { text: "Gap: ", options: { bold: true } },
    { text: "residual Koopman models exist for healthy drones and other robots (Todde et al. 2026; Bruder et al. 2025); we did not find them for the spinning regime after complete rotor loss." },
  ], { x: 0.6, y: 5.5, w: 12.1, h: 1.1, fontSize: 15, objectName: "why and gap" });
}

// 4 model
pres.addSection({ title: S2 });
{
  const s = content(S2, "model", "FOUNDATION", "Simulator and vehicle");
  const items = [
    "6-DOF rigid body, quaternion attitude, rotor gyroscopic terms",
    "Per-rotor thrust 0.2–3.8 N; a motor can also be stopped",
    "First-order motor lag, 15 ms",
    "Reduced attitude n: the \"up\" direction seen from the body (all that is controlled after the failure)",
    "RK4 integration; controller sample period 1–5 ms, command held between samples",
    "\"Truth\" plants for learning data: same simulator plus effects the design model lacks (thrust loss at high spin, inertia error, slower motors)",
  ];
  text(s, items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 8 } })),
    { x: 0.6, y: 1.75, w: 6.6, h: 4.6, fontSize: 17, objectName: "model bullets" });
  table(s, [
    ["Parameter", "Value"],
    ["Mass", "0.50 kg"], ["Arm length", "0.17 m"], ["Inertia Ixx, Izz", "3.2, 5.5 × 10⁻³ kg m²"],
    ["Thrust coefficient κf (f = κf Ω²)", "6.41 × 10⁻⁶ N s²/rad²"], ["Yaw torque per newton κτ", "0.0169 m"], ["Yaw air drag γ", "2.75 × 10⁻³ N m s/rad"],
  ], { x: 7.6, y: 1.75, w: 5.1, colW: [2.6, 2.5], objectName: "parameter table" });
  text(s, "All values from Mueller & D'Andrea, ICRA 2014, Sec. V-A", { x: 7.6, y: 4.95, w: 5.1, h: 0.35, fontSize: 12, color: C.accent6, objectName: "param source" });
}

// 5 validation
{
  const s = content(S2, "validation", "FOUNDATION", "The model matches three published papers");
  table(s, [
    ["Source", "What we compared", "Result"],
    ["Mueller & D'Andrea 2014", "Two- and three-rotor-loss equilibria", "Every printed digit (≤ 0.8%)"],
    ["Mueller & D'Andrea 2014", "One-rotor-loss equilibrium", "Thrusts, yaw rate, n_z ≤ 0.5%; pitch rate −6% *"],
    ["Mueller & D'Andrea 2016", "Their more detailed model, 5 hover cases (separate code)", "Body rates within 4%"],
    ["Sun et al. 2021", "Second drone (Parrot Bebop 2), two rotors lost", "Equal to the paper's formula"],
    [{ text: "Flight data", options: { fill: { color: C.accent4 } } }, { text: "Spin-up to 10 rad/s at the flight thrust (2.95 N)", options: { fill: { color: C.accent4 } } }, { text: "0.65 s vs 0.62 s in flight (4%)", options: { fill: { color: C.accent4 }, bold: true } }],
  ], { x: 0.6, y: 1.7, w: 12.1, colW: [2.4, 4.9, 4.8], rowH: 0.42, objectName: "validation table" });
  text(s, [
    { text: "* The paper's own published values do not satisfy its own roll equation; its other two cases match exactly. " },
    { text: "47 automated tests", options: { bold: true } },
    { text: " (46 pass; 1 expected failure keeps that inconsistency visible) also check conservation laws, closed-form solutions and these published numbers." },
  ], { x: 0.6, y: 5.35, w: 12.1, h: 0.7, fontSize: 14, color: C.accent6, objectName: "validation note" });
}

// 6 equilibrium
{
  const s = content(S2, "equilibrium", "FOUNDATION", "The spinning equilibrium");
  figure(s, "e1_rho_sweep.png", 0.6, 1.65, 7.2, "Relaxed-hover equilibrium versus thrust ratio rho");
  text(s, [
    { text: "Rotor 4 lost. f₁ = f₃: the two side rotors; f₂: the rotor opposite the failed one. Design ratio ρ = f₂/f₁ = 0.5:", options: { breakLine: true } },
    { text: "f = (2.04, 1.02, 2.04) N", options: { bold: true, color: C.text2, breakLine: true, paraSpaceBefore: 12 } },
    { text: "spin 19.6 rad/s, axis tilted 16°", options: { bold: true, color: C.text2, breakLine: true } },
    { text: "Thrusts, yaw rate and n_z match the paper within 0.5%; pitch rate and tilt are about 5% lower (see validation).", options: { breakLine: true, paraSpaceBefore: 16 } },
    { text: "The figure shows how the equilibrium changes with ρ; it reproduces the paper's Fig. 3 (minimum spin 18.6 vs 19.0 rad/s).", options: { paraSpaceBefore: 16 } },
  ], { x: 8.2, y: 2.0, w: 4.5, h: 4.0, fontSize: 17, objectName: "equilibrium text" });
}

// 7 structure
{
  const s = content(S2, "structure", "FOUNDATION", "Linear model: controllable, but what can we observe?");
  text(s, [
    { text: "7 states (p, q, r, n_x, n_y, z, v_z), inputs f₁, f₂, f₃. Linear and time-invariant in body axes.", options: { breakLine: true } },
    { text: "Open-loop modes: ±10.1j, ±19.6j, −0.51 and an altitude double integrator.", options: { breakLine: true, paraSpaceBefore: 12 } },
    { text: "Controllable: ", options: { bold: true, paraSpaceBefore: 12 } },
    { text: "the three rotors can steer all 7 states (controllability rank 7 of 7; every mode can be influenced, PBH test)." },
  ], { x: 0.6, y: 1.75, w: 5.2, h: 3.6, fontSize: 17, objectName: "linear model text" });
  table(s, [
    ["Sensors", "Observable (of 7)", "Cannot see"],
    ["Gyro", "3 / 7", "tilt, altitude"],
    ["Gyro + tilt estimate", "5 / 7", "altitude"],
    [{ text: "Gyro + barometer", options: { fill: { color: C.accent4 } } }, { text: "7 / 7", options: { fill: { color: C.accent4 } } }, { text: "none (weak)", options: { fill: { color: C.accent4 } } }],
    ["Gyro + tilt + barometer", "7 / 7", "none"],
  ], { x: 6.3, y: 1.75, w: 6.4, colW: [3.0, 1.2, 2.2], rowH: 0.42, objectName: "observability table" });
  text(s, "The equilibrium is tilted, so vertical acceleration depends on tilt. A barometer then reveals the tilt in principle, but with realistic sensor noise the weakest direction is about 2,700× less visible than with a tilt sensor (smallest observability-Gramian eigenvalue).",
    { x: 6.3, y: 4.15, w: 6.4, h: 1.2, fontSize: 15, color: C.accent6, objectName: "observability note" });
}

// 8 lqr
{
  const s = content(S2, "lqr", "FOUNDATION", "LQR baseline at the spinning equilibrium");
  stat(s, "18 ms", "input-delay margin (healthy LQR: 40 ms)", 0.6, 1.65, 3.9);
  stat(s, "ζ ≈ 0.19", "damping of the least-damped mode", 4.7, 1.65, 3.9);
  stat(s, "1.8–2.5 s", "to settle altitude, tilt and yaw rate", 8.8, 1.65, 3.9);
  figure(s, "e3_failed_lqr_nonlinear.png", 0.9, 3.0, 11.5, "Failure-mode LQR on the nonlinear model converging to the equilibrium");
  text(s, "Nonlinear simulation from 1 m below the set-point with rate and tilt errors, rotor 4 off, motor lag and thrust limits. Weights from Mueller & D'Andrea, plus motor states and altitude. The delay margin is less than half the healthy value: the spinning drone is much less forgiving.", { x: 0.6, y: 6.3, w: 12.1, h: 0.6, fontSize: 12, color: C.accent6, objectName: "lqr source" });
}

// 9 part 1 divider
pres.addSection({ title: S3 });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: S3 });
  s.addText("THE APPROACH", { placeholder: "eyebrow" });
  s.addText("Residual Koopman models of the failed vehicle", { placeholder: "title" });
  s.addText("Learn only what the physics model gets wrong, then use it inside a convex MPC.", { placeholder: "body" });
  s.addNotes(notesFor("part1"));
}

// 10 koopman
{
  const s = content(S3, "koopman", "SET-UP", "Three predictors, same data");
  const cards = [
    ["Analytical", "Mueller & D'Andrea linear model about the spinning equilibrium. No data.\nx⁺ = A_d x + B_d u", C.background2],
    ["Full-state EDMDc", "Learns everything: 55 features of the state (constant, states, all pairwise products), linear model on them.\nζ⁺ = A ζ + B u", C.background2],
    ["Residual (proposed)", "Physics model plus a learned one-step correction, clipped at d_max (99.5th percentile of the training errors).\nx⁺ = A_d x + B_d u + clip(Wᵀψ(x, u))", C.accent4],
  ];
  cards.forEach(([h, b, fill], i) => card(s, [
    { text: h, options: { fontSize: 20, bold: true, color: C.text2, breakLine: true } },
    { text: b, options: { fontSize: 16, paraSpaceBefore: 8 } },
  ], { x: 0.6 + i * 4.1, y: 1.75, w: 3.85, h: 2.3, fill: { color: fill }, line: { color: i === 2 ? C.accent1 : fill, width: i === 2 ? 1.5 : 0.75 }, objectName: `predictor ${i + 1}` }));
  text(s, [
    { text: "Data: ", options: { bold: true } },
    { text: "40 episodes × 4 s at 5 ms, from a truth plant with effects the model lacks (thrust loss at high spin, inertia error, slower motors). " },
    { text: "Test: ", options: { bold: true } },
    { text: "10 new episodes from the same plant (A) and 10 from a different one (B)." },
  ], { x: 0.6, y: 4.45, w: 12.1, h: 1.2, fontSize: 17, objectName: "data description" });
}

// 11 prediction
{
  const s = content(S3, "prediction", "PREDICTION", "From 100 ms to 1 s, the residual model predicts best");
  figure(s, "e6_multistep_error.png", 0.6, 1.6, 7.6, "Multi-step prediction error versus horizon, four panels");
  text(s, "Error at a 1 s horizon on new data from plant A (normalized RMSE: error ÷ each state's typical spread; 1 = as large as normal variation):", { x: 8.55, y: 1.6, w: 4.15, h: 0.75, fontSize: 13, color: C.accent6, objectName: "table caption" });
  table(s, [
    ["Predictor", { text: "Error", options: { align: "right" } }],
    [{ text: "Residual EDMDc", options: { bold: true, fill: { color: C.accent4 } } }, { text: "0.64", options: { bold: true, align: "right", fill: { color: C.accent4 } } }],
    ["Full-state EDMDc", { text: "0.91", options: { align: "right" } }],
    ["\"No change\" baseline", { text: "2.38", options: { align: "right" } }],
    ["Analytical model", { text: "7.09", options: { align: "right" } }],
  ], { x: 8.55, y: 2.35, w: 4.15, colW: [2.95, 1.2], rowH: 0.42, objectName: "prediction table" });
  text(s, "Below 100 ms the full-state model is better (2.5× at 20 ms); it has 4 of 55 eigenvalues just outside the unit circle and falls behind \"no change\" by 2 s, as we hypothesised. Beyond about 2 s \"no change\" beats every model. The physics model drifts in open loop (undamped modes, unmodelled thrust loss) but works in closed loop.",
    { x: 8.55, y: 4.7, w: 4.15, h: 1.5, fontSize: 15, objectName: "prediction note" });
}

// 12 limits
{
  const s = content(S3, "limits", "LIMITS", "Little data needed, no generalization yet");
  figure(s, "e6_data_efficiency.png", 0.6, 1.65, 6.4, "Prediction error at 0.5 s versus number of training episodes");
  const blocks = [
    ["Data efficiency", "With 10 episodes the residual model (0.42) beats the full-state model trained on 40 (0.48), at a 0.5 s horizon.", C.text2],
    ["Generalization fails", "On the unseen plant B, both learned models are worse than the physics model alone. Training on randomized plants helps on B only up to about 100 ms and hurts on A: a model that sees only the current state cannot tell which vehicle it is on.", C.accent2],
    ["Next", "Update the residual online with recursive least squares (it is linear in its parameters).", C.text2],
  ];
  let y = 1.7;
  blocks.forEach(([h, b, col], i) => {
    text(s, [
      { text: h, options: { fontSize: 18, bold: true, color: col, breakLine: true } },
      { text: b, options: { fontSize: 15, paraSpaceBefore: 4 } },
    ], { x: 7.4, y, w: 5.3, h: i === 1 ? 1.75 : 1.25, objectName: `limit ${i + 1}` });
    y += i === 1 ? 1.95 : 1.4;
  });
}

// 13 mpc
{
  const s = content(S3, "mpc", "CONTROL", "Residual MPC removes a third of the bias");
  figure(s, "e7_altitude.png", 0.6, 1.7, 8.3, "Altitude regulation under model mismatch for three controllers");
  stat(s, "−32%", "settles 19 cm low instead of 29 cm (plant A)", 9.3, 1.8, 3.4);
  stat(s, "0.7 ms", "QP solver per 5 ms step (4.4 ms including the Python modelling layer)", 9.3, 3.2, 3.4);
  text(s, [
    { text: "The residual is evaluated outside the QP and added as a known disturbance, so the problem stays convex (as in Todde et al. 2026). It helps for every mismatch effect of plant A; on held-out plant B the correction can push the wrong way (one variant: 47% larger error). " },
    { text: "Missing baseline: integral action (offset-free MPC), which removes a constant bias completely in theory.", options: { bold: true } },
  ],
    { x: 0.6, y: 5.0, w: 12.1, h: 1.2, fontSize: 16, objectName: "mpc note" });
}

// 14 plan
pres.addSection({ title: S5 });
{
  const s = content(S5, "plan", "NEXT STEPS", "Plan for the remaining weeks");
  table(s, [
    ["Dates", "Work"],
    ["12–18 Oct", "MPC on the full-state Koopman model (the second controller of the proposal); integral-action (offset-free) MPC baseline"],
    ["19–25 Oct", "Online adaptation of the residual by recursive least squares, to fix generalization"],
    ["26–31 Oct", "Air-relative thrust in the truth plant; residual trained on spin-up transients; presentation 31 Oct"],
    ["1–13 Nov", "Final simulations and the journal-style report, due 13 Nov"],
  ], { x: 0.6, y: 1.7, w: 12.1, colW: [1.8, 10.3], rowH: 0.62, objectName: "plan table" });
  text(s, [
    { text: "Main risk: ", options: { bold: true } },
    { text: "online adaptation may need richer data than one flight provides. Fallback: a residual that also uses a short history of states." },
  ], { x: 0.6, y: 5.35, w: 12.1, h: 0.9, fontSize: 16, objectName: "risk" });
}

// 15 summary
{
  const s = pres.addSlide({ masterName: "DARK_CONTENT", sectionTitle: S5 });
  s.addText("SUMMARY", { placeholder: "eyebrow" });
  s.addText("Where we stand", { placeholder: "title" });
  const items = [
    ["1", "The simulator matches three published papers and the flight spin-up time within 4%.", C.accent3],
    ["2", "Learning only the error of the physics model predicts best from 100 ms to 1 s; with 10 training episodes it beats a full Koopman model trained on 40.", C.accent3],
    ["3", "Inside MPC it cuts the altitude bias by a third, but does not yet generalize to an unseen vehicle. Online adaptation is next.", C.accent5],
  ];
  items.forEach(([n, t, col], i) => {
    const y = 1.9 + i * 1.35;
    text(s, n, { x: 0.6, y, w: 0.6, h: 0.9, fontSize: 36, bold: true, color: col, objectName: `num ${n}` });
    text(s, t, { x: 1.4, y: y + 0.05, w: 11.3, h: 1.1, fontSize: 19, color: C.background1, objectName: `takeaway ${n}` });
  });
  text(s, "Questions?", { x: 0.6, y: 6.3, w: 6, h: 0.5, fontSize: 20, color: C.accent3, objectName: "questions" });
  s.addNotes(notesFor("summary"));
}


// 16 references (backup)
{
  const s = content(S5, "references", "BACKUP", "Key references");
  const refs = [
    "M. W. Mueller, R. D'Andrea. Stability and control of a quadrocopter despite the complete loss of one, two, or three propellers. ICRA 2014.",
    "M. W. Mueller, R. D'Andrea. Relaxed hover solutions for multicopters. IJRR 35(8), 2016.",
    "S. Sun, X. Wang, Q. Chu, C. de Visser. Incremental nonlinear fault-tolerant control of a quadrotor with complete loss of two opposing rotors. IEEE T-RO 37(1), 2021.",
    "M. Korda, I. Mezić. Linear predictors for nonlinear dynamical systems: Koopman operator meets model predictive control. Automatica 93, 2018.",
    "M. O. Williams, I. G. Kevrekidis, C. W. Rowley. A data-driven approximation of the Koopman operator: extending dynamic mode decomposition. J. Nonlinear Sci. 25, 2015.",
    "E. Todde, S. Martini, A. Rizzo, K. P. Valavanis. Residual Koopman-based model predictive control of quadrotors. ICUAS 2026.",
    "D. Bruder, D. Bombara, R. J. Wood. A Koopman-based residual modeling approach for the control of a soft robot arm. IJRR 44(3), 2025.",
    "S. S. K. S. Narayanan, U. Vaidya. RK-MPC: residual Koopman MPC for quadruped locomotion in offroad environments. arXiv:2604.04221, 2026.",
    "B. Stellato et al. OSQP: an operator splitting solver for quadratic programs. Math. Prog. Comp. 12, 2020.",
  ];
  text(s, refs.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < refs.length - 1, paraSpaceAfter: 6 } })),
    { x: 0.6, y: 1.65, w: 12.1, h: 5.0, fontSize: 14, objectName: "reference list" });
  text(s, "Full bibliography: the project report.", { x: 0.6, y: 6.6, w: 12.1, h: 0.3, fontSize: 12, color: C.accent6, objectName: "bib note" });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
