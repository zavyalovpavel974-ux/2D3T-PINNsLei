# 2D 3T PINNs Reproduction Context Compact

Date: 2026-05-27  
Workspace: `C:\Users\12412\Documents\Lei_code`

## One-Line Status

The author-code pipeline is runnable with local interpolated `80x80_from20` reference files, Example 2 and Example 5 have completed engineering runs under `runs/overnight_current`, but strict paper-grade reproduction is still blocked by missing reliable strict `80x80` finite-volume/KINSOL-style reference solutions.

## Goal And Scope

- User goal: reproduce the author experiments from the 2D 3T PINNs paper and compare against the paper tables.
- Paper DOI: <https://doi.org/10.1016/j.cpc.2025.109572>.
- Important distinction:
  - Pipeline validation: uses interpolated `80x80_from20` reference files derived from strict `20x20` data.
  - Strict paper reproduction: requires reliable strict `80x80` numerical reference solutions, not yet available.

## Current Data Status

- Root `sol1_*.txt` files exist and parse in the author format.
- Each root `sol1_*.txt` file has `19202` lines, matching `2 + 80*80*3`.
- These root files are currently treated as `80x80_from20` interpolated smoke-test or pipeline-validation references.
- Strict references generated so far:
  - `20x20`: completed for `aei70_krar` and `aei700_krartr`.
  - `32x32`: completed for `aei70_krar`; validation passed.
  - `32x32 aei700_krartr`: timed out near `t=0.965092`; no complete `.npz`.
  - `80x80`: not completed.

## Environment Notes

- Python: `3.12.7` Anaconda.
- PyTorch: `2.11.0+cu126`.
- GPU observed: `NVIDIA GeForce RTX 4060 Laptop GPU`.
- `KMP_DUPLICATE_LIB_OK=TRUE` is required for these runs because importing PyTorch otherwise triggers an OpenMP duplicate runtime error.

## Important Files

- Main author scripts:
  - `2D3T_wei_aei70_wer_krar_inverse.py`
  - `2D3T_wei_aei700_wer_krartr_time.py`
  - `sub_2D3T_wei_aei70_wer_krar_inverse.py`
  - `sub_2D3T_wei_aei700_wer_krartr_time.py`
- Reference tooling:
  - `reference_solver/generate_reference.py`
  - `scripts/start_ref_solver_segment.ps1`
  - `scripts/start_ref_solver_segment.py`
  - `scripts/watch_ref_solver_run.ps1`
- Runner and status tooling:
  - `repro_runner.py`
  - `repro_status.py`
  - `repro_background.py`
  - `summarize_repro.py`
- Key reports:
  - `reproduction_report.md`
  - `runs/overnight_current/reports/final_reproduction_report.md`
  - `runs/overnight_current/reports/example2_metrics.json`
  - `runs/overnight_current/reports/example5_metrics.json`
  - `reference_solver_outputs/example5_static_recalc/`
  - `process-summaries/`

## Example 2 / Inverse Status

### Earlier 2-Hour Validation Run

- Run directory: `runs/repro_current_20260522_220129`.
- Example 2 / inverse entered GPU training and ran until the 7200 s timeout.
- Last parsed line:
  - `It: 25600`
  - `rho: 1.10122`
  - `Loss: 1.133e+01`
- Relative error vs true `rho=1.1`: about `0.111%`.
- Generated intermediate image:
  - `runs/repro_current_20260522_220129/workdir/figures/Train_6000_30000_11242220/3x3.png`
- It did not naturally finish in that 2-hour window, so no final Table 4 metrics came from that run.

### Frozen `overnight_current` Run

- Status command:
  - `python repro_status.py --run-name overnight_current`
- Current status:
  - `example2`
  - stage: `inverse`
  - phase: `completed`
  - step: `6001`
  - checkpoint: `runs/overnight_current/checkpoints/example2/latest.pt`
  - metrics: `runs/overnight_current/reports/example2_metrics.json`
- Final density from metrics:
  - `rho = 1.102853289967324`
  - true `rho = 1.1`
  - relative error: `0.259389997%`
- Aggregate Example 2 metrics from `example2_metrics.json`:

