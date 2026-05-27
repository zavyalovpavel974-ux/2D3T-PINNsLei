# Aei70 80x80 诊断重试失败汇报

**本轮运行状态**
- 状态：报错失败
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
- PID：`37284`，已退出
- walltime 上限：3600 秒
- 运行时长：从 `2026-05-25T13:01:57+0800` 到 watcher 在 `2026-05-25 13:36:58 +08:00` 检出失败，约 35 分钟
- 退出原因：`RuntimeError: Reference solve failed: dt<1e-06 at t=0.007746; last residual=1.000e-03`

**本次进程概述**
- 本轮根据 watcher 终态 `FAILED`，只读检查 latest markdown、stdout/stderr、普通 checkpoint、failed checkpoint、`runs/overnight_current` 和 git 状态。
- 本轮没有重启 solve，没有启动 Segment 2，没有停止 PID。
- 诊断重试成功生成了失败前 debug checkpoint，可用于定位失败模式。

**取得的成果**
- watcher 终态：
  - `Status: FAILED`
  - `PID exists: False`
  - checkpoint 存在
  - failed checkpoint 存在
  - final output 不存在
- stdout 显示 run 从 `step=1` 推进到 `step=9`，最终在准备 `step=10` 时失败。
- failed checkpoint 路径：
  `C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\checkpoints\segment_1.ckpt.failed.npz`
- failed checkpoint 读取结果：
  - `step=9`
  - `t=0.0077455892`
  - `dt=7.873199999999999e-07`
  - `history_len=9`
  - `diagnostics_len=15`
- 最后 5 个 accepted step：
  - `step=5`, `t=0.0077105`, `dt=4.05e-05`, residual `0.000995421269697743`
  - `step=6`, `t=0.0077348`, `dt=2.43e-05`, residual `0.000998558386208171`
  - `step=7`, `t=0.00774209`, `dt=7.29e-06`, residual `0.0009994995211612993`
  - `step=8`, `t=0.007744277`, `dt=2.187e-06`, residual `0.0009997818616472379`
  - `step=9`, `t=0.0077455892`, `dt=1.3122e-06`, residual `0.000999951265938801`
- 最终 rejected step：
  - `step=10`
  - `time=0.0077455892`
  - `attempted_dt=1.57464e-06`
  - `next_dt=7.8732e-07`
  - `newton_iters=4`
  - `residual_norm=0.0010001545007217404`
  - `reason=line_search_failed`
  - `gmres_info=300`
- 所有读取到的 rejected diagnostics 均显示 `reason=line_search_failed` 且 `gmres_info=300`。
- `runs/overnight_current` 仍为 `Protected: True`。
- Example 2 仍为 `completed`，step `6001`。
- Example 5 仍为 stage `700`，`completed`，step `6001`。

**续跑状态与检查点**
- 当前普通 checkpoint：
  `C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\checkpoints\segment_1.ckpt.npz`
- 当前失败 checkpoint：
  `C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\checkpoints\segment_1.ckpt.failed.npz`
- 当前阶段：reference solver strict `80x80` `aei70_krar` 诊断重试 Segment 1；不是 Example 5 的 70/400/700 阶段。
- 当前步数或优化器阶段：失败前为 `step=9`, `t=0.0077455892`, 下一步 `dt=7.8732e-07` 已低于 `dt_min=1e-6`。
- 已完成阶段：strict `80x80` reference solver 未完成任何段。
- 下一次安全续跑命令：
  ```powershell
  当前不建议续跑或重启；需要先决定 solver 改进方向。
  ```
- 不应执行的危险操作：
  - 不要自动重启 Segment 1。
  - 不要启动 Segment 2。
  - 不要删除 failed checkpoint 或日志。
  - 不要修改、覆盖、删除 `runs/overnight_current`。
  - 不要重跑 Example 2 / Example 5。

**遇到的阻碍**
- 增大 `newton_max=16` 和 `gmres_maxiter=300` 后仍失败。
- 失败点仍在 `t≈0.007746`，与前一次 strict 80x80 失败位置一致。
- 主要失败模式清楚：每次 rejected step 都是 `line_search_failed`，且 GMRES 打满 `gmres_maxiter=300`。
- residual 长期贴近 `1e-3` 容差边界；accepted step 的 residual 从 `0.000995` 逐渐逼近 `0.00099995`，rejected step 在 `0.001000+` 侧失败。
- 继续只靠减小 dt 已不可行，因为下一步 `dt=7.8732e-07` 低于 `dt_min=1e-6`。

**未完成的部分**
- Segment 1 未完成。
- `outputs/reference_snapshots.npz` 未生成。
- validate 未执行。
- author txt 未导出。
- production 级 80x80 strict reference 数据未生成。

**在总体进程中的作用**
- 本轮诊断重试把失败机制从“dt 低于下限”细化为“GMRES 持续打满 300，导致 line search failed，residual 卡在 Newton 容差边界附近”。
- 这说明下一轮应优先改进线性求解/预条件器/雅可比策略，而不是简单继续提高 Newton 次数或盲目分段。

**总体进程中仍未完成**
- strict `80x80` `aei70_krar` reference 数据仍未生成。
- 后续 validate/export/作者脚本严格复现尚未进行。
- 需要决定下一轮 solver 改进方案。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- Example 5 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint、日志、metrics、reports 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt：不要提交到 Git。

**下一步建议**
1. 不要重启当前 run，也不要启动 Segment 2。
2. 修复 watcher markdown 编码/围栏显示问题：latest markdown 中中文标题乱码，代码围栏显示为 ``text，说明脚本写 UTF8 在 Windows PowerShell 中可能产生兼容问题；建议改为 ASCII 标题和普通 triple-backtick，或显式 `utf8NoBOM`。
3. 下一轮 solver 改进优先级：
   - 记录并暴露 GMRES residual 或 callback，以确认线性残差下降曲线。
   - 尝试更强预条件器，不再只用对角预条件。
   - 考虑 sparse/块结构 Jacobian 或物理块预条件器。
   - 谨慎评估把 Newton 判据改为 `<=` 或略放宽容差是否只是在“过线”，不能作为 paper-grade 方案。
4. 如需快速工程验证，可新建 run dir 做“容差敏感性”实验，但必须标记为诊断，不作为正式 strict reference。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-25-aei70-80-diagnostic-retry-failed-summary.md`

**需要确认**
- 是否允许我继续修改 solver，加入 GMRES callback/residual 诊断与更强预条件器实验。
- 是否先修复 watcher markdown 编码/围栏显示问题。
