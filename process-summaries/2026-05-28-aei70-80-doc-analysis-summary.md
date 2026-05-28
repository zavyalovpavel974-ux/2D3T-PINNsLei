**本轮运行状态**
- 状态：正常完成
- 命令：
  - `Get-Content ...2026-05-25-strict-80x80-aei70-handoff.md -Encoding UTF8`
  - `Get-Content ...2026-05-27-aei70-80-context-compression.md -Encoding UTF8`
  - `Get-Content ...2026-05-27-context-compression-handoff.md -Encoding UTF8`
  - `Get-Content ...2026-05-27-context-compression.md -Encoding UTF8`
  - `python .\repro_status.py --run-name overnight_current`
  - `git status --short --branch`
  - `python -c "...读取 segment_1.ckpt.failed.npz 摘要..."`
- walltime 上限：不适用，本轮是只读文档和 checkpoint 分析。
- 运行时长：需要确认。
- 退出原因：分析命令正常完成，未启动训练或 reference solver。

**本次进程概述**
本轮分析了四份 strict `80x80` `aei70_krar` reference solver 与上下文压缩交接文档，并只读验证了冻结目录状态和最新 failed checkpoint。整体结论是：传统网格 `80x80` strict reference solver 已从“准备分段长跑”推进到“早期失败点稳定复现”，当前不应继续启动 Segment 2 或重启旧 run，应转入 solver 方法改造与更细诊断。

**取得的成果**
- 已确认 `runs/overnight_current` 当前仍存在且 `Protected: True`。
- 已确认 Example 2 当前为 `completed`，step `6001`，checkpoint 和 metrics 均存在。
- 已确认 Example 5 当前为 stage `700`，phase `completed`，step `6001`，checkpoint 和 metrics 均存在。
- 已确认四份文档的主线变化：
  - `2026-05-25-strict-80x80-aei70-handoff.md` 主要是启动 strict `80x80` 分段长跑的交接说明。
  - `2026-05-27-aei70-80-context-compression.md` 与 `2026-05-27-context-compression-handoff.md` 已明确转为暂停重启、不要启动 Segment 2、转向 solver 方法改造。
  - `2026-05-27-context-compression.md` 同时保留了 Example 5 误差异常、reference solver smoke、strict 80x80 失败事实和后续建议。
- 已只读验证最新 failed checkpoint 存在：
  - `reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz`
- checkpoint 摘要已复现：
  - `step=9`
  - `t=0.0077455892`
  - `dt=7.873199999999999e-07`
  - `history_len=9`
  - `diagnostics_len=15`
- 最后 accepted history 显示 residual 逐步贴近 `1e-3`：
  - step 5 residual `0.000995421269697743`
  - step 6 residual `0.000998558386208171`
  - step 7 residual `0.0009994995211612993`
  - step 8 residual `0.0009997818616472379`
  - step 9 residual `0.000999951265938801`
- 最后三条 rejected diagnostics 均为 `line_search_failed`，且 `gmres_info=300`、`gmres_iterations=12000`、`gmres_last≈2.535664e-07`、`alpha=0.00390625`、`trial_norm` 刚高于 `1e-3`。
- 推断依据增强：失败不像是单纯 GMRES residual 不下降，也不像是后台进程、checkpoint/resume 或文件路径问题；更像是 JFNK 更新方向、finite-difference JVP 尺度、line search/damping、非线性容差边界或物理变量约束触发造成的非线性求解失败。

**续跑状态与检查点**
- 当前 checkpoint：`reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525/checkpoints/segment_1.ckpt.failed.npz`
- 当前阶段：strict `80x80` `aei70_krar` reference solver，不是 Example 5 的 `70/400/700` PINN 阶段。
- 当前步数或优化器阶段：reference solver `step=9`, `t=0.0077455892`, `dt=7.873199999999999e-07`；不是优化器阶段。
- 已完成阶段：没有生成 strict `80x80` final `reference_snapshots.npz`，因此没有完成可用于 paper-grade reference 的 strict 80x80 求解。
- 下一次安全续跑命令：
  ```powershell
  # 暂不建议续跑；需要先完成 solver 方法改造和诊断设计。
  # 不要启动旧 run 的 Segment 2。
  ```
- 不应执行的危险操作：
  - 不要删除或覆盖 `runs/overnight_current` 中已有 checkpoint、日志、metrics、reports 或结果文件。
  - 不要重跑 Example 2 或 Example 5。
  - 不要把 Example 5 的 `70/400/700` 阶段状态与 strict reference solver 状态混在一起判断。
  - 不要启动 `aei70_krar_80_strict_20260525`、`aei70_krar_80_diag_newton16_gmres300_20260525` 或 `aei70_krar_80_gmrescb_diag_20260525` 的旧 run。
  - 不要将 `reference_solver_outputs` 下的大输出、checkpoint、logs、validation 或 author txt 纳入提交。

