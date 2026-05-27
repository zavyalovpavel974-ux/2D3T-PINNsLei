# Aei70 80x80 GMRES callback 诊断失败汇报

**本轮运行状态**
- 状态：报错失败
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
- PID：`15828`，已退出
- walltime 上限：1800 秒
- 运行时长：需要确认；启动时间为 `2026-05-25T15:04:33+0800`
- 退出原因：`RuntimeError: Reference solve failed: dt<1e-06 at t=0.007746; last residual=1.000e-03`

**本次进程概述**
- 用户报告 stderr 已出现 traceback，failed checkpoint 存在，final output 不存在。
- Codex 只读读取 failed checkpoint、stdout、保护目录状态和 git 状态。
- 本轮没有重启 solve，没有启动 Segment 2，没有停止 PID。

**取得的成果**
- failed checkpoint 路径：
  `C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\checkpoints\segment_1.ckpt.failed.npz`
- failed checkpoint 读取结果：
  - `step=9`
  - `t=0.0077455892`
  - `dt=7.873199999999999e-07`
  - `history_len=9`
  - `diagnostics_len=15`
- final output 不存在：
  `reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/outputs/reference_snapshots.npz`
- stdout 完整显示从 `step=1` 到失败前 `step=9`。
- 所有 rejected step 均为：
  - `reason=line_search_failed`
  - `gmres_info=300`
  - `gmres_iterations=12000`
  - `gmres_last≈2.53566415e-07`
- 典型 rejected step：
  - `step=2`, `attempted_dt=6.000e-03`, `residual=1.420e-03`, `gmres_last=2.535664160365612e-07`
  - `step=5`, `attempted_dt=8.100e-05`, `residual=1.001e-03`, `gmres_last=2.5356641552748996e-07`
  - `step=9`, `attempted_dt=2.6244e-06`, `residual=1.000120621153883e-03`, `gmres_last=2.5356641515095724e-07`
  - `step=10`, `attempted_dt=1.57464e-06`, `next_dt=7.8732e-07`, `residual=1.0001545007217404e-03`, `gmres_last=2.535664154721429e-07`
- accepted step residual 逐步贴近容差：
  - `step=5`, residual `0.000995421269697743`
  - `step=6`, residual `0.000998558386208171`
  - `step=7`, residual `0.0009994995211612993`
  - `step=8`, residual `0.0009997818616472379`
  - `step=9`, residual `0.000999951265938801`
- `runs/overnight_current` 仍为 `Protected: True`。
- Example 2 仍为 `completed`，step `6001`。
- Example 5 仍为 stage `700`，`completed`，step `6001`。

**续跑状态与检查点**
- 当前普通 checkpoint：
  `C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\checkpoints\segment_1.ckpt.npz`
- 当前失败 checkpoint：
  `C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525\checkpoints\segment_1.ckpt.failed.npz`
- 当前阶段：reference solver strict `80x80` `aei70_krar` GMRES callback 诊断 Segment 1；不是 Example 5 的 70/400/700 阶段。
- 当前步数或优化器阶段：失败前为 `step=9`, `t=0.0077455892`；下一步 `dt=7.8732e-07` 已低于 `dt_min=1e-6`。
- 已完成阶段：strict `80x80` reference solver 未完成任何段。
- 下一次安全续跑命令：
  ```powershell
  当前不建议续跑或重启；需要先诊断 JFNK 方向 / Jv / line search。
  ```
- 不应执行的危险操作：
  - 不要自动重启当前 run。
  - 不要启动 Segment 2。
  - 不要删除或覆盖 failed checkpoint、stdout/stderr。
  - 不要修改、覆盖、删除 `runs/overnight_current`。
  - 不要重跑 Example 2 / Example 5。

**遇到的阻碍**
- 增强 GMRES callback 后仍失败在 `t≈0.007746`。
- 关键新证据：GMRES callback residual 很低且几乎常数，`gmres_last≈2.535e-07`，但 line search 仍失败。
- 因此，“GMRES 线性残差完全不收敛”不是主因。
- 更可能的问题：
  - JFNK 有限差分 Jacobian-vector 方向不够可信；
  - GMRES 的 callback residual 与真实非线性 residual 下降不一致；
  - line search 只接受严格下降，且 residual 贴近 `1e-3` 容差边界；
  - `trial_norm` 在最小 `alpha=0.00390625` 时仍略高于当前 norm 或容差边界；
  - 当前残差度量/容差判断导致小时间步区域反复“差一点”失败。

**未完成的部分**
- Segment 1 未完成。
- `reference_snapshots.npz` 未生成。
- validate/export 未执行。
- 尚未实现 JFNK/line-search 的更细诊断。

**在总体进程中的作用**
- 本轮把失败原因从“GMRES 打满 300”进一步细化为：“GMRES callback residual 已很低，但 Newton 更新方向无法通过 line search 使非线性 residual 严格下降到接受区间”。
- 下一步应停止继续增大 GMRES maxiter，转向 JFNK 有限差分尺度、line search、Newton 容差边界和 nonlinear residual 诊断。

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
1. 不要重启当前 run，不要启动 Segment 2。
2. 下一步代码诊断建议：
   - 记录 line search 每个 alpha 的 `trial_norm` 序列，而不是只保存最后一次。
   - 记录每次 Newton 迭代的 `norm_R` 序列。
   - 记录 `dU` 的范数、最大绝对值、是否产生负温度/触发 `temp_floor`。
   - 试验更稳健的 JFNK finite-difference epsilon 或方向缩放。
3. 若做参数敏感性，只作为诊断：
   - `newton_tol=1.01e-3` 或 `1.05e-3` 可验证是否只是容差边界问题。
   - `dt_min=1e-7` 可验证是否能越过早期困难区，但不应作为正式 paper-grade 解法。
4. 正式解决方向仍是改进 nonlinear step / line search / Jacobian-vector，而不是继续增大 GMRES maxiter。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-25-aei70-80-gmrescb-diagnostic-failed-summary.md`

**需要确认**
- 是否允许我继续添加 line-search alpha 轨迹、Newton norm 序列和 dU/温度诊断。
- 是否允许用新 run dir 做一个短 walltime 的容差敏感性诊断。
