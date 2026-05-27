# 2026-05-27 复现过程回顾汇报

**本轮运行状态**
- 状态：正常完成，只读回顾与证据核对。
- 命令：读取上下文交接文件、`python .\repro_status.py --run-name overnight_current`、`python .\repro_background.py status --run-name overnight_current`、读取 metrics/reports、检查 `reference_exports`、`reference_solver_outputs`、失败 checkpoint 和 `git status`。
- walltime 上限：不适用。
- 运行时长：需要确认。
- 退出原因：正常完成。

**本次进程概述**
- 本次不是重跑实验，而是根据你保存的窗口上下文、报告、metrics 和输出目录，重建之前的 2D 3T PINNs 复现路线。
- 已确认主线：先掌握作者代码并补齐运行工程链路，再用插值 `80x80_from20` 参考数据跑通 Example 2/Example 5，随后尝试生成严格传统参考解，最终 strict `80x80` 卡在 reference solver 方法问题。

**取得的成果**
- 已确认 `runs/overnight_current` 存在且 `Protected=True`，是冻结基线。
- Example 2 已完成：`stage=inverse`，`phase=completed`，`step=6001`，checkpoint 为 `runs/overnight_current/checkpoints/example2/latest.pt`。
- Example 2 反演结果：`rho=1.102853289967324`，真值 `1.1`，相对误差约 `0.259%`。
- Example 2 aggregate errors：Te L2 `2.240850784e-02`，Ti L2 `2.383876654e-02`，Tr L2 `3.739215547e-02`；但 Tr Linf `2.917777245e-01` 明显偏大。
- Example 5 已完成：`stage=700`，`phase=completed`，`step=6001`，checkpoint 为 `runs/overnight_current/checkpoints/example5/latest.pt`。
- Example 5 原始 aggregate errors 很大：Te L2 `0.7049614629`，Ti L2 `0.7081070316`，Tr L2 `0.6686891071`，不符合论文 Table 9 量级。
- 已确认 Example 5 后处理曾发现参考文件读取问题：五个时间点都用到 `_80_1/t=1` 参考；只读 per-time 修正后 L2 降为 Te `0.1957274767`、Ti `0.2065726908`、Tr `0.1632200766`，但仍不是论文级结果。
- 已确认严格 `20x20` 参考解已生成；`aei70_krar_32` 严格 `32x32` 已完成、验证并导出；`aei700_krartr_32` 在 30 分钟上限内到 `t=0.965092` 后未完成。
- 已确认 strict `80x80 aei70_krar` 多轮失败，最新关键 failed checkpoint 在 `reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz`。
- failed checkpoint 事实：`step=9`，`t=0.0077455892`，`dt=7.8732e-07`，`history_len=9`，`diagnostics_len=15`。
- 失败诊断显示 rejected step 主要为 `line_search_failed`，`gmres_info=300`，`gmres_iterations=12000`，`gmres_last≈2.535e-07`。

**续跑状态与检查点**
- 当前冻结 checkpoint：
  - Example 2：`runs/overnight_current/checkpoints/example2/latest.pt`
  - Example 5：`runs/overnight_current/checkpoints/example5/latest.pt`
- 当前阶段：
  - Example 2：`inverse`
  - Example 5：`700`
  - strict `80x80 aei70_krar`：失败诊断阶段，不建议续跑 Segment 2。
- 当前步数或优化器阶段：
  - Example 2：`completed`, step `6001`
  - Example 5：`completed`, step `6001`
  - strict `80x80`：reference solver 失败于 `step=9`, `t≈0.007746`
- 已完成阶段：Example 2 完成；Example 5 的 `70/400/700` 工程链路完成；strict reference 中 `20x20` 和 `aei70_krar_32` 完成。
- 下一次安全检查命令：
  ```powershell
  python .\repro_status.py --run-name overnight_current
  ```
