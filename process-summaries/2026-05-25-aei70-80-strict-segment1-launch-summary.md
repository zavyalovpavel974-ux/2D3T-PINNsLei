**本轮运行状态**
- 状态：FAILED / NEED_CONFIRM
- 命令：
  - `python .\repro_status.py --run-name overnight_current`
  - `git status --short --branch`
  - `Test-Path .\reference_solver_outputs\aei70_krar_80_strict_20260525\outputs\reference_snapshots.npz`
  - `.\scripts\start_ref_solver_segment.ps1 -RunDir .\reference_solver_outputs\aei70_krar_80_strict_20260525 -Segment 1 -WalltimeSeconds 3600`
  - 启动后 `Get-Process`、日志、checkpoint 检查
- walltime 上限：计划为 `3600` 秒
- 运行时长：启动进程均在短时间内退出，未形成有效 1 小时长跑段
- 退出原因：启动包装层失败，未产生 reference solver checkpoint 或日志输出；具体底层原因需要确认

**本次进程概述**
本轮尝试启动 strict `80x80` Aei70 reference solver 第 1 段，目标目录为 `reference_solver_outputs/aei70_krar_80_strict_20260525`。启动脚本在 Windows/PowerShell 环境下先后暴露 `Start-Process` 环境变量冲突、`python -c` 引号传参、`cmd /c` 包裹解析等问题。已对脚本做了多轮修正，但第 1 段最终仍未进入有效长跑状态。

**取得的成果**
- 启动前安全检查通过：
  - `runs/overnight_current` 显示 `Protected: True`
  - Example 2：phase `completed`，step `6001`
  - Example 5：stage `700`，phase `completed`，step `6001`
  - `reference_solver_outputs/aei70_krar_80_strict_20260525/outputs/reference_snapshots.npz` 不存在
- 更新了 `scripts/start_ref_solver_segment.ps1`，尝试规避：
  - `Start-Process` 因重复 `Path/PATH` 环境键报错
  - `python -c` 多行 launcher 的 PowerShell 引号问题
  - `cmd /c` 对引号开头命令的特殊解析问题
- 目标目录下只产生启动元数据和空日志：
  - `background/launch_segment_1.json`
  - `background/launch_process.py`
  - `background/launch_spec_segment_1.json`
  - `logs/segment_1.stdout.log`，长度 `0`
  - `logs/segment_1.stderr.log`，长度 `0`

**续跑状态与检查点**
- 未产生 checkpoint：
  - `checkpoints/segment_1.ckpt.npz` 不存在
- 未产生最终输出：
  - `outputs/reference_snapshots.npz` 不存在
- 不存在可 resume 的 strict `80x80` Aei70 checkpoint。
- 最近一次 launch JSON 记录的承载 PID 为 `14404`，但该进程很快退出。
- 检查期间曾短暂出现 `python` PID `19964`，随后也退出；未写日志、未写 checkpoint。

**遇到的阻碍**
- PowerShell 环境中存在重复 `Path/PATH` 键，导致 `Start-Process` 最初报错：`已添加项。字典中的关键字:“Path”所添加的关键字:“PATH”`。
- Python launcher 与 `cmd.exe` 包装方案均未能形成稳定后台长跑。
- 当前 stdout/stderr 均为空，无法从 reference solver 日志确认底层 Python 退出原因。

**未完成的部分**
- strict `80x80` Aei70 第 1 段未成功启动。
- 未生成 `segment_1.ckpt.npz`。
- 未生成 `reference_snapshots.npz`。
- 未运行 validate/export。

**在总体进程中的作用**
本轮没有推进 reference solver 数值计算本身，但暴露了 Windows/PowerShell 后台启动机制的问题。下一步应先把启动包装层降级为可观测、可诊断的短时前台或短 walltime 测试，再恢复 1 小时 strict 长跑。

**总体进程中仍未完成**
- strict `80x80` Aei70 reference solver 正式长跑仍未开始。
- Example 5 严格论文级 reference 仍未生成。
- 后台启动脚本需要进一步诊断或改用更可靠启动方式。

**受保护产物**
- `runs/overnight_current` 未被写入、删除、移动或覆盖。
- Example 2 已完成，未重跑。
- Example 5 已完成，未重跑。
- 未提交 `reference_solver_outputs` 下输出。

**下一步建议**
- 暂停 strict `80x80` 启动，不要继续自动重试。
- 先做一个可观测的启动包装层诊断，建议使用新的小 debug 输出目录和极短 walltime，或直接前台运行同一 command 的短 walltime 版本，以确认命令本身和日志重定向能正常工作。
- 若继续使用后台，建议让脚本先支持 `-DryRun` 输出最终命令行，并增加启动后短时自检：若 PID 退出且日志为空，立即将 launch 标记为 `failed_start`。

**Markdown 文档**
- 本报告已保存到 `process-summaries/2026-05-25-aei70-80-strict-segment1-launch-summary.md`。

**需要确认**
- 是否允许先进行一个小规模后台启动诊断，而不是继续尝试 strict `80x80`。
- 是否希望将启动脚本改为 Python 版后台 launcher，避免 PowerShell/cmd 引号和环境问题。
