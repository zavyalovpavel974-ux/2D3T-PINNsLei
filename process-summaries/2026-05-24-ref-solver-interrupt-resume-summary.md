**本轮运行状态**

- 状态：正常完成，但包含一次外层工具超时中断。
- 命令：执行了 reference solver 中断态 checkpoint/resume smoke test；未启动训练、未启动后台进程、未运行 Example 2、未运行 Example 5。
- walltime 上限：第一段 32x32 使用 `--max-walltime-seconds 30`；补充 16x16 闭环使用 `--max-walltime-seconds 1`。
- 运行时长：32x32 第一段约 33 秒；32x32 resume 段被外层工具超时中断；16x16 resume 段约 12 秒完成。
- 退出原因：32x32 第一段达到 solver walltime；32x32 第二段外层工具超时；16x16 补充闭环正常完成。

**本次进程概述**

本轮在新目录 `reference_solver_outputs/ref_solver_resume_interrupt_test` 中执行 reference solver checkpoint/resume 烟测。原计划 32x32 第一段成功触发 walltime 并保存 checkpoint，第二段从 checkpoint 继续推进，但未在外层工具时限内完成。为完成闭环，保留 32x32 产物不覆盖，并用 16x16 + 1 秒 walltime 文件名后缀补做了一次完整中断/续跑/validate 验证。

**取得的成果**

- 32x32 第一段成功触发 walltime：
  - checkpoint：`reference_solver_outputs/ref_solver_resume_interrupt_test/checkpoints/interrupt_checkpoint.npz`
  - checkpoint 状态：`step=29`，`t=0.017265633434534043`，`dt=0.0021464148744915505`
  - stderr 明确包含 `TimeoutError: reference solve reached walltime`
- 32x32 第二段从该 checkpoint resume，并确认继续推进：
  - stdout 含 resumed 信息。
  - `resumed_checkpoint.npz` 存在。
  - 推进到 `step=220`，`t=0.8072713745768957`，`step_advanced=True`，`t_advanced=True`
  - 未写出最终 `part2_resumed.npz`，因为外层工具超时。
- 16x16 + 1 秒 walltime 补充闭环成功：
  - 中断 checkpoint：`interrupt_checkpoint_16x16_wall1.npz`
  - 中断状态：`step=3`，`t=0.0033799999999999998`
  - resume checkpoint：`resumed_checkpoint_16x16_wall1.npz`
  - resume 完成状态：`step=220`，`t=1.0`
  - 输出：`outputs/part2_resumed_16x16_wall1.npz`
  - validate 输出：`outputs/part2_validate_16x16_wall1.json`
  - validate 确认 5 个时间点均 finite，顶部 `Tr` 边界误差均为 `0.0`。
- 最终确认没有 Python 进程残留。
- 最终确认 `runs/overnight_current` 仍 `Protected: True`。

**续跑状态与检查点**

- 32x32 可继续 resume 的 checkpoint：`reference_solver_outputs/ref_solver_resume_interrupt_test/checkpoints/resumed_checkpoint.npz`
- 32x32 当前阶段：reference solver `aei70_krar`，非 Example 2 / Example 5 训练。
- 32x32 当前步数：`step=220`，`t=0.8072713745768957`
- 16x16 补充验证已完成，无需续跑。
- 下一次安全续跑命令：
  ```powershell
  python .\reference_solver\generate_reference.py solve --case aei70_krar --nx 32 --ny 32 --times 1e-5,0.3,0.5,0.7,1.0 --dt-init 0.002 --dt-max 0.005 --newton-max 8 --gmres-maxiter 120 --resume-checkpoint .\reference_solver_outputs\ref_solver_resume_interrupt_test\checkpoints\resumed_checkpoint.npz --checkpoint .\reference_solver_outputs\ref_solver_resume_interrupt_test\checkpoints\resumed_checkpoint_continued.npz --checkpoint-interval-steps 10 --out .\reference_solver_outputs\ref_solver_resume_interrupt_test\outputs\part2_resumed_continued.npz
  ```
- 不应执行的危险操作：
  - 不要写入、覆盖或删除 `runs/overnight_current`。
  - 不要启动 Example 2。
  - 不要启动 Example 5。
  - 不要把 reference solver checkpoint 与 Example 5 的 70/400/700 训练 checkpoint 混用。

**遇到的阻碍**

- 32x32 第二段比预期慢，外层工具超时后曾留下一个 Python 残留进程；已停止并确认没有 Python 进程残留。
- 16x16 使用 30 秒 walltime 时完整跑完，无法形成中断态；因此追加了 1 秒 walltime 的 16x16 补充闭环。
- `reference_solver_outputs/` 属于本地实验输出，不建议提交。

**未完成的部分**

- 32x32 resume 未完整写出最终 `part2_resumed.npz`。
- 尚未运行严格 `80x80` reference solver。
- 尚未修正 Example 5 per-time reference 文件读取逻辑。

**在总体进程中的作用**

- 本轮验证了 reference solver 在 walltime 中断后能够保存 checkpoint。
- 本轮验证了从中断 checkpoint resume 后 step/t 能继续推进。
- 本轮通过 16x16 补充闭环确认 resume 后可以完成并通过 validate。
- 本轮继续保持 `runs/overnight_current` 冻结目录不被写入。

**总体进程中仍未完成**

- 整理 Git 工作区，决定哪些治理/summary 文件提交，哪些本地输出忽略或清理。
- 修正或隔离验证 Example 5 per-time reference 读取逻辑。
- 生成严格 `80x80` 数值参考解。
- 在新 run-name 下进行严格参考解验证。
- 更新最终论文级复现报告。

**受保护产物**

- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint、logs、reports、metrics、figures 和结果文件：默认不得删除或覆盖。
- Example 5 已完成到 stage 700：不得在 `runs/overnight_current` 中继续写入或覆盖。

**下一步建议**

1. 将 `reference_solver_outputs/` 继续视为本地输出，不提交。
2. 先整理 Git 工作区：提交正式治理/summary 文件，忽略或人工清理 `.zip/.bak/agents/reference_solver_outputs` 等本地产物。
3. 再修正 Example 5 per-time reference 文件读取逻辑，并用冻结产物只读复算 metrics 到新目录。

**Markdown 文档**

- 已保存：`process-summaries/2026-05-24-ref-solver-interrupt-resume-summary.md`

**需要确认**

- 是否继续完成 32x32 从 `t≈0.807` 到 `t=1.0` 的续跑。
- 是否提交本轮新增的 process summary 文档。
