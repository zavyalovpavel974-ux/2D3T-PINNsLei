#!/usr/bin/env python
"""Start one segmented reference-solver run in the background."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_DIR = Path("reference_solver_outputs/aei70_krar_80_strict_20260525")
PROTECTED_RUN = ROOT / "runs" / "overnight_current"


def resolve_workspace(path: Path) -> Path:
    return (ROOT / path).resolve() if not path.is_absolute() else path.resolve()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def quote_for_display(parts: list[str]) -> str:
    return " ".join(json.dumps(part) for part in parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--segment", type=int, required=True)
    parser.add_argument("--walltime-seconds", type=float, default=3600.0)
    parser.add_argument("--case", choices=["aei70_krar", "aei700_krartr"], default="aei70_krar")
    parser.add_argument("--nx", type=int, default=80)
    parser.add_argument("--ny", type=int, default=80)
    parser.add_argument("--times", default="1e-5,0.3,0.5,0.7,1.0")
    parser.add_argument("--dt-init", default="0.005")
    parser.add_argument("--dt-min", default="1e-6")
    parser.add_argument("--dt-max", default="0.02")
    parser.add_argument("--newton-max", default="8")
    parser.add_argument("--gmres-maxiter", default="120")
    parser.add_argument("--checkpoint-interval-steps", default="10")
    parser.add_argument("--log-every-step", action="store_true")
    parser.add_argument("--log-rejected-steps", action="store_true")
    parser.add_argument("--debug-on-failure", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.segment < 1:
        raise SystemExit("segment must be >= 1")
    if args.walltime_seconds <= 0:
        raise SystemExit("walltime-seconds must be > 0")

    run_dir = resolve_workspace(args.run_dir)
    protected = PROTECTED_RUN.resolve()
    if run_dir == protected or is_relative_to(run_dir, protected):
        raise SystemExit(f"Refusing to write inside protected run directory: {run_dir}")

    logs_dir = run_dir / "logs"
    ckpt_dir = run_dir / "checkpoints"
    out_dir = run_dir / "outputs"
    bg_dir = run_dir / "background"
    for directory in (logs_dir, ckpt_dir, out_dir, bg_dir):
        directory.mkdir(parents=True, exist_ok=True)

    output = out_dir / "reference_snapshots.npz"
    if output.exists():
        raise SystemExit(f"Output already exists; refusing to start solve: {output}")

    current_ckpt = ckpt_dir / f"segment_{args.segment}.ckpt.npz"
    if current_ckpt.exists():
        raise SystemExit(f"Current segment checkpoint already exists; refusing to overwrite: {current_ckpt}")

    command = [
        sys.executable,
        "-u",
        str(ROOT / "reference_solver" / "generate_reference.py"),
        "solve",
        "--case",
        args.case,
        "--nx",
        str(args.nx),
        "--ny",
        str(args.ny),
        "--times",
        args.times,
        "--dt-init",
        str(args.dt_init),
        "--dt-min",
        str(args.dt_min),
        "--dt-max",
        str(args.dt_max),
        "--newton-max",
        str(args.newton_max),
        "--gmres-maxiter",
        str(args.gmres_maxiter),
        "--checkpoint",
        str(current_ckpt),
        "--checkpoint-interval-steps",
        str(args.checkpoint_interval_steps),
        "--max-walltime-seconds",
        str(args.walltime_seconds),
        "--out",
        str(output),
    ]
    if args.log_every_step:
        command.append("--log-every-step")
    if args.log_rejected_steps:
        command.append("--log-rejected-steps")
    if args.debug_on_failure:
        command.append("--debug-on-failure")
    previous_ckpt = None
    if args.segment > 1:
        previous_ckpt = ckpt_dir / f"segment_{args.segment - 1}.ckpt.npz"
        if not previous_ckpt.exists():
            raise SystemExit(f"Previous segment checkpoint missing: {previous_ckpt}")
        insert_at = command.index("--checkpoint")
        command[insert_at:insert_at] = ["--resume-checkpoint", str(previous_ckpt)]

    stdout_path = logs_dir / f"segment_{args.segment}.stdout.log"
    stderr_path = logs_dir / f"segment_{args.segment}.stderr.log"
    if stdout_path.exists() and stdout_path.stat().st_size > 0:
        raise SystemExit(f"stdout log already has content; refusing to append: {stdout_path}")
    if stderr_path.exists() and stderr_path.stat().st_size > 0:
        raise SystemExit(f"stderr log already has content; refusing to append: {stderr_path}")

    launch = {
        "pid": None,
        "segment": args.segment,
        "case": args.case,
        "nx": args.nx,
        "ny": args.ny,
        "walltime_seconds": args.walltime_seconds,
        "command": command,
        "command_display": quote_for_display(command),
        "run_dir": str(run_dir),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "checkpoint": str(current_ckpt),
        "resume_checkpoint": str(previous_ckpt) if previous_ckpt else None,
        "output": str(output),
        "started_at": None,
        "dry_run": bool(args.dry_run),
    }
    if args.dry_run:
        print(json.dumps(launch, indent=2, ensure_ascii=False))
        return

    creationflags = 0
    if sys.platform.startswith("win"):
        creationflags = (
            getattr(subprocess, "CREATE_NO_WINDOW", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        )

    with stdout_path.open("a", encoding="utf-8") as stdout, stderr_path.open("a", encoding="utf-8") as stderr:
        proc = subprocess.Popen(
            command,
            cwd=str(ROOT),
            stdout=stdout,
            stderr=stderr,
            text=True,
            creationflags=creationflags,
        )

    launch["pid"] = proc.pid
    launch["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    launch_path = bg_dir / f"launch_segment_{args.segment}.json"
    launch_path.write_text(json.dumps(launch, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(launch, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
