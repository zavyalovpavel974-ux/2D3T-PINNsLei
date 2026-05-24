**本轮运行状态**
- 状态：正常完成
- 命令：
  - `git status --short --branch`
  - `python .\recalc_example5_metrics_per_time_reference.py --run-dir .\runs\overnight_current --out-dir .\reference_solver_outputs\example5_static_recalc --check-only`
  - `python .\recalc_example5_metrics_per_time_reference.py --run-dir .\runs\overnight_current --out-dir .\reference_solver_outputs\example5_static_recalc --require-t1-match`
  - `python .\repro_status.py --run-name overnight_current`
  - `python .\repro_background.py status --run-name overnight_current`
  - `git status --short --branch`
- walltime 上限：未设置，本轮未启动训练或后台长任务
- 运行时长：复算命令约 4.4 秒；其余为轻量检查
- 退出原因：正常完成

**本次进程概述**
本轮针对 Example 5 后处理误差计算中五个时间点 reference txt 的读取逻辑做静态确认，并新增只读复算脚本。脚本只读取冻结产物 `runs/overnight_current`，将修正后的 metrics 写入独立目录 `reference_solver_outputs/example5_static_recalc`。

**取得的成果**
- 新增 `recalc_example5_metrics_per_time_reference.py`。
- 确认 `2D3T_wei_aei700_wer_krartr_time.py` 中五个误差时间点均读取了 `sol1_wei_aei700_wer_krartr_80_1.txt`。
- 确认五个时间点 reference 文件映射：
  - `1e-5` -> `sol1_wei_aei700_wer_krartr_1e-5.txt`
  - `0.3` -> `sol1_wei_aei700_wer_krartr_0p3.txt`
  - `0.5` -> `sol1_wei_aei700_wer_krartr_0p5.txt`
  - `0.7` -> `sol1_wei_aei700_wer_krartr_0p7.txt`
  - `1.0` -> `sol1_wei_aei700_wer_krartr_1.txt`
- 确认 `sol1_wei_aei700_wer_krartr_80_1.txt` 与 `sol1_wei_aei700_wer_krartr_1.txt` 的 SHA256 相同。
- 确认 txt 原始变量顺序为 `(Tr, Te, Ti)`，沿用作者脚本的 `Data[:, :, (1, 2, 0)]` 映射为 `(Te, Ti, Tr)`，未修改变量顺序。
- t=1 自校验通过：原始 metrics 与重建模型复算 t=1 的最大绝对差为 `0.0`，说明冻结 checkpoint 的只读模型重建路径可复现原后处理。
- 修正后 aggregate metrics：
  - Te：L2 `0.19572747671859334`，L1 `0.04487529123587871`，Linf `0.18573869898024487`
  - Ti：L2 `0.2065726907818897`，L1 `0.041266198222607645`，Linf `0.16624924910151673`
  - Tr：L2 `0.16322007657200582`，L1 `0.11786110872174765`，Linf `0.5978782699339196`
- 对比原 aggregate，修正后明显降低：
  - Te：L2 `-0.5092339861472621`，L1 `-0.31760673285998886`，Linf `-0.4634198356774639`
  - Ti：L2 `-0.5015343407936252`，L1 `-0.2772245782951142`，Linf `-0.41027690539729333`
  - Tr：L2 `-0.5054690305667391`，L1 `-0.9321530006797081`，Linf `-1.40212992888567`

**续跑状态与检查点**
- 本轮未启动训练、未启动后台进程、未重跑 Example 2、未重跑 Example 5。
- `runs/overnight_current/checkpoints/example5/latest.pt` 只读加载，确认 checkpoint metadata 为 Example 5 stage `700`、phase `completed`、step `6001`。
- `runs/overnight_current/checkpoints/example2/latest.pt` 仍为 completed，step `6001`。
- 不存在需要续跑的本轮训练进程。

**遇到的阻碍**
- 运行复算脚本时 PyTorch 输出了一个已有代码中的 `SyntaxWarning` 和一个 tensor 标量转换 warning；它们未阻止复算，且 t=1 自校验为 0 差异。
- 修正后的 metrics 仍基于当前本地 per-time reference txt 文件，不等同于已完成严格论文级 80x80 参考解验证。

**未完成的部分**
- 未修改 `2D3T_wei_aei700_wer_krartr_time.py` 的训练/后处理主脚本。
- 未提交新增脚本。
- 未生成严格论文级 80x80 reference solver 正式解。

**在总体进程中的作用**
本轮把 Example 5 原 metrics 中“早期时间点误用 t=1 reference 文件”的问题从静态怀疑推进为已验证事实，并给出只读复算 metrics。由于 t=1 自校验精确匹配，修正主要影响 reference 文件选择，而不是模型重建或变量映射。

**总体进程中仍未完成**
- 严格 80x80 reference solver 正式求解仍未启动。
- Example 5 与严格 80x80 reference 的最终论文级 metrics 仍未确认。
- 是否将只读复算脚本纳入版本控制需要用户确认。

**受保护产物**
- `runs/overnight_current` 仍为 Protected=True。
- Example 2 已完成，其 checkpoint、logs、metrics、reports、figures 不得修改、覆盖、删除或重跑。
- Example 5 stage 700 已完成，其 checkpoint、logs、metrics、reports、figures 不得修改、覆盖、删除或重跑。
- 本轮未写入、删除、移动或覆盖 `runs/overnight_current` 下任何文件。

**下一步建议**
- 先决定是否提交 `recalc_example5_metrics_per_time_reference.py`。
- 若要让主脚本后处理也避免再次犯同类错误，可单独小改 `2D3T_wei_aei700_wer_krartr_time.py` 的五个 reference 文件读取路径，但仍不触碰训练逻辑、模型结构和 checkpoint 加载逻辑。
- 之后可以进入严格参考解链路：使用新的输出目录和 run-name，先做小规模 checkpoint/resume，再启动严格 80x80 正式 reference solver。

**Markdown 文档**
- 本报告已保存到 `process-summaries/2026-05-25-example5-per-time-recalc-summary.md`。

**需要确认**
- 当前 per-time txt 文件是否要作为“修正后但仍非严格论文级”的中间参考口径写入总报告。
- 是否提交新增只读复算脚本。
- 是否需要进一步修改原 Example 5 主脚本的后处理读取路径。
