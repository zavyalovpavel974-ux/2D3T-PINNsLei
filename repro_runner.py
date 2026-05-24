#!/usr/bin/env python
"""Run the current-result reproduction workflow in an isolated directory."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
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


SCRIPT_FILES = [
    "2D3T_wei_aei70_wer_krar_inverse.py",
    "2D3T_wei_aei700_wer_krartr_time.py",
    "sub_2D3T_wei_aei70_wer_krar_inverse.py",
    "sub_2D3T_wei_aei700_wer_krartr_time.py",
]


def now_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def copy_inputs(workdir: Path, data_source: Path) -> list[dict]:
    workdir.mkdir(parents=True, exist_ok=True)
    for name in SCRIPT_FILES:
        shutil.copy2(ROOT / name, workdir / name)
    records = []
    for src in sorted(data_source.glob("sol1_*.txt")):
        dst = workdir / src.name
        shutil.copy2(src, dst)
        records.append({"name": src.name, "lines": count_lines(dst), "bytes": dst.stat().st_size})
    if len(records) != 11:
        raise RuntimeError(f"expected 11 sol1_*.txt files, found {len(records)} in {data_source}")
    bad = [r for r in records if r["lines"] != 19202]
    if bad:
        raise RuntimeError(f"unexpected sol1 file line counts: {bad}")
    return records


def env_info() -> dict:
    code = (
        "import json, sys, torch; "
        "print(json.dumps({'python': sys.version, 'torch': torch.__version__, "
        "'cuda': torch.cuda.is_available(), "
        "'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}))"
    )
    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    out = subprocess.check_output([sys.executable, "-c", code], cwd=ROOT, env=env, text=True)
    return json.loads(out)


def infer_example5_resume_stage(checkpoint: Path, stdout_log: Path) -> int | None:
    try:
        import torch

        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        if payload.get("Aei") is not None:
            return int(float(payload["Aei"]))
    except Exception:
        pass

    if not stdout_log.exists():
        return None
    text = stdout_log.read_text(encoding="utf-8", errors="ignore")
    matches = re.findall(r"^Aei:\s*(\d+)", text, flags=re.MULTILINE)
    if not matches:
        return None
    previous_stage = int(matches[-1])
    stage_after_previous = {0: 70, 70: 400, 400: 700}
    return stage_after_previous.get(previous_stage)


def run_case(run_dir: Path, workdir: Path, case: str, max_walltime: float, max_iter_override: int | None) -> dict:
    logs = run_dir / "logs"
    reports = run_dir / "reports"
    checkpoints = run_dir / "checkpoints" / case
    logs.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    checkpoints.mkdir(parents=True, exist_ok=True)

    if case == "example2":
        script = "2D3T_wei_aei70_wer_krar_inverse.py"
        metrics = reports / "example2_metrics.json"
    elif case == "example5":
        script = "2D3T_wei_aei700_wer_krartr_time.py"
        metrics = reports / "example5_metrics.json"
    else:
        raise ValueError(case)

    cmd = [
        sys.executable,
        "-u",
        script,
        "--checkpoint-dir",
        str(checkpoints),
        "--checkpoint-interval",
        "200",
        "--metrics-json",
        str(metrics),
    ]
    latest = checkpoints / "latest.pt"
    stdout_path = logs / f"{case}.stdout.log"
    stderr_path = logs / f"{case}.stderr.log"
    if latest.exists():
        cmd += ["--resume-checkpoint", str(latest)]
        if case == "example5":
            resume_stage = infer_example5_resume_stage(latest, stdout_path)
            if resume_stage is not None:
                cmd += ["--resume-stage", str(resume_stage)]
    if max_walltime > 0:
        cmd += ["--max-walltime-seconds", str(max_walltime)]
    if max_iter_override is not None:
        cmd += ["--max-iter-override", str(max_iter_override)]

    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    start = time.time()
    with stdout_path.open("a", encoding="utf-8") as stdout, stderr_path.open("a", encoding="utf-8") as stderr:
        stdout.write("\n[repro_runner] command: %s\n" % " ".join(cmd))
        stdout.flush()
        proc = subprocess.run(cmd, cwd=workdir, env=env, stdout=stdout, stderr=stderr, text=True)
    result = {
        "case": case,
        "returncode": proc.returncode,
        "elapsed_seconds": time.time() - start,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "checkpoint": str(latest) if latest.exists() else None,
        "metrics": str(metrics) if metrics.exists() else None,
    }
    (reports / f"{case}_run_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def rel_delta(value: float, target: float) -> float | None:
    if target == 0:
        return None
    return abs(value - target) / abs(target)


def comparison_table(metrics: dict, paper_case: str) -> list[str]:
    lines = ["| Variable | Metric | This run | Paper | Relative difference |", "| --- | --- | ---: | ---: | ---: |"]
    aggregate = metrics.get("aggregate", {})
    for var in ("Te", "Ti", "Tr"):
        for metric in ("L2", "L1", "Linf"):
            value = aggregate.get(var, {}).get(metric)
            target = PAPER[paper_case][var][metric]
            diff = rel_delta(value, target) if value is not None else None
            lines.append(
                "| %s | %s | %s | %.3e | %s |"
                % (
                    var,
                    metric,
                    "n/a" if value is None else "%.3e" % value,
                    target,
                    "n/a" if diff is None else "%.1f%%" % (100 * diff),
                )
            )
    return lines


def write_report(run_dir: Path, inputs: list[dict], results: list[dict], info: dict) -> None:
    reports = run_dir / "reports"
    lines = [
        "# Reproduction Runner Report",
        "",
        f"Run directory: {run_dir}",
        "",
        "## Environment",
        "",
        f"- Python: {info.get('python')}",
        f"- PyTorch: {info.get('torch')}",
        f"- CUDA available: {info.get('cuda')}",
        f"- GPU: {info.get('gpu')}",
        "- Reference mode: interpolated 80x80_from20 validation data, not strict paper-grade 80x80 reference data.",
        "",
        "## Input Files",
        "",
    ]
    lines += [f"- {r['name']}: {r['lines']} lines, {r['bytes']} bytes" for r in inputs]
    lines += ["", "## Runs", ""]
    for result in results:
        lines += [
            f"### {result['case']}",
            "",
            f"- Return code: {result['returncode']}",
            f"- Elapsed seconds: {result['elapsed_seconds']:.1f}",
            f"- Stdout: {result['stdout']}",
            f"- Stderr: {result['stderr']}",
            f"- Checkpoint: {result['checkpoint']}",
            f"- Metrics: {result['metrics']}",
            "",
        ]
        if result["metrics"]:
            metrics = json.loads(Path(result["metrics"]).read_text(encoding="utf-8"))
            if result["case"] == "example2":
                rho = metrics.get("rho")
                lines += [
                    "Table 12 density inversion:",
                    "",
                    "| Case | rho | Relative error vs 1.1 |",
                    "| --- | ---: | ---: |",
                    f"| This run | {rho:.5f} | {metrics.get('rho_rel_error', 0.0) * 100:.3f}% |",
                    "| Paper, initial rho=0.5 | 1.11737 | 1.579% |",
                    "| Paper, initial rho=1 | 1.11717 | 1.561% |",
                    "",
                ]
                lines += comparison_table(metrics, "example2")
            elif result["case"] == "example5":
                lines += comparison_table(metrics, "example5")
            lines += ["", ""]
    (reports / "reproduction_runner_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=["example2", "example5", "all"], default="all")
    parser.add_argument("--data-source", type=Path, default=Path(r"C:\Users\12412\Documents\Lei_code"))
    parser.add_argument("--run-root", type=Path, default=ROOT / "runs")
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--max-walltime-seconds", type=float, default=0.0)
    parser.add_argument("--max-iter-override", type=int, default=None)
    args = parser.parse_args()

    run_dir = args.run_root / (args.run_name or f"repro_current_{now_tag()}")
    workdir = run_dir / "workdir"
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    inputs = copy_inputs(workdir, args.data_source)
    info = env_info()
    (run_dir / "reports" / "environment.json").write_text(json.dumps(info, indent=2), encoding="utf-8")

    cases = ["example2", "example5"] if args.case == "all" else [args.case]
    results = []
    for case in cases:
        result = run_case(run_dir, workdir, case, args.max_walltime_seconds, args.max_iter_override)
        results.append(result)
        write_report(run_dir, inputs, results, info)
        if result["returncode"] != 0:
            break
    write_report(run_dir, inputs, results, info)
    print(run_dir)


if __name__ == "__main__":
    main()
