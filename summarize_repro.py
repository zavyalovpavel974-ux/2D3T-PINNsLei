#!/usr/bin/env python
"""Build the final reproduction comparison report from runner artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path


PAPER = {
    "example2": {
        "Te": {"L2": 1.446e-2, "L1": 5.388e-3, "Linf": 1.684e-2},
        "Ti": {"L2": 7.902e-3, "L1": 1.153e-3, "Linf": 3.742e-3},
        "Tr": {"L2": 1.588e-2, "L1": 1.436e-2, "Linf": 4.834e-2},
    },
    "example5": {
        "Te": {"L2": 1.485e-2, "L1": 8.224e-3, "Linf": 1.547e-2},
        "Ti": {"L2": 1.738e-2, "L1": 8.504e-3, "Linf": 1.552e-2},
        "Tr": {"L2": 4.216e-3, "L1": 7.507e-3, "Linf": 1.370e-2},
    },
}

PAPER_TIMES = {
    "numerical_solution": 2588.4,
    "70": 7787.4,
    "400": 7553.4,
    "700": 7482.4,
    "total": 22823.2,
    "inference": 0.005,
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_inverse_metrics(reports: Path) -> tuple[str, dict, dict]:
    example6_metrics = reports / "example6_metrics.json"
    if example6_metrics.exists():
        return (
            "Example 6 inverse on Example 2 parameters",
            load_json(example6_metrics),
            load_json(reports / "example6_run_result.json"),
        )
    return (
        "Example 6 inverse on Example 2 parameters (legacy example2 artifact names)",
        load_json(reports / "example2_metrics.json"),
        load_json(reports / "example2_run_result.json"),
    )


def fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3e}"


def pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{100 * value:.1f}%"


def rel(value: float | None, target: float | None) -> float | None:
    if value is None or target in (None, 0):
        return None
    return abs(value - target) / abs(target)


def same_order(value: float | None, target: float | None) -> str:
    if value is None or target in (None, 0):
        return "n/a"
    ratio = max(abs(value / target), abs(target / value)) if value else float("inf")
    return "yes" if ratio <= 10 else "no"


def error_table(metrics: dict, paper_case: str) -> list[str]:
    lines = [
        "| Variable | Metric | This run | Paper | Relative difference | Same order |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    aggregate = metrics.get("aggregate", {})
    for var in ("Te", "Ti", "Tr"):
        for metric in ("L2", "L1", "Linf"):
            value = aggregate.get(var, {}).get(metric)
            target = PAPER[paper_case][var][metric]
            lines.append(
                f"| {var} | {metric} | {fmt(value)} | {fmt(target)} | {pct(rel(value, target))} | {same_order(value, target)} |"
            )
    return lines


def parse_example5_stage_times(stdout_path: Path) -> dict[str, float]:
    text = stdout_path.read_text(encoding="utf-8", errors="ignore")
    times = [float(x) for x in re.findall(r"(?<!Total )Training time: ([0-9.]+)", text)]
    stages = ["70", "400", "700"]
    return {stage: times[i] for i, stage in enumerate(stages) if i < len(times)}


def main() -> None:
    run_dir = Path("runs") / "overnight_current"
    reports = run_dir / "reports"
    inverse_label, inverse_metrics, inverse_result = load_inverse_metrics(reports)
    example5 = load_json(reports / "example5_metrics.json")
    ex5_result = load_json(reports / "example5_run_result.json")
    stage_times = parse_example5_stage_times(run_dir / "logs" / "example5.stdout.log")
    total_stage_time = sum(stage_times.values())

    lines = [
        "# Final Reproduction Report",
        "",
        f"Run directory: `{run_dir}`",
        "",
        "Reference mode: interpolated `80x80_from20` validation data. This is a current-result verification run, not a strict paper-grade reproduction with independently generated `80x80` numerical reference data.",
        "",
        "Paper baseline: DOI `10.1016/j.cpc.2025.109572`.",
        "",
        "## Status",
        "",
        f"- {inverse_label} run completed with return code `{inverse_result['returncode']}`.",
        f"- Example 5 transfer run completed with return code `{ex5_result['returncode']}` after checkpoint/resume across the three stages.",
        "- All 11 `sol1_*.txt` inputs were validated as author-format `80x80` files with `19202` lines.",
        "",
        "## Example 6: Table 12 Density",
        "",
        "| Case | rho | Relative error vs 1.1 |",
        "| --- | ---: | ---: |",
        f"| This run, rho_init={inverse_metrics.get('rho_init', 'n/a')} | {inverse_metrics['rho']:.5f} | {100 * inverse_metrics['rho_rel_error']:.3f}% |",
        "| Paper, initial rho=0.5 | 1.11737 | 1.579% |",
        "| Paper, initial rho=1 | 1.11717 | 1.561% |",
        "",
        "The density inversion is the primary Example 6 metric. Field errors are auxiliary diagnostics for this inverse run, not the main success criterion.",
        "",
        "## Auxiliary Field Diagnostics On Example 2 Parameters",
        "",
    ]
    lines += error_table(inverse_metrics, "example2")
    lines += [
        "",
        "These field errors are retained for diagnostics only because the inverse training objective differs from the Example 2 forward solve.",
        "",
        "## Example 5: Table 9 Errors",
        "",
    ]
    lines += error_table(example5, "example5")
    lines += [
        "",
        "Example 5 did not reproduce the paper-scale errors. The final aggregate errors are roughly `0.67-1.05` in absolute/relative terms where the paper reports `~0.004-0.017`, so this run should be treated as a failed current-data reproduction for Example 5.",
        "",
        "## Example 5: Table 11 Timing",
        "",
        "| Item | This run | Paper | Relative difference |",
        "| --- | ---: | ---: | ---: |",
        f"| Numerical solution | n/a | {PAPER_TIMES['numerical_solution']:.1f}s | n/a |",
    ]
    for stage in ("70", "400", "700"):
        value = stage_times.get(stage)
        lines.append(f"| Training Aei={stage} | {value:.1f}s | {PAPER_TIMES[stage]:.1f}s | {pct(rel(value, PAPER_TIMES[stage]))} |")
    lines += [
        f"| Total training | {total_stage_time:.1f}s | {PAPER_TIMES['total']:.1f}s | {pct(rel(total_stage_time, PAPER_TIMES['total']))} |",
        f"| Inference | {example5['inference_time_seconds']:.4f}s | {PAPER_TIMES['inference']:.3f}s | {pct(rel(example5['inference_time_seconds'], PAPER_TIMES['inference']))} |",
        "",
        "## Artifacts",
        "",
        f"- Example 6/inverse metrics: `{reports / ('example6_metrics.json' if (reports / 'example6_metrics.json').exists() else 'example2_metrics.json')}`",
        f"- Example 5 metrics: `{reports / 'example5_metrics.json'}`",
        f"- Logs: `{run_dir / 'logs'}`",
        f"- Checkpoints: `{run_dir / 'checkpoints'}`",
        f"- Figures and final models: `{run_dir / 'workdir' / 'figures'}`",
        "",
        "## Interpretation",
        "",
        "Example 6/inverse supports the current engineering changes: isolated execution, checkpointing, JSON metrics, final figures, and Table 12 density parsing all work. Its density estimate is the main result; field errors are auxiliary diagnostics.",
        "",
        "Example 5 is complete but not successful as a numerical reproduction. The most likely contributors are the interpolated `80x80_from20` reference data, the interrupted-and-resumed transfer workflow, and sensitivity of this training setup to optimizer state, precision, hardware, and reference-data fidelity. The next scientifically meaningful step is to finish a strict `80x80` traditional reference solver and rerun the same harness from a clean run directory.",
        "",
    ]

    out = reports / "final_reproduction_report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
