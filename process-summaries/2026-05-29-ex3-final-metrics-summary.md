# Ex3 最终训练与误差评估总结

## 1. 实验状态

- 实验名称：ex3_transfer_clean_20260528
- 当前阶段：Aei=400
- Checkpoint 状态：phase=completed
- Adam 迭代：6001
- 最终状态：训练完成
- 评估时间：2026-05-29 11:48 CST

## 2. 坐标约定

最终评估采用 `swapped_xy` 坐标约定，与 Ex2 的处理方式保持一致。

该坐标约定下，误差相比 standard xy 明显降低：

- standard xy: Te L2 = 7.31e-2
- swapped xy: Te L2 = 1.83e-2

说明此前 Ex3 误差异常偏大的主要原因很可能来自坐标约定不一致。

## 3. 参考解设置

- 参考解：aei400_krar
- 原始分辨率：20×20
- 评估方式：插值到 80×80 后与模型预测结果比较

由于参考解本身需要插值，最终误差可能受到参考解分辨率和插值方式影响。

## 4. 聚合误差

| 字段 | L2 rel | L1 abs | Linf abs |
|---|---:|---:|---:|
| Te | 1.829e-2 | 5.360e-3 | 1.094e-2 |
| Ti | 1.823e-2 | 4.342e-3 | 8.597e-3 |
| Tr | 1.350e-2 | 1.201e-2 | 2.254e-2 |

## 5. 与论文 Table 6 对比

| 字段 | 论文 L2 | 本次 L2 | 倍数 |
|---|---:|---:|---:|
| Te | 8.73e-3 | 1.83e-2 | 2.10x |
| Ti | 1.10e-2 | 1.82e-2 | 1.65x |
| Tr | 3.35e-3 | 1.35e-2 | 4.03x |

## 6. 结论

Ex3 已完成训练与最终 metrics 计算。采用 swapped_xy 坐标约定后，误差显著改善，Te/Ti 与论文结果处于较接近范围，整体达到同一数量级。

Tr 误差仍高于论文 Table 6，可能与参考解分辨率、插值误差、边界附近误差或 Tr 场本身敏感性有关。后续若继续优化，应优先检查 Tr 的空间误差分布、边界误差贡献和参考解生成方式。

## 7. 相关文件

- Checkpoint: runs/ex3_transfer_clean_20260528/checkpoints/example3/latest.pt
- Metrics: runs/ex3_transfer_clean_20260528/reports/example3_metrics.json
- 参考解: reference_solver_outputs/aei400_krar_20/outputs/reference_snapshots_80x80_from20.npz
- Metrics 计算脚本: scripts/compute_ex3_final_metrics.py
- 坐标检查脚本: scripts/ex3_coordinate_sanity_check.py
