// Builds docs/deck/progress-review-1.pptx. Speaker notes are read from source/slides/*.html.
// Usage: NODE_PATH=<folder with pptxgenjs>/node_modules node docs/deck/build_pptx.js
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "../..");   // repository root
const FIG = path.join(ROOT, "results/figures");
const SRC = path.join(ROOT, "docs/deck/source/slides");
const OUT = path.join(ROOT, "docs/deck/progress-review-1.pptx");

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
pres.title = "Rotor Loss Recovery: Progress Review 1";
const C = pres.SchemeColor;

// ------------------------------------------------------------------ notes from the HTML sources
function notesFor(id) {
  const html = fs.readFileSync(path.join(SRC, `${id}.html`), "utf8");
  const m = html.match(/<aside>([\s\S]*?)<\/aside>/);
  return m ? m[1].replace(/&amp;/g, "&").replace(/\s+/g, " ").trim() : "";
}

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "eyebrow", type: "body", x: 0.6, y: 0.32, w: 9.0, h: 0.36, fontSize: 12, bold: true, color: C.accent1, charSpacing: 1, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.66, w: 12.1, h: 0.78, fontSize: 30, bold: true, color: C.text2, margin: 0, valign: "top", align: "left" }, text: "" } },
    { text: { text: "EE650 · Progress review 1", options: { x: 0.6, y: 7.0, w: 8.0, h: 0.3, fontSize: 10, color: C.accent6, margin: 0 } } },
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
  "e4_delay_sweep.png": [2180, 715], "e4_undetected_phase.png": [1780, 656],
  "e5_certificate_slice.png": [1416, 900], "e6_data_efficiency.png": [1098, 700],
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
const S1 = "Problem and questions", S2 = "Foundation", S3 = "RQ1: Residual Koopman", S4 = "RQ2: Detection delay", S5 = "Plan and summary";

// 1 cover
pres.addSection({ title: S1 });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: S1 });
  s.addText("EE650 · BASICS OF MODERN CONTROL SYSTEMS · PROGRESS REVIEW 1", { placeholder: "eyebrow" });
  s.addText("Fault-tolerant control of a quadrotor after complete rotor loss", { placeholder: "title" });
  s.addText("Residual Koopman MPC, and certified limits on fault-detection delay", { placeholder: "body" });
  text(s, "Pranshu Kumar · Mudita Jain · Prashant Gupta · Aarush Singh Kushwaha", { x: 0.8, y: 6.4, w: 8.4, h: 0.4, fontSize: 16, color: C.accent3, objectName: "team" });
  text(s, "October 2026", { x: 9.5, y: 6.4, w: 3.0, h: 0.4, fontSize: 16, color: C.accent3, align: "right", objectName: "date" });
  s.addNotes(notesFor("cover"));
}

// 2 recap
{
  const s = content(S1, "recap", "RECAP", "Two research questions");
  card(s, [
    { text: "RQ1 · AS PROPOSED", options: { fontSize: 13, bold: true, color: C.accent1, breakLine: true } },
    { text: "Residual Koopman MPC", options: { fontSize: 22, bold: true, color: C.text2, breakLine: true, paraSpaceBefore: 6 } },
    { text: "Can a Koopman (EDMDc) model of only the mismatch, built on the known spinning-equilibrium model of Mueller & D'Andrea, predict and control better than the physics model alone or a full-state Koopman model?", options: { fontSize: 16, paraSpaceBefore: 8 } },
  ], { x: 0.6, y: 1.7, w: 5.9, h: 2.7, fill: { color: C.accent4 }, line: { color: C.accent4 }, objectName: "RQ1 card" });
  card(s, [
    { text: "RQ2 · ADDED AFTER THE PROPOSAL", options: { fontSize: 13, bold: true, color: C.accent2, breakLine: true } },
    { text: "Certified detection-delay budget", options: { fontSize: 22, bold: true, color: C.text2, breakLine: true, paraSpaceBefore: 6 } },
    { text: "A fault detector needs 30–130 ms to notice a dead rotor. What is the largest delay for which recovery is guaranteed, and how do the RQ1 controllers change it?", options: { fontSize: 16, paraSpaceBefore: 8 } },
  ], { x: 6.8, y: 1.7, w: 5.9, h: 2.7, fill: { color: C.accent5 }, line: { color: C.accent5 }, objectName: "RQ2 card" });
  text(s, [
    { text: "The link: ", options: { bold: true } },
    { text: "each capture controller (LQR, analytical MPC, residual Koopman MPC) is compared by the detection delay it can tolerate." },
  ], { x: 0.6, y: 4.8, w: 12.1, h: 0.8, fontSize: 18, objectName: "link" });
}

