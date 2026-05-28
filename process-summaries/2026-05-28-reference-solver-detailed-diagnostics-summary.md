**本轮运行状态**
- 状态：正常完成
- 命令：
  - `python -m py_compile .\reference_solver\generate_reference.py .\scripts\start_ref_solver_segment.py`
  - PowerShell AST 解析：`[System.Management.Automation.Language.Parser]::ParseFile(...)`
  - launcher dry-run：`python .\scripts\start_ref_solver_segment.py --run-dir .\reference_solver_outputs\diag_dry_run_20260528 --segment 1 --walltime-seconds 10 --detailed-diagnostics --debug-on-failure --dry-run`
  - 小规模验证：`python .\reference_solver\generate_reference.py solve --case aei70_krar --nx 6 --ny 6 ... --debug-on-failure --detailed-diagnostics`
  - validate：`python .\reference_solver\generate_reference.py validate --npz .\reference_solver_outputs\diag_lowres_20260528\outputs\reference_snapshots.npz --json-out .\reference_solver_outputs\diag_lowres_20260528\outputs\validation.json`
  - `16x16` 成功侧对照：`python .\reference_solver\generate_reference.py solve --case aei70_krar --nx 16 --ny 16 ... --debug-on-failure --detailed-diagnostics`
  - `16x16` validate：`python .\reference_solver\generate_reference.py validate --npz .\reference_solver_outputs\diag_16x16_detailed_20260528\outputs\reference_snapshots.npz --json-out .\reference_solver_outputs\diag_16x16_detailed_20260528\outputs\validation.json`
  - 只读冻结目录检查：`python .\repro_status.py --run-name overnight_current`
- walltime 上限：`6x6` 小规模验证设置 `--max-walltime-seconds 30`，`16x16` 对照设置 `--max-walltime-seconds 60`；均未达到 walltime。
- 运行时长：`6x6` solve 输出显示 `done in 1.1s`；`16x16` solve 输出显示 `done in 17.1s`。
- 退出原因：正常完成。

**本次进程概述**
本轮按上一份对照分析的结论，先做 reference solver 诊断增强，而不是启动新的 strict `80x80` 长跑或改变求解算法。修改范围集中在 `reference_solver/generate_reference.py`、`scripts/start_ref_solver_segment.py`、`scripts/start_ref_solver_segment.ps1`，新增显式开关 `--detailed-diagnostics` / `-DetailedDiagnostics`，用于在 debug run 中记录 JFNK/Newton/line-search 的细粒度信息。

**取得的成果**
- `reference_solver/generate_reference.py` 新增 `ReferenceConfig.detailed_diagnostics`。
- 新增诊断摘要函数：
  - `vector_summary`：记录向量 finite 状态、范数、最大绝对值、min/max。
  - `values_summary`：记录 JVP finite-difference epsilon 序列摘要。
  - `state_summary`：按 `Te/Ti/Tr` 记录 finite、nonfinite、below floor、nonpositive、min/max/mean。
- `jfnk_step` 在 `debug_on_failure` 或 `detailed_diagnostics` 打开时记录：
  - 每次 Newton iteration 的 `norm_R`。
  - 当前 state summary。
  - GMRES info 和 callback summary。
  - JVP epsilon summary。
  - `dU` summary。
  - 每个 line-search `alpha` 的 `trial_norm`、accepted 标记和 trial state summary。
  - accepted alpha。
- accepted history 和 rejected diagnostics 均会包含 `newton_diagnostics`。
- Python launcher 已支持 `--detailed-diagnostics` 并透传到 `generate_reference.py`。
- PowerShell wrapper 已支持 `-DetailedDiagnostics` 并透传到 Python launcher。
- 静态检查通过：
  - Python `py_compile` 通过。
  - PowerShell AST 解析通过。
  - launcher dry-run 确认生成命令包含 `--debug-on-failure` 和 `--detailed-diagnostics`。
- 小规模 `6x6` debug smoke 正常完成：
  - 输出目录：`reference_solver_outputs/diag_lowres_20260528`
  - final output：`outputs/reference_snapshots.npz`
  - checkpoint：`checkpoints/latest.npz`
  - validation：`outputs/validation.json`
  - solve 状态：`steps=81`, `t=1.0`
  - validate 确认五个时间点均 finite，顶部 `Tr` 边界误差 `0.0`。
- 新诊断结构已在 checkpoint 中确认：
  - `history_len=81`
  - `diagnostics_len=8`
  - accepted history 含 `newton_diagnostics`
  - rejected diagnostics 含 `newton_diagnostics`
  - 示例 rich step：step `4`，`line_search_trials` 数量 `6`，`accepted_alpha=0.03125`
  - 示例 `dU_summary.max_abs=0.004359999999705345`
  - 示例 JVP epsilon summary：`count=91`, `min≈1.49476184e-08`, `max≈1.31514715e-06`
- `16x16` 成功侧 detailed debug 对照正常完成：
  - 输出目录：`reference_solver_outputs/diag_16x16_detailed_20260528`
  - final output：`outputs/reference_snapshots.npz`
  - checkpoint：`checkpoints/latest.npz`
  - validation：`outputs/validation.json`
  - solve 状态：`steps=220`, `t=1.0`
  - diagnostics：`history_len=220`, `diagnostics_len=5`
  - validate 确认五个时间点均 finite，顶部 `Tr` 边界误差 `0.0`。
  - `t≈0.0077455892` 附近的最近 accepted step：step `16`, `t=0.007784294242058239`, `dt=0.0008024490403430396`, `residual=2.047761713697656e-06`, `newton=3`
  - 第一条 rich accepted step：step `4`，`line_search_trials=7`，`accepted_alpha=0.015625`
  - 示例 `dU_summary.max_abs=0.006975999998995958`
  - 示例 JVP epsilon summary：`count=4721`, `min≈1.50250471e-08`, `max≈3.90144626e-07`
  - rejected diagnostics 数量：`5`；早期 rejected 之后最终恢复 `dt` 并完成到 `t=1.0`
