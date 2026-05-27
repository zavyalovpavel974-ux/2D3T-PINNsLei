**本轮运行状态**
- 状态：正常完成。本轮只做 Example 5 状态复核与进展汇报，未启动训练，未写入 `runs/overnight_current`。
- 命令：
  - `git status`
  - `python repro_status.py --run-name overnight_current`
  - `python repro_background.py status --run-name overnight_current`
  - `Get-Content -Raw runs\overnight_current\reports\example5_metrics.json`
  - `rg -n "^Aei:|resume transfer stage|skipping completed transfer stage|resumed checkpoint|Training time|Total Training time|Tel2|Tel1|Teli|Inference time|wrote metrics" runs\overnight_current\logs\example5.stdout.log`
- walltime 上限：本轮未启动训练，非适用。
- 运行时长：本轮状态检查为短命令；Example 5 既有记录中最终 700 阶段 training time 为 `29110.0454s`。
- 退出原因：状态复核命令正常结束。

**本次进程概述**
- 目标是向用户汇报 Example 5 已取得成果、当前阶段、指标表现和下一步风险。
- 数据来源为冻结目录 `runs/overnight_current` 中的 status、checkpoint、metrics、stdout 日志。
- 本轮没有修改 Example 5 代码或结果文件。

**取得的成果**
- Example 5 已完成到 `stage: 700`，checkpoint phase 为 `completed`，step 为 `6001`。
- 当前 checkpoint 存在：`runs/overnight_current/checkpoints/example5/latest.pt`。
- metrics 存在：`runs/overnight_current/reports/example5_metrics.json`。
- stdout/stderr 日志存在：`runs/overnight_current/logs/example5.stdout.log`、`runs/overnight_current/logs/example5.stderr.log`。
- Example 5 已完成 70、400、700 三阶段续跑链路：
  - 日志显示第一段从 `Aei: 0` 开始并完成一个 training segment。
  - 后续日志显示 `resume transfer stage Aei=400`，跳过已完成的 `Aei=70`，从 checkpoint 恢复于 `phase=adam it=4400`。
  - 后续日志显示 `resume transfer stage Aei=700`，跳过已完成的 `Aei=70` 和 `Aei=400`，从 checkpoint 恢复于 `phase=adam it=2800`。
  - 最终 `Training time: 29110.0454`，`Total Training time: 29110.0454`，并写出 metrics。
- 最终 metrics 明确标记：
  - `case`: `example5_transfer`
  - `reference`: `interpolated_80x80_from20`
  - `inference_time_seconds`: `0.04833650588989258`
- 最终 aggregate 误差：
  - `Te`: L2 `0.7049614628658555`，L1 `0.36248202409586755`，Linf `0.6491585346577088`
  - `Ti`: L2 `0.7081070315755149`，L1 `0.31849077651772184`，Linf `0.5765261544988101`
  - `Tr`: L2 `0.6686891071387449`，L1 `1.0500141094014557`，Linf `2.0000081988195895`

**续跑状态与检查点**
- 当前 checkpoint：`runs/overnight_current/checkpoints/example5/latest.pt`。
- 当前阶段：Example 5 stage `700`。
- 当前步数或优化器阶段：phase `completed`，step `6001`。
- 已完成阶段：70、400、700 的训练/续跑链路已在日志中出现；当前最终 checkpoint 为 700 阶段完成态。
- 下一次安全续跑命令：不建议续跑 `overnight_current`，因为它是冻结受保护目录，且 Example 5 当前已完成。若需要新实验，必须使用新的 `--run-name` 和新输出目录。
- 不应执行的危险操作：
  - 不要写入、删除、覆盖、移动 `runs/overnight_current`。
  - 不要重跑 Example 5 已完成产物。
  - 不要把 70、400、700 阶段状态混在一起判断。
  - 不要从 `runs/overnight_current` 继续训练；需要新实验时使用新目录。

**遇到的阻碍**
- Example 5 虽然已完成工程流程，但数值误差明显偏大，未达到论文量级。
- 当前参考解为 `interpolated_80x80_from20`，不是严格独立 80x80 参考解。
- 既有静态审查指出：Example 5 误差计算五个时刻都读取同一个 `sol1_wei_aei700_wer_krartr_80_1.txt`，这是误差异常的重要嫌疑点。
- 当前工作区存在与本轮汇报无关的未提交改动：
  - `reference_solver/generate_reference.py`
  - `scripts/start_ref_solver_segment.ps1`
  - 多个 `process-summaries/2026-05-25-*`
  - `scripts/start_ref_solver_segment.py`
  - `scripts/watch_ref_solver_run.ps1`
  这些改动来源需要确认，本轮未回滚。

**未完成的部分**
- 尚未用严格独立 80x80 参考解重新评估 Example 5。
- 尚未最终确认 Example 5 误差异常的唯一原因。
- 尚未在新严格参考解下重跑 Example 5。

**在总体进程中的作用**
- Example 5 已证明当前 reproduction runner、checkpoint、stage resume、metrics 输出、日志记录和最终报告链路可以跑通。
- 它为后续排查“误差为何偏大”提供了完整的冻结基线。
- 它也暴露了当前验证数据 `interpolated_80x80_from20` 与严格参考解之间的潜在差异风险。

**总体进程中仍未完成**
- 严格 80x80 参考解生成。
- 严格参考解下 Example 2 重跑。
- 严格参考解下 Example 5 重跑。
- Example 5 误差异常根因确认。
- 最终论文级复现报告。

**受保护产物**
- `runs/overnight_current`：冻结目录，默认只读。
- Example 2 已完成产物：不得修改、覆盖、删除或重跑。
- Example 5 已完成产物：不得修改、覆盖、删除或重跑。
- `runs/overnight_current` 下 checkpoints、logs、reports、metrics、figures：不得删除或覆盖，除非用户明确要求。
- 后续任何新实验必须使用新的 `--run-name` 或新的输出目录。

**下一步建议**
1. 优先完成严格 80x80 参考解链路，不要重跑当前冻结 Example 5。
2. 对 Example 5 误差异常继续做只读/静态定位，重点核查五个时刻参考文件读取逻辑、`Te/Ti/Tr` 顺序、归一化、边界条件和 metrics 聚合。
3. 等严格参考解准备好后，用新的 run-name 重跑 Example 5，而不是续写 `overnight_current`。

**Markdown 文档**
- 已保存：`process-summaries/2026-05-25-example5-progress-report.md`

**需要确认**
- 当前工作区中 `reference_solver/generate_reference.py`、`scripts/start_ref_solver_segment.ps1` 以及新增脚本/报告是否都是预期保留内容。
- 是否将下一步聚焦在严格 80x80 参考解生成，还是先继续静态排查 Example 5 误差计算逻辑。
