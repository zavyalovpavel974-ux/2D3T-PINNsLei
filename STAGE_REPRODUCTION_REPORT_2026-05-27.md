# 2D 3T PINNs 阶段性复现报告

日期：2026-05-27  
工作目录：`C:\Users\12412\Documents\Lei_code`  
当前决策：暂停继续推进复现，先整理当前阶段成果。

## 1. 阶段结论

当前项目已经完成了 2D 3T PINNs 作者代码的本地工程化复现链路，并完成了基于插值参考数据的 Example 2 和 Example 5 验证版运行。

但当前结果不能称为论文级严格复现，原因是：

- Example 2 和 Example 5 使用的参考数据标记为 `interpolated_80x80_from20`，不是独立生成的严格 `80x80` 传统数值参考解。
- Example 5 虽然完成了 `Aei=70 -> 400 -> 700` 三阶段训练链路，但误差明显高于论文 Table 9。
- strict `80x80` reference solver 尚未成功，当前 blocker 是传统参考解生成方法本身，而不是 PINNs runner 是否能运行。

因此，本阶段成果应定位为：

```text
作者代码工程化 + 插值参考数据验证版闭环 + strict reference solver 诊断阶段
```

不应定位为：

```text
论文 Table 4 / Table 9 的严格数值复现完成
```

## 2. 已完成工作概览

### 2.1 作者代码与论文理解

已阅读并掌握论文：

- `Lei 等 - 2025 - 2D 3T PINNs for solving 2-D 3-T heat conduction equations based on physics-informed neural networks.pdf`
- 论文 DOI：`10.1016/j.cpc.2025.109572`

已掌握作者公开代码仓库：

- `programmer-lxj/2D3T-PINNs`

作者仓库主要包含：

- `2D3T_wei_aei70_wer_krar_inverse.py`
- `sub_2D3T_wei_aei70_wer_krar_inverse.py`
- `2D3T_wei_aei700_wer_krartr_time.py`
- `sub_2D3T_wei_aei700_wer_krartr_time.py`

对应关系：

- Example 2 / Example 6 inverse 路径：`Aei=70`, `Kr=Ar`, 反演 `rho`。
- Example 5 transfer 路径：`Aei=70 -> 400 -> 700`, `Kr=Ar*Tr`。

### 2.2 工程化 runner 与状态工具

当前项目已增加并使用过这些工程工具：

- `repro_runner.py`
- `repro_status.py`
- `repro_background.py`
- `summarize_repro.py`

这些工具提供：

- 隔离 run 目录；
- 复制作者脚本和 `sol1_*.txt` 输入；
- 校验 author-format 参考文件；
- 设置 `KMP_DUPLICATE_LIB_OK=TRUE`；
- checkpoint / resume；
- walltime 控制；
- metrics JSON 输出；
- final reproduction report；
- Example 5 阶段识别，区分 `70 / 400 / 700`；
- 对 `runs/overnight_current` 的写入保护。

## 3. 冻结基线：`runs/overnight_current`

`runs/overnight_current` 是当前阶段最重要的冻结实验目录，状态已确认：

```text
Exists: True
Protected: True
```

必须保持只读：

- 不得移动；
- 不得删除；
- 不得覆盖；
- 不得继续写入；
- 不得把新实验重跑到这个目录。

关键文件：

- `runs/overnight_current/checkpoints/example2/latest.pt`
- `runs/overnight_current/checkpoints/example5/latest.pt`
- `runs/overnight_current/reports/example2_metrics.json`
- `runs/overnight_current/reports/example5_metrics.json`
- `runs/overnight_current/reports/final_reproduction_report.md`
- `runs/overnight_current/logs`
- `runs/overnight_current/workdir/figures`

状态检查命令：

```powershell
python .\repro_status.py --run-name overnight_current
```

## 4. Example 2 阶段结果

### 4.1 运行状态

已确认：

```text
case: example2
stage: inverse
phase: completed
step: 6001
reference: interpolated_80x80_from20
```

checkpoint：

```text
runs/overnight_current/checkpoints/example2/latest.pt
```

metrics：

```text
runs/overnight_current/reports/example2_metrics.json
```

训练时间：

```text
8908.768689393997 s
```

### 4.2 密度反演结果

| 项目 | 数值 |
| --- | ---: |
| true `rho` | `1.1` |
| predicted `rho` | `1.102853289967324` |
| absolute error | `0.0028532899673239243` |
| relative error | `0.259389997%` |

