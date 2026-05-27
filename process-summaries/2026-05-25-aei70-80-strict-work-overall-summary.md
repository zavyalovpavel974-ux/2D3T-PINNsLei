# Aei70 80x80 strict reference solver 工作总汇报

**本轮运行状态**
- 状态：阶段性停止 / 需要后续确认
- 当前决定：暂时停止 strict `80x80` `aei70_krar` reference solver 求解线，不再启动新 run，不启动 Segment 2，不改参数继续试跑。
- 最近失败命令：
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
- walltime 上限：最近 GMRES callback 诊断 run 为 1800 秒；早期 strict/诊断 run 为 3600 秒。
- 退出原因：strict 80x80 相关 run 均在 `t≈0.007746` 附近因 `dt<1e-06` 失败。

**本次进程概述**
- 本阶段目标是正式启动、监控并诊断 strict `80x80` `aei70_krar` reference solver。
- 已确认 Codex 工具环境后台进程无法可靠保活，因此长跑需要用户本机 PowerShell 终端启动。
- 已完成多个层级诊断：原始 strict run、增强 Newton/GMRES 参数诊断、GMRES callback residual 诊断。
- 结论：当前 SciPy matrix-free JFNK 路径尚不能生成 paper-grade strict 80x80 reference 数据。

**取得的成果**
- 启动与巡检工具：
  - 新增 `scripts/start_ref_solver_segment.py`，实现安全分段启动、拒绝写入 `runs/overnight_current`、拒绝覆盖已有输出/checkpoint、支持 resume checkpoint。
  - 更新 `scripts/start_ref_solver_segment.ps1` 为 Python launcher 薄包装，并支持 `-DtInit`、`-DtMin`、`-DtMax`、`-NewtonMax`、`-GmresMaxiter`、`-CheckpointIntervalSteps`、`-LogEveryStep`、`-LogRejectedSteps`、`-DebugOnFailure`、`-DryRun`。
  - 新增 `scripts/watch_ref_solver_run.ps1`，用于只读自动巡检 PID/log/checkpoint/output/failed checkpoint/`overnight_current`/git status。
  - 修复 watcher 输出：ASCII 标题、标准 markdown 代码围栏，避免 Windows PowerShell 中文乱码和反引号转义问题。
- solver 诊断增强：
  - `reference_solver/generate_reference.py` 增加 `--log-every-step`。
  - 增加 `--log-rejected-steps`。
  - 增加 `--debug-on-failure`，失败前写 `segment_1.ckpt.failed.npz`。
  - rejected diagnostics 保存 `attempted_dt`、`next_dt`、Newton 次数、residual、line-search 失败原因、GMRES info。
  - GMRES 增加 callback residual 诊断，保存 `gmres_summary`，stdout 打印 `gmres_iterations` / `gmres_last`。
- 已验证：
  - Python 编译通过。
  - PowerShell AST 语法解析通过。
  - watcher 不包含 `Start-Process`、`Stop-Process`、`generate_reference.py`、`start_ref_solver_segment`、`Remove-Item`。
  - 小型 2x2 GMRES callback 自检通过。
- 诊断结果：
  - 原始 strict run 在 `t=0.007746` 附近失败，`dt<1e-06`。
  - 增强参数 run 使用 `NewtonMax=16`、`GmresMaxiter=300` 后仍在同一位置失败。
  - failed checkpoint 确认失败前 `step=9`, `t=0.0077455892`, `dt=7.8732e-07`。
  - 所有 rejected diagnostics 均为 `reason=line_search_failed`。
  - `gmres_info=300`，且 SciPy callback 显示 `gmres_iterations=12000`，对应 `maxiter=300` 个 restart cycle、`restart=40`。
  - `gmres_last≈2.535e-07`，说明 GMRES callback residual 已经很低，但 non-linear line search 仍无法接受步长。
- 保护状态：
  - `runs/overnight_current` 仍为 `Protected: True`。
  - Example 2 仍为 `completed`，step `6001`。
  - Example 5 仍为 stage `700`，`completed`，step `6001`。

