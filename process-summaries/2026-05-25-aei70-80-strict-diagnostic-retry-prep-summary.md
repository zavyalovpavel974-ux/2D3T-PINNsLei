# 80x80 strict aei70 诊断增强与参数重试准备汇报

**本轮运行状态**
- 状态：代码诊断增强已完成；参数诊断重试在 Codex 后台启动受阻，需要用户终端启动
- 代码验证命令：
  ```powershell
  python -m py_compile .\reference_solver\generate_reference.py .\scripts\start_ref_solver_segment.py
  ```
- PowerShell 语法验证命令：
  ```powershell
  $null = [System.Management.Automation.Language.Parser]::ParseFile('C:\Users\12412\Documents\Lei_code\scripts\start_ref_solver_segment.ps1', [ref]$null, [ref]$null)
  ```
- 诊断 dry-run 命令：
  ```powershell
  .\scripts\start_ref_solver_segment.ps1 -RunDir .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525 -Segment 1 -WalltimeSeconds 3600 -NewtonMax 16 -GmresMaxiter 300 -CheckpointIntervalSteps 1 -LogEveryStep -LogRejectedSteps -DebugOnFailure -DryRun
  ```
- Codex 实际启动命令：
  ```powershell
  .\scripts\start_ref_solver_segment.ps1 -RunDir .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525 -Segment 1 -WalltimeSeconds 3600 -NewtonMax 16 -GmresMaxiter 300 -CheckpointIntervalSteps 1 -LogEveryStep -LogRejectedSteps -DebugOnFailure
  ```
- Codex 启动 PID：`28532`
- walltime 上限：3600 秒
- 运行时长：约 10 秒后检查，PID `28532` 已不存在
- 退出原因：需要确认；stdout/stderr 为空，现象仍符合 Codex 工具环境后台子进程无法保活

**本次进程概述**
- 本轮按用户要求顺序执行两步建议：
  1. 增强 `reference_solver/generate_reference.py` 的诊断日志和失败前 debug checkpoint。
  2. 准备并尝试用新 run dir 启动参数诊断重试。
- 第 1 步已完成并通过编译验证。
- 第 2 步的启动命令和目录已准备好；Codex 工具环境内启动仍快速退出，沙箱外启动审批两次超时，因此需要用户本机 PowerShell 终端启动。

**取得的成果**
- 修改 `reference_solver/generate_reference.py`：
  - 新增 `--log-every-step`，可打印每个 accepted step。
  - 新增 `--log-rejected-steps`，可打印每个 rejected dt 的 `attempted_dt`、`next_dt`、Newton 次数、residual、失败原因和 GMRES info。
  - 新增 `--debug-on-failure`，在 `dt<dt_min` 前写入失败 debug checkpoint，路径形如 `segment_1.ckpt.failed.npz`。
  - JFNK 返回 `gmres_info` 和失败原因，history 中记录 accepted step 的 `gmres_info`。
  - checkpoint 可额外保存 `diagnostics_json`。
- 修改 `scripts/start_ref_solver_segment.py`：
  - 接通 `--dt-min`、`--log-every-step`、`--log-rejected-steps`、`--debug-on-failure`。
  - 保留原有保护逻辑：拒绝写入 `runs/overnight_current`，拒绝覆盖已有 output/current checkpoint。
- 修改 `scripts/start_ref_solver_segment.ps1`：
  - 新增参数 `-DtInit`、`-DtMin`、`-DtMax`、`-NewtonMax`、`-GmresMaxiter`、`-CheckpointIntervalSteps`、`-LogEveryStep`、`-LogRejectedSteps`、`-DebugOnFailure`。
- 验证通过：
  - `python -m py_compile` 成功。
  - PowerShell AST 解析成功。
  - dry-run 成功打印完整诊断命令。