- 不应执行的危险操作：
  - 不要删除、覆盖或继续写入 `runs/overnight_current`。
  - 不要重跑 Example 2 或 Example 5 到冻结目录。
  - 不要把 Example 5 的 `70/400/700` 阶段 checkpoint 混用。
  - 不要启动 strict `80x80` Segment 2 或重启失败 run，除非先完成 solver 方法改造并使用新输出目录。

**遇到的阻碍**
- 严格 `80x80` 传统参考解没有成功生成，这是论文级复现的核心 blocker。
- 当前 SciPy matrix-free JFNK 路线在 `aei70_krar_80` 上早期失败，表现更像 Newton/line-search/JFNK 步长接受边界问题，而不是单纯 GMRES 不收敛。
- Example 5 当前完成结果基于 `interpolated_80x80_from20`，不是独立严格 `80x80` 参考解。
- Example 5 原始后处理存在 per-time reference mismatch，虽然已只读修正统计口径，但仍未达到论文误差。
- Git 记录里曾多次出现 `.git/index.lock` 权限问题，导致某些提交未完成或需要在本机终端处理。

**未完成的部分**
- 严格 `80x80` reference solver 尚未完成。
- `aei700_krartr_32` strict reference 尚未完整完成。
- Example 3/Example 4 没有独立完整复现实验记录。
- Example 5 还没有基于严格 `80x80` 参考数据重跑并得到论文级表格。
- 当前工作区未提交改动和未跟踪汇报/脚本仍需人工筛选。

**在总体进程中的作用**
- 已完成的工作证明了作者代码可被工程化运行：隔离 run 目录、checkpoint/resume、walltime、metrics、报告和状态查询链路都已搭好。
- `runs/overnight_current` 是“插值参考数据验证版”的冻结证据，用来证明 pipeline 能跑通，不应用来宣称论文级复现。
- strict reference solver 的失败诊断明确了下一阶段应做 solver 方法改造，而不是继续盲目长跑。

**总体进程中仍未完成**
- 生成可靠 strict `80x80` 传统数值参考解。
- 用 strict `80x80` 参考解从新 run-name 重跑 Example 2/Example 5。
- 重新生成论文 Table 4、Table 9、Table 11、Table 12 对比。
- 整理可提交代码、笔记、summary，并排除大输出、checkpoint、logs。
- 决定下一步优先级：继续 solver 方法改造，还是先把当前工程验证版写成阶段报告。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- Example 5 已完整跑完：必须区分 `70/400/700` 阶段，先不要重跑到冻结目录。
- `runs/overnight_current` 中已有 checkpoint、logs、metrics、reports、figures：默认不得删除或覆盖，除非用户明确要求。
- `reference_solver_outputs/*/checkpoints`、`reference_solver_outputs/*/logs` 和 `reference_solver_outputs/example5_static_recalc`：保留为诊断证据。

**下一步建议**
1. 先不要启动任何新训练或 strict `80x80` 长跑；先决定是否把当前复现状态整理成“阶段性工程验证报告”。
2. 若继续论文级复现，优先改造 reference solver：记录 line-search 全部 alpha/trial norm、Newton residual 序列、`dU` 范数、温度 floor、JFNK finite-difference epsilon。
3. 若只是恢复记忆，建议按这个阅读顺序看文件：`CONTEXT_COMPACT_2026-05-27.md`、`WINDOW_CONTEXT_EXPORT.md`、`runs/overnight_current/reports/final_reproduction_report.md`、`process-summaries/2026-05-25-aei70-80-strict-work-overall-summary.md`。
4. 如需提交成果，先只提交脚本、报告和小型 `aei70_krar_32` 产物；不要提交 `reference_solver_outputs` 下的大输出/checkpoints/logs。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-27-reproduction-recap-summary.md`

**需要确认**
- 你下一步更想做哪条线：整理阶段性报告、修 strict `80x80` reference solver，还是回到 PINNs 代码本身继续学习/排查 Example 5。
- 当前未提交改动是否要保留并提交，需要你确认提交范围。
