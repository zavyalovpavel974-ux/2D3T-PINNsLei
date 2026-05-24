---
name: process-summary
description: Summarize an experiment, training command, code modification task, long-running job, or staged reproduction run after it completes, times out, is interrupted, fails, or remains running, then save the same report as a Markdown document. Use after long experiment commands, especially multi-stage training such as Example 5 with 70/400/700 stages and checkpoint continuation from runs/overnight_current, to report status, artifacts, blockers, safe resume commands, protected outputs, remaining work, and the path of the saved .md report. Prefer Chinese output.
---

# Process Summary

## Overview

Produce a structured end-of-run report for experiments, training jobs, code work, and long-running reproduction tasks, and save the same report as a Markdown document. Prioritize whether the job can be safely resumed, from which checkpoint, what must not be touched, and where the report file was written.

## Workflow

1. Collect the concrete evidence first: executed command, terminal output, walltime setting, elapsed time, exit code, logs, changed files, generated artifacts, checkpoints, and user-provided constraints.
2. Classify the run status as normal completion, walltime limit, outer-tool interruption, error failure, still running, or "需要确认".
3. For long training runs, identify the resume state before summarizing anything else: checkpoint path, experiment stage, current step or optimizer phase, completed stages, and next safe resume command.
4. Separate facts, inference, and unknowns. Do not invent metrics, durations, stages, results, files, or causes.
5. Preserve protected artifacts. Treat completed Example 2 outputs and existing `runs/overnight_current` checkpoints/results as read-only unless the user explicitly asks otherwise.
6. Summarize the current run first, then explain how it affects the broader reproduction or research process.
7. After sending the report in chat, also write the same content to a `.md` file and include the saved path in the chat response.

## Required Sections

Include these sections unless the user explicitly requests a different format:

- `本轮运行状态`: State whether the command completed normally, hit walltime, was interrupted by an outer tool, failed with an error, is still running, or needs confirmation. Include the actual command, walltime limit, elapsed time, and exit reason. If any item cannot be confirmed, write `需要确认`.
- `本次进程概述`: Briefly explain what this run or work session tried to accomplish, why it was done, and the current state.
- `取得的成果`: List completed stages, code changes, validation results, output files, log conclusions, checkpoint updates, and confirmed experimental results. Base every item on actual files, logs, command output, or user-provided information.
- `续跑状态与检查点`: For long training jobs, include checkpoint path, current experiment stage, current step or optimizer phase, completed stages, next safe resume command, and dangerous operations to avoid. For Example 5, explicitly distinguish whether the checkpoint belongs to the 70, 400, or 700 stage. If the stage cannot be confirmed, write `需要确认`.
- `遇到的阻碍`: List technical blockers, errors, environment issues, timeouts, outer-tool termination, missing logs, incomplete checkpoint information, or unverified results.
- `未完成的部分`: List only work unfinished inside this run or this experiment command.
- `在总体进程中的作用`: Explain how this run contributes to the larger reproduction or research workflow, such as advancing a stage, validating resume logic, exposing risk, establishing a baseline, generating final results, or supplying report data.
- `总体进程中仍未完成`: List broader unfinished work, such as whether Example 5 is fully complete, whether final results are extracted, whether figures are generated, whether Example 2 and Example 5 are compared, whether the reproduction report is updated, and whether logs/errors still need verification.
- `受保护产物`: List user-protected files or outputs. Always include that Example 2 has completed and its outputs must not be modified, overwritten, deleted, or rerun for now. Also state that existing checkpoints and result files under `runs/overnight_current` must not be deleted or overwritten unless the user explicitly requests it.
- `下一步建议`: List next actions in dependency order. The first item must be the most direct and safest next step. For long experiments, include a directly copyable resume command when enough information is available; otherwise state what must be checked first.
- `Markdown 文档`: State the path of the `.md` report saved after the chat summary. If the file could not be written, state the reason.
- `需要确认`: List only important gaps that affect judgment. Omit this section when there are no important gaps.

