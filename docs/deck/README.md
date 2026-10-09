# Slide deck: progress review

**Files**
- [`progress-review.pptx`](progress-review.pptx): PowerPoint, 19 slides with speaker notes, theme and sections
- [`progress-review.pdf`](progress-review.pdf): PDF export of the same deck

**Sources**
- [`build_pptx.js`](build_pptx.js): generates the .pptx with [pptxgenjs](https://gitbrent.github.io/PptxGenJS/). Figures are read from `results/figures/`.
- [`speaker-notes.md`](speaker-notes.md): the speaker notes, one section per slide.

To rebuild (Node.js with pptxgenjs installed in some folder, and LibreOffice for the PDF):

```bash
NODE_PATH=<folder>/node_modules node docs/deck/build_pptx.js
soffice --headless --convert-to pdf --outdir docs/deck docs/deck/progress-review.pptx
```

## Slide list (19 slides, about 12 to 14 minutes)

| # | Slide id | Content | Figure / table used |
|---|---|---|---|
| 1 | cover | Title and team | n/a |
| 2 | recap | Aim: residual Koopman MPC and a certified detection-delay budget, and how they connect | n/a |
| 3 | timeline | Failure timeline: healthy, rotor fails, undetected for τ, capture, relaxed hover | n/a |
| 4 | model | Simulator and vehicle parameters | `rotorfail/params.py` |
| 5 | validation | Model against three published papers and flight data | `results/tables/validation_report.md` |
| 6 | equilibrium | The relaxed-hover equilibrium (E1) | `e1_rho_sweep.png` |
| 7 | structure | Controllability and observability (E2) | `e2_structure.md` |
| 8 | lqr | LQR baseline, settling times and delay margins (E3) | `e3_failed_lqr_nonlinear.png` |
| 9 | part1 | Divider: learning the mismatch | n/a |
| 10 | koopman | Three predictors, same data | n/a |
| 11 | prediction | Multi-step prediction results (E6) | `e6_multistep_error.png` |
| 12 | limits | Data efficiency and generalization (E6) | `e6_data_efficiency.png` |
| 13 | mpc | Residual Koopman MPC in closed loop (E7) | `e7_altitude.png` |
| 14 | part2 | Divider: detection delay | n/a |
| 15 | undetected | Why the delay matters: the idle-thrust bound (E4) | `e4_undetected_phase.png` |
| 16 | delay | Probability of a safe recovery versus delay (E4) | `e4_p_safe.png` |
| 17 | certificate | First LMI certificate and its limit (E5) | `e5_certificate_slice.png` |
| 18 | plan | Plan up to the final presentation (31 Oct) and report (13 Nov) | `progress/task-list.md` |
| 19 | summary | Three takeaways | n/a |
