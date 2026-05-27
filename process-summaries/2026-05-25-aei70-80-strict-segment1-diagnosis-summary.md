# 80x80 strict aei70 reference solver 段 1 问题诊断汇报

**本轮运行状态**
- 状态：诊断完成；原 Segment 1 已报错失败
- 原命令：`.\scripts\start_ref_solver_segment.ps1 -RunDir .\reference_solver_outputs\aei70_krar_80_strict_20260525 -Segment 1 -WalltimeSeconds 3600`
- PID：`38932`，已退出
- walltime 上限：3600 秒
- 运行时长：需要确认
- 退出原因：`RuntimeError: Reference solve failed: dt<1e-06 at t=0.007746; last residual=1.000e-03`

**本次进程概述**
- 本轮未启动新的求解段，只做静态诊断和既有结果对照。
- 已读取 `reference_solver/generate_reference.py` 中的 JFNK、GMRES、时间步自适应、checkpoint 和 CLI 参数逻辑。
- 已读取失败 stderr：`reference_solver_outputs/aei70_krar_80_strict_20260525/logs/segment_1.stderr.log`。
- 已对照 `reproduction_report.md` 与既有 `aei70_krar_32` 历史记录。

**取得的成果**
- 确认失败不是启动器问题：用户终端启动后 PID 曾存活，最终由 solver 内部 RuntimeError 退出。
- 确认失败不是 Example 2 / Example 5 状态问题：`runs/overnight_current` 仍 `Protected: True`，Example 2 和 Example 5 均保持完成状态。
- 确认当前 case 是 `aei70_krar`：代码中对应 `PhysicalParams(Aei=70.0, kr_power=0.0)`。
- 确认当前数值配置来自启动脚本：
  - `nx=80`, `ny=80`
  - `dt_init=0.005`
  - `dt_max=0.02`
  - `dt_min=1e-6`
  - `newton_tol=1e-3`
  - `newton_max=8`
  - `gmres_tol=1e-5`
  - `gmres_maxiter=120`
- 确认失败机制：`jfnk_step` 返回 `ok=False` 后，`solve_reference` 将 `dt *= 0.5`；若 `dt < dt_min`，抛出当前 RuntimeError。
- 确认最后残差打印为 `1.000e-03`，正好位于 `newton_tol=1e-3` 边缘；代码收敛判据是 `norm_R < cfg.newton_tol`，不是 `<=`。
- 确认 stdout 为空的原因不是必然表示无推进：代码只在 `step % 25 == 0` 或最终完成时打印进度；若失败发生在第 25 个 accepted step 前，stdout 会保持为空。
- 确认 checkpoint 不存在意味着尚未触发保存条件；本次启动设置 `checkpoint_interval_steps=10`，因此很可能未到第 10 个 accepted step，或在第一个 checkpoint 前失败。
- 既有报告中已经记录类似结果：严格 `aei70_krar_80` 在 RMS residual 版本中曾推进到 `t=0.007746` 后失败，当前失败点完全复现该已知瓶颈。
- 对照 `aei70_krar_32` 成功历史：32x32 能完成 267 accepted steps，且在 `t≈0.0078` 附近可继续推进；80x80 在相近早期瞬态位置失败，说明网格加密后现有 JFNK/预条件器承压明显。

**续跑状态与检查点**
- 当前 checkpoint：不存在，路径应为 `C:\Users\12412\Documents\Lei_code\reference_solver_outputs\aei70_krar_80_strict_20260525\checkpoints\segment_1.ckpt.npz`。
- 当前阶段：reference solver strict `80x80` `aei70_krar` 段 1；不是 Example 5 的 70/400/700 阶段。
- 当前步数或优化器阶段：需要确认；没有 checkpoint/history 可读。
- 已完成阶段：strict `80x80` reference solver 未确认完成任何段。
- 下一次安全续跑命令：
  ```powershell
  当前不建议直接续跑或启动 Segment 2；需要先选择诊断重试方案或改进 solver。
  ```
- 不应执行的危险操作：
  - 不要自动重启失败任务，除非用户明确要求。
  - 不要启动 Segment 2。
  - 不要删除或覆盖 `runs/overnight_current`。
  - 不要重跑 Example 2 或 Example 5。
  - 不要把本 reference solver 状态与 Example 5 的 70/400/700 阶段混在一起。

**遇到的阻碍**
- 主要阻碍是数值收敛，不是进程生命周期。
- 当前 JFNK 使用矩阵自由有限差分 Jacobian-vector product 和对角预条件器；80x80 网格下扩散项刚性增强，早期顶部边界 `Tr=t0+2t` 升温瞬态使 Newton/GMRES 更难收敛。
- GMRES 的 `_info` 当前被忽略，失败时无法知道线性子问题是否达到 `gmres_maxiter` 或是否异常退出。
- 失败尝试没有逐步失败日志，也没有失败前 checkpoint，导致无法直接读取失败前的 accepted step、dt 轨迹和 Newton/GMRES 细节。
- `last residual=1.000e-03` 与 `newton_tol=1e-3` 几乎重合，说明失败可能在容差边界附近被严格 `<` 判据和舍入显示共同放大。

**未完成的部分**
- 未完成 Segment 1。
- 未生成 strict 80x80 `reference_snapshots.npz`。
- 未 validate。
- 未 export author txt。
- 未完成能解释每次 rejected dt 的细粒度日志。

**在总体进程中的作用**
- 本轮把问题从“后台进程是否能存活”定位到“严格 80x80 数值求解器在早期瞬态处收敛不足”。
- 当前最有价值的下一步不是继续分段，而是做一个新的、可观测性更强的诊断 run 或改进 solver 线性化/预条件器。

**总体进程中仍未完成**
- strict `80x80` reference 数据仍未生成。
- 80x80 production 级求解路径仍未打通。
- 后续 validate/export/作者脚本严格复现仍依赖该 reference 数据。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- Example 5 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint、日志、metrics、reports 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt：不要提交到 Git。

**下一步建议**
1. 不要在当前失败目录上直接重启；如需重试，使用新的 run dir 保留失败证据。
2. 先做最小诊断增强：让 solver 在每次 rejected dt、GMRES info、Newton residual、accepted step 时打印或保存 history，并在失败前保存 checkpoint/debug npz。
3. 参数层面的低风险试探可以放到新 run dir：提高 `newton_max` 到 12 或 16、提高 `gmres_maxiter` 到 240/300、把 `checkpoint_interval_steps` 降到 1，并把日志打开到每步；但这只是诊断，不保证生产可完成。
4. 不建议只降低 `dt_min` 作为正式方案；它可能让求解器继续在极小步长里消耗大量时间，而没有解决 JFNK/预条件器弱的问题。
5. 正式解决方向是增强 solver：检查 GMRES info，改进 Newton 接受判据和失败日志，考虑更强的 sparse Jacobian/块预条件器，或迁移既有参考文档中的 CuPy/JFNK 实现。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-25-aei70-80-strict-segment1-diagnosis-summary.md`

**需要确认**
- 是否允许修改 `reference_solver/generate_reference.py` 增加诊断日志与失败前 checkpoint。
- 是否允许用新的 run dir 做参数诊断重试。
- 是否目标仍坚持 strict 80x80 直接求解，还是允许先使用 `80x80_from20` 作为管线验证数据。
