# 2026-05-27 上下文压缩交接文档

## 当前目标

继续推进 `C:\Users\12412\Documents\Lei_code` 项目的 2D3T PINN 复现实验。当前核心目标不是重跑已完成实验，而是围绕严格参考解链路和 Example 5 误差异常做安全、可追踪的后续工作。

## 必须遵守的保护规则

- `runs/overnight_current` 是冻结实验目录，默认只读。
- 不得写入、移动、删除、覆盖 `runs/overnight_current` 中任何 checkpoint、logs、metrics、reports、figures 或结果文件。
- Example 2 已完成，默认不得重跑。
- Example 5 已完成，默认不得重跑。
- Example 5 必须区分 `70`、`400`、`700` 三个阶段，不得混在一起判断。
- 后续任何实验必须使用新的 `run-name` 或新的输出目录。
- 不得同时启动多个写入同一 `run-name` 的进程。
- 状态、日志或输出出现 `FAILED`、`NEED_CONFIRM`、`walltime`、`error`、`traceback`、`exception`、`nan`、`killed`、`completed`、`finished` 等关键词时，必须使用 `process-summary` skill 做结构化中文汇报。

## 冻结实验状态

只读状态命令：

```powershell
python repro_status.py --run-name overnight_current
```

已确认事实：

- `runs/overnight_current` exists: `True`
- `Protected`: `True`
- Example 2:
  - stage: `inverse`
  - phase: `completed`
  - step: `6001`
  - checkpoint: `runs/overnight_current/checkpoints/example2/latest.pt`
  - metrics: `runs/overnight_current/reports/example2_metrics.json`
  - rho: `1.102853289967324`
- Example 5:
  - stage: `700`
  - phase: `completed`
  - step: `6001`
  - checkpoint: `runs/overnight_current/checkpoints/example5/latest.pt`
  - metrics: `runs/overnight_current/reports/example5_metrics.json`
  - inference time: `0.04833650588989258s`
- `python repro_background.py status --run-name overnight_current` 显示没有 background launch metadata。

## Example 5 进展与问题

Example 5 已完成工程链路，但数值误差明显偏大，尚不能视作论文量级复现成功。

已确认成果：

- Example 5 跑通了 reproduction runner、checkpoint、stage resume、metrics 输出和日志记录链路。
- 日志显示三阶段续跑链路：
  - `resume transfer stage Aei=400`，跳过已完成的 `Aei=70`，从 checkpoint 恢复于 `phase=adam it=4400`。
  - `resume transfer stage Aei=700`，跳过已完成的 `Aei=70` 和 `Aei=400`，从 checkpoint 恢复于 `phase=adam it=2800`。
  - 最终 `Training time: 29110.0454`，`Total Training time: 29110.0454`，并写出 metrics。
- metrics 标记：
  - `case`: `example5_transfer`
  - `reference`: `interpolated_80x80_from20`

最终 aggregate 误差：

| Variable | L2 | L1 | Linf |
| --- | ---: | ---: | ---: |
| Te | 0.7049614628658555 | 0.36248202409586755 | 0.6491585346577088 |
| Ti | 0.7081070315755149 | 0.31849077651772184 | 0.5765261544988101 |
| Tr | 0.6686891071387449 | 1.0500141094014557 | 2.0000081988195895 |

重要嫌疑点：

- 当前参考解是 `interpolated_80x80_from20`，不是严格独立 80x80 参考解。
- 既有静态审查发现：Example 5 五个时刻误差计算都读取同一个 `sol1_wei_aei700_wer_krartr_80_1.txt`，只改变预测查询时间。这可能是误差异常的重要原因。
- 后续排查应继续只读检查五个时刻参考文件读取逻辑、`Te/Ti/Tr` 顺序、归一化/反归一化、边界条件和 metrics 聚合。

## Reference Solver 小规模 Smoke Test

已完成小规模 checkpoint/resume 验证，输出目录：

```text
reference_solver_outputs/ref_solver_smoke_test
```

结果：

- `12x12` 小网格。
- `part1.npz` 与 `part2.npz` 已生成。
- checkpoint 已生成：`reference_solver_outputs/ref_solver_smoke_test/checkpoints/latest.npz`
- `part2.log` 明确包含 `[reference] resumed ... step=10002 t=1.000000`。
- validate 结果显示各时刻数组 finite，顶部 `Tr` 边界误差为 `0.0`。
- 注意：最终保留的是完成态 checkpoint resume 验证，不是中断态 checkpoint 继续推进验证。

## Strict 80x80 Aei70 Reference Solver 当前结论

当前 strict `80x80` `aei70_krar` reference solver 求解线已暂停，不建议继续堆参数或启动 Segment 2。

关键输出目录：

