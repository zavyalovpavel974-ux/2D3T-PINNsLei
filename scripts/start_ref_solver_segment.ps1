param(
  [string]$RunDir = ".\reference_solver_outputs\aei70_krar_80_strict_20260525",
  [Parameter(Mandatory = $true)]
  [ValidateRange(1, 2147483647)]
  [int]$Segment,
  [int]$WalltimeSeconds = 3600
)

if ($WalltimeSeconds -le 0) {
  throw "WalltimeSeconds must be > 0"
}

$repoRoot = (Get-Location).Path
$protectedRun = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "runs\overnight_current"))
$resolvedRunDir = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $RunDir))

if ($resolvedRunDir.Equals($protectedRun, [System.StringComparison]::OrdinalIgnoreCase) -or
    $resolvedRunDir.StartsWith($protectedRun + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "Refusing to write inside protected run directory: $resolvedRunDir"
}

$logsDir = Join-Path $RunDir "logs"
$ckptDir = Join-Path $RunDir "checkpoints"
$outDir = Join-Path $RunDir "outputs"
$bgDir = Join-Path $RunDir "background"

New-Item -ItemType Directory -Force $logsDir, $ckptDir, $outDir, $bgDir | Out-Null

$out = Join-Path $outDir "reference_snapshots.npz"
if (Test-Path $out) {
  throw "Output already exists; refusing to start solve: $out"
}

$currentCkptName = "segment_{0}.ckpt.npz" -f $Segment
$currentCkpt = Join-Path $ckptDir $currentCkptName
if (Test-Path $currentCkpt) {
  throw "Current segment checkpoint already exists; refusing to overwrite: $currentCkpt"
}

$stdout = Join-Path $logsDir ("segment_{0}.stdout.log" -f $Segment)
$stderr = Join-Path $logsDir ("segment_{0}.stderr.log" -f $Segment)

$arguments = @(
  "-u", ".\reference_solver\generate_reference.py", "solve",
  "--case", "aei70_krar",
  "--nx", "80", "--ny", "80",
  "--times", "1e-5,0.3,0.5,0.7,1.0",
  "--dt-init", "0.005",
  "--dt-max", "0.02",
  "--newton-max", "8",
  "--gmres-maxiter", "120",
  "--checkpoint", $currentCkpt,
  "--checkpoint-interval-steps", "10",
  "--max-walltime-seconds", "$WalltimeSeconds",
  "--out", $out
)

if ($Segment -gt 1) {
  $previousCkpt = Join-Path $ckptDir ("segment_{0}.ckpt.npz" -f ($Segment - 1))
  if (-not (Test-Path $previousCkpt)) {
    throw "Previous segment checkpoint missing: $previousCkpt"
  }
  $arguments = @(
    "-u", ".\reference_solver\generate_reference.py", "solve",
    "--case", "aei70_krar",
    "--nx", "80", "--ny", "80",
    "--times", "1e-5,0.3,0.5,0.7,1.0",
    "--dt-init", "0.005",
    "--dt-max", "0.02",
    "--newton-max", "8",
    "--gmres-maxiter", "120",
    "--resume-checkpoint", $previousCkpt,
    "--checkpoint", $currentCkpt,
    "--checkpoint-interval-steps", "10",
    "--max-walltime-seconds", "$WalltimeSeconds",
    "--out", $out
  )
}

$proc = Start-Process -FilePath "python" `
  -ArgumentList $arguments `
  -WorkingDirectory $repoRoot `
  -RedirectStandardOutput $stdout `
  -RedirectStandardError $stderr `
  -WindowStyle Hidden `
  -PassThru

$resolvedRunDir = (Resolve-Path $RunDir).Path
$resolvedLogsDir = (Resolve-Path $logsDir).Path
$resolvedCkptDir = (Resolve-Path $ckptDir).Path
$resolvedOutDir = (Resolve-Path $outDir).Path

$launch = @{
  pid = $proc.Id
  segment = $Segment
  command = @("python") + $arguments
  run_dir = $resolvedRunDir
  stdout = Join-Path $resolvedLogsDir ("segment_{0}.stdout.log" -f $Segment)
  stderr = Join-Path $resolvedLogsDir ("segment_{0}.stderr.log" -f $Segment)
  checkpoint = Join-Path $resolvedCkptDir $currentCkptName
  output = Join-Path $resolvedOutDir "reference_snapshots.npz"
  started_at = (Get-Date).ToString("o")
}

$launchPath = Join-Path $bgDir ("launch_segment_{0}.json" -f $Segment)
$launch | ConvertTo-Json -Depth 5 | Set-Content $launchPath -Encoding UTF8

$launch | ConvertTo-Json -Depth 5
