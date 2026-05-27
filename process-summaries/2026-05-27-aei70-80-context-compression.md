# Aei70 80x80 strict reference solver 上下文压缩交接

## 当前结论

- 暂时停止 strict `80x80` `aei70_krar` reference solver 求解。
- 不要启动新 strict 80x80 run。
- 不要启动 Segment 2。
- 不要重启任何失败 run。
- 当前 SciPy matrix-free JFNK 路线尚不能生成 paper-grade strict 80x80 reference 数据。

核心失败点稳定复现：

```text
t ≈ 0.007746
dt < 1e-6
last residual ≈ 1.000e-03
```

最后一轮 GMRES callback 诊断显示：

```text
gmres_info=300
gmres_iterations=12000
gmres_last≈2.535e-07
reason=line_search_failed
```

因此，问题不应再简单归因于 GMRES 残差完全不下降；更可能与 JFNK 更新方向、finite-difference Jacobian-vector 尺度、line search、非线性残差容差边界有关。

## 保护约束

- `runs/overnight_current` 是冻结目录，默认只读。
- 不得移动、删除、覆盖或继续写入 `runs/overnight_current`。
- 不得重跑 Example 2。
- 不得重跑 Example 5。
- Example 5 必须区分 `70`、`400`、`700` 阶段。
- 不得提交 `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt。
- 当前 strict 80x80 失败证据目录也要保留，不要删除或覆盖。

只读状态最近已确认：

```text
runs/overnight_current Protected: True
Example 2: completed, step 6001
Example 5: stage 700, completed, step 6001
```

## 当前 Git / 文件状态要点

已修改或新增的关键代码：

- `reference_solver/generate_reference.py`
  - 增加每步日志、rejected step 日志。
  - 增加 `--debug-on-failure`，失败前写 `.failed.npz`。
  - 增加 GMRES callback residual 诊断。
  - accepted history 和 rejected diagnostics 中保存 `gmres_summary`。
- `scripts/start_ref_solver_segment.py`
  - 新增安全 Python launcher。
  - 拒绝写入 `runs/overnight_current`。
  - 拒绝覆盖已有 output/current checkpoint。
  - 支持分段、resume、walltime、诊断参数。
- `scripts/start_ref_solver_segment.ps1`
  - 作为 Python launcher 的 PowerShell 薄包装。
  - 支持 `-DtInit`、`-DtMin`、`-DtMax`、`-NewtonMax`、`-GmresMaxiter`、`-CheckpointIntervalSteps`、`-LogEveryStep`、`-LogRejectedSteps`、`-DebugOnFailure`、`-DryRun`。
- `scripts/watch_ref_solver_run.ps1`
  - 本地只读自动巡检脚本。
  - 只读检查 PID、stdout/stderr、checkpoint、failed checkpoint、final output、`overnight_current`、git status。
  - 每轮写 `process-summaries/aei70-80-diag-watch-latest.md`。

已验证：

- Python 编译通过。
- PowerShell AST 语法解析通过。
- watcher 不包含 `Start-Process`、`Stop-Process`、`generate_reference.py`、`start_ref_solver_segment`、`Remove-Item`。
- GMRES callback 小型 2x2 自检通过。

## 关键输出 / 证据目录

保留这些目录，不要删除或覆盖：

```text
reference_solver_outputs/aei70_krar_80_strict_20260525
reference_solver_outputs/aei70_krar_80_diag_newton16_gmres300_20260525
reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525
```

最近最重要的 failed checkpoint：

```text
reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz
```

读取结果：

```text
step=9
t=0.0077455892
dt=7.873199999999999e-07
history_len=9
diagnostics_len=15
```

最后 accepted steps 的 residual：

```text
step=5 residual=0.000995421269697743
step=6 residual=0.000998558386208171
step=7 residual=0.0009994995211612993
step=8 residual=0.0009997818616472379
step=9 residual=0.000999951265938801
```

所有 rejected diagnostics 的共同模式：

```text
reason=line_search_failed
gmres_info=300
gmres_iterations=12000
gmres_last≈2.535e-07
alpha=0.00390625
trial_norm just above 1e-3
```

## 已保存的重要汇报

建议优先读：

```text
process-summaries/2026-05-25-aei70-80-strict-work-overall-summary.md
process-summaries/2026-05-25-aei70-80-gmrescb-diagnostic-failed-summary.md
process-summaries/2026-05-25-aei70-80-gmres-diagnostics-and-watch-fix-summary.md
process-summaries/2026-05-25-aei70-80-watch-script-summary.md
process-summaries/2026-05-25-strict-80x80-aei70-handoff.md
```

本压缩文档：

```text
process-summaries/2026-05-27-aei70-80-context-compression.md
```

## 后续建议

短期不要继续堆参数：

- 不建议继续单纯增大 `gmres_maxiter`。
- 不建议直接降低 `dt_min` 作为正式方案。
- 不建议仅放宽 `newton_tol` 后把结果当作 paper-grade strict reference。

如后续继续 strict 80x80，应先做 solver 方法改造：

1. 记录 line search 每个 `alpha` 的完整 `trial_norm` 序列。
2. 记录每次 Newton 迭代的 `norm_R` 序列。
3. 记录 `dU` 范数、最大绝对值、是否产生负温度或触发 `temp_floor`。
4. 检查 JFNK finite-difference epsilon 尺度。
5. 尝试更稳健的 line search / damping。
6. 考虑 sparse/block Jacobian 或物理块预条件器。

如果只是验证 pipeline，可使用低分辨率或 `80x80_from20` 数据，但必须明确标记为 pipeline validation，不得当作 strict paper-grade reference。

## 安全恢复命令

只读检查冻结目录：

```powershell
python .\repro_status.py --run-name overnight_current
```

查看 git 状态：

```powershell
git status --short --branch
```

读取最近 failed checkpoint 摘要：

```powershell
python -c "import numpy as np, json; p='reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz'; d=np.load(p, allow_pickle=True); h=json.loads(str(d['history_json'][0])); diag=json.loads(str(d['diagnostics_json'][0])); print({'step': int(d['step'][0]), 't': float(d['t'][0]), 'dt': float(d['dt'][0]), 'history_len': len(h), 'diagnostics_len': len(diag)}); print('last_history=', h[-5:]); print('last_diag=', diag[-3:])"
```

## 不要执行

```powershell
# 不要执行
.\scripts\start_ref_solver_segment.ps1 -RunDir .\reference_solver_outputs\aei70_krar_80_gmrescb_diag_20260525 -Segment 2

# 不要执行
.\scripts\start_ref_solver_segment.ps1 -RunDir .\reference_solver_outputs\aei70_krar_80_strict_20260525 -Segment 1
```

除非用户明确恢复 strict 80x80 研究线，并指定新的 run dir 与新方案，否则不要启动新的 strict 80x80 solve。
