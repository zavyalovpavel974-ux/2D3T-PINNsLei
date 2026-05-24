# Project Rules

本文件是本项目的 Codex/agent 级操作规则。执行任何实验、检查、汇报或自动化任务前，必须优先遵守本文件。

## 冻结实验目录

- `runs/overnight_current` 是冻结实验目录，默认只读。
- 不得移动、删除、覆盖或继续写入 `runs/overnight_current`。
- 不得修改、删除或覆盖 `runs/overnight_current` 内的 checkpoint、日志、metrics、reports 或结果文件。
- 如需验证写入保护，只能使用不会落盘的 dry-run 或只读状态命令。

## 已完成实验

- Example 2 已完成，默认不得重跑。
- Example 5 已完成，默认不得重跑。
- Example 5 必须区分 `70`、`400`、`700` 三个阶段，不得把阶段状态混在一起判断。
- 后续任何实验必须使用新的 `run-name` 和新的输出目录。
- 不得同时启动多个写入同一 `run-name` 的进程。

## 长时间实验与后台运行

- 长时间实验优先使用后台运行或分段 `walltime`。
- 启动后台任务后，必须在回复中返回：
  - PID；
  - stdout/stderr 日志路径；
  - checkpoint 路径；
  - 状态检查命令；
  - 停止命令。
- 检查后台任务时，必须运行以下至少一个命令：
  - `python repro_background.py status --run-name <run-name>`
  - `python repro_status.py --run-name <run-name>`
- 不得自动重启失败、结束或需要确认的训练任务，除非用户明确要求。

## 状态审查与汇报

- 如果状态、日志或输出中出现以下任一状态或关键词，必须使用 `process-summary` skill 做结构化中文汇报：
  - `FINISHED`
  - `FAILED`
  - `NEED_CONFIRM`
  - `walltime`
  - `error`
  - `traceback`
  - `exception`
  - `nan`
  - `killed`
  - `completed`
  - `finished`
- 汇报时必须区分“已确认事实”和“需要确认”的内容。
- 不确定时写“需要确认”，不得猜测实验结果。

## 文件编码

- 读取中文 `SKILL.md` 时必须使用 UTF-8。
- 新增中文 Markdown 或 skill 文件时，优先保存为 UTF-8 无 BOM。
