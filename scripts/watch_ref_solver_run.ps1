param(
  [string]$RunDir = ".\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525",
  [Alias("Pid")]
  [int]$ProcessId = 37284,
  [int]$IntervalSeconds = 600
)

if ($IntervalSeconds -lt 1) {
  throw "IntervalSeconds must be >= 1"
}

$repoRoot = (Get-Location).Path
$resolvedRunDir = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $RunDir))
$protectedRun = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "runs\overnight_current"))

$stdoutPath = Join-Path $resolvedRunDir "logs\segment_1.stdout.log"
$stderrPath = Join-Path $resolvedRunDir "logs\segment_1.stderr.log"
$checkpointPath = Join-Path $resolvedRunDir "checkpoints\segment_1.ckpt.npz"
$failedCheckpointPath = Join-Path $resolvedRunDir "checkpoints\segment_1.ckpt.failed.npz"
$outputPath = Join-Path $resolvedRunDir "outputs\reference_snapshots.npz"
$summaryDir = Join-Path $repoRoot "process-summaries"
$latestSummary = Join-Path $summaryDir "aei70-80-diag-watch-latest.md"

function Get-TailText {
  param(
    [string]$Path,
    [int]$Count = 160
  )
  if (-not (Test-Path -LiteralPath $Path)) {
    return @("[missing] $Path")
  }
  $lines = Get-Content -LiteralPath $Path -Tail $Count -Encoding UTF8 -ErrorAction SilentlyContinue
  if ($null -eq $lines -or $lines.Count -eq 0) {
    return @("[empty]")
  }
  return $lines
}

function Test-StderrFailure {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    return $false
  }
  $matches = Select-String -LiteralPath $Path -Pattern "Traceback", "RuntimeError", "error", "exception", "nan", "killed" -CaseSensitive:$false -ErrorAction SilentlyContinue
  return [bool]$matches
}

function Get-CheckpointState {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    return "checkpoint_exists=False"
  }
  $script = "import numpy as np, sys; d=np.load(sys.argv[1], allow_pickle=True); print('step={0} t={1:.12g} dt={2:.12g}'.format(int(d['step'][0]), float(d['t'][0]), float(d['dt'][0])))"
  $output = & python -c $script $Path 2>&1
  if ($LASTEXITCODE -ne 0) {
    return "checkpoint_exists=True; read_error=$($output -join ' ')"
  }
  return "checkpoint_exists=True; $($output -join ' ')"
}

function Add-FencedBlock {
  param(
    [System.Collections.Generic.List[string]]$Lines,
    [string]$Title,
    [string[]]$Content
  )
  $Lines.Add("**$Title**")
  $Lines.Add('```text')
  foreach ($line in $Content) {
    $Lines.Add($line)
  }
  $Lines.Add('```')
  $Lines.Add("")
}

New-Item -ItemType Directory -Force -Path $summaryDir | Out-Null

while ($true) {
  $checkedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
  $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
  $pidExists = $null -ne $process
  $checkpointExists = Test-Path -LiteralPath $checkpointPath
  $failedCheckpointExists = Test-Path -LiteralPath $failedCheckpointPath
  $outputExists = Test-Path -LiteralPath $outputPath
  $stderrHasFailure = Test-StderrFailure -Path $stderrPath
  $checkpointState = Get-CheckpointState -Path $checkpointPath

  $stdoutTail = Get-TailText -Path $stdoutPath -Count 160
  $stderrTail = Get-TailText -Path $stderrPath -Count 160
  $overnightStatus = & python .\repro_status.py --run-name overnight_current 2>&1
  $gitStatus = & git status --short --branch 2>&1

  if ($outputExists) {
    $status = "FINISHED"
  } elseif ($failedCheckpointExists -or $stderrHasFailure) {
    $status = "FAILED"
  } elseif (-not $pidExists) {
    $status = "STOPPED_NEED_CONFIRM"
  } else {
    $status = "RUNNING"
  }

  $lines = [System.Collections.Generic.List[string]]::new()
  $lines.Add("# Aei70 80x80 diagnostic watch latest")
  $lines.Add("")
  $lines.Add("**Status**")
  $lines.Add("- Status: $status")
  $lines.Add("- Checked at: $checkedAt")
  $lines.Add("- PID: $ProcessId")
  $lines.Add("- PID exists: $pidExists")
  if ($pidExists) {
    $lines.Add("- Process: $($process.ProcessName)")
    $lines.Add("- StartTime: $($process.StartTime)")
    $lines.Add("- CPU: $($process.CPU)")
  }
  $lines.Add("- RunDir: $resolvedRunDir")
  $lines.Add("- Protected run: $protectedRun")
  $lines.Add("- Checkpoint: $checkpointExists")
  $lines.Add("- Failed checkpoint: $failedCheckpointExists")
  $lines.Add("- Final output: $outputExists")
  $lines.Add("- Stderr failure keyword: $stderrHasFailure")
  $lines.Add("- Checkpoint state: $checkpointState")
  $lines.Add("")

  Add-FencedBlock -Lines $lines -Title "stdout tail 160" -Content $stdoutTail
  Add-FencedBlock -Lines $lines -Title "stderr tail 160" -Content $stderrTail
  Add-FencedBlock -Lines $lines -Title "overnight_current readonly status" -Content $overnightStatus
  Add-FencedBlock -Lines $lines -Title "git status --short --branch" -Content $gitStatus

  $lines.Add("**Next Action**")
  if ($status -eq "FINISHED") {
    $lines.Add("- outputs/reference_snapshots.npz exists. Do not start Segment 2; validate next.")
  } elseif ($status -eq "FAILED") {
    $lines.Add("- Failure evidence detected. Do not restart automatically; inspect stderr and failed checkpoint diagnostics.")
  } elseif ($status -eq "STOPPED_NEED_CONFIRM") {
    $lines.Add("- PID is gone and final output is missing. Confirm whether this was manual stop, crash, or outer interruption.")
  } else {
    $lines.Add("- Still running. Wait $IntervalSeconds seconds, then check again.")
  }
  $lines.Add("")
  $lines.Add("**Read-Only Constraints**")
  $lines.Add("- This watcher does not start solve processes.")
  $lines.Add("- This watcher does not stop PID $ProcessId.")
  $lines.Add("- This watcher does not write to runs/overnight_current.")
  $lines.Add("- This watcher does not modify existing reference checkpoints/logs/outputs.")

  Set-Content -LiteralPath $latestSummary -Encoding UTF8 -Value $lines

  Write-Host "[$checkedAt] status=$status pid=$ProcessId pid_exists=$pidExists $checkpointState latest=$latestSummary"
  if ($status -eq "FINISHED" -or $status -eq "FAILED" -or $status -eq "STOPPED_NEED_CONFIRM") {
    Write-Host "Terminal state reached: $status"
    if ($status -eq "FINISHED") {
      Write-Host "Next: validate outputs/reference_snapshots.npz. Do not start Segment 2."
    } elseif ($status -eq "FAILED") {
      Write-Host "Next: inspect stderr and failed checkpoint diagnostics. Do not restart automatically."
    } else {
      Write-Host "Next: confirm why PID stopped before deciding whether to resume or retry."
    }
    break
  }

  Start-Sleep -Seconds $IntervalSeconds
}
