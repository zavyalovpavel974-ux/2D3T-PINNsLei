# Ex4 Transfer Clean Run Walltime 汇报

**本轮运行状态**
- 状态：达到 walltime 上限。
- 命令：`python .\repro_runner.py --case example4 --run-name ex4_transfer_clean_20260527 --max-walltime-seconds 7200`
- walltime 上限：`7200` 秒。
- 运行时长：`example4_run_result.json` 记录 `7205.07963681221` 秒。
- 退出原因：训练脚本在 walltime 检查处保存 checkpoint 后抛出 `ReproWalltimeReached`，runner 记录子进程 return code 为 `1`。
- 运行方式：前台 clean single run；未设置 `max_iter_override`，未人为分 Adam 和 L-BFGS。

**本次进程概述**
本次按用户要求执行 Example 4 变体：在 Ex4 中引入 transfer learning，使用 `Aei=70 -> 400`、`Kr=Ar*Tr`、Fourier feature embedding、log initial/boundary loss，权重沿用 Ex3/Ex4 设置。运行使用新的输出目录，不写入冻结目录。

**取得的成果**
- 已完成代码配置收紧：
  - `example3`：`70 -> 400`、`Kr=Ar`、关闭 FF、启用 log loss。
  - `example4`：按用户要求 `70 -> 400` transfer、`Kr=Ar*Tr`、启用 FF、启用 log loss。
  - `example5`：`70 -> 400 -> 700`、`Kr=Ar*Tr`、启用 FF、启用 log loss。
- 已修复 forward 脚本中的 L-BFGS 续跑标记：
  - checkpoint 保存时使用显式 `current_phase`，避免 L-BFGS 函数评估计数小于 `nIter` 时被误标成 `adam`。
  - resume 时 `phase in {"lbfgs", "lbfgs_start"}` 会直接跳过 Adam，进入 L-BFGS。
- 已对本次 clean run 的最新 checkpoint 做状态校正：`phase` 从误标的 `adam` 改为真实的 `lbfgs`。
- 当前 checkpoint 已确认：
  - `Aei=70.0`
  - `phase=lbfgs`
  - `it=3708`
  - `loss=0.24042076439840732`
  - `transfer_stages=70,400`
  - `kr_mode=linear_tr`
  - `use_ff=True`
  - `use_log_loss=True`
  - `lambda_brd=20.0`
  - `lambda_init=10.0`

**续跑状态与检查点**
- 当前 checkpoint：`runs/ex4_transfer_clean_20260527/checkpoints/example4/latest.pt`
- 当前阶段：`Aei=70`
- 当前优化器阶段：`L-BFGS`
- 当前步数/函数评估标记：`it=3708`
- 已完成阶段：尚未确认完成 `Aei=70` 阶段；尚未进入 `Aei=400` 阶段。
- 下一次安全续跑命令：
  ```powershell
  python .\repro_runner.py --case example4 --run-name ex4_transfer_clean_20260527 --allow-existing-run --max-walltime-seconds 7200
  ```
- 不应执行的危险操作：
  - 不要使用 `max_iter_override` 续跑该 clean run。
  - 不要从 `runs/ex4_transfer_aei400_krartr_smoke_20260527` 或 `runs/ex4_transfer_aei400_krartr_adamprobe_20260527` 的 checkpoint 续跑正式 clean run。
  - 不要写入、覆盖或续跑 `runs/overnight_current`。

**遇到的阻碍**
- 本轮达到 walltime，未完整完成 `Aei=70` 阶段。
- 因为未完成阶段训练，没有生成 `example4_metrics.json`。
- stderr 中出现 traceback，但根因是预期内的 `ReproWalltimeReached` 保存 checkpoint 后退出，不是数值崩溃。

**未完成的部分**
- `Aei=70` 阶段仍需继续 L-BFGS。
- `Aei=400` transfer 阶段尚未开始。
- Ex4 对应的最终指标仍未生成。
- Ex4/Ex3 匹配参考解问题仍需后续处理；当前 `--skip-metrics` 避免错误使用不匹配参考解。

**在总体进程中的作用**
- 这次运行建立了用户指定的 Ex4-transfer 正式路线：不再用短 Adam/L-BFGS 分段 smoke，而是前台长窗口 clean single run。
- 运行证明该配置可以进入训练并保存可续跑 checkpoint。
- L-BFGS 续跑修正已经落实，后续可以从当前 checkpoint 继续，而不是回到 Adam。

**总体进程中仍未完成**
- Example 4 transfer 变体尚未完成。
- Example 3 / Example 4 的匹配参考解尚未确认或生成，因此暂不能给出严格误差表。
- strict `80x80` reference solver 仍未解决。
- Example 5 原工程结果仍未达到论文 Table 9 精度。

**受保护产物**
- Example 2 已完成：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint、日志、metrics、reports 和 figures：默认不得删除、覆盖或继续写入。
- 本次新增目录 `runs/ex4_transfer_clean_20260527` 是新的 clean run 输出目录，不属于冻结目录。

**下一步建议**
1. 继续当前 clean run：
   ```powershell
   python .\repro_runner.py --case example4 --run-name ex4_transfer_clean_20260527 --allow-existing-run --max-walltime-seconds 7200
   ```
2. 若 `Aei=70` 阶段完成并进入 `Aei=400`，继续使用同一 run-name 续跑，不另起目录，保持 clean single run 证据链。
3. 完成训练后，再决定是否生成/导入匹配的 Ex4 参考解来计算误差表。

**Markdown 文档**
- 已保存：`process-summaries/2026-05-27-ex4-transfer-clean-walltime-summary.md`