- 新诊断 run dir：`C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525`。
- 当前该目录下 stdout/stderr 均为 0 字节，无 checkpoint、无 output。
- 确认 `runs/overnight_current` 仍存在且 `Protected: True`。
- 确认 Example 2：`completed`，step `6001`。
- 确认 Example 5：stage `700`，`completed`，step `6001`。

**续跑状态与检查点**
- 当前 strict 80x80 生产失败目录 checkpoint：不存在。
- 当前诊断重试目录 checkpoint：不存在。
- 当前阶段：reference solver strict `80x80` `aei70_krar` 诊断重试；不是 Example 5 的 70/400/700 阶段。
- 当前步数或优化器阶段：无 checkpoint，无法读取。
- 已完成阶段：strict `80x80` reference solver 尚未完成任何段。
- 下一次安全启动命令：
  ```powershell
  .\scripts\start_ref_solver_segment.ps1 `
    -RunDir .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525 `
    -Segment 1 `
    -WalltimeSeconds 3600 `
    -NewtonMax 16 `
    -GmresMaxiter 300 `
    -CheckpointIntervalSteps 1 `
    -LogEveryStep `
    -LogRejectedSteps `
    -DebugOnFailure
  ```
- 启动后状态检查命令：
  ```powershell
  Get-Content .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\background\launch_segment_1.json -Encoding UTF8
  Get-Process -Id <PID>
  Get-Content .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\logs\segment_1.stdout.log -Tail 120
  Get-Content .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\logs\segment_1.stderr.log -Tail 120
  Test-Path .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\checkpoints\segment_1.ckpt.npz
  Test-Path .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\checkpoints\segment_1.ckpt.failed.npz
  Test-Path .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525\outputs\reference_snapshots.npz
  python .\repro_status.py --run-name overnight_current
  ```
- 停止命令：
  ```powershell
  Stop-Process -Id <PID>
  ```
- 不应执行的危险操作：
  - 不要启动 Segment 2，除非 Segment 1 生成可用 checkpoint 且已确认 walltime 结束。
  - 不要删除或覆盖 `runs/overnight_current`。
  - 不要重跑 Example 2 或 Example 5。
  - 不要提交 `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt。

**遇到的阻碍**
- Codex 工具环境内后台启动 PID `28532` 后，约 10 秒检查进程已不存在。
- 沙箱外启动审批两次超时，未能由 Codex 直接启动持久后台进程。
- 当前诊断目录存在，但没有有效求解日志和 checkpoint；需要用户本机 PowerShell 终端启动同一命令。

**未完成的部分**
- 参数诊断重试尚未在可保活环境中运行。
- 尚未生成诊断 checkpoint。
- 尚未生成失败 debug checkpoint。
- 尚未获得 rejected dt / GMRES info / 每步 residual 的实际日志。

**在总体进程中的作用**
- 本轮已经把求解器改造成可诊断状态：下一次失败会留下比原来多得多的信息。
- 当前仍需用户终端负责后台进程生命周期；Codex 负责后续读取日志、分析和汇报。

**总体进程中仍未完成**
- strict `80x80` `aei70_krar` reference 数据未生成。
- 80x80 production 级求解路径未打通。
- validate/export/作者脚本严格复现仍未进行。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- Example 5 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint、日志、metrics、reports 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt：不要提交到 Git。

**下一步建议**
1. 用户在本机 PowerShell 终端运行上述诊断启动命令。
2. 启动后把 PID 告诉 Codex，或让 Codex读取 `launch_segment_1.json`。
3. Codex 检查 stdout/stderr、checkpoint、failed checkpoint、`runs/overnight_current` 保护状态。
4. 如果出现 `walltime`、`error`、`traceback`、`exception`、`nan`、`killed`、`FAILED` 或 `NEED_CONFIRM`，继续用 `process-summary` 汇报。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-25-aei70-80-strict-diagnostic-retry-prep-summary.md`

**需要确认**
- 用户是否已在本机 PowerShell 终端启动诊断重试。
- 启动后的真实 PID 需要确认。
