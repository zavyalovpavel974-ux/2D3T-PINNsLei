**本轮运行状态**
- 状态：评估流程修正完成
- 命令：
  - `python -m py_compile repro_runner.py scripts\compute_example2_forward_metrics.py`
  - `python .\scripts\compute_example2_forward_metrics.py --checkpoint runs\ex2_forward_clean_20260528\checkpoints\example2_forward\latest.pt --output-json runs\ex2_forward_clean_20260528\reports\example2_forward_metrics.json --comparison-md runs\ex2_forward_clean_20260528\reports\example2_forward_paper_comparison.md --data-dir runs\ex2_forward_clean_20260528\workdir --swap-xy`
  - `python .\repro_status.py --run-name ex2_forward_clean_20260528`
- walltime 上限：不适用，本轮没有启动训练
- 运行时长：需要确认；各检查和 metrics-only 命令均为短时命令
- 退出原因：正常完成

**本次进程概述**
本轮按用户要求执行“评估流程修正与锁定”。没有启动新训练，只整理 Example 2 forward clean run 的 corrected metrics 口径，并更新 runner 报告逻辑，避免再次把坐标评估错误误判为训练误差。

**取得的成果**
- 已确认 Ex2 clean run 仍为完成状态：`phase=completed`
- 已确认 corrected metrics 文件存在：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\reports\example2_forward_metrics.json`
- 已确认 metrics 使用坐标规则：`coordinate_evaluation=swapped_xy`
- 已更新 `repro_runner.py`：
  - `repro_status.py` 状态输出会显示 forward metrics 的 `metrics_available` 与 `coordinate_evaluation`
  - `reproduction_runner_report.md` 对 `example2_forward` 会展示论文 Table 4 对照，不再写“没有匹配参考文件”
- 已更新并验证 metrics-only 脚本：`C:\Users\12412\Documents\Lei_code\scripts\compute_example2_forward_metrics.py`
- 已重写当前 run 的 runner 报告：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\reports\reproduction_runner_report.md`
- 当前 corrected aggregate L2：
  - Te：`7.339e-03`
  - Ti：`6.268e-03`
  - Tr：`7.286e-03`

**续跑状态与检查点**
- 当前 checkpoint：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\checkpoints\example2_forward\latest.pt`
- 当前阶段：Example 2，`Aei=70`
- 当前步数或优化器阶段：已完成；L-BFGS 已达到正常结束
- 已完成阶段：Adam 与 L-BFGS 均已完成
- 下一次安全命令：
  ```powershell
  python .\repro_status.py --run-name ex2_forward_clean_20260528
  ```
- 不应执行的危险操作：
  - 不要继续写入或覆盖当前 completed run 的 checkpoint，除非明确开始新实验。
  - 不要删除或覆盖 `runs/overnight_current`。

**遇到的阻碍**
- 本轮没有新的训练错误。
- 仍需注意：当前 reference profile 显示 `80x80_from20` 且 `paper_grade=False`，说明这些参考文件适合当前管线对照，但不能直接宣称是严格 paper-grade 参考数据。

**未完成的部分**
- 尚未将 Ex3/Ex4/Ex5 的 metrics 全部统一到同一坐标检查流程。
- 尚未生成 corrected error map；当前只锁定数值 metrics 与报告口径。

**在总体进程中的作用**
- 本轮把 Ex2 的评估结论从“误差异常偏大”纠正为“坐标规则修正后达到较好误差水平”。
- 后续 Ex3/Ex4/Ex5 的指标计算必须显式记录坐标规则，避免复现报告再次混入错误口径。

**总体进程中仍未完成**
- Ex3/Ex4/Ex5 的 forward metrics 需要继续做 `(x,y,t)` 与 `(y,x,t)` sanity check。
- 最终复现报告需要明确区分：训练配置、参考数据来源、坐标评估规则、是否 paper-grade。

**受保护产物**
- Example 2 既有已完成产物：先不要修改、覆盖、删除或重跑它的产物，除非用户明确要求。
- `runs/overnight_current` 中已有 checkpoint 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- 当前 completed run：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528`

**下一步建议**
1. 接受 Ex2 corrected metrics 为当前正式口径。
2. 推进 Ex3/Ex4 前，先把对应 forward metrics 的坐标 sanity check 固化。
3. 报告中保留 `coordinate_evaluation=swapped_xy` 与 `reference paper-grade=False` 两个说明。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-28-ex2-forward-evaluation-lock-summary.md`

**需要确认**
- 是否把 `swapped_xy` 作为后续所有 forward cases 的默认评估规则，还是每个 case 都先保留双口径 sanity check。
