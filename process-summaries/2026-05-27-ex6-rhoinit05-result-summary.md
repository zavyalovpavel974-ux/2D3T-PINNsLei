# Ex6 rho_init=0.5 运行与对比总结

**本轮运行状态**
- 状态：正常完成，但中途经历过外层工具超时、分段 walltime 续跑、一次 L-BFGS 续跑状态修正。
- 主要完成命令：`python .\repro_runner.py --case example6 --run-name ex6_rhoinit05_seed12_20260527 --rho-init 0.5 --seed 12 --allow-existing-run`
- 最终命令 walltime 上限：无脚本内 walltime 上限。
- 最终命令运行时长：`7892.5649s`；metrics 内训练时间为 `7886.3224s`。
- 最终退出原因：正常完成，`example6_run_result.json` 中 `returncode=0`，并写出 `example6_metrics.json`。
- 中途状态：早期一次前台命令被外层工具 300s timeout 中断；随后多次用 `--max-walltime-seconds 180/300` 分段续跑并保存 checkpoint。

**本次进程概述**
本轮目标是按用户要求对 Ex6 反演任务使用 `rho_init=0.5` 跑出结果，并与冻结基线和论文 Table 12 对比。运行目录为 `runs/ex6_rhoinit05_seed12_20260527`，没有写入或覆盖 `runs/overnight_current`。

**取得的成果**
- 新 run 已完成：`C:\Users\12412\Documents\Lei_code\runs\ex6_rhoinit05_seed12_20260527`。
- 最终指标文件：`C:\Users\12412\Documents\Lei_code\runs\ex6_rhoinit05_seed12_20260527\reports\example6_metrics.json`。
- 最终 run result：`C:\Users\12412\Documents\Lei_code\runs\ex6_rhoinit05_seed12_20260527\reports\example6_run_result.json`。
- 最终 checkpoint：`C:\Users\12412\Documents\Lei_code\runs\ex6_rhoinit05_seed12_20260527\checkpoints\example6\latest.pt`，状态为 `phase=completed`。
- 本轮 `rho_init=0.5` 结果：`rho=1.068574358324482`，相对真值 `1.1` 的误差为 `2.8569%`。
- 冻结基线 `runs/overnight_current` 中 legacy inverse 结果：`rho=1.102853289967324`，相对误差 `0.2594%`。
- 论文 Table 12：初始 `rho=0.5` 时论文给出 `rho=1.11737`，相对误差约 `1.579%`；初始 `rho=1` 时论文给出 `rho=1.11717`，相对误差约 `1.561%`。
- 对比结论：本轮 `rho_init=0.5` 结果差于冻结基线，也差于论文 Table 12 的 `rho_init=0.5` 结果。
- 辅助场误差 full-grid：Te L2 `0.0243463`，Ti L2 `0.0260892`，Tr L2 `0.0269472`。
- 辅助 held-out 场误差：Te L2 `0.0243811`，Ti L2 `0.0261060`，Tr L2 `0.0270158`。这些仅作为 Ex6 辅助诊断，不作为主成败指标。

**续跑状态与检查点**
- 当前 checkpoint：`C:\Users\12412\Documents\Lei_code\runs\ex6_rhoinit05_seed12_20260527\checkpoints\example6\latest.pt`。
- 当前阶段：Ex6 inverse，已完成。
- 当前步数或优化器阶段：`phase=completed`，`repro_status.py` 显示 step `6001`；L-BFGS 日志自然推进到约 `It: 33200` 后写出 metrics。
- 已完成阶段：Adam 与 L-BFGS 均已完成。
- 下一次安全检查命令：
  ```powershell
  python .\repro_status.py --run-name ex6_rhoinit05_seed12_20260527
  ```
- 不应执行的危险操作：
  - 不要删除或覆盖 `runs/overnight_current` 中已有 checkpoint 和结果文件，除非用户明确要求。
  - 不要修改、覆盖、删除或重跑 Example 2 已完成产物，除非用户明确要求。
  - 不要把本轮 `rho_init=0.5` 结果直接覆盖冻结基线。

**遇到的阻碍**
- `repro_background.py status` 在 Windows 上触发 `os.kill(pid, 0)` 兼容性异常，不能可靠判断后台 PID。
- `repro_background.py start` 启动的后台进程很快退出且没有留下有效 stdout/stderr，因此改用前台分段和最终长窗口运行。
- L-BFGS 在分段中断后，旧 checkpoint 把 L-BFGS closure step 误标为 `phase=adam`，存在续跑回 Adam 的风险。
- 一次恢复 L-BFGS optimizer 半截状态时触发 `TypeError: sub(): argument 'other' must be Tensor, not NoneType`。已修正为：L-BFGS/`lbfgs_start` 阶段恢复时跳过半截 L-BFGS optimizer state，只恢复模型参数并重新初始化 L-BFGS optimizer。
- stderr 中保留了早期 walltime 和 TypeError traceback；最终 run result 已确认 `returncode=0`，最终 metrics 已写出。

**未完成的部分**
- 本轮用户要求的 `rho_init=0.5` 结果与对比已完成。
- 若要获得严格单次 uninterrupted 口径，需要另开新 run-name，用修正后的 L-BFGS checkpoint 逻辑从头完整跑一次；本轮结果包含分段续跑和一次 checkpoint 元数据修正，不能视为最干净的单次训练口径。

**在总体进程中的作用**
- 本轮验证了 `rho_init=0.5` 对 Ex6 反演结果的影响：在当前插值参考解和当前训练路径下，最终 rho 误差为 `2.8569%`，未优于冻结基线。
- 本轮也暴露并修复了 runner 续跑 Ex6 L-BFGS 阶段时的阶段标记问题，提升后续长实验续跑安全性。

**总体进程中仍未完成**
- 尚未做多 seed 的 `rho_init=0.5` 稳定性统计。
- 尚未做一个全新 run-name 的 clean single-shot `rho_init=0.5` 复核。
- 阶段性复现报告可加入本轮对比结论，但需要明确“本轮为分段续跑后完成，不是严格单次 uninterrupted run”。
- `repro_background.py` 的 Windows PID/status 问题仍可后续修。

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- 本轮新结果目录 `runs/ex6_rhoinit05_seed12_20260527` 已生成，应作为本轮对比证据保留。

**下一步建议**
1. 将本轮结果写入阶段报告：`rho_init=0.5` 最终 `rho=1.068574`，误差 `2.8569%`，低于冻结基线质量。
2. 若要排除分段续跑影响，用新 run-name 做一次 clean single-shot 复核：
   ```powershell
   python .\repro_runner.py --case example6 --run-name ex6_rhoinit05_seed12_clean --rho-init 0.5 --seed 12
   ```
3. 修复 `repro_background.py` 的 Windows PID/status 兼容性问题，再用于长任务后台运行。

**Markdown 文档**
- 已保存：`C:\Users\12412\Documents\Lei_code\process-summaries\2026-05-27-ex6-rhoinit05-result-summary.md`

**需要确认**
- 是否需要把 clean single-shot `rho_init=0.5` 作为最终报告口径。目前本轮完成结果可用，但包含分段续跑和一次 checkpoint 元数据修正。
