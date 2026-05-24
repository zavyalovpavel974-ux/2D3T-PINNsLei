**本轮运行状态**
- 状态：正常完成
- 命令：
  - `git status --short --branch`
  - `Test-Path .\scripts\start_ref_solver_segment.ps1`
  - PowerShell AST 语法解析 `scripts/start_ref_solver_segment.ps1`
  - 静态检查脚本内容是否使用 `repro_background.py`、`latest.ckpt.npz`、分段 checkpoint、防覆盖保护
  - `python .\repro_status.py --run-name overnight_current`
- walltime 上限：不适用，本轮未启动 reference solve、训练或后台长跑
- 运行时长：轻量脚本生成与静态检查
- 退出原因：正常完成

**本次进程概述**
本轮根据 strict `80x80` Aei70 长跑规划修正版，新增分段 reference solver 后台启动脚本。脚本采用独立分段 checkpoint：第 1 段写 `segment_1.ckpt.npz`，第 N 段从 `segment_(N-1).ckpt.npz` resume 并写入 `segment_N.ckpt.npz`。本轮没有实际启动 strict `80x80`。

**取得的成果**
- 新增脚本：`scripts/start_ref_solver_segment.ps1`
- 脚本默认目标目录：`reference_solver_outputs/aei70_krar_80_strict_20260525`
- 脚本参数：
  - `-RunDir`
  - `-Segment`
  - `-WalltimeSeconds`
- 已实现保护：
  - 若 `outputs/reference_snapshots.npz` 已存在，则拒绝启动 solve。
  - 若当前段 `checkpoints/segment_N.ckpt.npz` 已存在，则拒绝覆盖。
  - 若 `Segment > 1` 且 `checkpoints/segment_(N-1).ckpt.npz` 不存在，则拒绝启动。
  - 若 `RunDir` 指向或位于 `runs/overnight_current`，则拒绝写入。
- 已实现分段 checkpoint 策略：
  - 第 1 段不传 `--resume-checkpoint`。
  - 第 N 段传 `--resume-checkpoint segment_(N-1).ckpt.npz`。
  - 每段传 `--checkpoint segment_N.ckpt.npz`。
  - 脚本不使用 `latest.ckpt.npz`。
- 已实现每段独立输出：
  - `logs/segment_N.stdout.log`
  - `logs/segment_N.stderr.log`
  - `background/launch_segment_N.json`
- 静态检查结果：
  - PowerShell 语法解析通过。
  - `uses_repro_background=False`
  - `uses_latest_ckpt=False`
  - `has_segment_checkpoint=True`
  - `has_output_guard=True`
  - `has_overwrite_guard=True`
- `reference_solver_outputs/aei70_krar_80_strict_20260525` 当前不存在，说明本轮未启动长跑、未创建目标长跑输出目录。

**续跑状态与检查点**
- 本轮未产生新的 reference solver checkpoint。
- 后续实际运行时：
  - 第 1 段 checkpoint：`checkpoints/segment_1.ckpt.npz`
  - 第 N 段 resume 输入：`checkpoints/segment_(N-1).ckpt.npz`
  - 第 N 段 checkpoint 输出：`checkpoints/segment_N.ckpt.npz`
- 每段启动后脚本会返回 JSON，包含 PID、命令、日志路径、checkpoint 路径、输出路径和启动时间。

**遇到的阻碍**
- 无阻碍。
- 原规划中对尚未生成的 checkpoint 文件直接 `Resolve-Path` 会有启动后写 launch JSON 失败风险；脚本已改为解析目录路径后拼接 checkpoint 文件名。

**未完成的部分**
- strict `80x80` Aei70 长跑尚未启动。
- 尚未生成 `reference_solver_outputs/aei70_krar_80_strict_20260525` 下的 checkpoint、logs、outputs。
- 尚未 validate/export strict `80x80` 结果。

**在总体进程中的作用**
本轮把 strict `80x80` Aei70 长跑的启动机制从手工命令规划推进为可复用脚本，并修正了 checkpoint 同名读写风险。该脚本为后续分段 walltime 长跑提供了更安全的 resume 边界和审计记录。

**总体进程中仍未完成**
- 需要用户确认后实际启动第 1 段 strict `80x80` Aei70 reference solver。
- 需要每段完成或 walltime 后检查日志、checkpoint 和 `runs/overnight_current` 保护状态。
- Example 5 严格论文级结果仍需后续 strict `80x80` reference solver 结果支持。

**受保护产物**
- `runs/overnight_current` 未被写入、删除、移动或覆盖。
- `python .\repro_status.py --run-name overnight_current` 确认 `Protected: True`。
- Example 2 保持 completed，step `6001`，未重跑。
- Example 5 保持 stage `700` completed，step `6001`，未重跑。
- 本轮未提交 `reference_solver_outputs` 下任何输出。

**下一步建议**
- 等待用户确认后，可使用以下命令启动第 1 段：
  - `.\scripts\start_ref_solver_segment.ps1 -RunDir .\reference_solver_outputs\aei70_krar_80_strict_20260525 -Segment 1 -WalltimeSeconds 3600`
- 启动后必须记录脚本返回的 PID、stdout/stderr、checkpoint、output，并用 `process-summary` 汇报。
- 每段结束后先检查日志和 checkpoint，再决定是否启动下一段。

**Markdown 文档**
- 本报告已保存到 `process-summaries/2026-05-25-aei70-80-strict-launch-script-summary.md`。

**需要确认**
- 是否现在启动 strict `80x80` Aei70 第 1 段。
- 是否需要先提交 `scripts/start_ref_solver_segment.ps1` 与本 summary。
