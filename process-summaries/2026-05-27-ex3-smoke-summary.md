# Ex3 Aei400 KrAr Smoke 过程汇报

**本轮运行状态**
- 状态：达到 walltime 上限。
- 实际前台命令：`python .\repro_runner.py --case example3 --run-name ex3_aei400_krar_smoke_20260527 --allow-existing-run --max-iter-override 1 --max-walltime-seconds 30`
- 先前后台启动命令：`python .\repro_background.py start --case example3 --run-name ex3_aei400_krar_smoke_20260527 --max-iter-override 1 --max-walltime-seconds 120`
- 后台 PID：`22836`。
- walltime 上限：前台 smoke 为 `30` 秒；先前后台启动记录为 `120` 秒。
- 运行时长：`example3_run_result.json` 记录 `35.476988315582275` 秒。
- 退出原因：训练脚本在 `ReproWalltimeReached` 中保存 checkpoint 后退出；runner 记录 `example3` 子进程 return code 为 `1`。

**本次进程概述**
本次工作尝试把现有 Example 5 forward 脚本改造成可跑 Example 3 / Example 4 的较小诊断入口。已新增 `example3` runner 入口并完成一次短 smoke：`Aei=70 -> 400`、`Kr=Ar`、新 run-name，不写入冻结目录。

**取得的成果**
- 已确认新增 case 不会写入 `runs/overnight_current`，实际输出目录是 `runs/ex3_aei400_krar_smoke_20260527`。
- 已为 forward 子脚本新增 `--transfer-stages`，可配置为 `70,400` 或 `70,400,700`。
- 已为 forward 残差新增 `--kr-mode`，当前支持 `constant`、`linear_tr`、`power`。
- 已为缺少 Ex3/Ex4 参考解的场景新增 `--skip-metrics`，避免错误地拿 Example 5 的参考解计算 Ex3/Ex4 误差。
- 已为 runner 增加 `example3` 和 `example4` 入口。
- 已修复 `repro_background.py status` 在 Windows 下用 `os.kill(pid, 0)` 检查 PID 时触发异常的问题，改用 Win32 进程查询。
- 语法检查通过：`python -m py_compile repro_background.py repro_runner.py 2D3T_wei_aei700_wer_krartr_time.py sub_2D3T_wei_aei700_wer_krartr_time.py`。仅有原作者脚本既有的 `SyntaxWarning`。

**续跑状态与检查点**
- 当前 checkpoint：`runs/ex3_aei400_krar_smoke_20260527/checkpoints/example3/latest.pt`
- 当前阶段：`70`
- 当前步数或优化器阶段：`phase=lbfgs`，`step=19`
- 已完成阶段：需要确认。当前 status 只确认 checkpoint 仍处于 `Aei=70` 阶段，未确认完成 `70` 阶段，也未进入 `400` 阶段。
- 下一次安全续跑命令：
  ```powershell
  python .\repro_runner.py --case example3 --run-name ex3_aei400_krar_smoke_20260527 --allow-existing-run --max-walltime-seconds 600
  ```
- 不应执行的危险操作：
  - 不要删除或覆盖 `runs/overnight_current` 中已有 checkpoint、日志、metrics 和报告。
  - 不要把 Example 5 的 `70/400/700` checkpoint 与本次 Example 3 checkpoint 混用。
  - 不要修改、覆盖、删除或默认重跑 Example 2 已完成产物。

**遇到的阻碍**
- 前台 smoke 达到 `30` 秒 walltime，上层记录为 `returncode=1`，因此未生成 `example3_metrics.json`。
- `example3` 目前没有匹配的 `Aei=400, Kr=Ar` 参考文本文件，因此即使训练跑完，也不能直接产出论文级误差表。
- 先前后台启动留下了 `background/launch.json`，但后台 stdout/stderr 为空；实际可用证据来自后续前台运行、case stdout/stderr、run_result 和 status。

**未完成的部分**
- Example 3 的 `Aei=70 -> 400` 训练未完整跑完。
- Example 4 入口已具备 dry-run 验证，但尚未实际启动 smoke。
- Ex3/Ex4 对应传统数值参考解尚未生成或导入，误差表仍不可确认。

**在总体进程中的作用**
- 本次运行证明可以不继续推进失败的 Ex5，而把代码路线拆回到 Ex3/Ex4 的中间难度。
- 新入口允许逐步验证：先 `Aei=400, Kr=Ar`，再 `Aei=400, Kr=Ar*Tr`，比直接研究 `Aei=700, Kr=Ar*Tr` 更可控。
- 这为定位 Ex5 失败原因提供了中间台阶：可以区分“耦合增强”与“光子热导非线性”分别带来的影响。

**总体进程中仍未完成**
- strict `80x80` reference solver 仍未解决。
- Example 3 / Example 4 还没有完整训练结果。
- Example 3 / Example 4 没有可用匹配参考解，不能声明论文表格复现。
- Example 5 虽有工程链路结果，但仍未达到论文 Table 9 精度。

**受保护产物**
- Example 2 已完成：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint、日志、metrics、reports 和 figures：默认不得删除、覆盖或继续写入。
- 本次新增的 `runs/ex3_aei400_krar_smoke_20260527` 是新实验目录，不属于冻结目录。

**下一步建议**
1. 先续跑 Example 3 到至少完成 `Aei=70` 阶段，并确认能进入 `Aei=400` 阶段。
2. Example 3 smoke 稳定后，再启动 Example 4 smoke：`Aei=70 -> 400`、`Kr=Ar*Tr`、新 run-name。
3. 若要比较误差，需要先生成或提供 `Aei=400, Kr=Ar` 与 `Aei=400, Kr=Ar*Tr` 的匹配参考解；在此之前只能把训练损失、checkpoint 阶段和定性曲线作为诊断证据。

**Markdown 文档**
- 已保存：`process-summaries/2026-05-27-ex3-smoke-summary.md`

**需要确认**
- 后续是否要用较长 walltime 继续 `runs/ex3_aei400_krar_smoke_20260527`，还是另起一个更正式的新 run-name。
- 是否优先生成 Ex3/Ex4 的参考解，还是先只用训练损失和曲线判断中间难度是否可解。
