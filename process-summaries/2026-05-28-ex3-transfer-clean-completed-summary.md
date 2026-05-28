# Example 3 Transfer Clean Run 归档总结

**本轮运行状态**
- 状态：正常完成（`phase=completed`，`returncode=0`）
- 命令：
  ```
  python .\repro_runner.py --case example3 --run-name ex3_transfer_clean_20260528 --max-walltime-seconds 64800
  ```
- walltime 上限：64800 秒（18 小时）
- 实际运行时长：18123.61 秒（~5.03 小时），未触发 walltime
- 退出原因：Adam + L-BFGS 两阶段均正常完成，runner returncode=0

---

## 1. 训练完成状态确认

| 检查项 | 结果 |
|--------|------|
| `repro_status.py --run-name ex3_transfer_clean_20260528` | 已执行 |
| `phase` | `completed` ✅ |
| `final_stage` | `400` ✅ |
| `checkpoint latest.pt` | 存在 ✅（44 MB，2026-05-28 19:48 最后更新） |
| `metrics` | 存在 ✅（`example3_metrics.json`，473 bytes） |
| `returncode` | `0` ✅ |

---

## 2. 训练配置汇总

| 参数 | 值 | 来源 |
|------|-----|------|
| `transfer_stages` | `[70, 400]` | metrics / 命令行 |
| `final_stage` | `400` | metrics |
| `kr_mode` | `constant`（Kr=Ar） | metrics / 命令行 `--kr-mode constant` |
| `use_ff` | `False`（无 Fourier Feature） | 命令行 `--no-use-ff` |
| `use_log_loss` | `True`（logarithm initial loss） | 命令行 `--use-log-loss` |
| `lambda_brd` | `20.0`（photon Dirichlet boundary） | 命令行 `--lambda-brd 20` |
| `lambda_init` | `10.0` | 命令行 `--lambda-init 10` |
| `precision` | double（`torch.set_default_dtype(torch.float64)`） | checkpoint args |
| `skip_metrics` | `True` | 命令行 `--skip-metrics` |
| `metrics_available` | `False` | 见下方说明 |
| `checkpoint_interval` | `200` | 命令行 `--checkpoint-interval 200` |
| `seed` | default（未显式指定） | checkpoint args |
| `rho` | `1.1`（固定值，非反演参数） | checkpoint `rho: 1.100000` |

**`metrics_available=false` 原因**：
metrics JSON 中记录 `"reason": "skipped because matching reference text files are not available for this case"`。
这是因为 Example 3 使用 `Aei=400, Kr=Ar`，而 workdir 中的参考解文件为 `sol1_wei_aei700_wer_krartr_*`（Aei=700/Kr=Ar*Tr 变体）和 `sol1_wei_aei70_wer_krar_*`（Aei=70/Kr=Ar 变体），没有 `Aei=400, Kr=Ar` 的精确匹配参考解文件。因此 `--skip-metrics` 跳过了误差计算。

---

## 3. 训练时间汇总

| 阶段 | 训练时间 | 说明 |
|------|----------|------|
| Aei=70 | 9079.59 秒（~2.52 小时） | Adam 6001 步 + L-BFGS 30000 迭代 |
| Aei=400 | 9039.25 秒（~2.51 小时） | Adam 6001 步 + L-BFGS 30000 迭代 |
| **Total** | **18118.85 秒（~5.03 小时）** | 两阶段合计 |
| runner elapsed | 18123.61 秒 | 含 runner 开销 |

---

## 4. 日志健康检查

### stdout.log（378 行）
- 内容：命令回显 + GPU 检测 + checkpoint 保存记录 + 训练时间 + metrics stub 写入
- 关键行：
  - `Using GPU, NVIDIA GeForce RTX 4060 Laptop GPU`
  - `Aei: 0`（初始阶段标记）
  - `Training time: 9079.5925`（Aei=70 完成）
  - `Aei: 70`（转入 Aei=400 阶段）
  - `Training time: 9039.2546`（Aei=400 完成）
  - `Total Training time: 18118.8471`
  - `[repro] wrote metrics stub: ...example3_metrics.json`
- **无 error / traceback / exception / nan / killed / walltime / failed**

### stderr.log（21 行）
- 仅包含以下无害警告（共 11 条）：
  - **SyntaxWarning: invalid escape sequence**（8 条）：正则表达式中的 `\[` 和 `\#` 未使用 raw string，不影响训练结果
  - **DeprecationWarning: pyDOE**（1 条）：`pyDOE` 应改为 `pydoe`，不影响训练结果
  - **UserWarning: requires_grad tensor to scalar**（1 条）：`slope` 参数转换警告，不影响训练结果
- **无 error / traceback / exception / nan / killed / walltime / failed**
- 结论：所有警告均为代码风格/兼容性提示，不影响训练完成和结果正确性

---

## 5. Checkpoint 详细元数据

