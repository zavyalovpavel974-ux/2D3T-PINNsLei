# Aei70 80x80 GMRES callback 诊断运行中汇报

**本轮运行状态**
- 状态：仍在运行
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
- PID：`15828`
- walltime 上限：1800 秒
- 启动时间：`2026-05-25T15:04:33+0800`
- 退出原因：未退出；`Get-Process -Id 15828` 确认进程仍存在

**本次进程概述**
- 用户已在本机 PowerShell 终端启动 GMRES callback 诊断 run。
- 本轮只读检查 launch json、进程、stdout/stderr、checkpoint、failed checkpoint、final output 和 `runs/overnight_current`。
- 本轮没有重启 solve，没有启动 Segment 2，没有停止 PID。

**取得的成果**
- 确认 PID `15828` 仍在运行。
- 当前 checkpoint 已生成：
  `C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\checkpoints\segment_1.ckpt.npz`
- checkpoint 当前读取：
  - `step=1`
  - `t=0.005`
  - `dt=0.006`
  - `history_len=1`
  - `diagnostics_len=0`
- stdout 已出现 GMRES callback 诊断：
  ```text
  [reference] step=1 t=0.005000 dt=5.00e-03 newton=1 residual=6.455e-04 gmres_info=None gmres_iterations=None gmres_last=None
  [reference] reject step=2 t=0.005000 attempted_dt=6.000e-03 next_dt=3.000e-03 newton=3 residual=1.420e-03 reason=line_search_failed gmres_info=300 gmres_iterations=12000 gmres_last=2.535664160365612e-07
  [reference] reject step=2 t=0.005000 attempted_dt=3.000e-03 next_dt=1.500e-03 newton=2 residual=1.033e-03 reason=line_search_failed gmres_info=300 gmres_iterations=12000 gmres_last=2.535664158091015e-07
  [reference] step=2 t=0.006500 dt=1.50e-03 newton=1 residual=8.391e-04 gmres_info=None gmres_iterations=None gmres_last=None
  ```
- 当前 stderr 为空。
- 当前 failed checkpoint 不存在。
- 当前 final output 不存在。
- `runs/overnight_current` 仍为 `Protected: True`。
- Example 2 仍为 `completed`，step `6001`。
- Example 5 仍为 stage `700`，`completed`，step `6001`。

**续跑状态与检查点**
- 当前 checkpoint：`C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\checkpoints\segment_1.ckpt.npz`
- 当前阶段：reference solver strict `80x80` `aei70_krar` GMRES callback 诊断 Segment 1；不是 Example 5 的 70/400/700 阶段。
- 当前步数或优化器阶段：checkpoint 已保存 `step=1`, `t=0.005`, `dt=0.006`；stdout 已显示 accepted `step=2`。
- 已完成阶段：strict `80x80` reference solver 尚未完成任何段。
- 当前安全检查命令：
  ```powershell
  Get-Process -Id 15828
  Get-Content .\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\logs\segment_1.stdout.log -Tail 160
  Get-Content .\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\logs\segment_1.stderr.log -Tail 160
  Test-Path .\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\checkpoints\segment_1.ckpt.failed.npz
  Test-Path .\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\outputs\reference_snapshots.npz
  python .\repro_status.py --run-name overnight_current
  ```
- 停止命令：
  ```powershell
  Stop-Process -Id 15828
  ```

**遇到的阻碍**
- rejected step 仍出现 `line_search_failed` 和 `gmres_info=300`。
- 但新增 callback 显示 `gmres_iterations=12000`、`gmres_last≈2.54e-07`，说明 GMRES callback residual 已经降得很低。
- 这改变了问题判断：当前失败不应简单归因于 GMRES 线性残差不降；更可能与 JFNK 步方向、有限差分 Jacobian-vector、非线性 line search、残差容差边界或预条件残差与真实非线性下降不一致有关。

**未完成的部分**
- 诊断 run 尚未结束。
- 尚未生成 failed checkpoint 或 final output。
- 尚未读取完整 `gmres_summary` tail 序列。

**在总体进程中的作用**
- 本轮拿到了第一批真实 80x80 GMRES callback residual 数据。
- 该数据将下一步重点从“单纯增大 GMRES maxiter”转向检查 JFNK/line search/非线性残差下降机制。

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
1. 继续让 PID `15828` 运行到失败、walltime 或完成。
2. 若 failed checkpoint 出现，读取 `diagnostics_json` 中的 `gmres_summary.tail`，确认后续 rejected step 是否同样表现为低 GMRES callback residual 但 line search failed。
3. 若该模式持续，下一轮优先诊断 line search 和 JFNK 方向，而不是继续增大 `gmres_maxiter`。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-25-aei70-80-gmrescb-diagnostic-running-summary.md`

**需要确认**
- PID `15828` 后续是否失败、walltime 或完成。
- 完整 failed checkpoint 中的 GMRES residual tail 需要后续读取确认。