**遇到的阻碍**
- strict `80x80` 求解在很早期 `t≈0.007746` 附近稳定失败。
- `dt` 降到 `dt_min=1e-6` 以下，报错为 `Reference solve failed: dt<1e-06 at t=0.007746; last residual=1.000e-03`。
- 单纯提高 `newton_max` / `gmres_maxiter` 已试过，文档结论为未解决。
- GMRES callback residual 很低但 line search 仍失败，说明线性残差不等于非线性步接受成功。
- 当前文档中的 Git 状态与本轮实际 `git status` 不完全一致：本轮看到 modified 文件为 `2D3T_wei_aei70_wer_krar_inverse.py`、`repro_background.py`、`repro_runner.py`、`sub_2D3T_wei_aei700_wer_krartr_time.py`，另有若干 2026-05-27/28 summary 未跟踪；因此提交/清理前需要重新审查当前工作区，而不能完全依赖旧交接文档。

**未完成的部分**
- strict `80x80` `aei70_krar` final output `reference_snapshots.npz` 未生成。
- strict `80x80` validate 和 author txt export 未完成。
- JFNK/line-search 失败机理尚未定位到代码级根因。
- Example 5 虽已完成工程链路，但误差是否达到论文量级仍未确认；文档指出原 per-time reference 映射曾有明显问题，修正后数值属于“中间口径”，不是 strict paper-grade reference 结果。

**在总体进程中的作用**
- 这些文档把 strict `80x80` 传统网格求解线从“启动方案”推进成了“失败证据闭环”：启动器、watcher、failed checkpoint、GMRES callback 和 rejected diagnostics 都已经能说明失败不是偶发现象。
- 当前最有价值的产出不是 strict reference 数据本身，而是定位了下一步应集中在非线性 solver 方法上，而不是继续盲目堆参数或重复长跑。
- 对 Example 5 而言，这条线说明 `interpolated_80x80_from20` 只能作为 pipeline validation 或中间参考，不能替代 strict `80x80` paper-grade reference。

**总体进程中仍未完成**
- strict `80x80` reference solver 方法改造。
- line search 每个 `alpha` 的完整 `trial_norm` 序列记录。
- 每次 Newton 迭代 `norm_R` 序列记录。
- `dU` 范数、最大绝对值、温度 floor 或负温度触发情况记录。
- JFNK finite-difference epsilon 尺度检查。
- 更稳健 damping/line search、显式 sparse/block Jacobian 或物理块预条件器方案评估。
- 32x32 成功路径与 80x80 失败路径的 residual、dt、line-search 行为对比。
- 当前工作区改动的归类：哪些是应保留的诊断代码，哪些是实验输出或临时 summary，哪些不应提交。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- Example 5 已完整跑完：先不要修改、覆盖、删除或重跑它的产物；判断时必须区分 `70`、`400`、`700` 阶段。
- `runs/overnight_current` 中已有 checkpoint、日志、metrics、reports、figures 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- strict 80x80 失败证据目录应保留，不要删除或覆盖：
  - `reference_solver_outputs/aei70_krar_80_strict_20260525`
  - `reference_solver_outputs/aei70_krar_80_diag_newton16_gmres300_20260525`
  - `reference_solver_outputs/aei70_krar_80_gmrescb_diag_20260525`

**下一步建议**
1. 最安全的下一步：不要启动任何 strict 80x80 新 run，也不要启动 Segment 2；先做只读代码审查，定位 JFNK residual、line search、finite-difference JVP、变量 floor/约束和 dt reject 逻辑。
2. 增加诊断：记录每个 line-search `alpha` 的 `trial_norm` 序列、Newton residual 序列、`dU` 范数和温度 floor/负值触发情况。
3. 做小规模对照：用已能成功的低分辨率路径和 80x80 失败路径比较同一物理时间附近的 residual/dt/line-search 轨迹。
4. 再决定方法改造：优先考虑更稳健 damping/line search，其次检查 JFNK epsilon 和预条件器；若 matrix-free 路线仍不稳，再评估 sparse/block Jacobian 或物理块预条件。
5. 单独整理当前工作区改动，不要 `git add .`；`reference_solver_outputs` 下的大文件和 checkpoint/logs 仍应排除。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-28-aei70-80-doc-analysis-summary.md`

**需要确认**
- 用户是否希望下一步优先做 solver 方法改造，还是先继续 Example 5 误差静态排查。
- 当前工作区中 2026-05-28 已出现的新改动是否与 strict 80x80 线有关，需要单独审查确认。
- 是否需要把已有诊断代码整理成可提交补丁，并将 `reference_solver_outputs` 大输出明确排除。
