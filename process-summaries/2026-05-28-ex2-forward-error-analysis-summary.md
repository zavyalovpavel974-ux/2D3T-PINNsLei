**本轮运行状态**
- 状态：分析完成
- 命令：
  - `python .\repro_status.py --run-name ex2_forward_clean_20260528`
  - `python .\scripts\compute_example2_forward_metrics.py --checkpoint runs\ex2_forward_clean_20260528\checkpoints\example2_forward\latest.pt --output-json runs\ex2_forward_clean_20260528\reports\example2_forward_metrics.json --comparison-md runs\ex2_forward_clean_20260528\reports\example2_forward_paper_comparison.md --data-dir runs\ex2_forward_clean_20260528\workdir --swap-xy`
- walltime 上限：不适用，本轮为只读诊断与 metrics 重算
- 运行时长：metrics 重算约数秒
- 退出原因：正常完成

**本次进程概述**
本轮分析 Example 2 clean run 初始对照误差偏大的原因。诊断发现训练本身不是主要问题，主要问题是 metrics 计算时使用了参考文本文件的坐标顺序 `(x, y)`，而该文件/绘图约定与模型查询需要采用 `(y, x)` 对齐。加入 `--swap-xy` 后，误差显著降低。

**取得的成果**
- 已确认 run 状态：`phase=completed`
- 已确认 checkpoint：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\checkpoints\example2_forward\latest.pt`
- 已确认原通道顺序 `Te, Ti, Tr` 是最佳通道顺序，通道没有算反。
- 已确认坐标顺序是主要误差来源：
  - 原 `(x, y, t)` 评估 aggregate L2：Te `8.017e-02`，Ti `7.559e-02`，Tr `1.026e-01`
  - 修正为 `(y, x, t)` 后 aggregate L2：Te `7.339e-03`，Ti `6.268e-03`，Tr `7.286e-03`
- 已更新 metrics-only 脚本，新增 `--swap-xy` 开关：`C:\Users\12412\Documents\Lei_code\scripts\compute_example2_forward_metrics.py`
- 已用 `--swap-xy` 重算正式 metrics：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\reports\example2_forward_metrics.json`
- 已更新论文对照：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\reports\example2_forward_paper_comparison.md`

**续跑状态与检查点**
- 当前 checkpoint：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\checkpoints\example2_forward\latest.pt`
- 当前阶段：Example 2，`Aei=70`
- 当前步数或优化器阶段：已完成；L-BFGS `n_iter=30000`，`func_evals=33360`
- 已完成阶段：Adam 与 L-BFGS 均已完成
- 下一次安全命令：
  ```powershell
  python .\repro_status.py --run-name ex2_forward_clean_20260528
  ```
- 不应执行的危险操作：
  - 不要覆盖当前 completed run 的 checkpoint。
  - 不要删除或覆盖 `runs/overnight_current`。

**遇到的阻碍**
- 原始误差对照被坐标约定问题误导，导致误判为训练误差很大。
- 早期 `t=1e-5` 的相对 L2 仍然很大，原因是参考值约为 `3e-4`，分母很小；对应绝对误差并不主导 aggregate。

**未完成的部分**
- 尚未把 `--swap-xy` 规则推广到 Ex3/Ex4/Ex5 的 metrics 流程，需要后续统一检查。
- 尚未可视化误差场，但数值诊断已经足以确认坐标顺序是主因。

**在总体进程中的作用**
- 本轮纠正了 Example 2 clean run 的主要误差判断：训练结果不是失败，修正坐标后整体误差达到并优于论文表 4 的 L2/L1/Linf 指标。
- 这为后续 Example 3、Example 4 的复现提供了一个更可靠的基线，也提示后续所有 forward metrics 都要检查坐标约定。

**总体进程中仍未完成**
- Ex3/Ex4 的 metrics 计算需要显式继承或验证 `swap_xy` 坐标约定。
- 最终复现报告需要注明参考文本文件坐标与模型输入坐标的约定差异。

**受保护产物**
- Example 2 既有已完成产物：先不要修改、覆盖、删除或重跑它的产物，除非用户明确要求。
- `runs/overnight_current` 中已有 checkpoint 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- 当前 completed run：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528`

**下一步建议**
1. 接受当前 Ex2 clean run 的 corrected metrics，并在后续报告中使用 `coordinate_evaluation=swapped_xy` 的结果。
2. 将同样的坐标检查应用到 Ex3/Ex4/Ex5 metrics，避免再次误判。
3. 如需进一步增强说服力，可生成 Ex2 的 corrected error map，对比 `(x,y)` 与 `(y,x)` 两种评估方式。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-28-ex2-forward-error-analysis-summary.md`

**需要确认**
- 是否将 `--swap-xy` 作为后续 forward case metrics 的默认规则。
