# Reference Solver Workflow

This directory contains helper tooling for reproducing the missing numerical
reference solutions used by the public `2D3T-PINNs` scripts.

The author repository does not include the `sol1_...txt` files read by the
forward and inverse scripts. `generate_reference.py` fills that gap by either:

- solving the 2-D 3-T heat-conduction equations with a NumPy/SciPy JFNK solver;
- resampling a solved snapshot for pipeline smoke tests;
- exporting an existing `reference_snapshots.npz` into the text format expected
  by the author code.

## Quick Checks

Low-resolution export from a known-good snapshot:

```powershell
python reference_solver/generate_reference.py export `
  --case aei700_krartr `
  --npz "C:\Users\12412\Desktop\新建文件夹 (6)(1)\deliverables\example5_paper_run13\reference\reference_snapshots.npz" `
  --out-dir reference_exports\lowres_from_previous_worker
```

Generate a strict reference snapshot:

```powershell
python reference_solver/generate_reference.py solve `
  --case aei70_krar `
  --nx 80 --ny 80 `
  --out reference_exports\aei70_krar_80\reference_snapshots.npz
```

Export generated snapshots to author text files:

```powershell
python reference_solver/generate_reference.py export `
  --case aei70_krar `
  --npz reference_exports\aei70_krar_80\reference_snapshots.npz `
  --out-dir reference_exports\aei70_krar_80
```

Create an `80x80` smoke-test file from a lower-resolution solved reference:

```powershell
python reference_solver/generate_reference.py resample `
  --npz reference_exports\aei70_krar_20\reference_snapshots.npz `
  --out reference_exports\aei70_krar_80_from20\reference_snapshots.npz `
  --nx 80 --ny 80
```

## Notes

- Text files store variables as `(Tr, Te, Ti)` because the author readers remap
  `Data[:, :, (1, 2, 0)]` into `(Te, Ti, Tr)`.
- The CH material setting uses `Ar = 2.1e2 / rho^2`, matching the paper table
  and the author scripts.
- The nonlinear solver uses RMS residuals for its Newton stopping criterion, so
  the tolerance is comparable across grid resolutions.
- Resampled `80x80_from20` outputs are only for author-code plumbing checks;
  they are not paper-level `80x80` reference solutions.
- The public forward script reads only `t=1` text filenames for Example 5 even
  though the paper reports multiple time snapshots. The exporter therefore also
  writes per-time files for auditability.
