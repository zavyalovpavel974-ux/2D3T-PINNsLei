# Ex6 插值参考解复现缺陷清单

日期：2026-05-27  
范围：`C:\Users\12412\Documents\Lei_code` 中当前 Example 6 / inverse 路线。  
目标：在 `interpolated_80x80_from20` 参考解基础上，整理当前 Ex6 复现中所有会影响结论、指标或可复查性的缺陷。

## 已确认事实

- 当前 inverse 运行由 `2D3T_wei_aei70_wer_krar_inverse.py` 与 `sub_2D3T_wei_aei70_wer_krar_inverse.py` 执行。
- 物理参数对应论文 Example 2：`Aei=70`, `Kr=Ar`。
- 实验目标对应论文 Example 6：将 `rho` 注册为可训练参数，并用五个时刻监督数据反演密度。
- 当前冻结结果：
  - `rho_true = 1.1`
  - `rho_pred = 1.102853289967324`
  - `rho_rel_error = 0.259389997%`
- 当前 metrics 文件：
  - `runs/overnight_current/reports/example2_metrics.json`
  - `case = example2_inverse`
  - `reference = interpolated_80x80_from20`
- 当前场误差：
  - Te L2 `2.240850784e-02`
  - Ti L2 `2.383876654e-02`
  - Tr L2 `3.739215547e-02`
  - Tr Linf `2.917777245e-01`

## 缺陷 1：实验命名混淆 Ex2 与 Ex6

当前 runner、status 和 metrics 使用 `example2` / `example2_inverse` 命名。

问题：

- 从参数设置看，它确实基于 Example 2。
- 从论文实验目标看，它对应 Example 6。
- 报告中写“Example 2 已完成”容易误导为已经完成论文 Example 2 正问题。

建议：

- 改为 `example6_inverse` 或 `example6_inverse_on_example2_params`。
- 报告措辞统一为：
  ```text
  Example 6 inverse completed on Example 2 parameter setting.
  ```

## 缺陷 2：当前 Ex6 报告混用了 Ex2 Table 4 场误差口径

当前报告把 inverse 结果同时和论文 Table 12 的 `rho`、Table 4 的场误差对比。

问题：

- Table 12 是 Ex6 的反演密度表。
- Table 4 是 Ex2 正问题场误差表。
- Ex6 论文主要展示密度反演和 Fig. 11，不是以 Table 4 作为 Ex6 主表格。

建议：

- Ex6 主指标应以 `rho` 为第一指标。
- 场误差可作为辅助质量检查，标注为“基于 Ex2 参数参考解的 held-out field error”，不要直接写成 Ex6 完整论文表格复现。

## 缺陷 3：当前只跑了 `rho` 初始值 1.0

代码中：

```python
self.rou = torch.nn.Parameter(torch.tensor([1.0], requires_grad=True))
# self.rou = torch.nn.Parameter(torch.tensor([0.5], requires_grad=True))
```

问题：

- 论文 Table 12 报告了两个初始值：`0.5` 和 `1.0`。
- 当前冻结结果只覆盖 `rho_init=1.0`。

建议：

- 如果目标是 Ex6 较完整复现，应至少用新 run-name 分别跑：
  - `rho_init=0.5`
  - `rho_init=1.0`
- metrics 中显式保存 `rho_init`。

## 缺陷 4：监督点随机索引没有保存

代码对每个时刻使用：

```python
idx = np.random.permutation(80*80)[:100]
```

问题：

- 每个时刻随机取 100 个监督点，但具体 indices 没有写入 metrics 或 checkpoint 报告。
- 后续难以确认某次结果到底使用了哪些监督点。
- 虽然主脚本设置了 seed，但 resume、代码修改或运行环境变化后仍可能造成复查困难。

建议：

- 保存五个时刻的监督点 indices：
  - `supervision_indices_1e-5`
  - `supervision_indices_0p3`
  - `supervision_indices_0p5`
  - `supervision_indices_0p7`
  - `supervision_indices_1`
- 同时保存 seed。

