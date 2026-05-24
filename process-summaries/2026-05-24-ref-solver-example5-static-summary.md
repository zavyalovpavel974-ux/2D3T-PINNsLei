**本轮运行状态**

- 状态：正常完成。
- 命令：本轮为状态汇总；核心证据来自 `python repro_status.py --run-name overnight_current`、reference solver smoke test 输出、Example 5 静态审查结果。
- walltime 上限：不适用；本轮未启动训练。
- 运行时长：需要确认。
- 退出原因：正常完成。
- 本轮未启动训练、未启动后台进程、未重跑 Example 2、未重跑 Example 5、未写入 `runs/overnight_current`。

**本次进程概述**

本轮完成了“严格参考解链路小规模 checkpoint/resume 验证 + Example 5 失败原因静态审查”的阶段性收束。`reference_solver/generate_reference.py` 已确认支持小网格、独立输出、checkpoint、resume、checkpoint interval、walltime 中断控制；因此本轮未修改 solver 代码，只在新的测试目录 `runs/ref_solver_smoke_test` 中完成 smoke test。随后只读审查 Example 5 的 metrics、run_result、日志和相关脚本。

**取得的成果**

- `runs/overnight_current` 状态确认：Exists=True，Protected=True。
- Example 2 状态确认：stage=inverse，phase=completed，step=6001。
- Example 5 状态确认：stage=700，phase=completed，step=6001。
- 小规模 reference solver smoke test 通过：
  - 初始运行用极短 walltime 触发中断并保存 checkpoint。
  - 从 checkpoint resume 后完成到 `t=1.0`。
  - `reference_resumed.npz` validate 通过，`nx=8`、`ny=8`，时间点 `1e-5` 和 `0.05` 均 finite，顶部 `Tr` 边界误差为 `0.0`。
  - author txt export 成功。
- Example 5 静态审查确认：
  - `example5_metrics.json` 标记 `"reference": "interpolated_80x80_from20"`，不是严格论文级 `80x80` 参考解。
  - `2D3T_wei_aei700_wer_krartr_time.py` 在五个时间点误差计算中都读取 `sol1_wei_aei700_wer_krartr_80_1.txt`，而不是分别读取 `1e-5/0.3/0.5/0.7/1.0` 对应文件。
  - `runs/overnight_current/workdir` 中实际存在多个不同 hash 的 Example 5 参考文件，因此该后处理读取逻辑会污染非 t=1 时刻误差。
  - 变量顺序链路一致：reference export 写 `(Tr, Te, Ti)`，author reader 用 `(1,2,0)` 映射为 `Te, Ti, Tr`。
  - 日志未确认到 `nan`、`traceback`、`exception`、`killed` 等训练异常；stderr 主要是 warnings。

**续跑状态与检查点**

- 当前受保护 Example 5 checkpoint：`runs/overnight_current/checkpoints/example5/latest.pt`
- 当前阶段：700。
- 当前步数或优化器阶段：completed，step=6001。
- 已完成阶段：Example 5 已完成到 stage 700；stdout 显示曾从 70 resume 到 400，再从 400 resume 到 700。
- 下一次安全续跑命令：
  ```powershell
  需要先确认新的 run-name、严格参考解目录、以及是否先修正 Example 5 per-time 参考文件读取逻辑；不要直接续跑或覆盖 runs/overnight_current。
  ```
- 不应执行的危险操作：
  - 不要删除、覆盖或继续写入 `runs/overnight_current`。
  - 不要重跑 Example 2。
  - 不要重跑 Example 5。
  - 不要把 Example 5 的 70/400/700 阶段 checkpoint 误加载到错误阶段。

**遇到的阻碍**

- Example 5 当前 metrics 不是严格参考解指标，仍依赖 interpolated `80x80_from20` 验证数据。
- Example 5 后处理存在已确认的 per-time 参考文件读取风险：多个时间点都读 t=1 文件。
- `example5_metrics.json` 只保留最终 stage 700 的 `stage_training_time_seconds`；完整 70/400/700 时间需要从 stdout 解析。
- 当前工作区存在未跟踪/修改项，包括 `.codex` 下 skill 相关文件、`process-summaries/2026-05-24-ref-solver-smoke-summary.md`、`reference_solver_outputs/` 等，需要在提交前单独审查。

**未完成的部分**

- 尚未修正 Example 5 后处理代码。
- 尚未用现有冻结产物只读复算修正后的 Example 5 metrics 到新目录。
- 尚未启动严格 `80x80` reference solver 正式求解。
- 尚未用严格参考解重跑 Example 2 或 Example 5。

**在总体进程中的作用**

- 本轮证明 reference solver 的 checkpoint/resume 小规模链路可用。
- 本轮确认冻结目录保护仍有效。
- 本轮把 Example 5 失败原因从“可能是插值参考解或训练设置”推进到“已确认存在后处理读取错误风险”，为下一步修正和严格参考解求解降低了不确定性。

**总体进程中仍未完成**

- 修正或隔离验证 Example 5 per-time reference 读取逻辑。
- 生成严格 `80x80` 数值参考解。
- 在新 run-name 下进行严格参考解验证。
- 根据严格参考解重新评估 Example 2 / Example 5。
- 更新最终论文级复现报告。

**受保护产物**

- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint、logs、reports、metrics、figures 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- Example 5 已完成到 stage 700：不得在 `runs/overnight_current` 内继续写入或覆盖。

**下一步建议**

1. 先修正 Example 5 per-time 参考文件读取逻辑，并用现有冻结产物只读复算 metrics 到新的输出目录，确认误差变化。
2. 再启动严格 `80x80` reference solver 的正式分段或后台求解，使用新的 run-name/输出目录。
3. 严格参考解完成后，再决定是否在新 run-name 下重跑 Example 2 / Example 5。

**Markdown 文档**

- 已保存：`process-summaries/2026-05-24-ref-solver-example5-static-summary.md`

**需要确认**

- 是否先实施 Example 5 per-time reference 文件读取修正。
- 是否允许创建新的只读复算脚本或报告，用冻结 checkpoint/模型产物生成修正后 metrics。
