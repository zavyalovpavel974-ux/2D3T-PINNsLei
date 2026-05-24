# Reference Solver Interrupt/Resume Smoke Plan

## 1. 当前目的

补充验证 reference solver 在“中断态 checkpoint”下的续跑能力：第一段在 `t < 1.0` 时保存 checkpoint 并停止，第二段从该 checkpoint resume，并确认 `step` 或 `t` 继续推进。

本计划只用于小规模烟测，不启动 strict `80x80`，不重跑 Example 2，不重跑 Example 5，不启动训练。

## 2. 当前已知

`reference_solver/generate_reference.py solve` 当前已支持：

- `--checkpoint`
- `--resume-checkpoint`
- `--checkpoint-interval-steps`
- `--max-walltime-seconds`

当前不支持显式：

- `--max-steps`

因此优先使用极短 `--max-walltime-seconds` 触发受控中断。如果 walltime 不可控，再考虑最小改造。

## 3. 计划输出目录

```text
reference_solver_outputs/ref_solver_interrupt_resume_test
```

该目录是新的本地测试目录。不得写入 `runs/overnight_current`。

## 4. 第一段强制中断 checkpoint 命令

目标：在 `t < 1.0` 时生成 `interrupt.ckpt.npz`，并通过 walltime 停止。

```powershell
New-Item -ItemType Directory -Force `
  .\reference_solver_outputs\ref_solver_interrupt_resume_test, `
  .\reference_solver_outputs\ref_solver_interrupt_resume_test\logs | Out-Null

python .\reference_solver\generate_reference.py solve `
  --case aei700_krartr `
  --nx 20 --ny 20 `
  --times 1e-5,0.3,0.5,0.7,1.0 `
  --dt-init 0.0025 `
  --dt-max 0.02 `
  --newton-max 8 `
  --gmres-maxiter 120 `
  --checkpoint .\reference_solver_outputs\ref_solver_interrupt_resume_test\interrupt.ckpt.npz `
  --checkpoint-interval-steps 1 `
  --max-walltime-seconds 1 `
  --out .\reference_solver_outputs\ref_solver_interrupt_resume_test\interrupt_should_not_complete.npz `
  1> .\reference_solver_outputs\ref_solver_interrupt_resume_test\logs\part1.stdout.log `
  2> .\reference_solver_outputs\ref_solver_interrupt_resume_test\logs\part1.stderr.log
```

预期结果：

- 命令返回非零退出码。
- stderr 中出现 `TimeoutError` 或 `walltime`。
- `interrupt.ckpt.npz` 存在。
- checkpoint 中 `step > 0` 且 `t < 1.0`。
- `interrupt_should_not_complete.npz` 理想情况下不存在；若存在则说明第一段未形成中断态，需要停止并重新评估。

## 5. 第一段检查命令

```powershell
Test-Path .\reference_solver_outputs\ref_solver_interrupt_resume_test\interrupt.ckpt.npz
Get-Content .\reference_solver_outputs\ref_solver_interrupt_resume_test\logs\part1.stderr.log -Tail 40

python -c "import numpy as np; p='reference_solver_outputs/ref_solver_interrupt_resume_test/interrupt.ckpt.npz'; d=np.load(p, allow_pickle=True); print({'step': int(d['step'][0]), 't': float(d['t'][0]), 'dt': float(d['dt'][0]), 'interrupted_before_t1': float(d['t'][0]) < 1.0})"
```

必须确认：

- `Test-Path` 返回 `True`。
- `interrupted_before_t1` 返回 `True`。

## 6. 第二段 resume 命令

目标：从第一段 `interrupt.ckpt.npz` resume，生成 `resume.ckpt.npz` 和 `resume.npz`。

```powershell
python .\reference_solver\generate_reference.py solve `
  --case aei700_krartr `
  --nx 20 --ny 20 `
  --times 1e-5,0.3,0.5,0.7,1.0 `
  --dt-init 0.0025 `
  --dt-max 0.02 `
  --newton-max 8 `
  --gmres-maxiter 120 `
  --resume-checkpoint .\reference_solver_outputs\ref_solver_interrupt_resume_test\interrupt.ckpt.npz `
  --checkpoint .\reference_solver_outputs\ref_solver_interrupt_resume_test\resume.ckpt.npz `
  --checkpoint-interval-steps 10 `
  --out .\reference_solver_outputs\ref_solver_interrupt_resume_test\resume.npz `
  1> .\reference_solver_outputs\ref_solver_interrupt_resume_test\logs\part2.stdout.log `
  2> .\reference_solver_outputs\ref_solver_interrupt_resume_test\logs\part2.stderr.log
```

