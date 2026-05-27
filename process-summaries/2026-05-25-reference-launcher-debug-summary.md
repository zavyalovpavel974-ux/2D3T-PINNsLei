**本轮运行状态**
- 状态：NEED_CONFIRM
- 命令：
  - `python -m py_compile .\scripts\start_ref_solver_segment.py`
  - PowerShell AST 解析 `scripts/start_ref_solver_segment.ps1`
  - `python .\scripts\start_ref_solver_segment.py ... --dry-run`
  - `.\scripts\start_ref_solver_segment.ps1 ... -Nx 20 -Ny 20 -WalltimeSeconds 1`
  - 前台 20x20/1 秒 reference solver 健康检查
  - 后台 sleep 进程存活检查
  - `python .\repro_status.py --run-name overnight_current`
  - `git status --short --branch`
- walltime 上限：debug reference solve 使用 `1` 秒；strict `80x80` 未启动
- 运行时长：短诊断
- 退出原因：默认执行环境下后台子进程无法可靠存活；提升权限审批两次超时，无法继续验证外部后台启动

**本次进程概述**
用户采纳“先做小规模后台启动诊断、必要时改为 Python launcher”的建议。本轮新增 Python 版 reference solver 分段启动器，并保留 PowerShell 薄包装；随后用 20x20/1 秒小规模 debug 验证启动路径。结果显示 reference solver 命令本身健康，但默认工具执行环境中的后台子进程会在父命令结束后被清掉或快速退出，不能直接用于 strict `80x80` 长跑。

**取得的成果**
- 新增 `scripts/start_ref_solver_segment.py`：
  - 支持 `--run-dir`
  - 支持 `--segment`
  - 支持 `--walltime-seconds`
  - 支持 `--case`
  - 支持 `--nx/--ny`
  - 支持 `--dry-run`
  - 第 1 段不使用 `--resume-checkpoint`
  - 第 N 段从 `segment_(N-1).ckpt.npz` resume，并写入 `segment_N.ckpt.npz`
  - 拒绝写入 `runs/overnight_current`
  - 拒绝覆盖已有 output 或当前段 checkpoint
- 更新 `scripts/start_ref_solver_segment.ps1` 为 Python launcher 的薄包装。
- 静态检查通过：
  - Python launcher `py_compile` 通过
  - PowerShell wrapper AST 语法检查通过
  - dry-run 输出的第 1 段命令不包含 `--resume-checkpoint`
- 前台 20x20/1 秒 reference solver 命令健康：
  - 目录：`reference_solver_outputs/launcher_debug_foreground_20260525_084200`
  - 产生 checkpoint：`checkpoints/segment_1.ckpt.npz`
  - checkpoint：`step=4`, `t=0.0038350000000000003`, `dt=0.000162`
  - 未生成最终 `reference_snapshots.npz`，符合 1 秒 walltime 中断预期
  - 日志显示预期 `TimeoutError: reference solve reached walltime`
- `runs/overnight_current` 仍显示 `Protected: True`。
- Example 2 和 Example 5 均未重跑。
- 当前没有残留 `python` 进程。

**续跑状态与检查点**
- strict `80x80` Aei70 没有可 resume checkpoint：
  - `reference_solver_outputs/aei70_krar_80_strict_20260525/checkpoints/segment_1.ckpt.npz` 不存在
  - `reference_solver_outputs/aei70_krar_80_strict_20260525/outputs/reference_snapshots.npz` 不存在
- 小规模前台 debug checkpoint 可读，但它位于 debug 目录，不用于 strict `80x80` 续跑。

**遇到的阻碍**
- PowerShell `Start-Process` 在当前环境中因重复 `Path/PATH` 键失败。
- Python launcher 的后台子进程在默认工具执行环境中不能可靠存活；20x20 后台 debug 返回 PID 后日志为空、无 checkpoint。
- .NET `ProcessStartInfo` 启动的 60 秒 sleep 子进程也无法在默认执行环境中存活，说明问题更像执行环境/沙箱对子进程生命周期的限制。
- 请求提升权限做最小后台存活测试两次超时，无法确认沙箱外后台进程是否可用。

**未完成的部分**
- strict `80x80` Aei70 第 1 段未启动。
- 未生成 strict `80x80` checkpoint、output、validation 或 author txt。
- 后台长跑启动方式仍需要用户明确授权或改由用户在本机终端手动运行。

**在总体进程中的作用**
本轮将问题从“reference solver 是否能跑”缩小到“Codex 当前工具环境无法可靠持有后台子进程”。前台短测证明 reference solver 命令本身健康；后续可选择由用户终端直接运行脚本，或给 Codex 外部执行权限后再启动后台长跑。

**总体进程中仍未完成**
- strict `80x80` Aei70 reference solver 正式长跑。
- strict `80x80` Aei70 validate/export。
- Example 5 论文级 strict reference 结果。

**受保护产物**
- `runs/overnight_current` 未被写入、删除、移动或覆盖。
- Example 2 已完成，未重跑。
- Example 5 已完成，未重跑。
- 未提交 `reference_solver_outputs` 下输出。

**下一步建议**
- 推荐由用户在本机 PowerShell 直接运行：
  - `.\scripts\start_ref_solver_segment.ps1 -RunDir .\reference_solver_outputs\aei70_krar_80_strict_20260525 -Segment 1 -WalltimeSeconds 3600`
- 或者用户明确授权 Codex 以非沙箱/外部权限启动后台进程后，再由 Codex 运行同一命令。
- 如果要先完全绕开后台限制，可由用户确认改为前台分段执行；但这会占用当前命令直到 walltime 或中断。

**Markdown 文档**
- 本报告已保存到 `process-summaries/2026-05-25-reference-launcher-debug-summary.md`。

**需要确认**
- 是否允许 Codex 使用外部权限启动后台进程。
- 是否改为用户本机终端手动启动第 1 段。
- 是否接受前台分段作为备用执行方式。
