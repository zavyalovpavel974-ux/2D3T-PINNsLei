**本轮运行状态**
- 状态：对比分析完成
- 命令：
  - `Get-Content process-summaries\lei2025_paper_text.txt`
  - `Get-Content runs\ex2_forward_clean_20260528\reports\example2_forward_paper_comparison.md`
  - `python -c "...example2_forward_metrics.json..."`
- walltime 上限：不适用，本轮没有训练
- 运行时长：短时只读检查
- 退出原因：正常完成

**本次进程概述**
本轮对照原文 Example 2 的技术设定与 Table 4 误差，检查 `ex2_forward_clean_20260528` 的训练效果。对照采用 corrected metrics，即 `coordinate_evaluation=swapped_xy`。

**取得的成果**
- 原文 Example 2 设定确认：`Aei=70`，`Kr=Ar` 常数，正值约束，double precision，weighted loss，权重为 residual `1`、photon Dirichlet boundary `1000`、initial losses `10`。
- 本次训练配置确认：`Aei=70`，`kr_mode=constant`，`use_ff=False`，`use_log_loss=False`，`lambda_brd=1000`，`lambda_init=10`。
- 本次 checkpoint 已完成：`phase=completed`，L-BFGS `n_iter=30000`，`func_evals=33360`。
- corrected aggregate L2/L1/Linf 全部低于原文 Table 4 数值。

**续跑状态与检查点**
- 当前 checkpoint：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\checkpoints\example2_forward\latest.pt`
- 当前阶段：Example 2，`Aei=70`
- 当前步数或优化器阶段：已完成
- 已完成阶段：Adam 与 L-BFGS
- 下一次安全命令：
  ```powershell
  python .\repro_status.py --run-name ex2_forward_clean_20260528
  ```

**遇到的阻碍**
- 当前 reference profile 为 `80x80_from20` 且 `paper_grade=False`，所以本次对照是当前管线一致性对照，最终论文级表述需注明参考数据来源。
- `t=1e-5` 的相对 L2 因参考值约 `3e-4` 而被小分母放大，但 aggregate 误差仍优于论文表 4。

**未完成的部分**
- 尚未把同样的 corrected coordinate metrics 流程推广到 Ex3/Ex4/Ex5。

**在总体进程中的作用**
- 本轮确认 Ex2 clean run 训练效果有效，可作为 Ex3/Ex4 的基线。

**总体进程中仍未完成**
- Ex3/Ex4/Ex5 的训练与 corrected metrics 对照仍需继续。
- 最终报告需明确坐标规则 `swapped_xy` 与参考数据 profile。

**受保护产物**
- Example 2 既有已完成产物：不要修改、覆盖、删除或重跑，除非用户明确要求。
- `runs/overnight_current`：默认不得删除或覆盖。
- 当前 completed run：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528`

**下一步建议**
1. 将 Ex2 corrected metrics 作为当前正式结果。
2. 在推进 Ex3/Ex4 前，先复用同样的坐标 sanity check。
3. 最终报告中注明参考数据不是严格 paper-grade。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-28-ex2-forward-paper-comparison-summary.md`
