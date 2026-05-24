---
name: process-summary
description: Use this skill after long experiments, background runs, status checks, interruptions, failures, completions, or checkpoint/resume inspections to produce a structured Chinese progress report for the reproduction workflow.
---

# Process Summary Skill

## Purpose

本 skill 用于长时间实验、后台任务、状态检查、失败、中断、完成、checkpoint/resume 检查之后，生成结构化中文进程汇报。

适用场景包括：

- `repro_runner.py` 运行结束、失败、中断或超时；
- `repro_background.py status` 检查后台任务；
- `repro_status.py` 检查实验目录；
- Example 2 / Example 5 训练、续跑、静态审查；
- reference solver 小规模或正式验证；
- checkpoint、日志、metrics、reports 的状态检查；
- 用户询问“现在进行到哪一步”“下一步做什么”“能否安全续跑”。

## Required Sections

每次汇报必须包含以下栏目。

### 1. 本轮运行状态

说明本轮是：

- 正常完成；
- 仍在运行；
- 已停止；
- 失败；
- 超时；
- 需要确认。

必须写清楚实际运行或检查的命令。若没有启动训练，也必须明确说明“本轮未启动训练”。

### 2. 本次进程概述

概括本轮做了什么，包括：

- 检查了哪些文件；
- 运行了哪些轻量命令；
- 是否读取了 checkpoint、logs、metrics；
- 是否进行了代码修改；
- 是否产生新文件。

### 3. 取得的成果

列出已经确认的事实，不得虚构结果。

例如：

- `runs/overnight_current` 是否存在；
- `Protected` 是否为 True；
- Example 2 是否 completed；
- Example 5 当前阶段是否为 70、400 或 700；
- checkpoint 是否存在；
- metrics / logs / figures 是否存在；
- 轻量检查是否通过。

### 4. 续跑状态与检查点

必须说明：

- checkpoint 路径；
- checkpoint 是否存在；
- 当前阶段；
- 当前 step；
- 是否可以安全续跑；
- 下一次安全续跑命令。

如果不能确认，必须写“需要确认”。

### 5. 遇到的阻碍

列出阻碍和证据，例如：

- Git 分支不一致；
- 文件缺失；
- 权限问题；
- checkpoint 缺失；
- 日志异常；
- error / traceback / nan / killed；
- reference solver 不支持 resume；
- 自动审查配置未补齐。

### 6. 未完成的部分

列出本轮尚未完成的任务。

不得把未完成项写成已完成。

### 7. 在总体进程中的作用

说明本轮对总体复现流程的意义，例如：

- 冻结旧实验；
- 验证防覆盖；
- 建立后台检查机制；
- 为严格参考解验证做准备；
- 排查 Example 5 误差异常。

### 8. 总体进程中仍未完成

说明整个项目仍未完成的事项，例如：

- 严格 80x80 参考解；
- reference solver checkpoint/resume 验证；
- 严格参考解下 Example 2 重跑；
- 严格参考解下 Example 5 重跑；
- Example 5 误差异常原因确认；
- 最终论文级复现报告。

### 9. 受保护产物

必须列出不可写入、不可覆盖、不可删除的产物。

当前默认包括：

- `runs/overnight_current`
- Example 2 已完成产物；
- Example 5 已完成产物；
- `checkpoints`
- `logs`
- `reports`
- `metrics`
- `figures`

必须提醒：后续新实验使用新的 `--run-name`。

### 10. 下一步建议

给出下一步操作，必须具体、可执行。

如果存在风险，必须先建议轻量检查，不得直接建议启动长跑。

### 11. 需要确认

列出仍需要用户确认的事项。

如果没有需要确认的事项，写“暂无”。

## Style Requirements

- 使用中文。
- 用事实、路径、命令说话。
- 区分“已确认事实”“推断”“需要确认”。
- 不得虚构实验结果、指标、checkpoint 或日志内容。
- 不确定时写“需要确认”。
- 不得建议写入 `runs/overnight_current`。
- 不得建议覆盖旧 checkpoint。
- 不得自动重启训练。
- 对 Example 5 必须区分 70、400、700 阶段。
- 读取中文文件时使用 UTF-8。