// 3 timeline
{
  const s = content(S1, "timeline", "THE PROBLEM", "What happens when a rotor fails");
  const steps = [
    ["Healthy flight", "Normal controller, four rotors", C.background2],
    ["Rotor fails", "t = 0, thrust of rotor 4 lost", C.background2],
    ["Undetected, τ", "Healthy controller still flying a 3-rotor vehicle", C.accent5],
    ["Capture", "Failure controller takes over", C.background2],
    ["Relaxed hover", "Steady spin ≈ 19 rad/s, axis tilted", C.accent4],
  ];
  const w = 2.1, gap = 0.4, y = 1.95;
  steps.forEach(([h, b, fill], i) => {
    const x = 0.6 + i * (w + gap);
    card(s, [
      { text: h, options: { fontSize: 18, bold: true, color: i === 2 ? C.accent2 : C.text2, breakLine: true } },
      { text: b, options: { fontSize: 14, color: C.accent6, paraSpaceBefore: 6 } },
    ], { x, y, w, h: 1.7, fill: { color: fill }, line: { color: i === 2 ? C.accent2 : fill, width: i === 2 ? 1.5 : 0.75 }, objectName: `step ${i + 1}` });
    if (i < steps.length - 1) {
      s.addShape(pres.shapes.RIGHT_ARROW, { x: x + w + 0.06, y: y + 0.7, w: gap - 0.12, h: 0.3, fill: { color: C.accent6 }, line: { color: C.accent6 }, objectName: `arrow ${i + 1}` });
    }
  });
  card(s, [
    { text: "Most recovery methods with a guarantee assume τ = 0.", options: { fontSize: 20, bold: true, color: C.text2, breakLine: true } },
    { text: "Stability with a fixed delay is shown for a linear model; a certified maximum delay under thrust limits was not found.", options: { fontSize: 16, paraSpaceBefore: 8 } },
  ], { x: 0.6, y: 4.2, w: 12.1, h: 1.35, objectName: "gap statement" });
  text(s, "Simha et al. 2017; Al Lawati & Akhtar 2026; Başak & Prempain 2015; Strack van Schijndel et al. 2021", { x: 0.6, y: 5.8, w: 12.1, h: 0.35, fontSize: 12, color: C.accent6, objectName: "sources" });
}

// 4 model
pres.addSection({ title: S2 });
{
  const s = content(S2, "model", "FOUNDATION", "Simulator and vehicle");
  const items = [
    "6-DOF rigid body, quaternion attitude, rotor gyroscopic terms",
    "Per-rotor thrust 0.2–3.8 N; a motor can also be stopped",
    "First-order motor lag, 15 ms",
    "Reduced attitude n = Rᵀe₃: the \"up\" direction seen from the body",
    "RK4 integration; controller at 1–5 ms (zero-order hold)",
    "Truth plants for learning add thrust loss at high spin, inertia error and a different motor lag",
  ];
  text(s, items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 8 } })),
    { x: 0.6, y: 1.75, w: 6.6, h: 4.6, fontSize: 17, objectName: "model bullets" });
  table(s, [
    ["Parameter", "Value"],
    ["Mass", "0.50 kg"], ["Arm length", "0.17 m"], ["Inertia Ixx, Izz", "3.2, 5.5 × 10⁻³ kg m²"],
    ["Thrust coefficient κf", "6.41 × 10⁻⁶ N s²"], ["Torque ratio κτ", "0.0169 m"], ["Yaw drag γ", "2.75 × 10⁻³ N m s"],
  ], { x: 7.6, y: 1.75, w: 5.1, colW: [2.6, 2.5], objectName: "parameter table" });
  text(s, "All values from Mueller & D'Andrea, ICRA 2014, Sec. V-A", { x: 7.6, y: 4.95, w: 5.1, h: 0.35, fontSize: 12, color: C.accent6, objectName: "param source" });
}