## Markdown Document Output

- Always save a Markdown copy of the final report after producing the chat response.
- Use the same structure and content as the chat report; do not create a shortened or divergent version.
- Prefer a user-specified report path when one is given.
- If no path is specified, create a non-destructive report folder such as `process-summaries/` in the current workspace or repository root.
- Use a filename that includes the date/time and a short task label, for example `2026-05-24-example5-stage400-summary.md`.
- Do not write the report by overwriting logs, checkpoints, result files, or protected artifacts.
- Do not place the report inside `runs/overnight_current` unless the user explicitly asks for that location.
- Include the saved report path in the final chat output under `Markdown 文档`.

## Style

- Write in Chinese by default.
- Be concise, operational, and easy to scan.
- Use bullets; avoid empty praise and vague progress language.
- Clearly distinguish facts, inference, and `需要确认`.
- Never fabricate experimental results, elapsed time, metrics, files, logs, checkpoints, stage numbers, or completion status.
- Include concrete commands, paths, stage numbers, checkpoints, logs, and metrics whenever available.
- For long training jobs, lead with whether safe resume is possible and where to resume from.
- Treat Example 2 outputs as protected unless the user explicitly changes that instruction.
- Treat `runs/overnight_current` checkpoint and result files as protected from deletion or overwrite by default.
- Save a same-content Markdown report and mention its path.

## Output Template

````markdown
**本轮运行状态**
- 状态：[正常完成 / 达到 walltime 上限 / 被中断 / 报错失败 / 仍在运行 / 需要确认]
- 命令：`[实际执行命令]`
- walltime 上限：[可获得则填写，否则写需要确认]
- 运行时长：[可获得则填写，否则写需要确认]
- 退出原因：[正常完成 / 达到 max-walltime / 外层工具中断 / 报错 / 需要确认]

**本次进程概述**
[说明本次实验/进程的目标、范围和当前状态。]

**取得的成果**
- [成果 1]
- [成果 2]

**续跑状态与检查点**
- 当前 checkpoint：`[路径 / 需要确认]`
- 当前阶段：[例如 70 / 400 / 700 / 需要确认]
- 当前步数或优化器阶段：[如 Adam 第 xxxx 步 / L-BFGS / 需要确认]
- 已完成阶段：[列出已完成阶段 / 需要确认]
- 下一次安全续跑命令：
  ```powershell
  [命令；如条件不足，写“需要先确认 checkpoint 阶段/路径/命令参数”]
  ```
- 不应执行的危险操作：
  - 不要删除或覆盖 `runs/overnight_current` 中已有 checkpoint 和结果文件，除非用户明确要求。
  - 不要把 Example 5 的 70/400/700 阶段 checkpoint 误加载到错误阶段。
  - 不要修改、覆盖、删除或重跑 Example 2 已完成产物，除非用户明确要求。

**遇到的阻碍**
- [阻碍 1]
- [阻碍 2]

**未完成的部分**
- [本轮命令或本次实验内部尚未完成的事项]

**在总体进程中的作用**
- [说明本次运行如何推进总体复现/研究流程]

**总体进程中仍未完成**
- [例如 Example 5 是否完整结束 / 最终结果是否提取 / 图表是否生成 / Example 2 与 Example 5 是否完成对比 / reproduction report 是否更新 / 是否还需重新验证日志和误差]

**受保护产物**
- Example 2 已完整跑完：先不要修改、覆盖、删除或重跑它的产物。
- `runs/overnight_current` 中已有 checkpoint 和结果文件：默认不得删除或覆盖，除非用户明确要求。
- [其他用户明确要求保护的产物]

**下一步建议**
1. [最直接、最安全的下一步；长实验优先给出续跑命令或说明需要先检查什么]
2. [后续动作]

**Markdown 文档**
- 已保存：`[报告 .md 路径 / 写入失败原因]`

**需要确认**
- [只列出会影响判断的重要缺口；没有重要缺口时省略本节]
````
