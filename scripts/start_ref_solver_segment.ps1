param(
  [string]$RunDir = ".\reference_solver_outputs\aei70_krar_80_strict_20260525",
  [Parameter(Mandatory = $true)]
  [ValidateRange(1, 2147483647)]
  [int]$Segment,
  [int]$WalltimeSeconds = 3600,
  [string]$Case = "aei70_krar",
  [int]$Nx = 80,
  [int]$Ny = 80,
  [string]$DtInit = "0.005",
  [string]$DtMin = "1e-6",
  [string]$DtMax = "0.02",
  [int]$NewtonMax = 8,
  [int]$GmresMaxiter = 120,
  [int]$CheckpointIntervalSteps = 10,
  [switch]$LogEveryStep,
  [switch]$LogRejectedSteps,
  [switch]$DebugOnFailure,
  [switch]$DetailedDiagnostics,
  [switch]$DryRun
)

$argsList = @(
  ".\scripts\start_ref_solver_segment.py",
  "--run-dir", $RunDir,
  "--segment", "$Segment",
  "--walltime-seconds", "$WalltimeSeconds",
  "--case", $Case,
  "--nx", "$Nx",
  "--ny", "$Ny",
  "--dt-init", $DtInit,
  "--dt-min", $DtMin,
  "--dt-max", $DtMax,
  "--newton-max", "$NewtonMax",
  "--gmres-maxiter", "$GmresMaxiter",
  "--checkpoint-interval-steps", "$CheckpointIntervalSteps"
)

if ($LogEveryStep) {
  $argsList += "--log-every-step"
}
if ($LogRejectedSteps) {
  $argsList += "--log-rejected-steps"
}
if ($DebugOnFailure) {
  $argsList += "--debug-on-failure"
}
if ($DetailedDiagnostics) {
  $argsList += "--detailed-diagnostics"
}
if ($DryRun) {
  $argsList += "--dry-run"
}

& python @argsList
exit $LASTEXITCODE
