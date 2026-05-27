# 80x80 strict aei70 诊断重试下一步建议汇报

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
- 本轮检查诊断重试的当前进度，并判断接下来应继续等待、停止、还是启动下一步实验。
- 当前不应停止，也不应启动 Segment 2；应继续让 PID `37284` 跑到 walltime、失败或完成。

**取得的成果**
- 进程仍在运行。
- checkpoint 已更新到：
  - `step=4`
  - `t=0.007670000000000001`
  - `dt=0.000324`
  - `history_len=4`
  - `diagnostics_len=5`
- stdout 最新 accepted/rejected 轨迹显示：
  - `step=1`, `t=0.005000`, `dt=5.00e-03`, accepted
  - `step=2`, `attempted_dt=6.000e-03`, rejected, `gmres_info=300`
  - `step=2`, `attempted_dt=3.000e-03`, rejected, `gmres_info=300`
  - `step=2`, `t=0.006500`, `dt=1.50e-03`, accepted
  - `step=3`, `attempted_dt=1.800e-03`, rejected, `gmres_info=300`
  - `step=3`, `t=0.007400`, `dt=9.00e-04`, accepted
  - `step=4`, `attempted_dt=1.080e-03`, rejected, `gmres_info=300`
  - `step=4`, `attempted_dt=5.400e-04`, rejected, `gmres_info=300`
  - `step=4`, `t=0.007670`, `dt=2.70e-04`, accepted
- stderr 当前为空。
- failed checkpoint 尚未生成。
- final output `reference_snapshots.npz` 尚未生成。
- `runs/overnight_current` 仍 `Protected: True`。

**续跑状态与检查点**
- 当前 checkpoint：`C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\checkpoints\segment_1.ckpt.npz`
- 当前阶段：reference solver strict `80x80` `aei70_krar` 诊断重试 Segment 1；不是 Example 5 的 70/400/700 阶段。
- 当前步数或优化器阶段：`step=4`, `t=0.007670000000000001`, `dt=0.000324`。
- 已完成阶段：strict `80x80` reference solver 尚未完成任何段。
- 下一次安全检查命令：
  ```powershell
  Get-Process -Id 37284
  Get-Content .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\logs\segment_1.stdout.log -Tail 160
  Get-Content .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\logs\segment_1.stderr.log -Tail 160
  Test-Path .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\checkpoints\segment_1.ckpt.failed.npz
  Test-Path .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\outputs\reference_snapshots.npz
  python .\repro_status.py --run-name overnight_current
  ```
- 停止命令：
  ```powershell
  Stop-Process -Id 37284
  ```

**遇到的阻碍**
- 多次 rejected step 的共同特征是 `reason=line_search_failed` 且 `gmres_info=300`。
- 这说明 GMRES 持续打满 `gmres_maxiter=300`，当前瓶颈仍偏向线性子问题/预条件器，而不是单纯后台或 checkpoint 问题。
- 当前还能靠减小 dt 接受新步，因此暂时不应打断。

**未完成的部分**
- Segment 1 未完成。
- final reference output 未生成。
- validate/export 未执行。
- 是否会再次低于 `dt_min` 仍需观察。

**在总体进程中的作用**
- 当前 run 正在提供关键诊断数据：80x80 早期瞬态中，GMRES 打满与线搜索失败如何随 dt 收缩演化。
- 如果最终失败，failed debug checkpoint 将用于决定下一轮是继续增大 GMRES、改 preconditioner，还是改更强的 solver。

**总体进程中仍未完成**
- strict `80x80` `aei70_krar` reference 数据未生成。
- production 级 80x80 求解路径未打通。
- 后续 validate/export/作者脚本严格复现尚未进行。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- Example 5 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint、日志、metrics、reports 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt：不要提交到 Git。

**下一步建议**
1. 继续等待 PID `37284`，不要停止，不要重复启动同一 run。
2. 每 10-20 分钟检查一次 stdout/stderr、checkpoint、failed checkpoint 和 final output。
3. 如果出现 `segment_1.ckpt.failed.npz` 或 stderr traceback，再读取 diagnostics 并决定下一轮 solver 改动。
4. 如果进程达到 walltime 并保存 checkpoint，再用 Segment 2 从该 checkpoint 续跑。
5. 如果 final `reference_snapshots.npz` 出现，不启动下一段，直接 validate。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-25-aei70-80-diagnostic-retry-next-action-summary.md`

**需要确认**
- PID `37284` 后续是否能越过早期小 dt 区域需要确认。
- 若失败，failed checkpoint 中的 `diagnostics_json` 需要读取确认。
