# Strict 80x80 Aei70 Reference Solver Handoff

## 交接目的

本文件交给新开的 Codex/终端窗口，用于正式启动并监控 strict `80x80` `aei70_krar` reference solver 长跑。

注意：这里的“80x80”是 reference solver 正式求解，不是 Example 2 / Example 5 的 PINN 训练。

## 当前硬约束

- 不写入、移动、删除、覆盖 `runs/overnight_current`。
- 不重跑 Example 2。
- 不重跑 Example 5。
- 不启动 Example 5。
- 不提交 `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt。
- 每次检查 `overnight_current` 必须只读运行：

```powershell
python .\repro_status.py --run-name overnight_current
```

当前只读状态：

- `runs/overnight_current` exists 且 `Protected: True`
- Example 2: `completed`, step `6001`
- Example 5: stage `700`, `completed`, step `6001`

## 当前 Git / 文件状态

当前分支：

```text
main
```

当前未提交变更：

```text
 M scripts/start_ref_solver_segment.ps1
?? scripts/start_ref_solver_segment.py
?? process-summaries/2026-05-25-aei70-80-strict-segment1-launch-summary.md
?? process-summaries/2026-05-25-reference-launcher-debug-summary.md
?? process-summaries/2026-05-25-strict-80x80-aei70-handoff.md
```

其中关键启动脚本：

- `scripts/start_ref_solver_segment.py`
- `scripts/start_ref_solver_segment.ps1`

`scripts/start_ref_solver_segment.ps1` 是薄包装，实际调用 Python launcher。

## 为什么需要用户终端执行

Codex 工具环境中后台子进程无法可靠存活：

- `Start-Process` 曾遇到 PowerShell 环境变量 `Path/PATH` 冲突。
- Python launcher 在 Codex 工具环境中返回 PID 后，子进程快速退出。
- 60 秒 sleep 后台测试也无法在默认工具环境中存活。
- 前台 20x20/1 秒 reference solver 测试是健康的，能生成 checkpoint。

结论：reference solver 命令本身健康，问题在 Codex 当前工具执行环境的后台进程生命周期。正式长跑建议由用户在本机 PowerShell 终端启动。

## 目标输出目录

正式 strict `80x80` Aei70 输出目录：

```text
reference_solver_outputs/aei70_krar_80_strict_20260525
```

当前确认：

- `outputs/reference_snapshots.npz` 不存在。
- `checkpoints/segment_1.ckpt.npz` 不存在。

## 启动第 1 段

请在项目根目录运行：

```powershell
.\scripts\start_ref_solver_segment.ps1 `
  -RunDir .\reference_solver_outputs\aei70_krar_80_strict_20260525 `
  -Segment 1 `
  -WalltimeSeconds 3600
```

这会启动：

- case: `aei70_krar`
- grid: `80x80`
- walltime: `3600` 秒
- checkpoint: `reference_solver_outputs/aei70_krar_80_strict_20260525/checkpoints/segment_1.ckpt.npz`
- stdout: `reference_solver_outputs/aei70_krar_80_strict_20260525/logs/segment_1.stdout.log`
- stderr: `reference_solver_outputs/aei70_krar_80_strict_20260525/logs/segment_1.stderr.log`
- launch json: `reference_solver_outputs/aei70_krar_80_strict_20260525/background/launch_segment_1.json`

脚本会拒绝：

- 写入 `runs/overnight_current`
- 覆盖已有 `outputs/reference_snapshots.npz`
- 覆盖已有当前段 checkpoint
- 第 N 段缺少上一段 checkpoint 时启动

## 启动后立即记录

脚本会输出 JSON。请记录其中：

- `pid`
- `stdout`
- `stderr`
- `checkpoint`
- `output`
- `run_dir`

如果新窗口是 Codex，请让它读取：

```powershell
Get-Content .\reference_solver_outputs\aei70_krar_80_strict_20260525\background\launch_segment_1.json -Encoding UTF8
```

## 检查后台进程

用启动 JSON 中的 PID：

```powershell
Get-Process -Id <PID>
```

停止命令：

```powershell
Stop-Process -Id <PID>
```

如果 `Stop-Process` 不能停止整棵子进程树，可在用户终端谨慎使用：

```powershell
taskkill /PID <PID> /T /F
```

## 检查第 1 段日志

