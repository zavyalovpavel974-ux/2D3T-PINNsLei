# overnight_current Freeze Manifest

Freeze date: 2026-05-24

Scope: `runs/overnight_current`

Policy:
- Do not move, delete, overwrite, or rerun into `runs/overnight_current`.
- Treat the directory as the frozen baseline for the interpolated `80x80_from20` validation run.
- Future strict-reference or clean reruns must use a new run name.

## Run Status

- Example 2 inverse: completed, return code `0`.
- Example 5 transfer: completed, return code `0`.
- Reference mode: interpolated `80x80_from20` validation data, not strict paper-grade `80x80` reference data.

## Key Checkpoints

| Case | Path | Stage | Phase | Step | SHA256 |
| --- | --- | --- | --- | ---: | --- |
| Example 2 | `runs/overnight_current/checkpoints/example2/latest.pt` | inverse | completed | 6001 | `7865474A3420C514369A559AD8E5E2A3255B3D7D6BB2121728ACDCB771BAA7A0` |
| Example 5 | `runs/overnight_current/checkpoints/example5/latest.pt` | Aei=700 | completed | 6001 | `731531C92D12C3FD4CEFB1EEF15A0FD204BD3C01054D5E80F63B43A753352FE1` |

## Reports And Metrics

- `runs/overnight_current/reports/final_reproduction_report.md`
- `runs/overnight_current/reports/reproduction_runner_report.md`
- `runs/overnight_current/reports/example2_metrics.json`
- `runs/overnight_current/reports/example2_run_result.json`
- `runs/overnight_current/reports/example5_metrics.json`
- `runs/overnight_current/reports/example5_run_result.json`
- `runs/overnight_current/reports/environment.json`

## Logs

- `runs/overnight_current/logs/example2.stdout.log`
- `runs/overnight_current/logs/example2.stderr.log`
- `runs/overnight_current/logs/example5.stdout.log`
- `runs/overnight_current/logs/example5.stderr.log`

## Figures And Models

- `runs/overnight_current/workdir/figures`
- Example 5 stage model files include `_70_after.pt`, `_400_after.pt`, and `_700_after.pt` under the figures tree.

## Confirmed Metrics

### Example 2

- `rho = 1.102853289967324`
- `rho_rel_error = 0.0025938999702944765`
- Aggregate errors:
  - Te: L2 `2.2408507842887438e-02`, L1 `5.363038081799549e-03`, Linf `5.2142490360830906e-02`
  - Ti: L2 `2.383876653545687e-02`, L1 `2.5622473754670643e-03`, Linf `1.6381098688873302e-02`
  - Tr: L2 `3.739215546553336e-02`, L1 `2.09356635451822e-02`, Linf `2.9177772453405737e-01`

### Example 5

- Final stage: Aei=700, completed.
- Final stage training time recorded in `example5_metrics.json`: `29110.045404195786s`
- Full stage times parsed from log: Aei=70 `31099.7s`, Aei=400 `27970.4s`, Aei=700 `29110.0s`.
- Inference time: `0.04833650588989258s`
- Aggregate errors:
  - Te: L2 `7.049614628658555e-01`, L1 `3.6248202409586755e-01`, Linf `6.491585346577088e-01`
  - Ti: L2 `7.081070315755149e-01`, L1 `3.1849077651772184e-01`, Linf `5.765261544988101e-01`
  - Tr: L2 `6.686891071387449e-01`, L1 `1.0500141094014557e+00`, Linf `2.0000081988195895e+00`

## Git Snapshot At Freeze

Tracked modified files:
- `2D3T_wei_aei700_wer_krartr_time.py`
- `2D3T_wei_aei70_wer_krar_inverse.py`
- `reference_solver/generate_reference.py`
- `sub_2D3T_wei_aei700_wer_krartr_time.py`
- `sub_2D3T_wei_aei70_wer_krar_inverse.py`

New files:
- `repro_runner.py`
- `summarize_repro.py`
- `OVERNIGHT_CURRENT_FREEZE_MANIFEST.md`

## Safe Next Run Pattern

Use a new run name. Do not reuse `overnight_current`.

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'; python -u repro_runner.py --case all --run-name repro_clean_<timestamp>
```