| Variable | L2 | L1 | Linf |
| --- | ---: | ---: | ---: |
| Te | 2.240850784e-02 | 5.363038082e-03 | 5.214249036e-02 |
| Ti | 2.383876654e-02 | 2.562247375e-03 | 1.638109869e-02 |
| Tr | 3.739215547e-02 | 2.093566355e-02 | 2.917777245e-01 |

Paper Table 4 target values:

| Variable | L2 | L1 | Linf |
| --- | ---: | ---: | ---: |
| Te | 1.446e-02 | 5.388e-03 | 1.684e-02 |
| Ti | 7.902e-03 | 1.153e-03 | 3.742e-03 |
| Tr | 1.588e-02 | 1.436e-02 | 4.834e-02 |

Interpretation: Example 2 pipeline completed, and `rho` inversion is close to true value, but the aggregate solution errors are not paper-level, especially `Tr Linf`.

## Example 3 And Example 4 Status

- No separate full Example 3 or Example 4 reproduction run has been completed in this workspace.
- Existing author scripts mainly cover:
  - Example 2 / inverse data path through `2D3T_wei_aei70_wer_krar_inverse.py`.
  - Example 5 transfer path through `2D3T_wei_aei700_wer_krartr_time.py`.
- Some paper discussion notes and learning notes exist, but they are not completed Ex3/Ex4 experiments.

## Example 5 Status

### Frozen `overnight_current` Run

- Current status:
  - `example5`
  - stage: `700`
  - phase: `completed`
  - step: `6001`
  - checkpoint: `runs/overnight_current/checkpoints/example5/latest.pt`
  - metrics: `runs/overnight_current/reports/example5_metrics.json`
- Recorded inference time:
  - `0.04833650588989258 s`
- Recorded total/stage training time in `example5_metrics.json`:
  - `29110.045404195786 s`
- Metrics reference label:
  - `interpolated_80x80_from20`

Original aggregate Example 5 metrics from `example5_metrics.json`:

| Variable | L2 | L1 | Linf |
| --- | ---: | ---: | ---: |
| Te | 7.049614629e-01 | 3.624820241e-01 | 6.491585347e-01 |
| Ti | 7.081070316e-01 | 3.184907765e-01 | 5.765261545e-01 |
| Tr | 6.686891071e-01 | 1.050014109e+00 | 2.000008199e+00 |

Paper Table 9 target values:

| Variable | L2 | L1 | Linf |
| --- | ---: | ---: | ---: |
| Te | 1.485e-02 | 8.224e-03 | 1.547e-02 |
| Ti | 1.738e-02 | 8.504e-03 | 1.552e-02 |
| Tr | 4.216e-03 | 7.507e-03 | 1.370e-02 |

Interpretation: Example 5 engineering run completed, but original metrics are far from paper-level.

### Example 5 Per-Time Reference Recalculation

- A static post-processing issue was found:
  - The original Example 5 script reads `sol1_wei_aei700_wer_krartr_80_1.txt` for all five diagnostic time blocks.
  - That file has the same SHA256 hash as `sol1_wei_aei700_wer_krartr_1.txt`, so it is effectively the `t=1` reference.
- Read-only recalculation script:
  - `recalc_example5_metrics_per_time_reference.py`
- Corrected per-time reference mapping:
  - `1e-5` -> `sol1_wei_aei700_wer_krartr_1e-5.txt`
  - `0.3` -> `sol1_wei_aei700_wer_krartr_0p3.txt`
  - `0.5` -> `sol1_wei_aei700_wer_krartr_0p5.txt`
  - `0.7` -> `sol1_wei_aei700_wer_krartr_0p7.txt`
  - `1.0` -> `sol1_wei_aei700_wer_krartr_1.txt`
- The recalculation did not modify `runs/overnight_current`; it wrote under `reference_solver_outputs/example5_static_recalc/`.
- Corrected aggregate metrics reported in `reproduction_report.md`:

| Variable | L2 | L1 | Linf |
| --- | ---: | ---: | ---: |
| Te | 1.957274767e-01 | 4.487529124e-02 | 1.857386990e-01 |
| Ti | 2.065726908e-01 | 4.126619822e-02 | 1.662492491e-01 |
| Tr | 1.632200766e-01 | 1.178611087e-01 | 5.978782699e-01 |

