#!/usr/bin/env python
"""Run, inspect, and protect reproduction workflows.

Default behavior is conservative: existing run directories are not writable
unless --allow-existing-run is supplied, and frozen protected runs are never
writable through this runner.
"""

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
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_RUN_ROOT = ROOT / "runs"
PROTECTED_RUN_NAMES = {"overnight_current"}
EXAMPLE5_STAGES = (70, 400, 700)
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


def normalize_path(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def run_dir_for(run_root: Path, run_name: str | None) -> Path:
    return run_root / (run_name or f"repro_current_{now_tag()}")


def is_protected_run_dir(run_dir: Path) -> bool:
    resolved = normalize_path(run_dir)
    protected = {normalize_path(DEFAULT_RUN_ROOT / name) for name in PROTECTED_RUN_NAMES}
    return run_dir.name in PROTECTED_RUN_NAMES or resolved in protected


def ensure_run_can_be_written(run_dir: Path, allow_existing_run: bool) -> None:
    if is_protected_run_dir(run_dir):
        raise RuntimeError(
            f"refusing to write protected frozen run directory: {run_dir}. "
            "Use a new --run-name instead."
        )
    if run_dir.exists() and not allow_existing_run:
        raise RuntimeError(
            f"refusing to write existing run directory by default: {run_dir}. "
            "Use a new --run-name, or pass --allow-existing-run for a non-protected resumable run."
        )


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def copy_inputs(workdir: Path, data_source: Path) -> list[dict[str, Any]]:
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


def env_info() -> dict[str, Any]:
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


def read_checkpoint_meta(checkpoint: Path) -> dict[str, Any]:
    if not checkpoint.exists():
        return {"exists": False, "path": str(checkpoint)}
    stat = checkpoint.stat()
    meta: dict[str, Any] = {
        "exists": True,
        "path": str(checkpoint),
        "bytes": stat.st_size,
        "mtime": stat.st_mtime,
    }
    try:
        os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
        import torch

        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        for key in ("Aei", "phase", "it", "adam_iter", "rho", "loss", "elapsed_seconds"):
            if key in payload:
                value = payload.get(key)
                if hasattr(value, "item"):
                    value = value.item()
                meta[key] = value
    except Exception as exc:
        meta["read_error"] = str(exc)
    return meta


def infer_example5_checkpoint_stage(checkpoint: Path, stdout_log: Path) -> int | None:
    meta = read_checkpoint_meta(checkpoint)
    if meta.get("Aei") is not None:
        try:
            stage = int(float(meta["Aei"]))
            return stage if stage in EXAMPLE5_STAGES else None
        except (TypeError, ValueError):
            return None

    if not stdout_log.exists():
        return None
    text = stdout_log.read_text(encoding="utf-8", errors="ignore")
    training_times = re.findall(r"(?<!Total )Training time: ([0-9.]+)", text)
    if len(training_times) >= len(EXAMPLE5_STAGES):
        return EXAMPLE5_STAGES[-1]
    matches = re.findall(r"^Aei:\s*(\d+)", text, flags=re.MULTILINE)
    if not matches:
        return None
    previous_stage = int(matches[-1])
    stage_after_previous = {0: 70, 70: 400, 400: 700}
    return stage_after_previous.get(previous_stage)


def infer_example5_resume_stage(checkpoint: Path, stdout_log: Path) -> int | None:
    return infer_example5_checkpoint_stage(checkpoint, stdout_log)


def file_record(path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if path.exists():
        stat = path.stat()
        record.update({"bytes": stat.st_size, "mtime": stat.st_mtime})
    return record


def list_files(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [file_record(p) for p in sorted(path.iterdir()) if p.is_file()]


def collect_run_status(run_dir: Path) -> dict[str, Any]:
    logs = run_dir / "logs"
    reports = run_dir / "reports"
    checkpoints = run_dir / "checkpoints"
    figures = run_dir / "workdir" / "figures"
    status: dict[str, Any] = {
        "run_dir": str(run_dir),
        "exists": run_dir.exists(),
        "protected": is_protected_run_dir(run_dir),
        "logs_dir": str(logs),
        "reports_dir": str(reports),
        "checkpoints_dir": str(checkpoints),
        "figures_dir": str(figures),
        "logs": list_files(logs),
        "reports": list_files(reports),
        "figures_exists": figures.exists(),
        "cases": {},
    }
    for case in ("example2", "example5"):
        stdout_log = logs / f"{case}.stdout.log"
        checkpoint = checkpoints / case / "latest.pt"
        metrics = reports / f"{case}_metrics.json"
        case_status: dict[str, Any] = {
            "stdout": file_record(stdout_log),
            "stderr": file_record(logs / f"{case}.stderr.log"),
            "metrics": file_record(metrics),
            "run_result": file_record(reports / f"{case}_run_result.json"),
            "checkpoint": read_checkpoint_meta(checkpoint),
        }
        if metrics.exists():
            try:
                parsed = json.loads(metrics.read_text(encoding="utf-8"))
                case_status["metrics_case"] = parsed.get("case")
                case_status["aggregate"] = parsed.get("aggregate")
                if case == "example2":
                    case_status["rho"] = parsed.get("rho")
                    case_status["rho_rel_error"] = parsed.get("rho_rel_error")
                if case == "example5":
                    case_status["inference_time_seconds"] = parsed.get("inference_time_seconds")
            except Exception as exc:
                case_status["metrics_read_error"] = str(exc)
        if case == "example5":
            case_status["stage"] = infer_example5_checkpoint_stage(checkpoint, stdout_log)
        else:
            case_status["stage"] = "inverse"
        status["cases"][case] = case_status
    return status


def format_status(status: dict[str, Any]) -> str:
    lines = [
        f"Run: {status['run_dir']}",
        f"Exists: {status['exists']}",
        f"Protected: {status['protected']}",
        "",
        "Cases:",
    ]
    for case, case_status in status["cases"].items():
        checkpoint = case_status["checkpoint"]
        stage = case_status.get("stage")
        stage_text = "unknown" if stage is None else stage
        lines += [
            f"- {case}",
            f"  stage: {stage_text}",
            f"  checkpoint: {checkpoint.get('path')} ({'exists' if checkpoint.get('exists') else 'missing'})",
            f"  phase: {checkpoint.get('phase', 'n/a')}",
            f"  step: {checkpoint.get('it', checkpoint.get('adam_iter', 'n/a'))}",
            f"  metrics: {case_status['metrics']['path']} ({'exists' if case_status['metrics']['exists'] else 'missing'})",
            f"  stdout: {case_status['stdout']['path']} ({'exists' if case_status['stdout']['exists'] else 'missing'})",
            f"  stderr: {case_status['stderr']['path']} ({'exists' if case_status['stderr']['exists'] else 'missing'})",
        ]
        if case == "example2" and "rho" in case_status:
            lines.append(f"  rho: {case_status['rho']}")
        if case == "example5" and "inference_time_seconds" in case_status:
            lines.append(f"  inference_time_seconds: {case_status['inference_time_seconds']}")
    lines += [
        "",
        f"Reports: {status['reports_dir']}",
        f"Logs: {status['logs_dir']}",
        f"Figures: {status['figures_dir']} ({'exists' if status['figures_exists'] else 'missing'})",
    ]
    return "\n".join(lines)


def build_case_command(
    checkpoints_root: Path,
    reports: Path,
    logs: Path,
    case: str,
    max_walltime: float,
    max_iter_override: int | None,
) -> tuple[list[str], Path, Path, Path]:
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
        str(checkpoints_root / case),
        "--checkpoint-interval",
        "200",
        "--metrics-json",
        str(metrics),
    ]
    latest = checkpoints_root / case / "latest.pt"
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
    return cmd, stdout_path, stderr_path, metrics


def run_case(run_dir: Path, workdir: Path, case: str, max_walltime: float, max_iter_override: int | None) -> dict[str, Any]:
    logs = run_dir / "logs"
    reports = run_dir / "reports"
    checkpoints_root = run_dir / "checkpoints"
    logs.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    (checkpoints_root / case).mkdir(parents=True, exist_ok=True)

    latest = checkpoints_root / case / "latest.pt"
    cmd, stdout_path, stderr_path, metrics = build_case_command(
        checkpoints_root, reports, logs, case, max_walltime, max_iter_override
    )

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


def comparison_table(metrics: dict[str, Any], paper_case: str) -> list[str]:
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


def write_report(run_dir: Path, inputs: list[dict[str, Any]], results: list[dict[str, Any]], info: dict[str, Any]) -> None:
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


def run_workflow(args: argparse.Namespace) -> Path:
    run_dir = run_dir_for(args.run_root, args.run_name)
    ensure_run_can_be_written(run_dir, args.allow_existing_run)
    if args.dry_run:
        print(f"dry-run: would write run directory {run_dir}")
        return run_dir

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
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=["example2", "example5", "all"], default="all")
    parser.add_argument("--data-source", type=Path, default=Path(r"C:\Users\12412\Documents\Lei_code"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--max-walltime-seconds", type=float, default=0.0)
    parser.add_argument("--max-iter-override", type=int, default=None)
    parser.add_argument("--allow-existing-run", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--status", action="store_true", help="read-only run status query")
    parser.add_argument("--json", action="store_true", help="with --status, emit JSON")
    args = parser.parse_args()

    run_dir = run_dir_for(args.run_root, args.run_name)
    if args.status:
        if not args.run_name:
            parser.error("--status requires --run-name")
        status = collect_run_status(run_dir)
        if args.json:
            print(json.dumps(status, indent=2, ensure_ascii=False))
        else:
            print(format_status(status))
        return
    try:
        run_workflow(args)
    except RuntimeError as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
