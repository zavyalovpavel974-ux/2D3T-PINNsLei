**本轮运行状态**
- 状态：正常完成
- 命令：
  - `rg -n "32|20x20|80x80|interpol|reference|grid|sol1|from20" .`
  - `Get-ChildItem -Recurse -File | Where-Object { $_.Name -match '32|20|80|reference|interp|sol1' }`
  - `Get-Content reference_solver\generate_reference.py`
  - `Get-Content 2D3T_wei_aei700_wer_krartr_time.py`
  - `python - ...` 只读比较 `reference_exports\aei70_krar_20`、`reference_exports\aei70_krar_32`、`reference_exports\aei70_krar_80_from20`
- walltime 上限：不适用，本轮只做只读审查与数值对比。
- 运行时长：需要确认。
- 退出原因：只读审查命令正常完成，未启动训练或 reference solver。

**本次进程概述**
本轮审查 strict `32x32` 网格求解与 `20x20` 插值求解之间的差异，重点判断当前用 `20x20 -> 80x80` 插值文件作为 PINN 评估参考是否存在缺陷或不合理之处。审查未写入 `runs/overnight_current`，未重跑 Example 2 或 Example 5。

**取得的成果**
- 已确认存在 strict `20x20`、strict `32x32`、`80x80_from20` 三组 `aei70_krar` reference 数据：
  - `reference_exports\aei70_krar_20\reference_snapshots.npz`
  - `reference_exports\aei70_krar_32\reference_snapshots.npz`
  - `reference_exports\aei70_krar_80_from20\reference_snapshots.npz`
- 已确认 `reference_exports\aei70_krar_80_from20` 是 strict `20x20` 的直接插值产物：逐时刻逐变量重算 `20 -> 80` 插值后，与 `80_from20` 数组差异为 0。
- 已确认根目录 `sol1_wei_aei70_wer_krar_*.txt` 与 `reference_exports\aei70_krar_80_from20` 下同名 txt 文件 SHA256 完全一致，因此当前根目录 aei70 参考文件就是 `80x80_from20`。
- 已比较 `20x20` 插值到 `32x32` 与 strict `32x32` 的差异。最大相对 L2 量级约为 `0.0036`，最大绝对差异随变量和时刻变化，最大约为 `0.0060`。
- 已确认代码坐标口径不一致：
  - `reference_solver\generate_reference.py` 中 solver/resample 使用 `np.linspace(0.0, 1.0, n)`，即端点网格。
  - `2D3T_wei_aei700_wer_krartr_time.py` 和 `2D3T_wei_aei70_wer_krar_inverse.py` 读取 author txt 后用 `(i+1/2)/N`、`(j+1/2)/N` 构造坐标，即单元中心网格。
  - 训练脚本中已有注释提示“这个不是中心点，第二个是似乎 x 和 y 搞反了”。

**关键数值对比**
- `20x20` 插值到 `32x32` 对 strict `32x32`，相对 L2：
  - `t=0.3`：Te `0.00289`，Ti `0.00212`，Tr `0.00375`
  - `t=0.5`：Te `0.00209`，Ti `0.00206`，Tr `0.00254`
  - `t=0.7`：Te `0.00273`，Ti `0.00295`，Tr `0.00277`
  - `t=1.0`：Te `0.00345`，Ti `0.00359`，Tr `0.00087`
- 对应最大绝对差异：
  - Te 最大约 `0.00415`
  - Ti 最大约 `0.00157`
  - Tr 最大约 `0.00601`
- 这些差异不算灾难性，但足以说明 `20x20` 插值参考不是严格高分辨率参考，不能用于 paper-grade 误差声称。