// 5 validation
{
  const s = content(S2, "validation", "FOUNDATION", "The model matches three published papers");
  table(s, [
    ["Source", "What we compared", "Result"],
    ["ICRA 2014", "Two-rotor-loss equilibrium", "All published digits (≤ 0.14%)"],
    ["ICRA 2014", "Three-rotor-loss equilibrium", "All published digits (≤ 0.8%)"],
    ["ICRA 2014", "One-rotor-loss equilibrium", "f, r, n_z ≤ 0.5%; pitch rate −6% *"],
    ["ICRA 2014", "ā and controllability loss (eqs. 28, 39)", "Exact"],
    ["IJRR 2016", "Five failure cases, own implementation", "0–4%; ≤ 0.7% within rounding"],
    ["Sun et al. 2020", "Bebop 2, two-rotor loss (eq. 60)", "Exact"],
    [{ text: "Flight data", options: { fill: { color: C.accent5 } } }, { text: "Time to spin up to 10 rad/s", options: { fill: { color: C.accent5 } } }, { text: "0.80 s vs 0.62 s: model 30% slower", options: { fill: { color: C.accent5 }, bold: true } }],
  ], { x: 0.6, y: 1.7, w: 12.1, colW: [2.4, 4.9, 4.8], rowH: 0.42, objectName: "validation table" });
  text(s, [
    { text: "* The paper's own published values do not satisfy its eq. (12); its other two cases match exactly. " },
    { text: "45 automated tests", options: { bold: true } },
    { text: " also check conservation laws, closed-form solutions and these published numbers." },
  ], { x: 0.6, y: 5.35, w: 12.1, h: 0.7, fontSize: 14, color: C.accent6, objectName: "validation note" });
}

// 6 equilibrium
{
  const s = content(S2, "equilibrium", "FOUNDATION", "The spinning equilibrium");
  figure(s, "e1_rho_sweep.png", 0.6, 1.65, 7.2, "Relaxed-hover equilibrium versus thrust ratio rho");
  text(s, [
    { text: "Rotor 4 lost, design ratio ρ = f₂/f₁ = 0.5:", options: { breakLine: true } },
    { text: "f = (2.04, 1.02, 2.04) N", options: { bold: true, color: C.text2, breakLine: true, paraSpaceBefore: 12 } },
    { text: "spin 18.8 rad/s, axis tilted 16°", options: { bold: true, color: C.text2, breakLine: true } },
    { text: "Thrust, spin rate and tilt match the paper within 0.5%.", options: { breakLine: true, paraSpaceBefore: 16 } },
    { text: "The ρ sweep reproduces the paper's Fig. 3 (minimum spin 18.6 vs 19.0 rad/s).", options: { paraSpaceBefore: 16 } },
  ], { x: 8.2, y: 2.0, w: 4.5, h: 4.0, fontSize: 17, objectName: "equilibrium text" });
}

// 7 structure
{
  const s = content(S2, "structure", "FOUNDATION", "Linear model: controllable, but what can we observe?");
  text(s, [
    { text: "7 states (p, q, r, n_x, n_y, z, v_z), inputs f₁, f₂, f₃. Linear and time-invariant in body axes.", options: { breakLine: true } },
    { text: "Open-loop modes: ±10.1j, ±19.6j, −0.51 and an altitude double integrator.", options: { breakLine: true, paraSpaceBefore: 12 } },
    { text: "Controllable: ", options: { bold: true, paraSpaceBefore: 12 } },
    { text: "rank 7 of 7; every mode passes the PBH test." },
  ], { x: 0.6, y: 1.75, w: 5.2, h: 3.6, fontSize: 17, objectName: "linear model text" });
  table(s, [
    ["Sensors", "Rank", "Missing"],
    ["Gyro", "3 / 7", "tilt, altitude"],
    ["Gyro + tilt estimate", "5 / 7", "altitude"],
    [{ text: "Gyro + barometer", options: { fill: { color: C.accent4 } } }, { text: "7 / 7", options: { fill: { color: C.accent4 } } }, { text: "none (weak)", options: { fill: { color: C.accent4 } } }],
    ["Gyro + tilt + barometer", "7 / 7", "none"],
  ], { x: 6.3, y: 1.75, w: 6.4, colW: [3.0, 1.2, 2.2], rowH: 0.42, objectName: "observability table" });
  text(s, "The equilibrium is tilted, so vertical acceleration depends on tilt. A barometer alone then reveals the tilt, but about 2,700× more weakly than a tilt sensor (observability Gramian).",
    { x: 6.3, y: 4.15, w: 6.4, h: 1.2, fontSize: 15, color: C.accent6, objectName: "observability note" });
}

