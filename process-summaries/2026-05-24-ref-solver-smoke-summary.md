**本轮运行状态**
- 状态：正常完成。
- 命令：
  - `git status`
  - `python repro_status.py --run-name overnight_current`
  - `python reference_solver\generate_reference.py solve --case aei700_krartr --out reference_solver_outputs\ref_solver_smoke_test\part1.npz --nx 12 --ny 12 --times 1e-5,0.3,0.5,0.7,1.0 --dt-init 1e-4 --dt-max 1e-4 --gmres-maxiter 80 --checkpoint reference_solver_outputs\ref_solver_smoke_test\checkpoints\latest.npz --checkpoint-interval-steps 1 --max-walltime-seconds 300 *> reference_solver_outputs\ref_solver_smoke_test\logs\part1.log`
  - `python reference_solver\generate_reference.py solve --case aei700_krartr --out reference_solver_outputs\ref_solver_smoke_test\part2.npz --nx 12 --ny 12 --times 1e-5,0.3,0.5,0.7,1.0 --dt-init 1e-4 --dt-max 1e-4 --gmres-maxiter 80 --checkpoint reference_solver_outputs\ref_solver_smoke_test\checkpoints\latest.npz --resume-checkpoint reference_solver_outputs\ref_solver_smoke_test\checkpoints\latest.npz --checkpoint-interval-steps 1 --max-walltime-seconds 300 *> reference_solver_outputs\ref_solver_smoke_test\logs\part2.log`
- walltime 上限：每段 `300` 秒。
- 运行时长：第一段日志显示 `114.3s`；第二段日志显示 `0.0s`。
- 退出原因：两段均正常完成；未启动 Example 2、Example 5，未启动完整 80x80。

**本次进程概述**
- 本轮目标是验证 `reference_solver/generate_reference.py` 的小规模 checkpoint/resume 链路。
- 使用新输出目录 `reference_solver_outputs/ref_solver_smoke_test`，没有写入 `runs/overnight_current`。
- 第一段生成 checkpoint 与 `part1.npz`；第二段用 `--resume-checkpoint` 从同一 checkpoint 恢复并写出 `part2.npz`。
- 未修改代码；当前工作区另有 `.codex/skills/process-summary/SKILL.md` 修改和 skill 相关未跟踪文件，来源需要确认。

**取得的成果**
- `runs/overnight_current` 已确认存在且 `Protected: True`。
- Example 2 已确认：stage `inverse`，phase `completed`，step `6001`。
- Example 5 已确认：stage `700`，phase `completed`，step `6001`。
- 新 checkpoint 已生成：`reference_solver_outputs/ref_solver_smoke_test/checkpoints/latest.npz`。
- 第一段输出已生成：`reference_solver_outputs/ref_solver_smoke_test/part1.npz`。
- 第二段输出已生成：`reference_solver_outputs/ref_solver_smoke_test/part2.npz`。
- 第二段日志明确包含：`[reference] resumed reference_solver_outputs\ref_solver_smoke_test\checkpoints\latest.npz at step=10002 t=1.000000 dt=8.59e-05`。
- `part1.npz` 与 `part2.npz` 已做 validate：均为 `12x12`，各时刻数组 finite，顶部 `Tr` 边界误差为 `0.0`。

**续跑状态与检查点**
- 当前 smoke checkpoint：`reference_solver_outputs/ref_solver_smoke_test/checkpoints/latest.npz`。
- 当前阶段：reference solver smoke test，不属于 Example 5 的 70/400/700 训练阶段。
- 当前步数或优化器阶段：checkpoint 恢复日志显示 `step=10002`、`t=1.000000`，为完成态 checkpoint。
- 已完成阶段：小规模 reference solver 第一段 checkpoint 生成、第二段完成态 resume 加载。
- 下一次安全续跑命令：
  ```powershell
  python reference_solver\generate_reference.py solve --case aei700_krartr --out reference_solver_outputs\ref_solver_smoke_test\part2.npz --nx 12 --ny 12 --times 1e-5,0.3,0.5,0.7,1.0 --dt-init 1e-4 --dt-max 1e-4 --gmres-maxiter 80 --checkpoint reference_solver_outputs\ref_solver_smoke_test\checkpoints\latest.npz --resume-checkpoint reference_solver_outputs\ref_solver_smoke_test\checkpoints\latest.npz --checkpoint-interval-steps 1 --max-walltime-seconds 300 *> reference_solver_outputs\ref_solver_smoke_test\logs\part2.log
  ```
- 不应执行的危险操作：
  - 不要删除、覆盖、移动或继续写入 `runs/overnight_current`。
  - 不要重跑 Example 2 或 Example 5 已完成产物。
  - 不要把 Example 5 的 70/400/700 阶段 checkpoint 混用或误判。
  - 不要用旧 `run-name` 启动新实验。

**遇到的阻碍**
- 初始后台 `Start-Process powershell ... *> log` 包装未可靠生成日志/checkpoint，后续改为直接命令执行并成功。
- `12x12` 第一段在 `300` 秒上限内完整完成，因此最终保留的是完成态 checkpoint resume 验证，不是中断态 checkpoint 继续推进验证。
- 当前 `git status` 显示 `.codex/skills/process-summary/SKILL.md` 已修改，并有 `.codex/skills/process-summaries/`、`.codex/skills/process-summary.zip`、`.codex/skills/process-summary/SKILL.md.bak`、`.codex/skills/process-summary/agents/` 等未跟踪项；这些不是本轮 smoke test 的必要产物，来源需要确认。

**未完成的部分**
- 未进行严格 80x80 参考解生成。
- 未启动 Example 2 或 Example 5。
- 未保留“中断态 checkpoint 继续推进”的最终验证产物。

**在总体进程中的作用**
- 本轮证明 reference solver 的小网格、独立输出目录、checkpoint 保存、resume 加载、日志输出链路可用。
- 这为后续严格 80x80 参考解生成前的安全验证提供了依据。

**总体进程中仍未完成**
- 严格 80x80 参考解。
- 严格参考解下 Example 2 重跑。
- 严格参考解下 Example 5 重跑。
- Example 5 误差异常最终原因确认。
- 最终论文级复现报告。

**受保护产物**
- `runs/overnight_current`：冻结目录，默认只读。
- Example 2 已完成产物：不得修改、覆盖、删除或重跑。
- Example 5 已完成产物：必须区分 70、400、700 阶段，不得混用阶段状态。
- `runs/overnight_current` 下的 checkpoints、logs、reports、metrics、figures：不得删除或覆盖，除非用户明确要求。
- 后续新实验必须使用新的 `--run-name` 或新的输出目录。

**下一步建议**
1. 若要补齐 checkpoint/resume 证据链，建议新建 `reference_solver_outputs/ref_solver_resume_interrupt_test`，用 `--max-walltime-seconds 30` 强制生成中断态 checkpoint，再 resume 验证 step/t 继续推进。
2. 在进入严格 80x80 前，先清点当前工作区中 `.codex/skills/...` 的非本轮改动，确认是否保留。
3. 严格 80x80 参考解应使用新的输出目录，不能写入 `runs/overnight_current`。

**Markdown 文档**
- 已保存：`process-summaries/2026-05-24-ref-solver-smoke-summary.md`

**需要确认**
- 是否保留 `reference_solver_outputs/`。
- 是否保留或清理当前 `.codex/skills/...` 下的修改和未跟踪文件。
- 是否执行“中断态 checkpoint/resume 推进”补充烟测。
