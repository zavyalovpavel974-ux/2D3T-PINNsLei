# Codex App Automation Prompt: 后台实验每小时状态检查

请每 1 小时执行一次本 prompt，用于检查指定后台实验状态。

将 `<run-name>` 替换为需要检查的 run-name。不要使用 `overnight_current` 作为新实验输出目标；`runs/overnight_current` 是冻结实验目录，默认只读。

## 必须执行的检查命令

```powershell
python repro_background.py status --run-name <run-name>
python repro_status.py --run-name <run-name>
```

## 判断与汇报规则

1. 如果任务仍在运行，且没有发现异常关键词，只做简短状态记录，包含：
   - 检查时间；
   - run-name；
   - 当前状态；
   - PID；
   - 日志路径；
   - checkpoint 路径；
   - 下一次建议检查时间。

2. 如果任务已经结束、失败、需要确认，或输出/日志中出现以下任一关键词，必须使用 `process-summary` skill 汇报：
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

3. 使用 `process-summary` skill 汇报时，必须包含：
   - 本轮运行状态；
   - 本次进程概述；
   - 取得的成果；
   - 续跑状态与检查点；
   - 遇到的阻碍；
   - 未完成的部分；
   - 在总体进程中的作用；
   - 总体进程中仍未完成；
   - 受保护产物；
   - 下一步建议；
   - 需要确认。

## 禁止操作

- 不自动重启训练。
- 不启动新的训练。
- 不写入 `runs/overnight_current`。
- 不删除、不移动、不覆盖任何 checkpoint、日志、metrics 或结果。
- 不同时启动多个写入同一 `run-name` 的进程。
- 不猜测实验结果；不确定时写“需要确认”。