| 字段 | 值 |
|------|-----|
| `Aei` | `400.0` |
| `phase` | `completed` |
| `it` | `6001` |
| `adam_iter` | `6001` |
| `rho` | `1.100000` |
| `loss` | `None`（completed 时未记录最终 loss） |
| `elapsed_seconds` | `9039.05`（Aei=400 阶段） |
| `model` | `OrderedDict len=22`（完整模型权重） |
| `optimizer` | dict（Adam 状态） |
| `scheduler` | `gamma=0.999, last_epoch=6001, last_lr=2.47e-07` |
| `lbfgs` | dict（L-BFGS 状态） |
| `args` | dict len=25（训练配置快照） |

---

## 6. 生成产物

### Figures
| 文件 | 说明 |
|------|------|
| `workdir/figures/Train_6000_30000_2406032237/2x3Temperature.png` | 温度曲线 2x3 图 |
| `workdir/figures/Train_6000_30000_2406032237/_70_after.pt` | Aei=70 阶段结束后快照 |
| `workdir/figures/Train_6000_30000_2406032237/_400_after.pt` | Aei=400 阶段结束后快照 |

### Reports
| 文件 | 说明 |
|------|------|
| `reports/example3_metrics.json` | metrics stub（metrics_available=false） |
| `reports/example3_run_result.json` | runner 运行结果（returncode=0） |
| `reports/environment.json` | 环境信息（Python 3.12.7, PyTorch 2.11.0+cu126, RTX 4060） |

---

## 7. 文件归档建议

### 必须保留（受保护产物）
| 文件 | 路径 | 说明 |
|------|------|------|
| Checkpoint | `checkpoints/example3/latest.pt` | 完整训练状态，可用于续跑或评估 |
| stdout | `logs/example3.stdout.log` | 训练过程记录 |
| stderr | `logs/example3.stderr.log` | 警告记录 |
| Metrics | `reports/example3_metrics.json` | 配置和时间汇总 |
| Run result | `reports/example3_run_result.json` | runner 退出状态 |
| Environment | `reports/environment.json` | 运行环境快照 |
| Figures | `workdir/figures/` | 温度曲线和阶段快照 |

### 建议保留
| 文件 | 路径 | 说明 |
|------|------|------|
| 参考解文件 | `workdir/sol1_*.txt` | workdir 中的 11 个参考解文件 |
| 源码快照 | `workdir/2D3T_wei_aei700_wer_krartr_time.py` | 训练时使用的源码副本 |
| 子模块快照 | `workdir/sub_2D3T_wei_aei700_wer_krartr_time.py` | 训练时使用的子模块副本 |

### 本总结
| 文件 | 路径 |
|------|------|
| 归档总结 | `process-summaries/2026-05-28-ex3-transfer-clean-completed-summary.md` |

---

## 8. 总体进程中的作用

- Example 3 是论文中 `Aei=70→400` transfer learning + `Kr=Ar` 常数模式的正向问题。
- 本次 clean run 验证了该配置可以正常完成两阶段训练。
- 与 Example 2（`Aei=70, Kr=Ar`）相比，Ex3 增加了 transfer 到 `Aei=400` 的阶段。
- 与 Example 4（`Aei=70→400, Kr=Ar*Tr`）相比，Ex3 使用常数 Kr 而非线性 Tr 依赖。
- 训练产物可作为 Ex4 的对照基线。

---

## 9. 已确认事实 vs 需要确认

### 已确认事实
- ✅ Ex3 训练已正常完成，phase=completed，returncode=0
- ✅ Checkpoint 有效，包含完整模型权重和优化器状态
- ✅ 两阶段（Aei=70 和 Aei=400）均完成 Adam 6001 步 + L-BFGS 训练
- ✅ 无 error/traceback/nan/killed/walltime
- ✅ stderr 仅含无害警告，不影响结果
- ✅ `metrics_available=false` 是因为缺少 `Aei=400, Kr=Ar` 的匹配参考解文件

### 需要确认
- ❓ 是否存在 `Aei=400, Kr=Ar` 的精确参考解文件（`sol1_wei_aei400_wer_krar_*`），用于补算误差指标
- ❓ Ex3 训练结果的场误差水平是否达到论文 Table 对应标准
- ❓ 是否需要将 Ex3 结果纳入阶段性复现报告

---

## 10. 下一步建议

1. **补算 metrics**（如果参考解可用）：
   - 确认是否存在 `sol1_wei_aei400_wer_krar_*.txt` 参考解文件
   - 如果存在，将文件复制到 workdir，用 checkpoint 补算误差指标
   - 坐标评估需遵循 Ex2 已确认的 `swapped_xy` 口径

2. **转入 Example 4**：
   - Ex4 使用 `Aei=70→400, Kr=Ar*Tr, FF, log_loss`，是 Ex3 的变体
   - 当前 Ex4 checkpoint 在 `runs/ex4_transfer_clean_20260527`，处于 Aei=70 L-BFGS 中途
   - 可从该 checkpoint 续跑

3. **其他**：
   - 本实验不修改 `runs/overnight_current`
   - 本实验不覆盖已完成的 Ex2
   - 本总结仅作归档，不触发任何自动操作
