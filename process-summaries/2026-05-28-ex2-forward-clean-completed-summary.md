**本轮运行状态**
- 状态：正常完成
- 命令：`python .\repro_runner.py --case example2_forward --run-name ex2_forward_clean_20260528 --allow-existing-run --max-walltime-seconds 43200`
- walltime 上限：43200 秒
- 运行时长：约 8784.1 秒
- 退出原因：L-BFGS 正常返回，runner return code 为 0

**本次进程概述**
本轮按用户选择的 12 小时 walltime 以前台长跑继续推进 Example 2 clean run。训练没有用满 12 小时，约 2 小时 26 分钟后正常完成。随后运行状态检查，确认 checkpoint phase 为 `completed`，并使用 completed checkpoint 对 Example 2 的 `aei70/krar` 参考文件补算 metrics 与论文 Example 2 对照结果。

**取得的成果**
- 完成运行目录：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528`
- 当前 checkpoint：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\checkpoints\example2_forward\latest.pt`
- checkpoint 状态：
  - `Aei=70.0`
  - `phase=completed`
  - `adam_iter=6001`
  - `lbfgs_n_iter=30000`
  - `lbfgs_func_evals=33360`
  - checkpoint elapsed_seconds 约 8779.12 秒
- 状态检查命令已运行：`python .\repro_status.py --run-name ex2_forward_clean_20260528`
- metrics 已补算：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\reports\example2_forward_metrics.json`
- 论文对照 Markdown 已生成：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\reports\example2_forward_paper_comparison.md`
- 新增 metrics-only 脚本：`C:\Users\12412\Documents\Lei_code\scripts\compute_example2_forward_metrics.py`
- metrics-only 脚本已通过语法检查：`python -m py_compile scripts\compute_example2_forward_metrics.py`

**续跑状态与检查点**
- 当前 checkpoint：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\checkpoints\example2_forward\latest.pt`
- 当前阶段：Example 2，`Aei=70`
- 当前步数或优化器阶段：已完成；L-BFGS 达到 `n_iter=30000`
- 已完成阶段：Adam 与 L-BFGS 均已完成
- 下一次安全续跑命令：
  ```powershell
  # 当前已 completed，默认不建议继续续跑同一 run。
  python .\repro_status.py --run-name ex2_forward_clean_20260528
  ```
- 不应执行的危险操作：
  - 不要删除或覆盖 `runs/overnight_current` 中已有 checkpoint 和结果文件，除非用户明确要求。
  - 不要在当前 completed run 上再次启动训练并写入同一 `run-name`，除非明确要覆盖或追加新实验。

**遇到的阻碍**
- metrics-only 脚本首次运行时因 `scripts/` 路径下找不到根目录模块 `sub_2D3T_wei_aei700_wer_krartr_time` 出现 `ModuleNotFoundError`；已通过加入仓库根目录到 `sys.path` 修复。
- stderr 日志中仍保留此前 walltime 与 L-BFGS 续跑失败的历史 traceback；本轮 12 小时前台长跑本身 return code 为 0。
- metrics-only 运行出现一个 PyTorch `UserWarning`，未阻止指标计算。

**未完成的部分**
- `reproduction_runner_report.md` 是 runner 在训练命令结束时生成的报告，尚未内联更新 metrics-only 后的完整对照；完整对照已单独写入 `example2_forward_paper_comparison.md`。

**在总体进程中的作用**
- 本轮完成了 Example 2 forward clean run，可作为后续 Example 3、Example 4 的对照基线。
- 本轮验证了 12 小时 walltime 对当前 L-BFGS 末段是足够的，实际只用了约 8784 秒。
- 本轮把 Ex2 的训练状态从 walltime 中断推进到 completed，并补齐了可对照的误差指标。

**总体进程中仍未完成**
- 需要决定是否接受当前 Example 2 clean run 的误差水平，或进一步分析误差偏大的原因。
- Example 3、Example 4 与论文设定/用户设定的最终对照仍需继续整理。
- 后续报告中应注明 Ex2 metrics 使用的是 `sol1_wei_aei70_wer_krar_*` 参考文件，而不是 Ex5 的 `aei700/krartr` 文件。

**受保护产物**
- Example 2 既有已完成产物：先不要修改、覆盖、删除或重跑它的产物，除非用户明确要求。
- `runs/overnight_current` 中已有 checkpoint 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- 当前 completed run：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528`，作为本次 clean run 产物，不应被覆盖或并发写入。

**下一步建议**
1. 先查看对照结果：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\reports\example2_forward_paper_comparison.md`
2. 如果接受该 Ex2 clean run，下一步可以按已确认技术矩阵推进 Ex3 或 Ex4。
3. 如果不接受该误差水平，优先分析 Ex2 与论文误差差异来源，包括参考数据分辨率、采样点、损失权重、训练随机性、以及是否完全复现论文 Ex2 的网络/数据设置。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-28-ex2-forward-clean-completed-summary.md`