// 8 lqr
{
  const s = content(S2, "lqr", "FOUNDATION", "LQR baseline at the spinning equilibrium");
  stat(s, "18 ms", "input-delay margin (healthy LQR: 40 ms)", 0.6, 1.65, 3.9);
  stat(s, "ζ ≈ 0.19", "damping of the slowest oscillation", 4.7, 1.65, 3.9);
  stat(s, "1–4 s", "to settle tilt, altitude and spin", 8.8, 1.65, 3.9);
  figure(s, "e3_failed_lqr_nonlinear.png", 0.9, 3.0, 11.5, "Failure-mode LQR on the nonlinear model converging to the equilibrium");
  text(s, "Weights from Mueller & D'Andrea, plus motor states and altitude", { x: 0.6, y: 6.55, w: 12.1, h: 0.3, fontSize: 12, color: C.accent6, objectName: "lqr source" });
}

// 9 RQ1 divider
pres.addSection({ title: S3 });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: S3 });
  s.addText("RESEARCH QUESTION 1 · AS PROPOSED", { placeholder: "eyebrow" });
  s.addText("Residual Koopman models of the failed vehicle", { placeholder: "title" });
  s.addText("Learn only what the physics model gets wrong, then use it inside a convex MPC.", { placeholder: "body" });
  s.addNotes(notesFor("rq1"));
}

// 10 koopman
{
  const s = content(S3, "koopman", "RQ1 · SET-UP", "Three predictors, same data");
  const cards = [
    ["Analytical", "Mueller & D'Andrea linear model about the spinning equilibrium. No data.", C.background2],
    ["Full-state EDMDc", "Learns all the dynamics from data: 55 lifted states (quadratic dictionary).", C.background2],
    ["Residual EDMDc (proposed)", "Physics model plus a learned one-step correction e = x_true − x_model, clipped at d_max.", C.accent4],
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
  const s = content(S3, "prediction", "RQ1 · PREDICTION", "The residual model predicts best");
  figure(s, "e6_multistep_error.png", 0.6, 1.6, 7.6, "Multi-step prediction error versus horizon, four panels");
  text(s, "Error at a 1 s horizon, test family A (normalized RMSE):", { x: 8.55, y: 1.7, w: 4.15, h: 0.6, fontSize: 15, color: C.accent6, objectName: "table caption" });
  table(s, [
    ["Predictor", { text: "Error", options: { align: "right" } }],
    [{ text: "Residual EDMDc", options: { bold: true, fill: { color: C.accent4 } } }, { text: "0.42", options: { bold: true, align: "right", fill: { color: C.accent4 } } }],
    ["Full-state EDMDc", { text: "0.70", options: { align: "right" } }],
    ["\"No change\" baseline", { text: "2.0", options: { align: "right" } }],
    ["Analytical model", { text: "5.1", options: { align: "right" } }],
  ], { x: 8.55, y: 2.35, w: 4.15, colW: [2.95, 1.2], rowH: 0.42, objectName: "prediction table" });
  text(s, "Full-state EDMDc has 4 of 55 eigenvalues outside the unit circle and falls behind \"no change\" after 2–3 s, as the proposal predicted.",
    { x: 8.55, y: 4.7, w: 4.15, h: 1.5, fontSize: 15, objectName: "prediction note" });
}

// 12 limits
{
  const s = content(S3, "limits", "RQ1 · LIMITS", "Little data needed, no generalization yet");
  figure(s, "e6_data_efficiency.png", 0.6, 1.65, 6.4, "Prediction error at 0.5 s versus number of training episodes");
  const blocks = [
    ["Data efficiency", "With 10 episodes the residual model (0.32) beats the full-state model trained on 40 (0.43), at a 0.5 s horizon.", C.text2],
    ["Generalization fails", "On the unseen plant B, both learned models are worse than the physics model alone. Training on randomized plants makes them worse: the unknown parameters cannot be read from one state sample.", C.accent2],
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
  const s = content(S3, "mpc", "RQ1 · CONTROL", "Residual MPC removes a third of the bias");
  figure(s, "e7_altitude.png", 0.6, 1.7, 8.3, "Altitude regulation under model mismatch for three controllers");
  stat(s, "−32%", "steady altitude error on plant A (−0.29 → −0.19 m)", 9.3, 1.8, 3.4);
  stat(s, "≈ 5 ms", "per QP (horizon 20 × 5 ms, OSQP)", 9.3, 3.2, 3.4);
  text(s, "The residual enters the QP as a measured disturbance, so the problem stays convex (as in Todde et al. 2026, who report 35% in healthy flight). No harm on plant B. As the controller that catches the vehicle after a detection delay, neither MPC beats LQR yet.",
    { x: 0.6, y: 5.0, w: 12.1, h: 1.2, fontSize: 16, objectName: "mpc note" });
}

// 14 RQ2 divider
pres.addSection({ title: S4 });
{
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: S4 });
  s.addText([{ text: "RESEARCH QUESTION 2 · ADDED", options: { color: C.accent5 } }], { placeholder: "eyebrow" });
  s.addText("How long can fault detection take?", { placeholder: "title" });
  s.addText("Most recovery methods assume instant detection. Fast detectors take 30–130 ms.", { placeholder: "body" });
  s.addNotes(notesFor("rq2"));
}

