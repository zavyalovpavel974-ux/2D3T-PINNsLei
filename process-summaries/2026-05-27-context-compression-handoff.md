# Context Compression Handoff - 2026-05-27

## 当前一句话结论

strict `80x80` `aei70_krar` reference solver 已经过多轮启动、后台、诊断和 GMRES callback 诊断；当前结论是：**不要继续重启 80x80 run，不要启动 Segment 2，应暂停求解线，转入 solver 方法改造/诊断设计**。

这里的 `80x80` 指 reference solver 正式求解，不是 Example 2 / Example 5 的 PINN 训练。

## 绝对保护规则

- `runs/overnight_current` 是冻结目录，只读。
- 不得写入、移动、删除、覆盖 `runs/overnight_current`。
- 不重跑 Example 2。
- 不重跑 Example 5。
- 不启动 Example 5。
- 不提交 `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt。
- 不确定实验结果时写“需要确认”，不得猜测。

当前只读状态：

```text
runs/overnight_current: Exists=True, Protected=True
Example 2: completed, step 6001
Example 5: stage 700, completed, step 6001
```

只读检查命令：

```powershell
python .\repro_status.py --run-name overnight_current
```

## 当前 Git 状态摘要

当前分支：

```text
main
```

当前工作区有未提交改动，主要包括：

```text
 M reference_solver/generate_reference.py
 M scripts/start_ref_solver_segment.ps1
