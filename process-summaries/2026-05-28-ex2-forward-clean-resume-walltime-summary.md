**本轮运行状态**
- 状态：达到 walltime 上限，未达到正常完成
- 续跑命令 1：`python .\repro_runner.py --case example2_forward --run-name ex2_forward_clean_20260528 --allow-existing-run --max-walltime-seconds 7200`
- 续跑命令 2：`python .\repro_runner.py --case example2_forward --run-name ex2_forward_clean_20260528 --allow-existing-run --max-walltime-seconds 7200`
- 续跑命令 3：`python .\repro_runner.py --case example2_forward --run-name ex2_forward_clean_20260528 --allow-existing-run --max-walltime-seconds 7200`
- walltime 上限：每次 7200 秒
- 运行时长：第一次快速失败约 4.7 秒；第二次约 7204.3 秒；第三次约 7204.3 秒
- 退出原因：第一次为 L-BFGS optimizer history 中 `prev_flat_grad=None` 导致 `TypeError`；第二、三次为 `ReproWalltimeReached`，checkpoint 已保存

**本次进程概述**
本轮按要求继续推进 `ex2_forward_clean_20260528` 的 Example 2 clean run，从当前 L-BFGS checkpoint 续跑，并在每次续跑后运行状态检查。第一次续跑暴露 L-BFGS 续跑保护问题，已修正代码；随后两次续跑均稳定运行到 walltime 并保存 checkpoint，但尚未达到正常结束，因此未补跑 metrics，也未进行最终论文 Example 2 指标对照。

**取得的成果**
- 已运行状态检查：`python .\repro_status.py --run-name ex2_forward_clean_20260528`
- 已修正 `sub_2D3T_wei_aei700_wer_krartr_time.py` 中两个 L-BFGS 续跑问题：
  - L-BFGS 续跑时不再先写 `lbfgs_start` 覆盖已有 checkpoint。
  - 检测到无效 L-BFGS optimizer history 时清空 L-BFGS 历史，保留模型权重继续跑。
- 修正后通过语法检查：`python -m py_compile sub_2D3T_wei_aei700_wer_krartr_time.py repro_runner.py`
- 当前 checkpoint 存在：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\checkpoints\example2_forward\latest.pt`
- 当前 checkpoint 内确认：
  - `Aei=70.0`
  - `phase=lbfgs`
  - `it=28554`
  - `adam_iter=6001`
  - `loss=0.003215144290658192`
  - `elapsed_seconds=7200.206770896912`
- 当前状态检查确认 logs、figures、checkpoint 均存在；metrics 仍缺失。

**续跑状态与检查点**
- 当前 checkpoint：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\checkpoints\example2_forward\latest.pt`
- 当前阶段：Example 2，`Aei=70`
- 当前步数或优化器阶段：L-BFGS，`it=28554`
- 已完成阶段：Adam 已完成；L-BFGS 已推进但尚未正常结束
- 下一次安全续跑命令：
  ```powershell
  python .\repro_runner.py --case example2_forward --run-name ex2_forward_clean_20260528 --allow-existing-run --max-walltime-seconds 7200
  ```
- 不应执行的危险操作：
  - 不要删除或覆盖 `runs/overnight_current` 中已有 checkpoint 和结果文件，除非用户明确要求。
  - 不要把 Example 5 的 70/400/700 阶段 checkpoint 误加载到 Example 2。
  - 不要在当前 run 上启动另一个同时写入同一 `run-name` 的进程。

**遇到的阻碍**
- 第一次续跑前，原 `it=25110` checkpoint 被 `lbfgs_start` 保存逻辑覆盖为 `it=6001`；这是本轮已修复的问题，但被覆盖的 checkpoint 文件本身未发现可用备份。
- 第一次续跑触发 `TypeError: sub(): argument 'other' (position 1) must be Tensor, not NoneType`，原因是 L-BFGS optimizer history 中 `prev_flat_grad=None`。
- 修复后两轮续跑均达到 walltime，不是正常完成。
- metrics 未补跑，因为用户设定的条件是“若达到正常结束，再补跑 metrics”，而当前尚未正常完成。

**未完成的部分**
- Example 2 clean run 尚未达到正常结束。
- metrics JSON 尚未生成。
- 与论文 Example 2 的最终指标对照尚未整理。

**在总体进程中的作用**
- 本轮修复了 L-BFGS 续跑路径，使后续从 L-BFGS checkpoint 继续训练更可靠。
- 当前 Ex2 clean run 已继续推进到 `lbfgs/28554`，loss 从上一轮确认的约 `0.0092075` 降到约 `0.0032151`。
- 本轮没有修改或写入冻结目录 `runs/overnight_current`。

**总体进程中仍未完成**
- 需要继续推进 Ex2 clean run 到正常结束，或由用户决定是否接受当前 checkpoint 作为阶段性结果。
- 正常结束后需要补跑或生成 metrics。
- metrics 生成后才适合整理与论文 Example 2 的误差对照。
- Example 3、Example 4 与后续复现实验的汇总仍需基于各自最终产物确认。

**受保护产物**
- Example 2 既有已完成产物：先不要修改、覆盖、删除或重跑它的产物，除非用户明确要求。
- `runs/overnight_current` 中已有 checkpoint 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- 当前 run：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528`，作为本次 clean run 的续跑来源，不应被删除或并发写入。

**下一步建议**
1. 最直接安全的下一步是继续从当前 checkpoint 续跑：
   ```powershell
   python .\repro_runner.py --case example2_forward --run-name ex2_forward_clean_20260528 --allow-existing-run --max-walltime-seconds 7200
   ```
2. 若希望减少人工等待，可改为后台长任务，但需要使用同一个 `run-name` 时确保没有并发写入。
3. 只有当状态变为 `completed` 或正常完成后，再补跑 metrics 并整理与论文 Example 2 的对照结果。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-28-ex2-forward-clean-resume-walltime-summary.md`

**需要确认**
- 是否继续再跑一个 7200 秒 walltime，或改用后台长任务继续推进当前 L-BFGS checkpoint。