解释：

- 从密度反演角度看，Example 2 的工程验证结果较好。
- 该结果甚至比论文 Table 12 中 `rho≈1.117` 的两行更接近真值 `1.1`。
- 但由于参考数据不是 strict `80x80`，不能直接作为论文复现结论。

### 4.3 Example 2 aggregate errors

| Variable | L2 | L1 | Linf |
| --- | ---: | ---: | ---: |
| Te | `2.240850784e-02` | `5.363038082e-03` | `5.214249036e-02` |
| Ti | `2.383876654e-02` | `2.562247375e-03` | `1.638109869e-02` |
| Tr | `3.739215547e-02` | `2.093566355e-02` | `2.917777245e-01` |

论文 Table 4 对照：

| Variable | Paper L2 | Paper L1 | Paper Linf |
| --- | ---: | ---: | ---: |
| Te | `1.446e-02` | `5.388e-03` | `1.684e-02` |
| Ti | `7.902e-03` | `1.153e-03` | `3.742e-03` |
| Tr | `1.588e-02` | `1.436e-02` | `4.834e-02` |

阶段判断：

- Example 2 已完成工程闭环。
- 多数指标与论文处于相近量级。
- `Tr Linf` 明显偏大，是当前 Example 2 的主要误差问题。

## 5. Example 5 阶段结果

### 5.1 运行状态

已确认：

```text
case: example5
stage: 700
phase: completed
step: 6001
reference: interpolated_80x80_from20
```

checkpoint：

```text
runs/overnight_current/checkpoints/example5/latest.pt
```

metrics：

```text
runs/overnight_current/reports/example5_metrics.json
```

inference time：

```text
0.04833650588989258 s
```

### 5.2 三阶段训练链路

Example 5 的工程链路已经跑通：

```text
Aei=70 -> Aei=400 -> Aei=700
```

冻结清单与上下文中记录的训练时间：

| Stage | Training time |
| --- | ---: |
| Aei=70 | `31099.7 s` |
| Aei=400 | `27970.4 s` |
| Aei=700 | `29110.0 s` |
| Total | `88180.1 s` |

注意：`example5_metrics.json` 中当前只记录 final stage `700` 的 `29110.045404195786 s`，完整三阶段时间来自日志/冻结清单。

### 5.3 Example 5 原始 aggregate errors

| Variable | L2 | L1 | Linf |
| --- | ---: | ---: | ---: |
| Te | `7.049614629e-01` | `3.624820241e-01` | `6.491585347e-01` |
| Ti | `7.081070316e-01` | `3.184907765e-01` | `5.765261545e-01` |
| Tr | `6.686891071e-01` | `1.050014109e+00` | `2.000008199e+00` |

论文 Table 9 对照：

| Variable | Paper L2 | Paper L1 | Paper Linf |
| --- | ---: | ---: | ---: |
| Te | `1.485e-02` | `8.224e-03` | `1.547e-02` |
| Ti | `1.738e-02` | `8.504e-03` | `1.552e-02` |
| Tr | `4.216e-03` | `7.507e-03` | `1.370e-02` |

阶段判断：

- Example 5 已完整跑完，但数值复现失败。
- 当前误差远高于论文 Table 9。
- 该结果应表述为“工程链路完成，但当前数据/参考条件下未复现论文误差”。

### 5.4 Example 5 per-time reference 修正

只读排查发现：

- 原 Example 5 后处理五个时间点都读取 `sol1_wei_aei700_wer_krartr_80_1.txt`。
- 该文件与 `sol1_wei_aei700_wer_krartr_1.txt` 哈希一致，本质上是 `t=1` 参考。
- 因此前期时间点曾错误地拿预测结果和 `t=1` 参考作比较。

正确映射应为：

| Time | Reference file |
| --- | --- |
| `1e-5` | `sol1_wei_aei700_wer_krartr_1e-5.txt` |
| `0.3` | `sol1_wei_aei700_wer_krartr_0p3.txt` |
| `0.5` | `sol1_wei_aei700_wer_krartr_0p5.txt` |
| `0.7` | `sol1_wei_aei700_wer_krartr_0p7.txt` |
| `1.0` | `sol1_wei_aei700_wer_krartr_1.txt` |

只读修正输出目录：

