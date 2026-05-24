**本轮运行状态**
- 状态：只读检查正常完成
- 命令：
  - `Get-ChildItem .\reference_solver_outputs\ref_solver_interrupt_resume_test_20260525_021958`
  - `Test-Path` 检查 `interrupt.ckpt.npz`、`resume.ckpt.npz`、`resume.npz`、`resume_validate.json`
  - 只读读取 `interrupt.ckpt.npz` 和 `resume.ckpt.npz` 的 `step/t/dt`
  - 只读读取 `resume_validate.json`
  - `python .\repro_status.py --run-name overnight_current`
  - `git status --short --branch`
- walltime 上限：本轮未启动命令；读取到第一段既有日志显示此前 smoke 使用 walltime 并触发 `TimeoutError`
- 运行时长：本轮为轻量只读检查
- 退出原因：正常完成

**本次进程概述**
本轮只读检查已有中断态 reference solver checkpoint/resume smoke 结果，目标目录为 `reference_solver_outputs/ref_solver_interrupt_resume_test_20260525_021958`。未启动 strict `80x80`，未重跑 Example 2，未重跑 Example 5，未写入 `runs/overnight_current`。

**取得的成果**
- 目标目录存在，包含：
  - `interrupt.ckpt.npz`
  - `resume.ckpt.npz`
  - `resume.history.json`
  - `resume.npz`
  - `resume_validate.json`
  - `logs/`
- 第一段中断 checkpoint 存在：
  - 路径：`reference_solver_outputs/ref_solver_interrupt_resume_test_20260525_021958/interrupt.ckpt.npz`
  - `step=5`
  - `t=0.003916`
  - `dt=9.72e-05`
  - `step > 0` 为 `True`
  - `t < 1.0` 为 `True`
- 第一段日志确认 walltime 中断：
  - `TimeoutError: reference solve reached walltime at step=5 t=0.003916`
  - checkpoint 指向 `interrupt.ckpt.npz`
- 第二段 resume checkpoint 存在：
  - 路径：`reference_solver_outputs/ref_solver_interrupt_resume_test_20260525_021958/resume.ckpt.npz`
  - `step=201`
  - `t=1.0`
  - `dt=0.01988652931993986`
- 第二段输出存在：
  - `reference_solver_outputs/ref_solver_interrupt_resume_test_20260525_021958/resume.npz`
- 第二段 stdout 确认从中断 checkpoint resume：
  - `resumed ... interrupt.ckpt.npz at step=5 t=0.003916 dt=9.72e-05`
  - 最终 `done in 5.4s, steps=201`
- resume 推进确认：
  - `step_advanced=True`
  - `t_advanced=True`
- validate 输出存在并通过：
  - `reference_solver_outputs/ref_solver_interrupt_resume_test_20260525_021958/resume_validate.json`
  - `nx=20`
  - `ny=20`
  - `num_times=5`
  - 时间点：`1e-5`、`0.3`、`0.5`、`0.7`、`1.0`
  - 所有 `Te/Ti/Tr` 数组 finite
  - `max_top_Tr_error=0.0`
- `repro_status.py --run-name overnight_current` 确认：
  - `runs/overnight_current` exists
  - `Protected: True`
  - Example 2：stage `inverse`，phase `completed`，step `6001`
  - Example 5：stage `700`，phase `completed`，step `6001`
- `git status --short --branch` 在保存本 summary 前显示：
  - `## run-interrupt-resume-smoke`
  - 工作区无未提交改动

**续跑状态与检查点**
- 本轮没有新的求解进程，也没有后台任务。
- 已有 smoke 结果严格证明了中断态 checkpoint 可以 resume：
  - interrupt：`step=5, t=0.003916`
  - resume：`step=201, t=1.0`
- 从 `interrupt.ckpt.npz` 续跑到完整 `resume.npz` 成功，validate 通过。

**遇到的阻碍**
- 无阻碍。
- 第一段 stderr 中出现 `TimeoutError`，这是本 smoke 的预期中断机制，不是失败。

**未完成的部分**
- strict `80x80` reference solver 正式长跑尚未启动。
- strict `80x80` 长跑的后台/分段 walltime 方案仍需单独规划。
- 未提交 `reference_solver_outputs` 下输出。

**在总体进程中的作用**
本轮确认了 reference solver 的关键运行安全链路：小网格求解可以在 `t < 1.0` 时保存 checkpoint，中断后可以从 checkpoint resume，并且 `step/t` 继续推进到完整解。这为后续 strict `80x80` 长跑的分段 walltime 和 checkpoint 续跑方案提供了直接依据。

**总体进程中仍未完成**
- Example 5 的最终论文级 metrics 仍需 strict `80x80` reference solver 正式结果确认。
- strict `80x80` 的输出目录、checkpoint 周期、walltime 切分、日志审查、后台检查命令和停止命令仍需确认。

**受保护产物**
- `runs/overnight_current` 未被写入、删除、移动或覆盖。
- Example 2 已完成，其 checkpoint、logs、metrics、reports、figures 不得修改、覆盖、删除或重跑。
- Example 5 已完成，其 stage `700` checkpoint、logs、metrics、reports、figures 不得修改、覆盖、删除或重跑。
- 本轮未启动 strict `80x80`，未重跑 Example 2，未重跑 Example 5，未提交 `reference_solver_outputs` 下输出。

**下一步建议**
- 可以进入 strict `80x80` reference solver 正式长跑规划。
- 规划中应沿用本 smoke 验证过的安全机制：独立输出目录、checkpoint、`--resume-checkpoint`、分段 walltime、日志路径、`repro_status.py --run-name overnight_current` 安全检查。
- 正式长跑前应明确是否后台运行，以及每段 walltime、checkpoint 文件、检查命令和停止命令。

**Markdown 文档**
- 本报告已保存到 `process-summaries/2026-05-25-ref-solver-interrupt-resume-smoke-summary.md`。

**需要确认**
- strict `80x80` reference solver 正式长跑的输出目录与 run-name。
- 是否采用后台运行或手动分段 walltime。