```powershell
$RUN_DIR = ".\reference_solver_outputs\aei70_krar_80_strict_20260525"
Get-Content "$RUN_DIR\logs\segment_1.stdout.log" -Tail 60
Get-Content "$RUN_DIR\logs\segment_1.stderr.log" -Tail 100
Test-Path "$RUN_DIR\checkpoints\segment_1.ckpt.npz"
Test-Path "$RUN_DIR\outputs\reference_snapshots.npz"
python .\repro_status.py --run-name overnight_current
git status --short --branch
```

如果 checkpoint 存在，读取进度：

```powershell
python -c "import numpy as np; p='reference_solver_outputs/aei70_krar_80_strict_20260525/checkpoints/segment_1.ckpt.npz'; d=np.load(p, allow_pickle=True); print({'step': int(d['step'][0]), 't': float(d['t'][0]), 'dt': float(d['dt'][0])})"
```

## 第 1 段结束后的判断

### 情况 A：输出已完成

如果存在：

```text
reference_solver_outputs/aei70_krar_80_strict_20260525/outputs/reference_snapshots.npz
```

不要再启动下一段，直接 validate。

### 情况 B：达到 walltime，checkpoint 已保存

如果 stderr 出现预期 `TimeoutError` / `walltime`，且 `segment_1.ckpt.npz` 存在，可启动第 2 段。

### 情况 C：出现异常

如果日志出现以下关键词，停止推进，使用 `process-summary` 汇报：

```text
FAILED
NEED_CONFIRM
error
traceback
exception
nan
killed
```

## 启动第 N 段

第 2 段：

```powershell
.\scripts\start_ref_solver_segment.ps1 `
  -RunDir .\reference_solver_outputs\aei70_krar_80_strict_20260525 `
  -Segment 2 `
  -WalltimeSeconds 3600
```

第 N 段同理，只改 `-Segment N`。

脚本逻辑：

- 第 N 段从 `checkpoints/segment_(N-1).ckpt.npz` resume。
- 第 N 段写入 `checkpoints/segment_N.ckpt.npz`。
- 每段独立 stdout/stderr。
- 每段独立 `background/launch_segment_N.json`。

## Validate

最终 `reference_snapshots.npz` 生成后：

```powershell
python .\reference_solver\generate_reference.py validate `
  --npz .\reference_solver_outputs\aei70_krar_80_strict_20260525\outputs\reference_snapshots.npz `
  --json-out .\reference_solver_outputs\aei70_krar_80_strict_20260525\outputs\validation.json
```

通过标准：

- 五个时间点齐全：`1e-5`, `0.3`, `0.5`, `0.7`, `1.0`
- 所有 `Te/Ti/Tr` finite
- `top_Tr_max_abs_error=0.0` 或数值上接近 0

## Export author txt

validate 通过后导出 author txt：

```powershell
python .\reference_solver\generate_reference.py export `
  --case aei70_krar `
  --npz .\reference_solver_outputs\aei70_krar_80_strict_20260525\outputs\reference_snapshots.npz `
  --out-dir .\reference_solver_outputs\aei70_krar_80_strict_20260525\author_txt
```

期望生成：

```text
sol1_wei_aei70_wer_krar_1e-5.txt
sol1_wei_aei70_wer_krar_0p3.txt
sol1_wei_aei70_wer_krar_0p5.txt
sol1_wei_aei70_wer_krar_0p7.txt
sol1_wei_aei70_wer_krar_1.txt
```

## 必须保存的汇报

每次段结束、walltime、失败、完成、validate、export 后，都使用 `process-summary` skill 汇报，并保存到：

```text
process-summaries/
```

汇报必须包含：

- 本轮运行状态
- PID
- stdout/stderr 路径
- checkpoint 路径
- 当前 `step/t/dt`
- 是否生成 `reference_snapshots.npz`
- `runs/overnight_current` 是否仍 `Protected: True`
- 是否可以安全启动下一段
- 需要确认的问题

## 已知 debug 记录

可参考：

- `process-summaries/2026-05-25-aei70-80-strict-segment1-launch-summary.md`
- `process-summaries/2026-05-25-reference-launcher-debug-summary.md`

关键结论：

- Codex 工具环境后台进程不可靠。
- 用户本机 PowerShell 终端启动是推荐方式。
- reference solver 命令本身在前台短测中健康。

