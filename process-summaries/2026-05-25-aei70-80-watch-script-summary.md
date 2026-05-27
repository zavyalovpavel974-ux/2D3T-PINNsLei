# Aei70 80x80 诊断运行只读巡检脚本汇报

**本轮运行状态**
- 状态：正常完成
- 命令：
  ```powershell
  PowerShell AST 解析 scripts/watch_ref_solver_run.ps1
  Select-String 检查 Start-Process / Stop-Process / generate_reference.py / start_ref_solver_segment / Remove-Item
  ```
- walltime 上限：不适用
- 运行时长：短命令检查，未启动长任务
- 退出原因：脚本创建与静态验证完成

**本次进程概述**
- 本轮根据当前 Aei70 80x80 诊断运行新增本地只读自动巡检脚本：
  `C:\Users\12412\Documents\Lei_code\scripts\watch_ref_solver_run.ps1`。
- 脚本面向当前 PID `37284` 和 run dir：
  `reference_solver_outputs/aei70_krar_80_diag_newton16_gmres300_20260525`。
- 本轮没有启动新的 strict 80x80 任务，没有启动 Segment 2，没有停止 PID。

**取得的成果**
- 新增脚本：`scripts/watch_ref_solver_run.ps1`。
- 支持参数：
  - `-RunDir`
  - `-Pid`，通过 `Alias("Pid")` 映射到内部 `ProcessId`，避免与 PowerShell 内置只读 `$PID` 冲突。
  - `-IntervalSeconds`
- 每轮只读检查：
  - `Get-Process -Id <Pid>`
  - 读取 `logs/segment_1.stdout.log` 尾部 160 行
  - 读取 `logs/segment_1.stderr.log` 尾部 160 行
  - 检查 `checkpoints/segment_1.ckpt.npz`
  - 检查 `checkpoints/segment_1.ckpt.failed.npz`
  - 检查 `outputs/reference_snapshots.npz`
  - checkpoint 存在时只读读取 `step/t/dt`
  - 运行 `python .\repro_status.py --run-name overnight_current`
  - 运行 `git status --short --branch`
- 自动状态判断：
  - `RUNNING`
  - `FINISHED`
  - `FAILED`
  - `STOPPED_NEED_CONFIRM`
- 每轮写出 latest markdown：
  `C:\Users\12412\Documents\Lei_code\process-summaries\aei70-80-diag-watch-latest.md`。
- 若状态为 `FINISHED`、`FAILED` 或 `STOPPED_NEED_CONFIRM`，脚本会停止循环并提示下一步。
- 若状态为 `RUNNING`，脚本等待 `IntervalSeconds` 后继续检查。

**续跑状态与检查点**
- 当前巡检脚本不会续跑，不会启动 solve，不会启动 Segment 2。
- 当前被巡检 checkpoint 路径：
  `reference_solver_outputs/aei70_krar_80_diag_newton16_gmres300_20260525/checkpoints/segment_1.ckpt.npz`。
- 当前阶段：reference solver strict `80x80` `aei70_krar` 诊断重试 Segment 1；不是 Example 5 的 70/400/700 阶段。
- 下一次安全使用命令：
  ```powershell
  .\scripts\watch_ref_solver_run.ps1 `
    -RunDir .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525 `
    -Pid 37284 `
    -IntervalSeconds 600
  ```
- 不应执行的危险操作：
  - 不要停止 PID `37284`。
  - 不要启动 Segment 2。
  - 不要重跑 Example 2 / Example 5。
  - 不要写入 `runs/overnight_current`。
  - 不要修改 `reference_solver_outputs` 下已有 checkpoint/log/output。

**遇到的阻碍**
- PowerShell 中 `$PID` 是内置只读变量，因此脚本不能直接使用 `$Pid` 作为内部变量名。
- 已通过 `[Alias("Pid")] [int]$ProcessId` 解决，外部仍可使用用户要求的 `-Pid` 参数。
- 初版 markdown 反引号写法触发 PowerShell 解析错误，已改为安全普通文本。

**未完成的部分**
- 本轮未实际运行 watcher 循环，以避免长时间占用当前 Codex 执行会话。
- `aei70-80-diag-watch-latest.md` 会在用户运行 watcher 后生成/更新。

**在总体进程中的作用**
- 该脚本把当前人工巡检流程固化为只读自动巡检，适合持续观察 PID `37284` 是否越过早期困难区、失败、walltime 或完成。
- 它保留实验安全边界：只读观察，不自动恢复、不重启、不停止、不改参数。

**总体进程中仍未完成**
- strict `80x80` `aei70_krar` reference 数据尚未生成。
- production 级 80x80 求解路径尚未打通。
- validate/export/作者脚本严格复现尚未进行。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- Example 5 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint、日志、metrics、reports 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt：不要提交到 Git。

**下一步建议**
1. 在本机 PowerShell 终端运行：
   ```powershell
   .\scripts\watch_ref_solver_run.ps1 `
     -RunDir .\reference_solver_outputs\aei70_krar_80_diag_newton16_gmres300_20260525 `
     -Pid 37284 `
     -IntervalSeconds 600
   ```
2. watcher 运行后查看：
   `process-summaries/aei70-80-diag-watch-latest.md`。
3. 若 watcher 报 `FINISHED`，不要启动 Segment 2，进入 validate。
4. 若 watcher 报 `FAILED`，读取 stderr 与 failed checkpoint diagnostics。
5. 若 watcher 报 `STOPPED_NEED_CONFIRM`，先确认进程为何停止，再决定是否续跑或重试。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-25-aei70-80-watch-script-summary.md`

**需要确认**
- 用户是否希望立即在独立 PowerShell 终端运行 watcher。
