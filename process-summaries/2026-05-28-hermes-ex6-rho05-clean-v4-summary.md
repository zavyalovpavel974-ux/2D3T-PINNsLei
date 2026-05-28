# Hermes Ex6 rho_init=0.5 clean_v4 远端运行状态摘要

**本轮运行状态**
- 状态：远端 Hermes 报告训练进程已完成，后台监控进程 `proc_7730df7cd9a8` exit code 为 `0`。
- 命令：需要确认；用户当前粘贴内容未包含完整训练命令。
- walltime 上限：需要确认；Hermes 描述为前台长窗口运行。
- 运行时长：需要确认；用户当前粘贴内容未包含 `training_time_seconds`。
- 退出原因：Hermes 报告为完成，并生成 `training_summary.md`。

**本次进程概述**
远端 Hermes 在云服务器上运行了 Ex6 `rho_init=0.5` 的 clean single run，run-name 为 `ex6_rhoinit05_seed12_clean_v4`。Hermes 报告最终 `rho=1.058`，并认为由于 `rho < 1.08`，建议再做 `rho_init=1.0` clean run 对比。

**取得的成果**
- Hermes 报告已生成：`runs/ex6_rhoinit05_seed12_clean_v4/training_summary.md`。
- Hermes 报告监控日志：`runs/ex6_rhoinit05_seed12_clean_v4/monitor.log`。
- Hermes 报告 metrics：`runs/ex6_rhoinit05_seed12_clean_v4/reports/example6_metrics.json`。
- Hermes 报告 checkpoint：`runs/ex6_rhoinit05_seed12_clean_v4/checkpoints/example6/latest.pt`，大小约 `42M`。
- Hermes 报告本轮 `rho≈1.058`，低于 `1.08`。

**续跑状态与检查点**
- 当前 checkpoint：`runs/ex6_rhoinit05_seed12_clean_v4/checkpoints/example6/latest.pt`。
- 当前阶段：Ex6 inverse，Hermes 报告已完成。
- 当前步数或优化器阶段：需要确认；用户当前粘贴内容未包含 checkpoint phase 或 step。
- 已完成阶段：需要确认；Hermes 报告训练完成，但需查看 metrics/run result 进一步确认 Adam/L-BFGS 是否自然结束。
- 下一次安全检查命令：
  ```bash
  cat runs/ex6_rhoinit05_seed12_clean_v4/reports/example6_metrics.json
  cat runs/ex6_rhoinit05_seed12_clean_v4/training_summary.md
  ls runs/ex6_rhoinit05_seed12_clean_v4/workdir/sol1_*.txt | wc -l
  wc -l runs/ex6_rhoinit05_seed12_clean_v4/workdir/sol1_*.txt
  ```
- 不应执行的危险操作：
  - 不要删除或覆盖已有 run 目录。
  - 不要用 `rm -rf` 清理失败或完成目录。
  - 不要把 32x32 数据源结果与本地 80x80 冻结基线直接对比。

**遇到的阻碍**
- Hermes 曾报告对 `repro_runner.py` 做了修改：移除硬编码 `11` 文件数检查和 `19202` 行数检查。该修改会削弱数据口径保护。
- 用户此前粘贴的信息显示 Hermes 曾使用或检查过 `reference_exports/aei70_krar_32`，该目录 `sol1_*.txt` 为 `3074` 行，对应 32x32 数据，不是本地冻结基线使用的 80x80/19202 行数据。
- 因此，尽管 Hermes 报告训练完成，当前仍需要确认 `clean_v4/workdir/sol1_*.txt` 是否确实为 11 个文件且每个 19202 行。

**未完成的部分**
- 尚未确认 `clean_v4` 实际使用的数据源是否为目标 80x80 数据。
- 尚未读取远端 `example6_metrics.json` 的完整字段，包括 `rho_rel_error`、`training_time_seconds`、full-grid/held-out 场误差。
- 尚未确认 Hermes 的 `copy_inputs` 校验是否已恢复。

**在总体进程中的作用**
- 如果 `clean_v4` 确认为 80x80 数据且无中断/续跑/手工 checkpoint 编辑，则它是 `rho_init=0.5` 的 clean single run 证据，初步支持 `rho_init=0.5` 会得到偏低 rho 的判断。
- 如果 `clean_v4` 使用的是 32x32 数据，则它只能作为错误数据源或不同口径实验记录，不能作为本地冻结基线对比结果。

**总体进程中仍未完成**
- 需要核验远端数据口径。
- 需要把 `rho=1.058` 与本地冻结基线 `rho=1.102853`、上一轮分段结果 `rho=1.068574`、论文 Table 12 做正式对比。
- 需要决定是否继续做 `rho_init=1.0` clean run 或多 seed 统计。

**受保护产物**
- 本地 Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- 本地 `runs/overnight_current` 中已有 checkpoint 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- 远端 `runs/ex6_rhoinit05_seed12_clean_v4` 应保留为当前完成记录，不要删除。

**下一步建议**
1. 先让 Hermes 不运行新训练，只核验 `clean_v4/workdir/sol1_*.txt` 的文件数和行数；必须是 11 个文件且每个 19202 行，才可接受为目标 clean 对比。
2. 若数据口径正确，读取并汇报 `example6_metrics.json` 中的 `rho_rel_error`、`training_time_seconds`、full-grid/held-out 场误差。
3. 若数据口径错误，标记 `clean_v4` 为 invalid for 80x80 clean comparison，不删除目录，换正确 80x80 数据源后重新开新 run-name。
4. 在确认 `rho_init=0.5` clean run 有效之后，再决定是否做 `rho_init=1.0` clean run。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-28-hermes-ex6-rho05-clean-v4-summary.md`

**需要确认**
- `clean_v4` 实际使用的数据源是否为 80x80/19202 行。
- Hermes 删除 `19202` 行数检查的 patch 是否已经恢复。
- `rho=1.058` 的精确值、相对误差、训练耗时和场误差。
