# Runner/Status/Background 工程增强总结

**本轮运行状态**
- 状态：正常完成，未启动训练。
- 主要命令：
  - `python -m py_compile repro_runner.py repro_status.py repro_background.py`
  - `python repro_runner.py --status --run-name overnight_current`
  - `python repro_status.py --run-name overnight_current`
  - `python repro_background.py status --run-name overnight_current`
  - `python repro_runner.py --case example2 --run-name overnight_current --dry-run`
- walltime 上限：不适用，本轮只做工程增强和轻量检查。
- 运行时长：不适用。
- 退出原因：工程修改和轻量检查完成；防覆盖检查按预期拒绝写入冻结 run。

**本次进程概述**
本轮目标是增强复现实验 runner 的运行安全性和可观察性：默认防止覆盖已有 run，硬保护 `runs/overnight_current`，提供只读 status 查询，增加后台启动/检查脚本，并完善 Example 5 的 70/400/700 阶段识别。全程没有启动训练，也没有写入、移动、删除或覆盖 `runs/overnight_current`。

**取得的成果**
- 修改 `repro_runner.py`：
  - 默认禁止写入已有 run 目录。
  - 硬保护 `runs/overnight_current`，即使 `--allow-existing-run` 也不会写入。
  - 新增 `--status` 只读查询。
  - 新增 `--json` 输出结构化状态。
  - 新增 `--dry-run`，可验证将要写入的 run 目录但不创建、不训练。
  - Example 5 checkpoint 阶段识别会读取 `Aei`，明确区分 `70 / 400 / 700`。
- 新增 `repro_status.py`：
  - 专门做只读状态查询。
  - 输出 checkpoint、阶段、phase、step、metrics、logs、figures 路径。
- 新增 `repro_background.py`：
  - `start`：用于后台启动新 run，并记录 PID、命令、stdout/stderr 路径。
  - `status`：只读检查后台 PID metadata 和 run 状态。
- 轻量检查通过：
  - `python -m py_compile repro_runner.py repro_status.py repro_background.py`
- 保护检查通过：
  - `python repro_runner.py --case example2 --run-name overnight_current --dry-run`
  - 结果按预期拒绝写入：`refusing to write protected frozen run directory`
- 状态查询确认：
  - `overnight_current` 显示 `Protected: True`
  - Example 2：`stage: inverse`，`phase: completed`，`step: 6001`
  - Example 5：`stage: 700`，`phase: completed`，`step: 6001`

**续跑状态与检查点**
- 当前 checkpoint：
  - `runs/overnight_current/checkpoints/example2/latest.pt`
  - `runs/overnight_current/checkpoints/example5/latest.pt`
- 当前阶段：
  - Example 2：inverse，completed
  - Example 5：700，completed
- 当前步数或优化器阶段：
  - Example 2：`phase=completed`，`it=6001`
  - Example 5：`phase=completed`，`it=6001`
- 已完成阶段：Example 2 已完成；Example 5 的 70、400、700 阶段均已完成。
- 下一次安全运行命令：
  ```powershell
  $env:KMP_DUPLICATE_LIB_OK='TRUE'; python -u repro_runner.py --case all --run-name repro_clean_<timestamp>
  ```
- 后台启动模板：
  ```powershell
  python repro_background.py start --case all --run-name repro_clean_<timestamp> --max-walltime-seconds 21600
  ```
- 不应执行的危险操作：
  - 不要删除或覆盖 `runs/overnight_current` 中已有 checkpoint 和结果文件。
  - 不要在 `runs/overnight_current` 上继续训练或写入新报告。
  - 不要把 Example 5 的阶段 checkpoint 加载到错误阶段。

**遇到的阻碍**
- 未遇到阻碍。
- 只有一个预期内的失败：对 `overnight_current` 执行 `--dry-run` 写入检查时被拒绝，这是防覆盖保护的正确行为。

**未完成的部分**
- 本轮未提交 git commit。
- 未启动后台训练，也未验证真实后台训练流程；只验证了后台脚本的 `status` 和 `help` 路径。
- 未新增单元测试文件，目前是命令级轻量检查。

**在总体进程中的作用**
- 降低后续长实验误写冻结基线的风险。
- 为后续严格 `80x80` 复现实验提供安全入口：新 run 默认安全，旧 run 默认只读。
- 让长训练具备更好的可观察性：可以查询 checkpoint、阶段、日志、metrics 和后台 PID。

**总体进程中仍未完成**
- 严格 `80x80` 传统参考解仍未完成。
- 论文级 Example 2 / Example 5 重跑尚未开始。
- Example 5 当前失败原因仍需进一步分析。
- 本轮 runner 增强还未提交，需要后续 git add / commit。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint 和结果文件：默认不得删除或覆盖。
- `runs/overnight_current/reports/final_reproduction_report.md`
- `runs/overnight_current/checkpoints/example2/latest.pt`
- `runs/overnight_current/checkpoints/example5/latest.pt`
- `runs/overnight_current/logs`
- `runs/overnight_current/workdir/figures`

**下一步建议**
1. 提交本轮 runner/status/background 工程增强：
   ```powershell
   git add repro_runner.py repro_status.py repro_background.py process-summaries/2026-05-24-runner-status-background-summary.md
   git commit -m "Add protected runner status and background helpers"
   ```
2. 下一步开始做 `reference_solver` 小网格 checkpoint/resume 验证，但使用新的 run 或输出目录，不写入 `overnight_current`。
3. 后续长实验优先用后台模式或分段 walltime，避免外层工具中断训练状态。

**Markdown 文档**
- 已保存：`process-summaries/2026-05-24-runner-status-background-summary.md`
