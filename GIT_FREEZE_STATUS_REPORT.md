# Git Freeze Status Report

Date: 2026-05-24

Purpose: record the repository state at the time `runs/overnight_current` was frozen.

## Commit Status

Git commit was attempted but could not be completed because `git add` could not write the linked worktree Git index:

```text
fatal: Unable to create 'C:/Users/12412/Documents/Lei_code/.git/worktrees/Lei_code/index.lock': Permission denied
```

No files under `runs/overnight_current` were moved, deleted, or overwritten.

## Working Tree Status

```text
 M 2D3T_wei_aei700_wer_krartr_time.py
 M 2D3T_wei_aei70_wer_krar_inverse.py
 M reference_solver/generate_reference.py
 M sub_2D3T_wei_aei700_wer_krartr_time.py
 M sub_2D3T_wei_aei70_wer_krar_inverse.py
?? OVERNIGHT_CURRENT_FREEZE_MANIFEST.md
?? repro_runner.py
?? summarize_repro.py
```

## Diff Stat

```text
 2D3T_wei_aei700_wer_krartr_time.py     | 74 ++++++++++++++++++++++++++-
 2D3T_wei_aei70_wer_krar_inverse.py     | 51 ++++++++++++++++++-
 reference_solver/generate_reference.py | 66 +++++++++++++++++++++++-
 sub_2D3T_wei_aei700_wer_krartr_time.py | 93 +++++++++++++++++++++++++++++++---
 sub_2D3T_wei_aei70_wer_krar_inverse.py | 91 ++++++++++++++++++++++++++++++---
 5 files changed, 358 insertions(+), 17 deletions(-)
```

The diff stat above only includes tracked modified files. New files at this freeze point:

- `OVERNIGHT_CURRENT_FREEZE_MANIFEST.md`
- `repro_runner.py`
- `summarize_repro.py`

## Validation

The following compile check passed:

```powershell
python -m py_compile repro_runner.py summarize_repro.py 2D3T_wei_aei70_wer_krar_inverse.py 2D3T_wei_aei700_wer_krartr_time.py sub_2D3T_wei_aei70_wer_krar_inverse.py sub_2D3T_wei_aei700_wer_krartr_time.py reference_solver\generate_reference.py
```

The check emitted existing `SyntaxWarning` messages for old string escapes in author scripts, but returned exit code `0`.

## Suggested Commit Command

Run this from `C:\Users\12412\.codex\worktrees\d940\Lei_code` once Git index write permission is available:

```powershell
git add 2D3T_wei_aei700_wer_krartr_time.py 2D3T_wei_aei70_wer_krar_inverse.py reference_solver/generate_reference.py sub_2D3T_wei_aei700_wer_krartr_time.py sub_2D3T_wei_aei70_wer_krar_inverse.py repro_runner.py summarize_repro.py OVERNIGHT_CURRENT_FREEZE_MANIFEST.md GIT_FREEZE_STATUS_REPORT.md
git commit -m "Add reproducible experiment runner and freeze manifest"
```
