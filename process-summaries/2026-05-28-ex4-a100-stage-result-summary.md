**本轮运行状态**
- 状态：阶段性成果保存
- 来源：用户提供的 Hermes agent CLI Ex4 报告片段
- 训练状态：`completed`
- walltime / error / traceback：报告中显示无 `error/FAILED/walltime`
- Markdown 文档：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-28-ex4-a100-stage-result-summary.md`

**本次进程概述**
本记录保存云服务器 A100-PCIE-40GB 上 Example 4 训练的阶段性成果。当前事实表明 Ex4 训练已正常完成，checkpoint、日志、figures、environment 与 metrics stub 均已生成；但由于缺少 Ex4 对应参考解文件，尚未计算 L2/L1/Linf 精度指标。

**已确认事实**
- run-name：`ex4_transfer_ff_clean_a100_20260528`
- GPU：NVIDIA A100-PCIE-40GB
- 训练阶段：
  - Stage 1：`Aei=70`，耗时 `4466.87s`，约 `74.4 min`
  - Stage 2：`Aei=400`，耗时 `4175.61s`，约 `69.6 min`
  - 总计：`8642.48s`，约 `144 min / 2.4h`
- 最终状态：
  - `phase=completed`
  - `step=6001`
  - `final_stage=400`
  - checkpoint：`runs/ex4_transfer_ff_clean_a100_20260528/checkpoints/example4/latest.pt`
  - checkpoint 大小：约 `279MB`
  - `metrics_available=False`
  - metrics 原因：缺少 Ex4 对应参考解文件
- 已生成文件：
  - stdout：`runs/ex4_transfer_ff_clean_a100_20260528/logs/example4.stdout.log`
  - stderr：`runs/ex4_transfer_ff_clean_a100_20260528/logs/example4.stderr.log`
  - metrics stub：`runs/ex4_transfer_ff_clean_a100_20260528/reports/example4_metrics.json`
  - figures：`runs/ex4_transfer_ff_clean_a100_20260528/workdir/figures/Train_6000_30000_2406032237/`
  - environment：`runs/ex4_transfer_ff_clean_a100_20260528/reports/environment.json`

**训练设定说明**
- 本次 Ex4 按用户指定方案执行：在 Ex4 中也引入 transfer。
- 预期技术设定：
  - transfer stages：`70 -> 400`
  - `Kr = Ar * Tr`
  - 使用 Fourier feature embedding
  - 使用 logarithm initial loss 与 photon Dirichlet boundary loss
  - `lambda_brd=20`
  - `lambda_init=10`
  - double precision

**当前判断**
- Ex4 训练产物可以先视为有效阶段性成果。
- 当前不建议为 metrics 继续续跑 Ex4；metrics 缺失原因是缺少参考解，不是训练未完成。
- `step=6001` 不应解读为只跑完 Adam；在当前保存逻辑中，`completed` checkpoint 的 `step` 字段不等同于 L-BFGS 内部迭代数。若需要确认 L-BFGS 实际迭代，应读取 checkpoint 中 `lbfgs.state[*].n_iter` 与 `lbfgs.state[*].func_evals`。

**待补事项**
- 需要补充 Ex4 对应参考解文件：`Aei=400, Kr=Ar*Tr`，并覆盖论文要求的时刻 `t=1e-5, 0.3, 0.5, 0.7, 1`。
- 有参考解后，需要做坐标 sanity check：
  - `(x,y,t)`
  - `(y,x,t)`
  - Ex2 corrected 口径为 `coordinate_evaluation=swapped_xy`
- 之后再计算 L2/L1/Linf，并与原文 Ex4 表格对照。

**建议在云服务器执行的保存命令**
```bash
python ./repro_status.py --run-name ex4_transfer_ff_clean_a100_20260528
mkdir -p archives
tar -czf archives/ex4_transfer_ff_clean_a100_20260528_artifacts.tar.gz \
  runs/ex4_transfer_ff_clean_a100_20260528/checkpoints/example4/latest.pt \
  runs/ex4_transfer_ff_clean_a100_20260528/logs \
  runs/ex4_transfer_ff_clean_a100_20260528/reports \
  runs/ex4_transfer_ff_clean_a100_20260528/workdir/figures
sha256sum archives/ex4_transfer_ff_clean_a100_20260528_artifacts.tar.gz \
  > archives/ex4_transfer_ff_clean_a100_20260528_artifacts.tar.gz.sha256
```

**受保护产物**
- 云端 run：`runs/ex4_transfer_ff_clean_a100_20260528`
- checkpoint：`runs/ex4_transfer_ff_clean_a100_20260528/checkpoints/example4/latest.pt`
- logs、reports、figures 与 environment 文件均应保留。
- 本地冻结目录 `runs/overnight_current` 默认不得修改、删除或覆盖。
- 本地 Ex2 completed run `runs/ex2_forward_clean_20260528` 默认不得修改、删除或覆盖。

**下一步建议**
1. 先在云服务器打包并校验 Ex4 artifacts。
2. 趁 A100 仍可用，启动 Ex5 clean run。
3. 后续再补 Ex4/Ex5 参考解与 corrected metrics 对照。

**需要确认**
- Hermes 报告中“三项 L-BFGS 续跑防护均已到位”具体检查的是云端 run workdir 内脚本，还是项目根目录脚本。
- 云服务器上的 Ex4 artifacts 是否已经下载或同步到本地。
