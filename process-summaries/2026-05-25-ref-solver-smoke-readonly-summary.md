**本轮运行状态**
- 状态：只读检查正常完成
- 命令：
  - `Get-ChildItem .\reference_solver_outputs\ref_solver_smoke_test`
  - `Test-Path` 检查四个目标文件
  - 只读读取两个 checkpoint 的 `step/t/dt`
  - 只读读取 `aei700_krartr_20x20_smoke_resume_validate.json`
  - `python .\repro_status.py --run-name overnight_current`
  - `git status --short --branch`
- walltime 上限：不适用，本轮未启动训练、未启动 reference solve、未启动后台任务
- 运行时长：轻量只读检查
- 退出原因：正常完成

**本次进程概述**
本轮仅检查已有 `reference_solver_outputs/ref_solver_smoke_test` 结果，确认 Aei=700、Kr=Ar*Tr 的 `20x20` 小规模 reference solver checkpoint/resume 产物、validate 文件、冻结 run 状态和 Git 状态。未写入 `runs/overnight_current`。

**取得的成果**
- `reference_solver_outputs/ref_solver_smoke_test` 存在，并包含目标烟测文件。
- 第一段 checkpoint 存在：
  - `reference_solver_outputs/ref_solver_smoke_test/aei700_krartr_20x20_smoke.ckpt.npz`
  - `step=201`
  - `t=1.0`
  - `dt=0.01988652931993986`
  - 包含五个 snapshot：`1e-5`、`0.3`、`0.5`、`0.7`、`1.0`
- 第二段 resume checkpoint 存在：
  - `reference_solver_outputs/ref_solver_smoke_test/aei700_krartr_20x20_smoke_resume.ckpt.npz`
  - `step=201`
  - `t=1.0`
  - `dt=0.01988652931993986`
  - 包含同样五个 snapshot
- 第二段 resume 输出存在：
  - `reference_solver_outputs/ref_solver_smoke_test/aei700_krartr_20x20_smoke_resume.npz`
- validate 输出存在：
  - `reference_solver_outputs/ref_solver_smoke_test/aei700_krartr_20x20_smoke_resume_validate.json`
  - `nx=20`
  - `ny=20`
  - `num_times=5`
  - 所有 `Te/Ti/Tr` 数组 finite
  - `top_Tr_max_abs_error=0.0`
- `repro_status.py --run-name overnight_current` 确认：
  - `runs/overnight_current` exists 且 `Protected: True`
  - Example 2：stage `inverse`，phase `completed`，step `6001`
  - Example 5：stage `700`，phase `completed`，step `6001`
- `git status --short --branch` 显示：
  - `## ref-solver-smoke-resume`
  - 工作区无未提交改动

**续跑状态与检查点**
- 当前这组 `20x20_smoke` 结果显示 resume 命令可读取 checkpoint 并写出 resume checkpoint/output。
- 但第一段 checkpoint 已经是完成态：`step=201, t=1.0`。
- 第二段 resume checkpoint 仍为 `step=201, t=1.0`，history 长度也与第一段相同，都是 `201`。
- 因此，本轮读取到的结果可以确认“completed checkpoint 的 resume 读取和输出路径正常”，但不能单独证明“walltime 中断态 checkpoint resume 后 step/t 继续推进”。

**遇到的阻碍**
- 当前目录下目标 `aei700_krartr_20x20_smoke` 第一段不是中断态，而是已完成态。
- `logs/part2.log` 属于同目录内另一组旧 `part2` 文件，显示从 `checkpoints/latest.npz` 的 `step=10002, t=1.0` resume 后立即完成；它不是本次四个目标文件的直接日志证据。

**未完成的部分**
- 本轮没有启动新的中断态复测。
- 对“中断后 checkpoint resume 并推进 step/t”的严格验证，在当前这组目标文件中仍需要确认。
- 未提交 `reference_solver_outputs` 下任何大输出。

**在总体进程中的作用**
本轮确认了小规模 `20x20` Example 5 reference solver 输出、checkpoint、resume 输出和 validate 文件均存在且 validate 通过，为后续 strict `80x80` reference solver 规划提供了基础信号。但因为当前第一段已完成，正式长跑前仍应在规划里区分“完成态 resume”与“中断态 resume 推进”。

**总体进程中仍未完成**
- strict `80x80` reference solver 正式长跑尚未启动。
- strict `80x80` 长跑的分段 walltime、checkpoint 间隔、日志路径、停止/检查命令仍需规划。
- Example 5 的最终论文级 metrics 仍需 strict `80x80` reference solver 结果确认。

**受保护产物**
- `runs/overnight_current` 仍为冻结只读产物，本轮未写入、删除、移动或覆盖。
- Example 2 已完成，输出不得修改、覆盖、删除或重跑。
- Example 5 已完成，stage `700` 输出不得修改、覆盖、删除或重跑。
- 本轮未启动训练、未启动完整 `80x80`、未重跑 Example 2、未重跑 Example 5。

**下一步建议**
- 可以进入 strict `80x80` reference solver 正式长跑规划，但建议在计划中明确：
  - 新输出目录；
  - checkpoint 文件路径；
  - checkpoint interval；
  - walltime 分段；
  - status 检查命令；
  - 停止命令；
  - 不写入 `runs/overnight_current`。
- 若必须先证明“中断态 step/t 继续推进”，应另用新的输出目录做一次更短 walltime 的中断态 smoke；本轮未执行。
- 暂未发现需要修改 `reference_solver/generate_reference.py` 的证据；现有结果说明 solve/checkpoint/resume/validate 基本链路可用。

**Markdown 文档**
- 本报告已保存到 `process-summaries/2026-05-25-ref-solver-smoke-readonly-summary.md`。

**需要确认**
- 是否接受当前完成态 resume 结果作为进入 strict `80x80` 长跑规划的充分条件。
- 是否还要追加一次“中断态 checkpoint resume 后 step/t 继续推进”的独立 smoke，使用新的输出目录。