```text
reference_solver_outputs/example5_static_recalc/
```

修正后 aggregate L2：

| Variable | Corrected L2 |
| --- | ---: |
| Te | `0.1957274767` |
| Ti | `0.2065726908` |
| Tr | `0.1632200766` |

阶段判断：

- per-time reference 修正显著降低了 Example 5 误差。
- 但修正后仍远高于论文 Table 9。
- 这说明原始误差被后处理问题放大，但不是唯一原因。

## 6. Reference Solver 阶段结果

### 6.1 已生成参考数据

`reference_exports/` 当前包含：

- `aei70_krar_20`
- `aei700_krartr_20`
- `aei70_krar_32`
- `aei70_krar_80_from20`
- `aei700_krartr_80_from20`
- `lowres_from_previous_worker`

其中：

- strict `20x20`：`aei70_krar` 与 `aei700_krartr` 均已完成。
- strict `32x32`：`aei70_krar_32` 已完成、validate、export。
- `80x80_from20`：是从 `20x20` 插值得到，只能用于 pipeline validation。

### 6.2 `aei70_krar_32`

已完成：

```text
reference_exports/aei70_krar_32/reference_snapshots.npz
reference_exports/aei70_krar_32/validation.json
reference_exports/aei70_krar_32/sol1_wei_aei70_wer_krar_*.txt
```

记录结果：

```text
nx = 32
ny = 32
steps = 267
final t = 1.0
final dt = 5.197840918050867e-04
final residual = 7.342448501751627e-04
top_Tr_max_abs_error = 0.0
```

阶段判断：

- `aei70_krar` 可以在 `32x32` strict reference 路线上跑通。
- 这是 reference solver 能力的重要正例。

### 6.3 `aei700_krartr_32`

记录结果：

```text
timeout = 1800 s
last printed step = 525
t = 0.965092
dt = 1.82e-03
newton = 3
residual = 9.187e-04
```

阶段判断：

- `aei700_krartr_32` 在 30 分钟上限内未完成。
- 因当时 solver 只在完成全部目标后保存 `.npz`，所以没有完整 reference output。
- 这促使后续加入 checkpoint/resume 和分段启动工具。

### 6.4 strict `80x80 aei70_krar`

当前最关键失败目录：

```text
reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525
```

failed checkpoint：

```text
reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz
```

已确认失败状态：

```text
step = 9
t = 0.0077455892
dt = 7.8732e-07
history_len = 9
diagnostics_len = 15
```

最后 accepted residual 接近：

```text
~1.0e-03
```

rejected step 诊断：

```text
reason = line_search_failed
gmres_info = 300
gmres_iterations = 12000
gmres_last ~= 2.535e-07
```

阶段判断：

- strict `80x80` reference solver 当前失败不是简单的“后台没跑完”或“文件路径问题”。
- 也不应继续简单归因于 GMRES residual 不下降。
- 更可能与 Newton/JFNK 更新方向、line search、finite-difference Jacobian-vector 尺度、非线性残差容差边界有关。
- 继续复现前需要 solver 方法改造，而不是继续堆 `gmres_maxiter` 或重启 Segment 2。

## 7. Git 与工作区状态

当前 `git status --short --branch` 显示：

```text
## main...origin/main
 M reference_solver/generate_reference.py
 M scripts/start_ref_solver_segment.ps1
?? CONTEXT_COMPACT_2026-05-27.md
?? NET_F_LEARNING_NOTES.md
?? PAPER_EXPERIMENT_DISCUSSION_NOTES.md
?? TRAIN_LEARNING_NOTES.md
?? WINDOW_CONTEXT_EXPORT.md
?? process-summaries/...
?? scripts/start_ref_solver_segment.py
?? scripts/watch_ref_solver_run.ps1
```

已知 Git 问题：

- 之前多次 `git add` 或 `git commit` 曾因 `.git/index.lock` 权限问题失败。
- 当前未提交文件不应默认丢弃。
- 如果以后要提交，应人工筛选：
  - 可考虑提交：runner、status/background 工具、reference solver 诊断工具、报告、学习笔记、小型 `aei70_krar_32` 产物。
  - 不建议提交：`reference_solver_outputs` 下的大输出、checkpoint、logs、failed checkpoint。

## 8. 当前阶段判断

### 已确认事实

