# 80x80 strict aei70 reference solver 段 1 失败汇报

**本轮运行状态**
- 状态：报错失败
- 命令：`.\scripts\start_ref_solver_segment.ps1 -RunDir .\reference_solver_outputs\aei70_krar_80_strict_20260525 -Segment 1 -WalltimeSeconds 3600`
- PID：`38932`
- walltime 上限：3600 秒
- 运行时长：需要确认；启动时间为 `2026-05-25T12:32:29+0800`
- 退出原因：`RuntimeError: Reference solve failed: dt<1e-06 at t=0.007746; last residual=1.000e-03`

**本次进程概述**
- 本轮检查 strict `80x80` `aei70_krar` reference solver 第 1 段进度。
- `launch_segment_1.json` 记录 PID 为 `38932`。
- `Get-Process -Id 38932` 未返回进程，说明该进程已退出。
- stdout 为空，stderr 中出现 Python traceback 和 RuntimeError。
- 当前没有生成 checkpoint，也没有生成最终 `reference_snapshots.npz`。

**取得的成果**
- 已确认第 1 段不是仍在运行，而是报错退出。
- stderr 路径：`C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_strict_20260525\logs\segment_1.stderr.log`，大小 `660` 字节。
- stdout 路径：`C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_strict_20260525\logs\segment_1.stdout.log`，大小 `0` 字节。
- 已确认失败位置：`t=0.007746`。
- 已确认失败原因文本：`dt<1e-06`，最后残差 `1.000e-03`。
- 已确认 `segment_1.ckpt.npz` 不存在。
- 已确认 `reference_snapshots.npz` 不存在。
- 已确认 `runs/overnight_current` 仍存在且 `Protected: True`。
- 已确认 Example 2：`completed`，step `6001`。
- 已确认 Example 5：stage `700`，`completed`，step `6001`。

**续跑状态与检查点**
- 当前 checkpoint：不存在，路径应为 `C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_strict_20260525\checkpoints\segment_1.ckpt.npz`。
- 当前阶段：reference solver strict `80x80` `aei70_krar` 段 1；不是 Example 5 的 70/400/700 训练阶段。
- 当前步数或优化器阶段：无 checkpoint，无法读取 step/t/dt。
- 已完成阶段：本 strict `80x80` reference solver 尚未确认完成任何段。
- 下一次安全续跑命令：
  ```powershell
  需要先确认是否调整 solver 参数或代码；按项目规则，不自动重启失败训练/求解任务。
  ```
- 不应执行的危险操作：
  - 不要自动重启第 1 段，除非用户明确要求。
  - 不要删除或覆盖 `runs/overnight_current` 中已有 checkpoint 和结果文件，除非用户明确要求。
  - 不要重跑 Example 2 或 Example 5。
  - 不要把 Example 5 的 70/400/700 阶段状态与本 reference solver 段状态混在一起。
  - 不要提交 `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt。

**遇到的阻碍**
- 第 1 段在 `t=0.007746` 时失败，错误为 `dt<1e-06`。
- stderr 出现 traceback：
  ```text
  RuntimeError: Reference solve failed: dt<1e-06 at t=0.007746; last residual=1.000e-03
  ```
- 没有 checkpoint，无法从中恢复或读取进度。
- stdout 为空，缺少额外运行进度信息。

**未完成的部分**
- 第 1 段未完成。
- 未生成 checkpoint。
- 未生成 `reference_snapshots.npz`。
- 未执行 validate。
- 未导出 author txt。
- 未启动后续段。

**在总体进程中的作用**
- 本次检查确认 strict `80x80` reference solver 的当前瓶颈不再是后台进程存活，而是数值求解在早期时间 `t=0.007746` 失败。
- 下一步需要围绕 reference solver 的时间步、牛顿/GMRES 参数或失败保护逻辑进行诊断，而不是直接启动下一段。

**总体进程中仍未完成**
- strict `80x80` `aei70_krar` reference solver 尚未完成第 1 段。
- 后续段 2/N 尚未启动，且当前不能安全启动。
- 最终 `reference_snapshots.npz` 尚未生成。
- validation 尚未完成。
- author txt 尚未导出。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- Example 5 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint、日志、metrics、reports 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt：不要提交到 Git。

**下一步建议**
1. 暂停推进，不要启动 Segment 2，也不要重复启动 Segment 1。
2. 诊断 `reference_solver/generate_reference.py` 中 `dt_min`、Newton 收敛、GMRES 参数、`dt-init`/`dt-max` 与失败时 `t=0.007746` 的关系。
3. 若要重试，应使用新的 run dir 或先明确如何处理当前空日志/失败记录；不要覆盖已有失败证据。
4. 如需我继续处理，建议下一步让我检查 reference solver 参数和失败逻辑，提出最小可控的重试方案。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-25-aei70-80-strict-segment1-failed-summary.md`

**需要确认**
- 是否允许修改 reference solver 参数或代码需要确认。
- 是否允许使用新的 run dir 做调参重试需要确认。
