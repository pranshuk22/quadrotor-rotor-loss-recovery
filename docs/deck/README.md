# Slide deck

**Final presentation (RQ1, residual Koopman MPC)**
- [`final-presentation.pptx`](final-presentation.pptx): PowerPoint, 22 slides (21 + 1 backup) with speaker notes, theme and sections; clean light academic template
- [`final-presentation.pdf`](final-presentation.pdf): PDF export of the same deck
- [`build_pptx.js`](build_pptx.js): generates the .pptx with [pptxgenjs](https://gitbrent.github.io/PptxGenJS/). Figures are read from `results/figures/`.
- [`speaker-notes.md`](speaker-notes.md): the speaker notes, one section per slide id.

To rebuild (Node.js with pptxgenjs installed in some folder, and LibreOffice for the PDF):

```bash
NODE_PATH=<folder>/node_modules node docs/deck/build_pptx.js
soffice --headless --convert-to pdf --outdir docs/deck docs/deck/final-presentation.pptx
```

**Earlier progress review (October 2026, kept as an archive):** `progress-review-oct.pptx/.pdf`, built by `build_pptx_oct.js` from `speaker-notes-oct.md`.

## Slide list (21 slides plus 1 backup)

The deck covers research question 1 only (the residual Koopman work); the detection-delay and certificate work is in the report.

| # | Slide id | Content | Figure / table used |
|---|---|---|---|
| 1 | cover | Title and team | n/a |
| 2 | timeline | What happens when a rotor fails; the relaxed hover | n/a |
| 3 | problem | Problem statement, research question, gap | n/a |
| 4 | model | Simulator and vehicle parameters | `rotorfail/params.py` |
| 5 | validation | Model against three published papers and flight data | `results/tables/validation_report.md` |
| 6 | equilibrium | The relaxed-hover equilibrium (E1) | `e1_rho_sweep.png` |
| 7 | structure | Controllability and observability (E2) | `e2_structure.md` |
| 8 | lqr | LQR baseline (E3) | `e3_failed_lqr_nonlinear.png` |
| 9 | part1 | Divider: the approach | n/a |
| 10 | koopman | Three predictors, same data | n/a |
| 11 | prediction | Multi-step prediction (E6) | `e6_multistep_error.png` |
| 12 | limits | Data efficiency and generalization (E6) | `e6_data_efficiency.png` |
| 13 | mpc | Residual Koopman MPC in closed loop (E7) | `e7_altitude.png` |
| 14 | part2 | Divider: is the residual the right tool? | n/a |
| 15 | offsetfree | Offset-free and integral baselines (E8a) | `e8_altitude.png`, `e8_offset_free.md` |
| 16 | fullstate | MPC on the full-state Koopman model (E8b) | `e8_full_koopman.png` |
| 17 | adapt | Online adaptation by RLS (E8c) | `e8c_adaptive.png` |
| 18 | transient | Transient training and MPC tuning (E8d, E8e) | `e8d_spinup.png` |
| 19 | ablations | Ablations and the realistic plant (E8f, E8g) | `e8f_ablations.png` |
| 20 | hypotheses | Status of H1 to H4 | n/a |
| 21 | summary | What we learned, limits and next steps | n/a |
| 22 | references | Backup: key references | `docs/report/references.bib` |