// 15 undetected
{
  const s = content(S4, "undetected", "RQ2 · WHY DELAY MATTERS", "Before detection, nothing stops the roll", true);
  figure(s, "e4_undetected_phase.png", 1.4, 1.6, 10.5, "Tilt during the undetected phase and thrust of rotor 2");
  text(s, [
    { text: "Rotor 2 cannot go below its idle thrust (0.2 N), so the roll acceleration is at least " },
    { text: "l·f_min / I_xx = 10.6 rad/s²", options: { bold: true } },
    { text: " for any healthy-controller tuning. Tilt reaches about 13° at 100 ms and 37° at 200 ms." },
  ], { x: 0.6, y: 5.6, w: 12.1, h: 0.9, fontSize: 17, objectName: "bound statement" });
}

// 16 delay
{
  const s = content(S4, "delay", "RQ2 · KEY RESULT", "The published strategy tolerates about 10 ms", true);
  figure(s, "e4_delay_sweep.png", 0.6, 1.7, 8.3, "Altitude loss and worst tilt versus detection delay");
  text(s, "Safe recoveries, 20 random starts:", { x: 9.3, y: 1.7, w: 3.4, h: 0.4, fontSize: 15, color: C.accent6, objectName: "mc caption" });
  table(s, [
    ["Delay", { text: "Safe", options: { align: "right" } }],
    ["0 ms", { text: "20 / 20", options: { align: "right" } }],
    ["10 ms", { text: "17 / 20", options: { align: "right" } }],
    ["20 ms", { text: "6 / 20", options: { align: "right" } }],
    ["30 ms", { text: "1 / 20", options: { align: "right" } }],
    [{ text: "50 ms", options: { fill: { color: C.accent5 } } }, { text: "0 / 20", options: { align: "right", bold: true, fill: { color: C.accent5 } } }],
  ], { x: 9.3, y: 2.15, w: 3.4, colW: [1.7, 1.7], rowH: 0.4, objectName: "monte carlo table" });
  text(s, "Safe = attitude recovered, altitude loss under 2 m, never upside down (fixed before the runs). At τ = 0 the strategy loses 0.4 m, consistent with the paper's flight. With the looser \"attitude recovered\" criterion the tolerance is about 40 ms. Our model spins up more slowly than the real vehicle, so these numbers hold for the published model.",
    { x: 0.6, y: 4.85, w: 12.1, h: 1.5, fontSize: 15, objectName: "delay note" });
}