**续跑状态与检查点**
- 当前没有可用于正式 strict 80x80 Segment 2 的 checkpoint。
- 已保留三个关键输出目录作为证据：
  - `reference_solver_outputs/aei70_krar_80_strict_20260525`
  - `reference_solver_outputs/aei70_krar_80_diag_newton16_gmres300_20260525`
  - `reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525`
- 最近 failed checkpoint：
  `reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz`
- 当前阶段：strict `80x80` `aei70_krar` reference solver 诊断暂停；不是 Example 5 的 70/400/700 阶段。
- 当前步数或优化器阶段：最近失败 run 停在 `step=9`, `t=0.0077455892`，下一步 `dt=7.8732e-07 < dt_min=1e-6`。
- 下一次安全续跑命令：
  ```powershell
  当前不建议续跑或重启；需要先设计新的 JFNK / line-search / Jacobian-vector 诊断或 solver 改进方案。
  ```
- 不应执行的危险操作：
  - 不要重启当前失败 run。
  - 不要启动 Segment 2。
  - 不要删除或覆盖 failed checkpoint、stdout/stderr、watch latest。
  - 不要修改、覆盖、删除 `runs/overnight_current`。
  - 不要重跑 Example 2 / Example 5。

**遇到的阻碍**
- Codex 工具环境后台进程不保活，正式运行必须由用户本机 PowerShell 启动。
- 当前 SciPy matrix-free JFNK + 对角预条件器无法越过早期 `t≈0.007746` 困难区。
- 单纯增大 `newton_max` 和 `gmres_maxiter` 没有解决问题。
- GMRES callback residual 很低但 line search failed，说明问题不应继续简单归因于 GMRES 残差不降。
- accepted residual 逐步贴近 `newton_tol=1e-3`，rejected residual 总在 `1e-3` 以上极小幅超限，表现为容差边界和非线性步长选择的组合问题。

**未完成的部分**
- strict `80x80` `aei70_krar` reference snapshots 未生成。
- `outputs/reference_snapshots.npz` 未生成。
- validation 未执行。
- author txt 未导出。
- strict 80x80 paper-grade reference 数据未产出。
- 尚未实现更强预条件器、显式 sparse/block Jacobian、或更稳健的 line-search/Jv 方案。

**在总体进程中的作用**
- 本阶段没有产出正式 strict 80x80 reference，但明确排除了多条错误路径：
  - 不是 Example 2/5 污染或冻结目录问题。
  - 不是单纯后台启动问题。
  - 不是单纯把 `newton_max` / `gmres_maxiter` 调大即可解决。
  - 不是简单的 GMRES callback residual 完全不下降。
- 本阶段保留了完整失败证据链，为下一轮 solver 改造提供依据。

**总体进程中仍未完成**
- strict 80x80 reference 数据仍未生成。
- 基于 strict 80x80 reference 的 author txt、validate、作者脚本严格复现仍未完成。
- 后续如果继续 strict 80x80，建议先进入 solver 方法改造，而不是继续堆参数。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- Example 5 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint、日志、metrics、reports 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt：不要提交到 Git。
- 当前 strict 80x80 失败证据目录也应保留，不要删除或覆盖。

**下一步建议**
1. 暂停 strict 80x80 求解，不再启动新 run。
2. 若后续恢复 strict 80x80，优先做 solver 改造：
   - 记录 line search 每个 alpha 的完整 `trial_norm` 序列。
   - 记录每次 Newton 迭代的 `norm_R` 序列。
   - 记录 `dU` 范数、最大绝对值、温度 floor 触发情况。
   - 检查 JFNK finite-difference epsilon 尺度。
   - 考虑更稳健的 line search 或阻尼 Newton。
   - 考虑 sparse/block Jacobian 或物理块预条件器。
3. 若只是验证 pipeline，可继续使用 `80x80_from20` 或低分辨率 reference，但必须标记为 pipeline validation，不作为 strict paper-grade 结果。
4. 在提交代码前，明确区分：
   - 可提交的小脚本/诊断代码/summary；
   - 不应提交的 `reference_solver_outputs` 大输出、checkpoint、日志。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-25-aei70-80-strict-work-overall-summary.md`

**需要确认**
- 后续是否转入 solver 方法改造。
- 是否需要整理当前改动为一次 commit，但排除 `reference_solver_outputs`。
