**本轮运行状态**
- 状态：达到 walltime 上限
- 命令：`python .\repro_runner.py --case example2_forward --run-name ex2_forward_clean_20260528 --max-walltime-seconds 7200`
- walltime 上限：7200 秒
- 运行时长：约 7204.5 秒；checkpoint 内记录训练 elapsed_seconds 为 7200.035942554474 秒
- 退出原因：达到 `max-walltime` 后保存 checkpoint，并抛出 `ReproWalltimeReached`

**本次进程概述**
本轮按用户要求重新进行了 Example 2 前向训练，使用新的 run-name `ex2_forward_clean_20260528`，作为 clean single run 执行。训练没有写入 `runs/overnight_current`，当前已进入 L-BFGS 阶段并在 walltime 到达时安全保存 checkpoint。

**取得的成果**
- 已创建新运行目录：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528`
- 已执行 Example 2 配置：`--transfer-stages 70 --kr-mode constant --no-use-ff --no-use-log-loss --lambda-brd 1000 --lambda-init 10 --skip-metrics`
- 已确认当前 checkpoint 存在：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\checkpoints\example2_forward\latest.pt`
- checkpoint 内确认：`Aei=70.0`，`phase=lbfgs`，`it=25110`，`adam_iter=6001`，`loss=0.0280657941067559`
- 日志存在：
  - stdout：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\logs\example2_forward.stdout.log`
  - stderr：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\logs\example2_forward.stderr.log`
- 状态命令确认 run 存在，checkpoint、logs、figures 均存在；metrics 文件缺失是因为本轮命令启用了 `--skip-metrics`

**续跑状态与检查点**
- 当前 checkpoint：`C:\Users\12412\Documents\Lei_code\runs\ex2_forward_clean_20260528\checkpoints\example2_forward\latest.pt`
- 当前阶段：70
- 当前步数或优化器阶段：L-BFGS，`it=25110`
- 已完成阶段：Example 2 的 70 阶段已完成 Adam 并进入 L-BFGS；完整训练是否收敛完成需要继续跑或检查最终停止条件
- 下一次安全续跑命令：
  ```powershell
  python .\repro_runner.py --case example2_forward --run-name ex2_forward_clean_20260528 --allow-existing-run --max-walltime-seconds 7200
  ```
- 不应执行的危险操作：
  - 不要删除或覆盖 `runs/overnight_current` 中已有 checkpoint 和结果文件，除非用户明确要求。
  - 不要把 Example 5 的 70/400/700 阶段 checkpoint 误加载到 Example 2 或其他阶段。
  - 不要修改、覆盖、删除或重跑既有已完成 Example 2 产物，除非用户明确要求；本轮新运行目录 `ex2_forward_clean_20260528` 是独立产物。

**遇到的阻碍**
- 本轮没有训练崩溃；stderr 中的 traceback 是 walltime 保护主动抛出的 `ReproWalltimeReached`。
- stderr 中仍有既有 `SyntaxWarning`、`DeprecationWarning` 和 PyTorch `UserWarning`，未见其阻止训练。
- metrics 未生成，因为命令明确使用了 `--skip-metrics`。

**未完成的部分**
- Example 2 clean run 尚未正常完成到最终结束条件；当前停在 L-BFGS 阶段，可从 checkpoint 续跑。
- 本轮未生成 metrics JSON，因此尚不能基于该 run 汇报 L2/L1/Linf 等最终指标。

**在总体进程中的作用**
- 本轮建立了一个新的、独立的 Example 2 forward clean run，用于后续与 Example 3、Example 4 或论文设定进行对照。
- 本轮也验证了 L-BFGS 阶段的 walltime 保存与续跑入口可以保留当前优化器阶段。

**总体进程中仍未完成**
- Example 2 clean run 需要继续从 L-BFGS checkpoint 续跑到正常结束，或在用户认可时再计算指标。
- Example 3、Example 4 与 Example 5 的最终对比和复现报告仍需在各自结果确认后整理。
- 需要在最终报告中区分论文设定与用户指定设定，尤其是 Ex4 中用户额外要求引入 transfer。

**受保护产物**
- Example 2 既有已完成产物：先不要修改、覆盖、删除或重跑它的产物，除非用户明确要求。
- `runs/overnight_current` 中已有 checkpoint 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- 本轮新产物 `runs\ex2_forward_clean_20260528`：作为当前 clean run 的续跑来源，不应被覆盖或删除。

**下一步建议**
1. 如继续推进本次 Ex2 clean run，直接从当前 L-BFGS checkpoint 续跑：
   ```powershell
   python .\repro_runner.py --case example2_forward --run-name ex2_forward_clean_20260528 --allow-existing-run --max-walltime-seconds 7200
   ```
2. 续跑结束后运行状态检查：
   ```powershell
   python .\repro_status.py --run-name ex2_forward_clean_20260528
   ```
3. 若达到正常结束，再决定是否补跑 metrics 或整理与论文 Example 2 的对照结果。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-28-ex2-forward-clean-walltime-summary.md`

**需要确认**
- 是否现在继续从 L-BFGS checkpoint 续跑，还是先暂停并检查 loss 曲线、日志或图像。
