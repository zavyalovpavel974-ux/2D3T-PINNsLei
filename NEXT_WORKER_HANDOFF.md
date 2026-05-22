# Handoff Summary: 2D 3T PINNs Reproduction

## What Was Achieved

The reproduction work has moved from a blocked state to a runnable pipeline.
Initially, the public author code could not run because the required numerical
reference files (`sol1_*.txt`) were missing. The current workspace now contains
a reference-generation workflow, exported reference files in the author format,
and smoke-tested author scripts that can enter GPU training.

Main achievements:

- Added a reproducible helper workflow under `reference_solver/`.
- Generated strict low-resolution `20x20` reference solutions for:
  - `Aei=70, Kr=Ar`
  - `Aei=700, Kr=Ar*Tr`
- Ran the planned intermediate `32x32` strict-grid experiment:
  - `Aei=70, Kr=Ar` completed and exported successfully.
  - `Aei=700, Kr=Ar*Tr` reached `t=0.965092` but did not complete within the
    planned 30-minute cap, so no complete `32x32` `.npz` was saved for that
    case.
- Validated the generated references:
  - no `NaN` or `Inf`
  - initial/early temperature near `3e-4`
  - top photon boundary satisfies `Tr(y=1)=3e-4+2t` with zero validation error
- Exported the reference data into the exact text format expected by the author
  scripts.
- Created `80x80_from20` interpolated files for pipeline smoke tests.
- Copied 11 `sol1_*.txt` files into the `Lei_code` root so the author scripts
  can find them directly.
- Fixed a runtime compatibility issue in the inverse script where a `(1,)`
  tensor/NumPy value was formatted as a scalar.
- Ensured internal figure folders are created before intermediate plots are
  saved.
- Documented the current reproduction state in `reproduction_report.md`.

## Current Demonstrated Behavior

The author inverse script now successfully reads the five required `Aei=70,
Kr=Ar` reference files, passes the previous `FileNotFoundError` and `80*80`
indexing blockers, uses the local GPU, and enters training.

Observed inverse smoke-test output:

```text
Using GPU, NVIDIA GeForce RTX 4060 Laptop GPU
It: 0, rho: 1.00000e+00, Loss: 6.423e+03
```

The Example 5 forward/transfer-learning script also starts correctly, creates
its output directory, uses the GPU, and enters the first `Aei=70` stage.

Observed Example 5 smoke-test output:

```text
Create Folder: ./figures/
Create Folder: ./figures/Train_6000_30000_2406032237/
Using GPU, NVIDIA GeForce RTX 4060 Laptop GPU
Aei: 0
```

These smoke tests were intentionally cut off by a 120-second timeout. They are
not full training runs.

## Important Caveat

The current root-level `80x80` `sol1_*.txt` files are interpolated from strict
`20x20` reference solutions. They are useful for checking that the author PINNs
code can load data and enter training, but they are not paper-level strict
`80x80` reference solutions.

Strict paper reproduction is therefore not complete yet.

The main unresolved blocker is generating reliable strict `80x80` traditional
numerical reference data.

Current SciPy/JFNK reference solver behavior:

- `20x20` works for both target cases.
- Direct strict `80x80` is too slow and not yet robust enough.
- `Aei=70, Kr=Ar, 80x80` failed once after about 699 seconds at `t=0.000055`
  using the original absolute Newton norm.
- After switching to an RMS residual criterion, it advanced to `t=0.007746`,
  but still failed after about 512 seconds near the `1e-3` tolerance edge.

## Key Files and Directories

- `reference_solver/generate_reference.py`  
  Main helper script. Supports `solve`, `validate`, `export`, and `resample`.

- `reference_exports/aei70_krar_20/`  
  Strict `20x20` reference data for `Aei=70, Kr=Ar`.

- `reference_exports/aei70_krar_32/`  
  Strict `32x32` reference data for `Aei=70, Kr=Ar`. This run completed in
  about 1066 s with 267 accepted steps; validation passed and author-format
  text files were exported.

- `reference_exports/aei700_krartr_20/`  
  Strict `20x20` reference data for `Aei=700, Kr=Ar*Tr`.

- `reference_exports/aei700_krartr_32/`  
  Not present as a complete solve output. The attempted strict `32x32` run
  timed out after 1800 s at the last printed progress line
  `step=525, t=0.965092, residual=9.187e-04`.

- `reference_exports/aei70_krar_80_from20/`  
  Interpolated `80x80` smoke-test data for the inverse/Example 2 path.

- `reference_exports/aei700_krartr_80_from20/`  
  Interpolated `80x80` smoke-test data for Example 5.

- `reproduction_report.md`  
  Current reproduction log, commands, validation checklist, run notes, and open
  risks.

- `sub_2D3T_wei_aei70_wer_krar_inverse.py`  
  Patched for scalar formatting compatibility and internal figure directory
  creation.

- `sub_2D3T_wei_aei700_wer_krartr_time.py`  
  Patched for internal figure directory creation.

## Recommended Next Tasks

1. Improve or replace the strict `80x80` reference solver.
   - Best next direction: implement a stronger sparse Jacobian/preconditioner,
     or port the CuPy/JFNK approach from the provided reference-solution Word
     document into a working local setup.
   - The current SciPy matrix-free JFNK solver is good enough for low-resolution
     checks but not for paper-grade `80x80` production.

2. Improve the intermediate-grid path before trying `40x40`.
   - `32x32` is feasible for `Aei=70, Kr=Ar`, but `Aei=700, Kr=Ar*Tr` did not
     complete within 30 minutes despite getting close to `t=1`.
   - Best practical next step is adding checkpoint/resume support or improving
     the solver/preconditioner before another longer `aei700_krartr_32` attempt.

3. Complete one full inverse-script training run using the `80x80_from20`
   smoke-test files.
   - This should be labeled clearly as a pipeline validation run, not a strict
     paper reproduction.
   - Save stdout/stderr, runtime, figures, model outputs, and final errors.

4. Complete one full Example 5 transfer-learning run using the `80x80_from20`
   smoke-test files.
   - Run the `Aei=70 -> 400 -> 700` chain.
   - Save all stage outputs and training logs.

5. Once strict `80x80` reference data is available, rerun the author scripts and
   compare against the paper tables.
   - Target tables: Table 4, Table 6, Table 7, Table 9, Table 11, Table 12.
   - Keep strict paper results separate from low-resolution or interpolated
     pipeline-validation results.

## Current Bottom Line

The reproduction pipeline is now assembled and the author code can run past the
original missing-data blockers. The remaining hard problem is producing strict
`80x80` numerical reference solutions that are close enough to the authors'
unpublished traditional solver to support a real paper-table comparison.