```text
reference_solver_outputs/aei70_krar_80_strict_20260525
reference_solver_outputs/aei70_krar_80_diag_newton16_gmres300_20260525
reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525
```

最近诊断失败目录：

```text
reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525
```

失败事实：

- 状态：`FAILED`
- PID `15828` 已不存在。
- final output 未生成。
- checkpoint 存在，failed checkpoint 存在。
- failed checkpoint：`reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz`
- 失败位置：`step=9`, `t≈0.0077455892`, `dt≈1.57464e-06`，随后下一步降到 `dt=7.873e-07 < dt_min=1e-6`。
- stderr 报错：
  ```text
  RuntimeError: Reference solve failed: dt<1e-06 at t=0.007746; last residual=1.000e-03
  ```
- stdout 诊断显示 rejected steps 多为 `reason=line_search_failed`。
- `gmres_info=300`，`gmres_iterations=12000`，`gmres_last≈2.535e-07`。
- 推断：问题不应继续简单归因于 GMRES residual 不降；更像是 Newton/line-search/JFNK 步长接受边界或非线性模型问题。

当前结论：

- 当前 SciPy matrix-free JFNK + 对角预条件器路径尚不能生成 paper-grade strict 80x80 reference 数据。
- 单纯提高 `newton_max` / `gmres_maxiter` 已试过，未解决。
- 后续如果继续 strict 80x80，应先做 solver 方法改造，而不是继续重启长跑。

## 已做代码/脚本方向

当前工作区存在未提交改动和未跟踪文件。不要默认回滚；先确认是否保留。

`git status` 当前显示：

- modified:
  - `reference_solver/generate_reference.py`
  - `scripts/start_ref_solver_segment.ps1`
- untracked:
  - `scripts/start_ref_solver_segment.py`
  - `scripts/watch_ref_solver_run.ps1`
  - 多个 `process-summaries/2026-05-25-*`
  - `NET_F_LEARNING_NOTES.md`
  - `PAPER_EXPERIMENT_DISCUSSION_NOTES.md`
  - `TRAIN_LEARNING_NOTES.md`

根据既有报告，这些改动大致包括：

- `generate_reference.py` 增加诊断能力：
  - `--log-every-step`
  - `--log-rejected-steps`
  - `--debug-on-failure`
  - rejected diagnostics
  - failed checkpoint
  - GMRES callback residual 诊断
- `scripts/start_ref_solver_segment.py` / `.ps1` 用于安全分段启动 strict reference solver。
- `scripts/watch_ref_solver_run.ps1` 用于只读巡检 PID、logs、checkpoint、failed checkpoint、output、`overnight_current` 状态和 git status。

## Codex / 后台运行注意事项

既有结论：

- Codex 工具环境后台进程不可靠，正式 reference solver 长跑应由用户本机 PowerShell 终端启动。
- watcher 只读，不应启动或停止 solver。
- 启动后台任务后必须返回 PID、stdout/stderr、checkpoint、状态检查命令和停止命令。

## 建议下一步

优先级从高到低：

1. 暂停 strict 80x80 长跑，不自动重启失败 run，不启动 Segment 2。
2. 先整理/确认当前工作区改动：哪些脚本和诊断代码要保留，哪些输出目录不要提交。
3. 如果继续 strict 80x80，先设计 solver 方法改造：
   - 记录 line search 每个 alpha 的 trial norm。
   - 记录 Newton residual 序列。
   - 记录 `dU` 范数、最大绝对值、温度 floor 触发情况。
   - 检查 JFNK finite-difference epsilon 尺度。
   - 考虑阻尼 Newton、更稳健 line search、显式 sparse/block Jacobian 或物理块预条件器。
4. 如果目标是先推进 pipeline 验证，可继续用 `80x80_from20` 或低分辨率 reference，但必须明确标记为 pipeline validation，不作为 strict paper-grade 结果。
5. Example 5 后续重跑必须使用新 `run-name` 和新输出目录，不能写入 `runs/overnight_current`。

## 关键报告索引

- Example 5 进展：`process-summaries/2026-05-25-example5-progress-report.md`
- strict 80x80 总结：`process-summaries/2026-05-25-aei70-80-strict-work-overall-summary.md`
- strict 80x80 早期交接：`process-summaries/2026-05-25-strict-80x80-aei70-handoff.md`
- 最新 Aei70 80x80 诊断 watch：`process-summaries/aei70-80-diag-watch-latest.md`
- 当前压缩文档：`process-summaries/2026-05-27-context-compression.md`

## 需要确认

- 当前 `reference_solver/generate_reference.py` 和 `scripts/*` 改动是否作为诊断工具链保留。
- 是否将下一步切换到 solver 方法改造。
- 是否需要把可提交代码与不可提交大输出/checkpoint/logs 分离。
- 是否继续只做 Example 5 误差静态排查，还是先解决 strict reference solver。