## 缺陷 5：评估集包含监督点，缺少 held-out 指标

当前 metrics 用完整 `80x80` 网格计算场误差，而训练监督点来自同一批参考文件和同一网格。

问题：

- 全场误差包含训练监督点。
- 不能区分“监督点拟合得好”与“未监督区域泛化得好”。

建议：

- 增加三类指标：
  1. supervised point error；
  2. held-out grid error；
  3. full-grid error。
- Ex6 报告优先展示 `rho` 与 held-out field error。

## 缺陷 6：参考数据是插值 `80x80_from20`，不是 strict `80x80`

当前 metrics 已标记：

```json
"reference": "interpolated_80x80_from20"
```

问题：

- 该数据适合 pipeline validation。
- 它不是论文级 strict `80x80` 传统数值解。
- 用它得到的 Ex6 好结果只能称为“插值参考解下的 Ex6 复现结果”。

建议：

- 当前目标既然明确是插值参考解基础，应在报告标题和 metrics 中始终写清楚。
- 同时保存输入 `sol1_*.txt` 的 SHA256，证明本次用的是哪一版插值参考数据。

## 缺陷 7：`80*80` 被硬编码

inverse 子模块多处写死：

```python
idx = np.random.permutation(80*80)[:100]
```

问题：

- 对当前 root-level `80x80_from20` 文件可用。
- 如果切换到 `20x20`、`32x32` 或 future strict `80x80` 的不同布局，容易出错。

建议：

- 用解析出的网格尺寸替代硬编码：
  ```python
  n_points = (Imax - Imin + 1) * (Jmax - Jmin + 1)
  idx = np.random.permutation(n_points)[:100]
  ```

## 缺陷 8：可能存在坐标/网格解释风险

代码中有作者/本地注释：

```python
# TODO 一个问题是这个不是中心点，第二个是似乎 x 和 y 搞反了
```

问题：

- 当前参考文件读入时使用 `(i+1/2)/N` 和 `(j+1/2)/N` 生成坐标。
- 如果文件中 i/j 与 x/y 的约定不同，监督点位置和评估位置会发生系统性错位。
- 当前结果能跑通，但该风险没有被单独验证。

建议：

- 增加只读校验：检查参考文件坐标构造是否与 `X_mesh/Y_mesh` 和 `imshow(... .T)` 使用一致。
- 至少对 t=1 的边界 `Tr(y=1)=3e-4+2t` 做空间位置校验。

## 缺陷 9：`Ar` 使用 true rho 预先计算，可能造成反问题设定争议

主脚本中：

```python
rou = 1.1
Ar = 2.1e2/(rou*rou)
...
model = PhysicsInformedNN(..., rou, ce, ci, cr, beta, Ae, Ai, Ar, Aei, Aer)
```

子模块中又将 `self.rou` 设为 trainable parameter。

问题：

- 如果按照材料表 `Ar = 2.1e2 / rho^2` 且 `rho` 是未知参数，那么用 true `rho=1.1` 计算固定 `Ar` 会引入真实密度信息。
- 如果论文/作者意图是“只反演 PDE 中显式出现的 rho，其他系数视为已知常数”，则当前做法可接受。

状态：

- 需要确认论文和作者代码意图。

建议：

- 报告中明确当前采用“author-compatible fixed-Ar”口径。
- 不要在未说明的情况下把 `Ar` 改成随 trainable rho 变化；那会变成另一个反问题。

## 缺陷 10：`rho` 没有正性约束

当前：

```python
self.rou = torch.nn.Parameter(torch.tensor([1.0], requires_grad=True))
```

问题：

- `rho` 理论上应为正。
- 当前结果没有出问题，但优化过程中参数没有硬约束，其他 seed 或初始值可能产生非物理值。

建议：

- 若保持作者兼容，可暂不改。
- 若做稳健工程版，可使用 `rho = softplus(raw_rho)` 或 clamp，但报告中必须注明方法改变。

## 缺陷 11：metrics 缺少训练过程关键信息