// 17 certificate
{
  const s = content(S4, "certificate", "RQ2 · FIRST CERTIFICATE", "A first LMI certificate, and its limit", true);
  figure(s, "e5_certificate_slice.png", 0.6, 1.6, 6.8, "Certified ellipse slice versus nonlinear simulation grid");
  text(s, "Saturation-aware invariant ellipsoid (Hu–Lin LMIs) for the LQR on the linear model at the spinning equilibrium.",
    { x: 7.8, y: 1.7, w: 4.9, h: 1.0, fontSize: 15, objectName: "certificate intro" });
  stat(s, "22%", "of the way to hover onset, certified", 7.8, 2.85, 2.35);
  stat(s, "70%", "recovered in simulation", 10.35, 2.85, 2.35, C.accent2);
  text(s, "The LQR fails only when the spin is near zero, exactly where the hover-onset state lies. Next: a certificate valid over the whole spin-up, treating the yaw rate r as a varying parameter (LPV).",
    { x: 7.8, y: 4.25, w: 4.9, h: 1.9, fontSize: 15, objectName: "certificate note" });
}

// 18 plan
pres.addSection({ title: S5 });
{
  const s = content(S5, "plan", "NEXT STEPS", "Plan for the remaining weeks");
  table(s, [
    ["Weeks", "RQ1 · Residual Koopman", "RQ2 · Delay budget"],
    ["1–2", "MPC on the full-state Koopman model; integral-action MPC baseline", "Read Stephan 2018 and Lanzon 2014; certificate over the spin-up (LPV in r)"],
    ["3–4", "Online residual adaptation (recursive least squares)", "Reachable set of the undetected phase; first certified delay budget τ*"],
    ["5–6", "Air-relative thrust in the truth plant; residual trained on spin-up data", "Trade study incl. yaw-drag and thrust-model sensitivity; τ* per controller"],
    ["7–8", "Ablations and write-up", "Simulation check of the certified τ*; final report"],
  ], { x: 0.6, y: 1.7, w: 12.1, colW: [1.3, 5.4, 5.4], rowH: 0.62, objectName: "plan table" });
  text(s, [
    { text: "Main risk: ", options: { bold: true } },
    { text: "a certificate over the whole spin-up may be infeasible or too conservative. Fallbacks: a parameter-dependent Lyapunov function, or a chain of nested ellipsoids." },
  ], { x: 0.6, y: 5.35, w: 12.1, h: 0.9, fontSize: 16, objectName: "risk" });
}

// 19 summary
{
  const s = pres.addSlide({ masterName: "DARK_CONTENT", sectionTitle: S5 });
  s.addText("SUMMARY", { placeholder: "eyebrow" });
  s.addText("Where we stand", { placeholder: "title" });
  const items = [
    ["1", "The simulator matches three published papers. Known gap: the real vehicle spins up about 30% faster.", C.accent3],
    ["2", "RQ1: the residual Koopman model predicts best, needs less data and cuts the MPC altitude bias by a third, but does not yet generalize to an unseen vehicle.", C.accent3],
    ["3", "RQ2: the published recovery tolerates about 10 ms of detection delay; detectors need 30–130 ms. Certifying the spin-up is next.", C.accent5],
  ];
  items.forEach(([n, t, col], i) => {
    const y = 1.9 + i * 1.35;
    text(s, n, { x: 0.6, y, w: 0.6, h: 0.9, fontSize: 36, bold: true, color: col, objectName: `num ${n}` });
    text(s, t, { x: 1.4, y: y + 0.05, w: 11.3, h: 1.1, fontSize: 19, color: C.background1, objectName: `takeaway ${n}` });
  });
  text(s, "Questions?", { x: 0.6, y: 6.3, w: 6, h: 0.5, fontSize: 20, color: C.accent3, objectName: "questions" });
  s.addNotes(notesFor("summary"));
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