?? scripts/start_ref_solver_segment.py
?? scripts/watch_ref_solver_run.ps1
?? process-summaries/*.md
?? NET_F_LEARNING_NOTES.md
?? PAPER_EXPERIMENT_DISCUSSION_NOTES.md
?? TRAIN_LEARNING_NOTES.md
```

注意：

- 不要 `git add .`。
- 提交前需要人工筛选：脚本、诊断改造、summary 可以考虑；`reference_solver_outputs` 大输出不要提交。

## 已完成的重要工作

### 1. Example 5 per-time reference 修正

- 已确认原 Example 5 后处理五个时间点都错误读取 `sol1_wei_aei700_wer_krartr_80_1.txt`。
- 已确认 `_80_1` 与 `sol1_wei_aei700_wer_krartr_1.txt` 哈希相同，只代表 `t=1`。
- per-time 映射应为：

```text
1e-5 -> sol1_wei_aei700_wer_krartr_1e-5.txt
0.3  -> sol1_wei_aei700_wer_krartr_0p3.txt
0.5  -> sol1_wei_aei700_wer_krartr_0p5.txt
0.7  -> sol1_wei_aei700_wer_krartr_0p7.txt
1.0  -> sol1_wei_aei700_wer_krartr_1.txt
```

- 只读复算脚本曾验证 t=1 自校验最大绝对差 `0.0`。
- 修正后 Example 5 aggregate L2 下降到中间口径：

```text
Te L2 = 0.1957274767
Ti L2 = 0.2065726908
Tr L2 = 0.1632200766
```

重要：这是“修正后中间口径”，不是 strict paper-grade `80x80` reference solver 结果。

### 2. reference solver checkpoint/resume smoke

- 完成态 checkpoint/resume/validate 链路已通过。
- 中断态 checkpoint/resume smoke 已严格通过：

```text
interrupt: step=5, t=0.003916
resume:    step=201, t=1.0
step_advanced=True
t_advanced=True
validate: finite, top_Tr_max_abs_error=0.0
```

说明 checkpoint/resume 机制本身可用。

### 3. 启动器与 watcher

已新增/修改：

- `scripts/start_ref_solver_segment.py`
- `scripts/start_ref_solver_segment.ps1`
- `scripts/watch_ref_solver_run.ps1`

功能概况：

- 分段启动 reference solver。
- 第 N 段从 `segment_(N-1).ckpt.npz` resume，写 `segment_N.ckpt.npz`。
- 支持参数：

```text
--run-dir / -RunDir
--segment / -Segment
--walltime-seconds / -WalltimeSeconds
--case / -Case
--nx / -Nx
--ny / -Ny
--dt-init / -DtInit
--dt-min / -DtMin
--dt-max / -DtMax
--newton-max / -NewtonMax
--gmres-maxiter / -GmresMaxiter
--checkpoint-interval-steps / -CheckpointIntervalSteps
--log-every-step / -LogEveryStep
--log-rejected-steps / -LogRejectedSteps
--debug-on-failure / -DebugOnFailure
--dry-run / -DryRun
```

Codex 工具环境后台进程不可靠；用户本机 PowerShell 终端可以启动后台长跑。当前不建议再启动长跑，除非先完成 solver 方法改造。

## `generate_reference.py` 当前诊断改造

当前 `reference_solver/generate_reference.py` 已被修改，增加：

- `--log-every-step`
- `--log-rejected-steps`
- `--debug-on-failure`
- GMRES callback residual 记录：
  - `gmres_iterations`
  - `gmres_last`
  - `gmres_summary`
- rejected step diagnostics：
  - `attempted_dt`
  - `next_dt`
  - `reason`
  - `gmres_info`
  - `gmres_summary`
  - `alpha`
  - `trial_norm`
- failure debug checkpoint：
  - `segment_1.ckpt.failed.npz`
  - 保存 `diagnostics_json`

这些改造用于诊断，不是最终 solver 方法修复。

## strict 80x80 Aei70 诊断结论

关键输出目录：

```text
reference_solver_outputs/aei70_krar_80_strict_20260525
reference_solver_outputs/aei70_krar_80_diag_newton16_gmres300_20260525
reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525
```

最新、最关键失败目录：

```text
reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525
```

最新 failed checkpoint：

```text
reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz
```

失败状态：

```text
step=9
t=0.0077455892
dt=7.8732e-07
dt_min=1e-6
failure: Reference solve failed: dt<1e-06 at t=0.007746; last residual=1.000e-03
```

stdout 关键信号：

```text
rejected steps reason = line_search_failed
gmres_info = 300
gmres_iterations = 12000
gmres_last ≈ 2.535e-07
accepted residual ≈ 1e-3 boundary
```

解释：

- 单纯增大 `newton_max` 和 `gmres_maxiter` 没有解决问题。
- GMRES callback residual 已经很低，但 line search 仍失败。
- 失败表现为非线性步长 / line-search / 容差边界问题，而不是单纯后台、checkpoint、文件路径或 Example 2/5 污染问题。

## 当前不建议做的事

不要执行：

```powershell
.\scripts\start_ref_solver_segment.ps1 `
  -RunDir .\reference_solver_outputs\aei70_krar_80_strict_20260525 `
  -Segment 2 `
  -WalltimeSeconds 3600
```

也不要重启这些 run：

```text
aei70_krar_80_strict_20260525
aei70_krar_80_diag_newton16_gmres300_20260525
aei70_krar_80_gmrescb_diag_20260525
```

原因：没有可用正式完成 checkpoint，且同一早期困难点已重复失败。

## 下一步建议

下一步应是 solver 方法改造，而不是继续堆参数或重跑。

建议优先设计：

1. 记录 line search 每个 alpha 的完整 `trial_norm` 序列。
2. 记录每次 Newton 迭代的 `norm_R` 序列。
3. 记录 `dU` 范数、最大绝对值、温度 floor 触发情况。
4. 检查 JFNK finite-difference epsilon 尺度。
5. 改进 line search / damping strategy。
6. 考虑 sparse/block Jacobian 或物理块预条件器。
7. 对比 32x32 成功路径与 80x80 失败路径的 residual 和 dt 演化。

## 可读参考 summary

优先读：

```text
process-summaries/2026-05-25-aei70-80-strict-work-overall-summary.md
process-summaries/aei70-80-diag-watch-latest.md
process-summaries/2026-05-25-aei70-80-gmres-diagnostics-and-watch-fix-summary.md
process-summaries/2026-05-25-aei70-80-gmrescb-diagnostic-failed-summary.md
process-summaries/2026-05-25-reference-launcher-debug-summary.md
process-summaries/2026-05-25-strict-80x80-aei70-handoff.md
```

## 新窗口工作建议

如果新窗口继续工作：

1. 先运行：

```powershell
git status --short --branch
python .\repro_status.py --run-name overnight_current
```

2. 不要启动新 long run。
3. 先读取 failed checkpoint 的 `diagnostics_json`。
4. 设计 solver 方法改造方案。
5. 若修改代码，先说明原因、影响范围和风险。
6. 每次完成后用 `process-summary` 汇报并保存到 `process-summaries/`。

