**本轮运行状态**
- 状态：正常完成
- 命令：
  - `Get-ChildItem reference_solver_outputs`
  - `Get-Content reference_solver_outputs/ref_solver_resume_interrupt_test/logs/part1.stdout.log`
  - `Get-Content reference_solver_outputs/ref_solver_resume_interrupt_test/logs/part2.stdout.log`
  - `Get-Content reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/logs/segment_1.stdout.log`
  - `python -c "...读取 32x32/16x16/80x80 checkpoint history_json 与 diagnostics_json..."`
  - `rg -n "...line_search/gmres/newton_tol/dt_min..." reference_solver/generate_reference.py`
- walltime 上限：不适用，本轮只做只读 checkpoint/log/code 分析，未启动求解。
- 运行时长：需要确认。
- 退出原因：只读分析命令正常完成。

**本次进程概述**
本轮执行“用低分辨率成功路径对比 `80x80` 失败路径的 residual/dt/line-search 行为”。选取了同属 `aei70_krar` reference solver 的低分辨率 checkpoint 作为成功对照，并与最新 strict `80x80` failed checkpoint 对比。未写入 `runs/overnight_current`，未启动 Example 2 / Example 5，未启动任何新的 strict `80x80` run。

**对照对象**
- `32x32` 成功推进路径：
  - `reference_solver_outputs/ref_solver_resume_interrupt_test/checkpoints/resumed_checkpoint.npz`
  - 状态：`step=220`, `t=0.8072713745768957`, `dt=0.0027772333221442055`
  - 注意：这是成功推进到 `t≈0.807` 的 partial path，不是完整 `t=1.0` final output。
- `16x16` 成功闭环路径：
  - `reference_solver_outputs/ref_solver_resume_interrupt_test/checkpoints/resumed_checkpoint_16x16_wall1.npz`
  - 状态：`step=220`, `t=1.0`, `dt=0.002662898758473231`
- `80x80` 失败路径：
  - `reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz`
  - 状态：`step=9`, `t=0.0077455892`, `dt=7.873199999999999e-07`
  - `diagnostics_len=15`

**关键对比结果**

| case | total accepted steps | no-update-like steps | actual Newton/GMRES-like steps | first actual correction | rejects |
| --- | ---: | ---: | ---: | --- | ---: |
| 32x32 success partial | 220 | 4 | 216 | step 5, t=0.0049004, dt=3.24e-05, residual=9.879e-04 | 0 recorded |
| 16x16 success complete | 220 | 3 | 217 | step 4, t=0.003488, dt=1.08e-04, residual=9.973e-04 | 0 recorded |
| 80x80 failed | 9 | 9 | 0 | none | 15 |

解释：
- `no-update-like steps` 指 `newton_iters=1` 且没有 GMRES summary 的 accepted step。结合 `reference_solver/generate_reference.py` 当前逻辑，这表示初始残差已经小于 `newton_tol=1e-3`，函数直接返回 converged，没有执行 JFNK/GMRES 更新。
- 低分辨率路径在早期也会经历残差接近 `1e-3` 的阶段，但很快进入实际 Newton/GMRES 校正，然后 residual 降低、`dt` 恢复增长。
- `80x80` 路径的 9 个 accepted steps 全部是 no-update-like steps；一旦需要实际校正，尝试都以 `line_search_failed` 被拒绝，`dt` 不断折半直到小于 `dt_min=1e-6`。

**早期 t≈0.0077 附近对比**
- `32x32` 在最接近 `t=0.0077455892` 的 accepted step：
  - `dt=0.0004991874990165979`
  - `residual=7.842326226581234e-07`
  - 已经完成实际校正并恢复步长。
- `16x16` 在最接近 `t=0.0077455892` 的 accepted step：
  - `dt=0.0008024490403430396`
  - `residual=2.047761713697656e-06`
  - 同样已进入实际校正并恢复步长。
- `80x80` 在 `t=0.0077455892`：
  - accepted `dt=1.3122e-06`
  - accepted residual `0.000999951265938801`
  - 随后 attempted `dt=1.57464e-06` 被拒绝，`next_dt=7.8732e-07 < dt_min`

**80x80 rejected diagnostics**
- rejected 数量：`15`
- rejected reason：全部为 `line_search_failed`
- 最后几条 rejected：
  - step 8, `attempted_dt=4.374e-06`, `next_dt=2.187e-06`, `newton=8`, `residual=0.00100006416`, `gmres_info=300`, `gmres_last≈2.535664134751478e-07`
  - step 9, `attempted_dt=2.6244e-06`, `next_dt=1.3122e-06`, `newton=16`, `residual=0.00100012062`, `gmres_info=300`, `gmres_last≈2.5356641515095724e-07`
  - step 10, `attempted_dt=1.57464e-06`, `next_dt=7.8732e-07`, `newton=4`, `residual=0.00100015450`, `gmres_info=300`, `gmres_last≈2.535664154721429e-07`
- 这说明 GMRES callback residual 很低，但 line search 无法找到使 nonlinear residual 严格下降的 `alpha`。

**代码层解释**
- `reference_solver/generate_reference.py` 中 `jfnk_step` 的关键行为：
  - 若 `norm_R < cfg.newton_tol`，直接返回 converged。
  - JFNK finite-difference JVP 使用 `eps = sqrt(machine_eps) * (1 + ||u||) / ||v||`。
  - line search 要求 `trial_norm < norm_R`，最多 `line_search_max=8` 次，每次 `alpha *= 0.5`。
  - 若所有 `alpha` 都不能严格下降，则返回 `line_search_failed`，外层将 `dt *= 0.5`。