当前 metrics 保存了最终 `rho` 和场误差，但缺少：

- `rho_init`
- seed；
- supervision indices；
- final loss；
- final PDE residual losses；
- final boundary losses；
- supervised losses；
- optimizer phase / L-BFGS function evaluations；
- checkpoint path；
- input file hashes。

问题：

- `rho` 结果虽好，但难以复盘“为什么好”。
- 后续无法判断不同 run 的差别来自训练随机性、监督点、参考文件还是优化过程。

建议：

- 扩展 metrics schema。
- 保存一份 `example6_inverse_diagnostics.json`。

## 缺陷 12：当前是单 seed / 单次运行

论文通常报告多次独立运行平均结果；当前冻结结果是一条固定 seed 的运行。

问题：

- 无法评估稳定性。
- `rho=1.10285` 很好，但不知道对监督点随机性和初始化是否稳定。

建议：

- 在插值参考解基础上做 3 到 5 个轻量复现实验。
- 每次使用新 run-name，不写入 `overnight_current`。
- 报告 `rho` 的 mean/std，以及 field error 的 mean/std。

## 缺陷 13：早期时刻相对 L2 指标误导性很强

当前 `1e-5` 时刻：

- Te L2 `2.541`
- Ti L2 `1.000`
- Tr L2 `12.905`

但对应绝对 L1 / Linf 很小：

- Te L1 `5.41e-04`
- Ti L1 `2.28e-04`
- Tr L1 `2.82e-03`

问题：

- 初始温度约 `3e-4`，分母很小，relative L2 容易巨大。
- 这会让 Ex6 场误差解读变得不直观。

建议：

- 对早期时刻同时报告 absolute metrics。
- Ex6 主报告不要用早期 relative L2 单独判断成败。

## 缺陷 14：GPU/环境硬编码

子模块中：

```python
DeviceDtype = {'device':'cuda', 'dtype':torch.float64}
```

问题：

- 当前机器有 GPU，所以已运行成功。
- 但代码不是环境自适应，换机器可能失败。

建议：

- 若后续整理成可复现实验包，应改为根据 `torch.cuda.is_available()` 选择 device。
- 当前冻结结果无需改动。

## 缺陷 15：当前报告没有把 Ex6 成功标准写清楚

目前阶段报告容易给人两个相反印象：

- `rho` 很好，所以 Ex6 成功；
- 场误差偏大，所以 Ex6 不成功。

问题：

- 缺少分层成功标准。

建议定义：

```text
Ex6 rho inversion success:
  rho relative error <= 1.6% paper Table 12 level

Ex6 interpolated-reference field consistency:
  held-out full-field errors reported separately, not used as sole success criterion

Strict paper-grade success:
  requires strict 80x80 reference data or author reference data
```

## 优先修复建议

如果目标是在插值参考解基础上得到较好的 Ex6 复现结果，建议优先级如下：

1. 修正命名和报告口径：把 `example2_inverse` 改为或别名为 `example6_inverse_on_example2_params`。
2. 增加 Ex6 专用 metrics：`rho_init`、seed、监督点 indices、input hashes、supervised/held-out/full-grid error。
3. 分别跑 `rho_init=0.5` 和 `rho_init=1.0`，使用新 run-name，不碰 `overnight_current`。
4. 保存并报告 held-out 指标，避免训练监督点混入评估导致结论不清。
5. 验证坐标映射和 `Te/Ti/Tr` 字段顺序。
6. 明确采用 fixed `Ar` 的 author-compatible 口径。
7. 做 3 到 5 个 seed 的稳定性统计。

## 当前可接受的阶段性结论

当前 Ex6 在插值参考解基础上的结论应写为：

```text
Ex6 inverse pipeline completed on interpolated 80x80_from20 reference data.
The recovered density is rho=1.102853..., with relative error about 0.259%,
which is better than the paper Table 12 reported rho relative errors.
However, field-error reporting and reproducibility metadata remain incomplete;
therefore this is a strong interpolated-reference inverse result, not a full strict paper-grade reproduction.
```

