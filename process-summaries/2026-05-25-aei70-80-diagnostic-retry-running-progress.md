# 80x80 strict aei70 诊断重试运行中进度汇报

**本轮运行状态**
- 状态：仍在运行
- 命令：
  ```powershell
  .\scripts\start_ref_solver_segment.ps1 `
    -RunDir .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525 `
    -Segment 1 `
    -WalltimeSeconds 3600 `
    -NewtonMax 16 `
    -GmresMaxiter 300 `
    -CheckpointIntervalSteps 1 `
    -LogEveryStep `
    -LogRejectedSteps `
    -DebugOnFailure
  ```
- PID：`37284`
- walltime 上限：3600 秒
- 启动时间：`2026-05-25T13:01:57+0800`
- 退出原因：未退出；`Get-Process -Id 37284` 确认进程仍存在

**本次进程概述**
- 用户已在本机 PowerShell 终端启动 strict `80x80` `aei70_krar` 参数诊断重试。
- 本轮检查 launch json、进程、stdout/stderr、checkpoint、failed checkpoint、final output 和 `runs/overnight_current` 保护状态。
- 本次 run 使用新目录：`C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525`。

**取得的成果**
- 确认用户终端启动有效，PID `37284` 仍在运行。
- stdout 已出现 accepted step：
  ```text
  [reference] step=1 t=0.005000 dt=5.00e-03 newton=1 residual=6.455e-04 gmres_info=None
  ```
- stdout 已出现 rejected step：
  ```text
  [reference] reject step=2 t=0.005000 attempted_dt=6.000e-03 next_dt=3.000e-03 newton=3 residual=1.420e-03 reason=line_search_failed gmres_info=300
  ```
- 当前 checkpoint 已生成：`C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\checkpoints\segment_1.ckpt.npz`。
- 当前 checkpoint 读取结果：
  - `step=1`
  - `t=0.005`
  - `dt=0.006`
  - `history_len=1`
  - `diagnostics_len=0`
- 当前 final output 尚不存在：`reference_snapshots.npz` 未生成。
- 当前 failed checkpoint 尚不存在：`segment_1.ckpt.failed.npz` 未生成。
- 当前 stderr 为空。
- 确认 `runs/overnight_current` 仍存在且 `Protected: True`。
- 确认 Example 2：`completed`，step `6001`。
- 确认 Example 5：stage `700`，`completed`，step `6001`。

**续跑状态与检查点**
- 当前 checkpoint：`C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\checkpoints\segment_1.ckpt.npz`。
- 当前阶段：reference solver strict `80x80` `aei70_krar` 诊断重试 Segment 1；不是 Example 5 的 70/400/700 阶段。
- 当前步数或优化器阶段：已接受 `step=1`，`t=0.005`，checkpoint 中保存的下一步 `dt=0.006`。
- 已完成阶段：strict `80x80` reference solver 尚未完成任何段。
- 当前状态检查命令：
  ```powershell
  Get-Process -Id 37284
  Get-Content .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\logs\segment_1.stdout.log -Tail 120
  Get-Content .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\logs\segment_1.stderr.log -Tail 120
  Test-Path .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\checkpoints\segment_1.ckpt.npz
  Test-Path .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\checkpoints\segment_1.ckpt.failed.npz
  Test-Path .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\outputs\reference_snapshots.npz
  python .\repro_status.py --run-name overnight_current
  ```
- 停止命令：
  ```powershell
  Stop-Process -Id 37284
  ```
- 不应执行的危险操作：
  - 不要重复启动同一 run dir 的 Segment 1。
  - 不要启动 Segment 2。
  - 不要删除或覆盖 `runs/overnight_current`。
  - 不要重跑 Example 2 或 Example 5。

**遇到的阻碍**
- 第 2 步第一次尝试被 rejected：
  - `attempted_dt=0.006`
  - `next_dt=0.003`
  - `reason=line_search_failed`
  - `gmres_info=300`
- `gmres_info=300` 表示 GMRES 到达 `gmres_maxiter=300`，说明当前瓶颈偏向线性子问题/预条件器强度，而不只是 Newton 总迭代次数。
- checkpoint 中 `diagnostics_len=0` 是当前实现的副作用：rejected-step 诊断会写入内存并打印日志，但 checkpoint 只在 accepted step 或 failure debug 时保存；该 rejected event 尚未落入 checkpoint。

**未完成的部分**
- Segment 1 尚未完成。
- 尚未生成 final `reference_snapshots.npz`。
- 尚未生成 failed debug checkpoint。
- 尚未到 walltime。
- 尚未 validate/export。

**在总体进程中的作用**
- 本次诊断 run 已经成功捕获关键新信息：80x80 在早期第二步尝试时 GMRES 打满 300 次并导致线搜索失败。
- 这比原始失败只看到 `dt<1e-06` 更具体，支持后续优先改进 Jacobian/预条件器或线性求解策略。

**总体进程中仍未完成**
- strict `80x80` `aei70_krar` reference 数据未生成。
- production 级 80x80 求解路径未打通。
- 后续 validate、export、作者脚本严格复现尚未进行。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- Example 5 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint、日志、metrics、reports 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt：不要提交到 Git。

**下一步建议**
1. 继续让 PID `37284` 运行，观察 `dt=0.003` 是否能接受并继续推进。
2. 稍后再次检查 stdout/stderr 和 checkpoint。
3. 如果出现 `walltime`、`error`、`traceback`、`exception`、`nan`、`killed`、`FAILED` 或 `NEED_CONFIRM`，停止推进并继续结构化汇报。
4. 如果最终失败并生成 `segment_1.ckpt.failed.npz`，读取其中 `diagnostics_json`，判断 GMRES 打满是否持续发生。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-25-aei70-80-diagnostic-retry-running-progress.md`

**需要确认**
- 后续 `dt=0.003` 是否能 accepted 需要确认。
- 如果失败，failed checkpoint 中的 `diagnostics_json` 需要进一步读取。