- Example 2 工程验证版已完成。
- Example 5 工程验证版已完成。
- `runs/overnight_current` 是冻结证据目录。
- Example 5 当前没有达到论文 Table 9 精度。
- strict `80x80` 参考解尚未生成。
- 当前 blocker 是 reference solver 的严格 `80x80` 传统数值解生成。

### 合理推断

- 如果没有 strict `80x80` 传统参考解，即使 PINNs runner 完整跑通，也无法严肃判断是否复现论文表格。
- Example 5 原始误差中有一部分来自后处理 per-time reference mismatch。
- 但 per-time 修正后误差仍偏大，说明还有参考数据、训练敏感性、optimizer state、硬件/随机性或实现差异等因素。

### 不能声称

- 不能声称已经复现论文 Table 9。
- 不能声称 strict `80x80` reference solver 已成功。
- 不能把 `80x80_from20` 插值数据当作 paper-grade reference。
- 不能把 `runs/overnight_current` 作为继续训练目录。

## 9. 受保护产物

默认不得修改、删除、覆盖或继续写入：

- `runs/overnight_current`
- `runs/overnight_current/checkpoints`
- `runs/overnight_current/logs`
- `runs/overnight_current/reports`
- `runs/overnight_current/workdir/figures`
- `reference_solver_outputs/*/checkpoints`
- `reference_solver_outputs/*/logs`
- `reference_solver_outputs/example5_static_recalc`
- root-level `sol1_*.txt`

特别说明：

- Example 2 已完成，默认不得重跑。
- Example 5 已完成，默认不得重跑。
- Example 5 必须区分 `70`、`400`、`700` 三阶段。

## 10. 若以后恢复工作的建议路线

虽然当前决定不继续推进复现，但如果以后恢复，建议按以下顺序：

1. 先保持 `runs/overnight_current` 冻结，只读检查状态：
   ```powershell
   python .\repro_status.py --run-name overnight_current
   ```
2. 不要启动新的 PINNs 训练，先处理 strict reference solver。
3. 如果继续 strict `80x80`，优先改造 solver 诊断：
   - 记录 line search 每个 alpha 的完整 trial norm；
   - 记录每次 Newton 迭代的 residual norm；
   - 记录 `dU` 范数、最大绝对值、温度 floor 触发情况；
   - 检查 JFNK finite-difference epsilon；
   - 考虑 sparse/block Jacobian 或物理块预条件器。
4. 如果只是写阶段论文/报告，不要新增实验，直接引用本报告和冻结 metrics。
5. 若要提交当前成果，先筛选 Git 范围，不要 `git add .`。

## 11. 推荐引用的证据文件

核心报告：

- `runs/overnight_current/reports/final_reproduction_report.md`
- `reproduction_report.md`
- `CONTEXT_COMPACT_2026-05-27.md`
- `WINDOW_CONTEXT_EXPORT.md`
- `process-summaries/2026-05-27-reproduction-recap-summary.md`

metrics：

- `runs/overnight_current/reports/example2_metrics.json`
- `runs/overnight_current/reports/example5_metrics.json`

冻结与状态：

- `OVERNIGHT_CURRENT_FREEZE_MANIFEST.md`
- `GIT_FREEZE_STATUS_REPORT.md`

reference solver 诊断：

- `process-summaries/2026-05-25-aei70-80-strict-work-overall-summary.md`
- `process-summaries/2026-05-25-aei70-80-gmrescb-diagnostic-failed-summary.md`
- `process-summaries/aei70-80-diag-watch-latest.md`
- `reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz`

学习笔记：

- `PAPER_EXPERIMENT_DISCUSSION_NOTES.md`
- `NET_F_LEARNING_NOTES.md`
- `TRAIN_LEARNING_NOTES.md`

## 12. 最终阶段性结论

本阶段复现工作的价值主要在于：

- 已经把作者公开代码从“缺少参考数据、难以直接跑”推进到“可由 runner 管理、可 checkpoint/resume、可输出 metrics/report”的工程状态。
- 已经形成了一个受保护的插值参考数据验证版基线。
- 已经明确了 Example 2、Example 5 当前结果与论文表格的差距。
- 已经定位了下一阶段真正的科学/数值 blocker：strict `80x80` 传统参考解生成。

当前建议归档本阶段，不再启动新实验。若后续恢复，应从 strict reference solver 方法改造或阶段性报告写作继续，而不是重跑冻结目录。