- 冻结目录只读检查确认：
  - `runs/overnight_current` exists: `True`
  - `Protected: True`
  - Example 2: `completed`, step `6001`
  - Example 5: stage `700`, `completed`, step `6001`

**续跑状态与检查点**
- 本轮没有续跑 strict `80x80`。
- `6x6` 小规模 smoke checkpoint：`reference_solver_outputs/diag_lowres_20260528/checkpoints/latest.npz`
- `6x6` 小规模 smoke 当前状态：`step=81`, `t=1.0`
- `16x16` 成功侧对照 checkpoint：`reference_solver_outputs/diag_16x16_detailed_20260528/checkpoints/latest.npz`
- `16x16` 成功侧对照当前状态：`step=220`, `t=1.0`
- 上述 smoke / 对照均为 reference solver debug run，不是 Example 5 的 `70/400/700` 阶段。
- strict `80x80` 旧失败 checkpoint 仍为：`reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz`
- 下一次安全续跑命令：不建议续跑旧 strict `80x80` run；若继续，应使用新 run dir，并显式打开详细诊断，例如：
  ```powershell
  .\scripts\start_ref_solver_segment.ps1 `
    -RunDir .\reference_solver_outputs\aei70_krar_80_detailed_diag_20260528 `
    -Segment 1 `
    -WalltimeSeconds 1800 `
    -NewtonMax 16 `
    -GmresMaxiter 300 `
    -LogEveryStep `
    -LogRejectedSteps `
    -DebugOnFailure `
    -DetailedDiagnostics
  ```
- 不应执行的危险操作：
  - 不要写入、移动、删除或覆盖 `runs/overnight_current`。
  - 不要重跑 Example 2 或 Example 5。
  - 不要启动旧 `80x80` run 的 Segment 2。
  - 不要覆盖已有 strict `80x80` 失败证据目录。

**遇到的阻碍**
- 本轮已验证 `6x6` 小规模结构，并完成 `16x16` 成功侧 detailed debug 对照；尚未运行新的 `32x32/80x80` 同参数详细诊断对照。
- 新诊断会增加 checkpoint/history JSON 体积；因此默认不打开，必须显式使用 `--detailed-diagnostics` 或 `-DetailedDiagnostics`。
- 小规模 smoke 出现了早期 rejected steps，但最终完成；这些 rejected steps 是有用诊断样本，不代表本轮失败。

**未完成的部分**
- 尚未运行新的 strict `80x80` detailed debug run。
- 尚未运行新的 `32x32` detailed debug 对照。
- 尚未基于新诊断判断 80x80 是 JFNK 方向非下降、line-search 次数不足、JVP epsilon 尺度问题、变量 floor/负温度问题，还是容差边界问题。
- 尚未改动 solver 算法本身。

**在总体进程中的作用**
- 本轮把后续诊断所需的观测量补齐：下一次 80x80 debug run 不再只知道最后 `line_search_failed`，而能看到每个 `alpha` 的 trial residual、trial 状态、`dU` 尺度和 JVP epsilon 尺度。
- 这使下一步可以更有依据地选择 damping/line-search、JVP epsilon、变量缩放、预条件器或 sparse/block Jacobian 方向。

**总体进程中仍未完成**
- strict `80x80` reference 数据仍未生成。
- Example 5 仍缺少 strict paper-grade `80x80` reference 支撑。
- 需要用新诊断在新输出目录进行小规模与 80x80 对照。
- 需要根据新诊断结果决定具体 solver 方法改造。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- Example 5 已完整跑完：先不要修改、覆盖、删除或重跑它的产物；判断时必须区分 `70`、`400`、`700` 阶段。
- `runs/overnight_current` 中已有 checkpoint、logs、metrics、reports、figures 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- strict 80x80 失败证据目录应保留，不要删除或覆盖：
  - `reference_solver_outputs/aei70_krar_80_strict_20260525`
  - `reference_solver_outputs/aei70_krar_80_diag_newton16_gmres300_20260525`
  - `reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525`

**下一步建议**
1. 使用新 run dir 运行 strict `80x80` detailed debug 第一段，让失败 checkpoint 带上完整 `newton_diagnostics`。
2. 对比 `16x16` 成功路径与新 `80x80` 失败路径的 `dU_summary.max_abs`、`jv_eps_summary`、trial state 的 negative/floor 触发、以及每个 alpha 的 `trial_norm` 下降曲线。
3. 如需要更平滑的中间尺度，再补 `32x32` detailed debug 对照。
4. 若 80x80 trial 全部不下降，优先查 JVP epsilon、变量缩放和预条件器；若能下降但严格准则卡住，优先改 damping/Armijo-like 接受准则。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-28-reference-solver-detailed-diagnostics-summary.md`

**需要确认**
- 是否允许下一步写入新的 `reference_solver_outputs/aei70_krar_80_detailed_diag_20260528` 目录并启动 strict `80x80` detailed debug run。
- 是否需要在 80x80 前再补 `32x32` detailed debug 对照。