Interpretation: corrected metrics are much lower than the original aggregate, but still not paper-level and still depend on interpolated references.

## Strict `80x80` Reference Solver Status

- Direct strict `80x80 aei70_krar` remains blocked.
- Repeated attempts with SciPy matrix-free JFNK fail very early near:
  - `t ~= 0.007746`
  - `dt < 1e-6`
  - residual near `1e-3`
- Increasing `NewtonMax` and `GmresMaxiter` did not solve the issue.
- Latest diagnostic evidence:
  - failed checkpoint: `reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz`
  - failure around `step=9`, `t=0.0077455892`, next `dt=7.8732e-07`.
  - rejected steps mostly show `reason=line_search_failed`.
  - GMRES callback residual became very small, around `2.535e-07`, so simply raising GMRES iterations is unlikely to be the right fix.
- Current conclusion: the strict solver likely needs method work, not more brute-force parameter increases.

Recommended strict solver next steps:

- Log full line-search alpha trial norms, not just the last rejected result.
- Log Newton residual norm sequence inside each nonlinear step.
- Log `dU` norm, max absolute update, and temperature-floor triggers.
- Investigate JFNK finite-difference epsilon and scaling.
- Consider a stronger sparse/block Jacobian or physics-aware preconditioner.
- Treat lower `dt_min` or looser `newton_tol` only as diagnostics, not paper-grade settings.

## Known Pitfalls

- Do not claim strict paper reproduction from `80x80_from20` results.
- Do not compare early Example 5 time predictions against `sol1_wei_aei700_wer_krartr_80_1.txt`; that is effectively the `t=1` reference.
- Do not overwrite or rerun inside `runs/overnight_current`; it is protected and should be treated as frozen evidence.
- Long training/background solver processes launched by Codex may not stay alive reliably; user-launched PowerShell is safer for long runs.
- Some process-summary files display mojibake in PowerShell output, but key facts have been restated cleanly in this compact.

## Protected Artifacts

Do not delete, overwrite, or mutate unless explicitly requested:

- `runs/overnight_current`
- `runs/overnight_current/checkpoints`
- `runs/overnight_current/logs`
- `runs/overnight_current/reports`
- `runs/overnight_current/workdir/figures`
- `reference_solver_outputs/*/checkpoints`
- `reference_solver_outputs/*/logs`
- `reference_solver_outputs/example5_static_recalc`
- Existing root `sol1_*.txt`

## Current Git / Worktree Notes

At the time this compact was written, `git status --short` showed modified/untracked files including:

- Modified:
  - `reference_solver/generate_reference.py`
  - `scripts/start_ref_solver_segment.ps1`
- Untracked:
  - learning/discussion notes such as `NET_F_LEARNING_NOTES.md`, `TRAIN_LEARNING_NOTES.md`, `PAPER_EXPERIMENT_DISCUSSION_NOTES.md`
  - many `process-summaries/2026-05-25-*`
  - `scripts/start_ref_solver_segment.py`
  - `scripts/watch_ref_solver_run.ps1`

Earlier `git add` failed because the linked worktree Git index could not be locked:

```text
fatal: Unable to create 'C:/Users/12412/Documents/Lei_code/.git/worktrees/Lei_code/index.lock': Permission denied
```

Do not assume the dirty tree is disposable; treat unrelated changes as user/workflow state.

## Best Next Actions

1. Preserve `runs/overnight_current` and all reference solver outputs.
2. Decide whether to commit the reusable tooling and notes, excluding large outputs/checkpoints/logs.
3. If the priority is a paper-grade result, work on the strict `80x80` reference solver first.
4. If the priority is reporting current engineering progress, base the report on:
   - Example 2 completed pipeline metrics from `example2_metrics.json`.
   - Example 5 completed pipeline metrics from `example5_metrics.json`.
   - Example 5 corrected per-time static recalculation under `reference_solver_outputs/example5_static_recalc/`.
5. For any new training or solver experiment, use a new run name/output directory. Do not reuse `overnight_current`.