- 因此，80x80 的失败模式可以更精确地描述为：
  - 时间推进早期主要靠“初始残差刚低于 `1e-3`”的无更新步前进。
  - 当残差略高于阈值、必须执行实际 Newton correction 时，JFNK 线性解虽然给出很小 callback residual，但 nonlinear trial residual 无法通过严格下降测试。
  - dt 反复折半使初始残差勉强低于阈值，直到下一次 correction 仍失败并穿过 `dt_min`。

**取得的成果**
- 已完成低分辨率成功路径与 strict 80x80 失败路径的 residual/dt/Newton 行为对比。
- 明确了 80x80 与低分辨率的核心差别不是“有没有早期残差接近阈值”，而是“能否在接近阈值后成功进入实际校正并恢复步长”。
- 当前证据支持优先改造 line search / damping / JFNK step 诊断，而不是继续单纯增加 `gmres_maxiter` 或盲目降低 `dt_min`。

**续跑状态与检查点**
- 当前 strict 80x80 checkpoint：`reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz`
- 当前阶段：strict `80x80` `aei70_krar` reference solver，不是 Example 5 的 `70/400/700` 阶段。
- 当前步数：`step=9`, `t=0.0077455892`, `dt=7.873199999999999e-07`
- 已完成阶段：没有完成 strict `80x80` reference output。
- 下一次安全续跑命令：
  ```powershell
  # 暂不续跑；先做 line-search/JFNK 诊断或方法改造。
  ```
- 不应执行的危险操作：
  - 不要启动旧 80x80 run 的 Segment 2。
  - 不要重启 `aei70_krar_80_strict_20260525`、`aei70_krar_80_diag_newton16_gmres300_20260525` 或 `aei70_krar_80_gmrescb_diag_20260525`。
  - 不要写入、移动、删除或覆盖 `runs/overnight_current`。
  - 不要重跑 Example 2 或 Example 5。

**遇到的阻碍**
- 低分辨率旧 checkpoint 没有 `diagnostics_json`，因此不能直接看到低分辨率 rejected line-search 序列；只能从 accepted history 推断其最终成功进入实际校正。
- `80x80` 当前 diagnostics 只保存最后 line-search 失败时的 `alpha` 和 `trial_norm`，没有保存每个 `alpha` 的完整 trial residual 序列，仍不足以判断是“方向不下降”还是“下降不足/容差边界太硬”。
- 目前没有 `dU` 范数、最大值、温度 floor/负温度触发信息，无法确认 JFNK step 是否过大、方向异常或触发物理变量约束。

**未完成的部分**
- 尚未修改 solver 代码。
- 尚未实现每个 line-search `alpha` 的完整 trial residual 记录。
- 尚未实现 Newton residual 序列、`dU` 范数、变量 floor/负温度触发记录。
- 尚未运行新的低分辨率和 80x80 同参数诊断对照。

**在总体进程中的作用**
- 本轮把“下一步改什么”从泛泛的 solver 方法改造收窄到：先解释为什么 `80x80` 的真实 Newton correction 全部 line-search 失败，而低分辨率能在同一早期区间进入 correction 并恢复 `dt`。
- 这一步为后续代码改造提供了更明确的目标：不是先追求最终 reference output，而是先让诊断记录足以判断 JFNK 方向、line-search 策略和容差阈值的相互作用。

**总体进程中仍未完成**
- strict `80x80` reference 数据仍未生成。
- Example 5 当前仍不能被 strict paper-grade `80x80` reference 佐证。
- 需要进一步做代码级诊断增强或方法改造，然后再决定是否启动新的 run dir 进行小规模和 80x80 对照。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- Example 5 已完整跑完：先不要修改、覆盖、删除或重跑它的产物；判断时必须区分 `70`、`400`、`700` 阶段。
- `runs/overnight_current` 中已有 checkpoint、logs、metrics、reports、figures 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- strict 80x80 失败证据目录应保留，不要删除或覆盖：
  - `reference_solver_outputs/aei70_krar_80_strict_20260525`
  - `reference_solver_outputs/aei70_krar_80_diag_newton16_gmres300_20260525`
  - `reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525`

**下一步建议**
1. 优先修改诊断而非启动新长跑：在 `jfnk_step` 内记录每次 Newton iteration 的 `norm_R`、`dU` norm/max、line-search 每个 `alpha` 的 `trial_norm`。
2. 同时记录 trial state 是否出现非 finite、负温度或触发 `temp_floor` 前后的极值。
3. 在新输出目录做一个低分辨率同参数 debug run，确认成功路径的 line-search trial 序列长什么样。
4. 再用新的 80x80 debug run 验证：是 JFNK 方向非下降、`eps` 尺度不合适、line-search 最大次数不够，还是 `newton_tol=1e-3` 和严格下降准则共同造成阈值附近卡死。
5. 若诊断显示方向基本可下降但幅度很小，优先改 damping/Armijo-like 接受准则；若方向不下降，优先检查 JVP epsilon、预条件器和变量缩放。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-28-aei70-80-lowres-vs-80-failure-summary.md`

**需要确认**
- 是否进入下一步：修改 `reference_solver/generate_reference.py` 的诊断记录，而暂不改变求解算法。
- 是否允许随后在新的输出目录运行一个短的低分辨率 debug 对照；这会写入 `reference_solver_outputs` 新目录，但不会触碰 `runs/overnight_current`。
