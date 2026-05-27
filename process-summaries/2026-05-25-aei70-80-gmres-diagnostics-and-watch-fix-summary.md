# Aei70 80x80 GMRES 诊断增强与 watcher 修复汇报

**本轮运行状态**
- 状态：正常完成
- 命令：
  ```powershell
  python -m py_compile .\reference_solver\generate_reference.py .\scripts\start_ref_solver_segment.py
  PowerShell AST 解析 scripts/watch_ref_solver_run.ps1
  .\scripts\watch_ref_solver_run.ps1 -RunDir .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525 -Pid 37284 -IntervalSeconds 600
  python -c "2x2 LinearOperator GMRES callback self-check"
  python .\repro_status.py --run-name overnight_current
  ```
- walltime 上限：不适用；本轮未启动 reference solve
- 运行时长：短命令检查
- 退出原因：代码修改和验证正常完成

**本次进程概述**
- 本轮按用户确认执行两项操作：
  1. 修复 `scripts/watch_ref_solver_run.ps1` 的 latest markdown 中文乱码和代码围栏显示问题。
  2. 给 `reference_solver/generate_reference.py` 增加 GMRES callback/residual 诊断。
- 本轮没有启动 strict 80x80 新任务，没有启动 Segment 2，没有停止任何 PID。

**取得的成果**
- 修复 watcher 输出：
  - latest markdown 标题改为 ASCII：`Status`、`Next Action`、`Read-Only Constraints`。
  - 代码围栏改为单引号字符串输出标准 ` ```text ` 和 ` ``` `，避免 PowerShell 反引号转义。
  - 已用失败终态 run 做一次只读 watcher 运行，`process-summaries/aei70-80-diag-watch-latest.md` 现在显示正常标题和标准围栏。
- 增强 GMRES 诊断：
  - 新增 `gmres_callback_summary(values, callback_type)`。
  - 新增 `gmres_log_text(summary)`。
  - `solve_gmres` 现在通过 SciPy `callback` 记录 GMRES callback residual。
  - 优先使用 `callback_type="pr_norm"`；若旧接口不支持，回退到 legacy callback。
  - `solve_gmres` 返回 `(x, info, summary)`。
  - `jfnk_step` 在 accepted/rejected details 中保存：
    - `gmres_info`
    - `gmres_summary`
  - accepted history 中保存 `gmres_summary`。
  - rejected diagnostics 中保存 `gmres_summary`。
  - stdout 的 accepted/rejected 行会打印：
    - `gmres_iterations`
    - `gmres_last`
- 验证通过：
  - `python -m py_compile .\reference_solver\generate_reference.py .\scripts\start_ref_solver_segment.py`
  - PowerShell AST 解析 `scripts/watch_ref_solver_run.ps1`
  - watcher 脚本中未发现 `Start-Process`、`Stop-Process`、`generate_reference.py`、`start_ref_solver_segment`、`Remove-Item`
  - `gmres_callback_summary([1.0, 0.5, 0.25], "pr_norm")` 自检通过
  - 2x2 单位 `LinearOperator` 的 `solve_gmres` 自检通过：`x≈[1.0,2.0]`, `info=0`, callback summary 正常
- 只读检查确认 `runs/overnight_current` 仍存在且 `Protected: True`。
- Example 2 仍为 `completed`，step `6001`。
- Example 5 仍为 stage `700`，`completed`，step `6001`。

**续跑状态与检查点**
- 本轮未续跑、未启动新 solve。
- 当前失败 run 的 checkpoint 和 failed checkpoint 保持原样：
  - `reference_solver_outputs/aei70_krar_80_diag_newton16_gmres300_20260525/checkpoints/segment_1.ckpt.npz`
  - `reference_solver_outputs/aei70_krar_80_diag_newton16_gmres300_20260525/checkpoints/segment_1.ckpt.failed.npz`
- 当前阶段：reference solver strict `80x80` `aei70_krar` 诊断改进；不是 Example 5 的 70/400/700 阶段。
- 下一次安全启动命令：需要用户确认新 run dir 和实验参数后再启动；当前不自动给出重启命令。
- 不应执行的危险操作：
  - 不要重启当前失败 run。
  - 不要启动 Segment 2。
  - 不要删除或覆盖失败 checkpoint、日志、outputs。
  - 不要修改、覆盖、删除 `runs/overnight_current`。
  - 不要重跑 Example 2 / Example 5。

**遇到的阻碍**
- 初始 GMRES 自检中 `LinearOperator` 的 `matvec=lambda x: x` 返回输入对象本身，SciPy 1.17.1 的 GMRES 得到异常测试结果；改为返回 copy 后自检正常。
- 这个自检问题不影响 reference solver 当前 `Jv` 和 preconditioner，因为它们返回新的数组表达式。

**未完成的部分**
- 尚未用 GMRES callback 增强版启动新的 80x80 诊断 run。
- 尚未获得真实 80x80 run 的 GMRES residual 曲线。
- 尚未实现更强预条件器或 sparse/块 Jacobian。

**在总体进程中的作用**
- 本轮完成了下一轮诊断所需的可观测性建设。
- 下一次 80x80 诊断 run 若失败，将能记录 GMRES callback residual 摘要，帮助判断 GMRES 是完全不降、下降太慢，还是预条件尺度不合适。

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
1. 如需继续诊断，使用新的 run dir 启动一轮短 walltime GMRES callback 诊断 run，保留当前失败目录。
2. 新 run 仍建议使用 `-LogEveryStep -LogRejectedSteps -DebugOnFailure -CheckpointIntervalSteps 1`。
3. 若 callback 显示 GMRES residual 明显停滞，再优先开发更强块预条件器；若 residual 下降但不够快，再评估 gmres 参数/容差敏感性。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-25-aei70-80-gmres-diagnostics-and-watch-fix-summary.md`

**需要确认**
- 是否启动下一轮新的 GMRES callback 诊断 run。
- 下一轮 run dir 名称和 walltime 需要确认。
