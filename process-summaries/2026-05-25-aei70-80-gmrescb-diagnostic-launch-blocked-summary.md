# Aei70 80x80 GMRES callback 诊断启动受阻汇报

**本轮运行状态**
- 状态：外层工具环境启动受阻 / 需要用户终端启动
- 命令：
  ```powershell
  .\scripts\start_ref_solver_segment.ps1 `
    -RunDir .\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525 `
    -Segment 1 `
    -WalltimeSeconds 1800 `
    -NewtonMax 16 `
    -GmresMaxiter 300 `
    -CheckpointIntervalSteps 1 `
    -LogEveryStep `
    -LogRejectedSteps `
    -DebugOnFailure
  ```
- PID：Codex 启动返回 `34936`，约 10 秒后已不存在
- walltime 上限：1800 秒
- 运行时长：约 10 秒内退出
- 退出原因：需要确认；stdout/stderr 均为空，仍符合 Codex 工具环境后台子进程无法保活的已知现象

**本次进程概述**
- 本轮推进下一步：准备新的 GMRES callback 诊断 run，用于获取真实 80x80 下的 GMRES residual 曲线。
- 已使用新 run dir：`C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525`。
- dry-run 成功，命令参数正确。
- Codex 工具环境尝试启动后 PID 未能保活；未得到有效日志或 checkpoint。

**取得的成果**
- 新诊断 run dir 已创建。
- dry-run 确认配置：
  - case: `aei70_krar`
  - grid: `80x80`
  - walltime: `1800`
  - `newton_max=16`
  - `gmres_maxiter=300`
  - `checkpoint_interval_steps=1`
  - `--log-every-step`
  - `--log-rejected-steps`
  - `--debug-on-failure`
- 当前 stdout 路径：
  `C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\logs\segment_1.stdout.log`
- 当前 stderr 路径：
  `C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\logs\segment_1.stderr.log`
- stdout/stderr 当前均为 `0` 字节。
- 当前 checkpoint 不存在。
- 当前 failed checkpoint 不存在。
- 当前 final output 不存在。
- `runs/overnight_current` 仍为 `Protected: True`。
- Example 2 仍为 `completed`，step `6001`。
- Example 5 仍为 stage `700`，`completed`，step `6001`。

**续跑状态与检查点**
- 当前 checkpoint：不存在，目标路径为
  `C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\checkpoints\segment_1.ckpt.npz`。
- 当前阶段：reference solver strict `80x80` `aei70_krar` GMRES callback 诊断 Segment 1；不是 Example 5 的 70/400/700 阶段。
- 当前步数或优化器阶段：无有效运行，无法读取。
- 已完成阶段：没有完成任何段。
- 下一次安全启动命令：
  ```powershell
  .\scripts\start_ref_solver_segment.ps1 `
    -RunDir .\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525 `
    -Segment 1 `
    -WalltimeSeconds 1800 `
    -NewtonMax 16 `
    -GmresMaxiter 300 `
    -CheckpointIntervalSteps 1 `
    -LogEveryStep `
    -LogRejectedSteps `
    -DebugOnFailure
  ```
- 启动后检查命令：
  ```powershell
  Get-Content .\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\background\launch_segment_1.json -Encoding UTF8
  Get-Process -Id <PID>
  Get-Content .\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\logs\segment_1.stdout.log -Tail 160
  Get-Content .\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\logs\segment_1.stderr.log -Tail 160
  Test-Path .\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\checkpoints\segment_1.ckpt.npz
  Test-Path .\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\checkpoints\segment_1.ckpt.failed.npz
  Test-Path .\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\outputs\reference_snapshots.npz
  python .\repro_status.py --run-name overnight_current
  ```
- 不应执行的危险操作：
  - 不要启动 Segment 2。
  - 不要删除或覆盖旧失败 run 的 checkpoint/log。
  - 不要修改、覆盖、删除 `runs/overnight_current`。
  - 不要重跑 Example 2 / Example 5。

**遇到的阻碍**
- Codex 工具环境无法保活后台子进程，PID `34936` 快速消失。
- stdout/stderr 为空，无法从本次 Codex 启动判断 solver 数值状态。

**未完成的部分**
- GMRES callback 诊断 run 尚未在用户终端保活启动。
- 尚未获得真实 80x80 GMRES callback residual 曲线。
- 尚未生成新 run checkpoint / failed checkpoint / final output。

**在总体进程中的作用**
- 本轮已经完成下一轮诊断命令准备；剩余动作是由用户本机 PowerShell 终端启动，Codex 继续负责监控和分析。

**总体进程中仍未完成**
- strict `80x80` `aei70_krar` reference 数据仍未生成。
- production 级 80x80 求解路径仍未打通。
- validate/export/作者脚本严格复现尚未进行。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- Example 5 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint、日志、metrics、reports 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt：不要提交到 Git。

**下一步建议**
1. 用户在本机 PowerShell 终端运行“下一次安全启动命令”。
2. 启动后把 PID 告诉 Codex，或让 Codex读取 `launch_segment_1.json`。
3. Codex 读取 stdout 中新增的 `gmres_iterations` / `gmres_last`，并在 checkpoint 或 failed checkpoint 中读取 `gmres_summary`。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-25-aei70-80-gmrescb-diagnostic-launch-blocked-summary.md`

**需要确认**
- 用户是否已在本机 PowerShell 终端启动该 GMRES callback 诊断 run。
- 启动后的真实 PID 需要确认。