**发现的问题**
- 高优先级：根目录 `sol1_wei_aei70_wer_krar_*.txt` 实际是 `80x80_from20` 插值文件，不是 strict `80x80` 数值解。用它评估 PINN 会把“相对低保真插值参考”伪装成 `80x80` 参考。
- 高优先级：reference solver 的 `.npz` 坐标是端点网格 `0..1`，author txt 读入后却按单元中心 `(i+0.5)/N` 解释。尤其顶边 `Tr` 被 solver 当作 `y=1` Dirichlet 边界，但 PINN 评估时同一行被放在 `y=1-0.5/N`，会造成边界附近系统性错位。
- 中优先级：20x20 插值到 32x32 与 strict 32x32 虽差异不大，但仍有约 `10^-3` 量级相对差；若 PINN 目标误差也在这个量级附近，参考误差会污染结论。
- 中优先级：插值文件制造了 80x80 点数，但没有新增真实 PDE 求解信息。用它计算 `full_grid_metrics` 会显得空间采样更密，实质上仍受 20x20 解质量和线性插值限制。
- 中优先级：`resample_npz` 使用逐轴 `np.interp` 的双线性插值，适合作为 pipeline smoke test；但在存在强边界层、非线性耦合和高梯度区域时，不应视为严格 reference。

**续跑状态与检查点**
- 本轮没有启动训练或 reference solver，因此没有新的续跑 checkpoint。
- 当前审查对象属于 reference 数据质量，不是 Example 5 的 `70/400/700` PINN 阶段。
- 下一次安全操作：
  ```powershell
  # 不建议基于 80x80_from20 声称 paper-grade 复现。
  # 若要继续，应优先用 strict 32x32 作为中间保真参考，或修正坐标口径后重新导出参考文件。
  ```
- 不应执行的危险操作：
  - 不要删除或覆盖 `runs/overnight_current`。
  - 不要把 `80x80_from20` 当作 strict `80x80` reference。
  - 不要在未修正坐标口径前把当前 author txt 的误差解释为严格物理坐标上的误差。

**遇到的阻碍**
- strict `80x80` reference 仍未完成，不能直接比较 strict `32x32`、strict `80x80` 和 `80x80_from20`。
- 当前 32x32 审查只覆盖 `aei70_krar`；`aei700_krartr` 的 strict 32x32 未确认完整完成。
- 现有 author txt 格式不保存真实坐标，只保存索引，因此 reader 如何解释坐标会直接影响指标口径。

**未完成的部分**
- 尚未把 strict `32x32` 导出成与作者 reader 坐标一致的中心点格式。
- 尚未重新计算 PINN 对 strict `32x32` 的 metrics。
- 尚未修正或分离 `pipeline validation reference` 与 `paper-grade reference` 的报告口径。

**在总体进程中的作用**
- 本轮确认了 `32x32` 解可以作为比 `20x20` 插值更可信的中间保真审查对象。
- 本轮也确认了 `20x20 -> 80x80` 插值只能用于流程验证，不适合支撑最终论文级误差结论。

**总体进程中仍未完成**
- strict `80x80` reference solver 仍需方法改造后再尝试。
- Example 2 / Example 5 若要做严格对照，应使用真实数值解，至少先用 strict `32x32` 中间口径明确标注。
- 需要修正 reference export/read 坐标口径，避免端点/中心点混用。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物，除非用户明确要求。
- Example 5 已完整跑完：先不要修改、覆盖、删除或重跑它的产物；判断时必须区分 `70`、`400`、`700` 阶段。
- `runs/overnight_current` 中已有 checkpoint 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- 现有 `reference_exports` 和 `reference_solver_outputs` 是审查证据，删除或覆盖前需要明确确认。

**下一步建议**
1. 先把当前根目录 `sol1_*.txt` 在报告中明确标记为 `80x80_from20`，不要再称为 strict `80x80`。
2. 修正 reference solver 导出/读入坐标口径：要么 solver 使用中心点网格，要么 author txt reader 也按端点坐标评估；二者必须一致。
3. 用 strict `32x32` 生成一套独立 metrics，标注为 `strict32` 中间参考，而不是论文最终参考。
4. 若 strict32 与 20interp 的差异在关键指标上影响结论，再优先推进 strict `80x80` solver 方法改造。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-28-32grid-vs-20interp-review.md`

**需要确认**
- 是否希望我下一步直接修改代码，将 reference mode 显式区分为 `strict32`、`80x80_from20`、`strict80`，并增加坐标口径检查。