## 7. 推进检查命令

```powershell
python -c "import numpy as np; a=np.load('reference_solver_outputs/ref_solver_interrupt_resume_test/interrupt.ckpt.npz', allow_pickle=True); b=np.load('reference_solver_outputs/ref_solver_interrupt_resume_test/resume.ckpt.npz', allow_pickle=True); print({'interrupt_step': int(a['step'][0]), 'interrupt_t': float(a['t'][0]), 'resume_step': int(b['step'][0]), 'resume_t': float(b['t'][0]), 'step_advanced': int(b['step'][0]) > int(a['step'][0]), 't_advanced': float(b['t'][0]) > float(a['t'][0])})"
```

必须确认：

- `step_advanced` 为 `True`，或 `t_advanced` 为 `True`。
- 理想情况下两者均为 `True`。

## 8. Validate 命令

```powershell
python .\reference_solver\generate_reference.py validate `
  --npz .\reference_solver_outputs\ref_solver_interrupt_resume_test\resume.npz `
  --json-out .\reference_solver_outputs\ref_solver_interrupt_resume_test\resume_validate.json
```

## 9. 安全检查命令

```powershell
python .\repro_status.py --run-name overnight_current
git status --short --branch
```

必须确认：

- `runs/overnight_current` 仍显示 `Protected: True`。
- Example 2 不被重跑。
- Example 5 不被重跑。
- 不提交 `reference_solver_outputs` 下输出。

## 10. 通过标准

本 smoke 通过需同时满足：

- 第一段 `interrupt.ckpt.npz` 存在。
- 第一段 checkpoint 中 `step > 0`。
- 第一段 checkpoint 中 `t < 1.0`。
- 第二段 `resume.ckpt.npz` 存在。
- 第二段 `resume.npz` 存在。
- 第二段相对第一段满足 `step_advanced=True` 或 `t_advanced=True`。
- `resume_validate.json` 存在。
- validate 报告中所有 `Te/Ti/Tr` 数组 finite。
- validate 报告中 `top_Tr_max_abs_error=0.0` 或接近 `0.0`。
- `runs/overnight_current` 未被写入，且仍为 protected。

## 11. 若 walltime 方案失败的处理策略

如果 `--max-walltime-seconds 1` 仍直接跑到 `t=1.0`，不得覆盖已有目录结果。应停止并使用新目录后缀重试，例如：

```text
reference_solver_outputs/ref_solver_interrupt_resume_test_wall005
```

可尝试更短 walltime，例如：

```powershell
--max-walltime-seconds 0.05
```

如果更短 walltime 仍无法稳定得到 `t < 1.0` 的 checkpoint，则停止并进入最小代码改造方案。

## 12. 最小改造方案

仅当 walltime 不可控时，才考虑为 `reference_solver/generate_reference.py solve` 增加：

```text
--max-steps
```

最小改造范围：

- 只改 reference solver 的控制流。
- 不修改物理方程。
- 不修改 checkpoint 格式。
- 不修改训练脚本。
- 不修改 Example 2。
- 不修改 Example 5。
- 每个 accepted step 后检查 `step >= max_steps`。
- 达到 `--max-steps` 时先保存 checkpoint，再抛出受控异常或正常返回一个明确状态。

验收目标：

- 可稳定生成 `step > 0` 且 `t < 1.0` 的 checkpoint。
- resume 后可验证 `step` 或 `t` 继续推进。

## 13. 明确禁止事项

- 不启动 strict `80x80`。
- 不写入 `runs/overnight_current`。
- 不重跑 Example 2。
- 不重跑 Example 5。
- 不启动训练。
- 不提交 `reference_solver_outputs` 下输出。
- 不删除、移动、覆盖 checkpoint、logs、metrics、figures。

## 14. 下一步

等待用户确认后，才能实际运行该 smoke。运行完成后必须使用 `process-summary` skill 汇报，并保存结构化 Markdown 总结。
