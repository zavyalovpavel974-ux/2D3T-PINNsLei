#!/usr/bin/env python
"""Start and inspect reproduction runs in the background.

This helper only creates files inside the target run directory when using the
`start` command. The `status` command is read-only.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from repro_runner import (
    DEFAULT_RUN_ROOT,
    ROOT,
    collect_run_status,
    ensure_run_can_be_written,
    format_status,
    run_dir_for,
)


def process_exists(pid: int) -> bool:
    if os.name == "nt":
        process_query_limited_information = 0x1000
        still_active = 259
        handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == still_active
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def launch_file(run_dir: Path) -> Path:
    return run_dir / "background" / "launch.json"


def read_launch(run_dir: Path) -> dict[str, Any] | None:
    path = launch_file(run_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def start(args: argparse.Namespace) -> None:
    run_dir = run_dir_for(args.run_root, args.run_name)
    ensure_run_can_be_written(run_dir, args.allow_existing_run)
    background_dir = run_dir / "background"
    background_dir.mkdir(parents=True, exist_ok=True)

    stdout_path = background_dir / "runner.stdout.log"
    stderr_path = background_dir / "runner.stderr.log"
    cmd = [
        sys.executable,
        "-u",
        str(ROOT / "repro_runner.py"),
        "--case",
        args.case,
        "--run-root",
        str(args.run_root),
        "--run-name",
        args.run_name,
        "--data-source",
        str(args.data_source),
        "--allow-existing-run",
    ]
    if args.max_walltime_seconds > 0:
        cmd += ["--max-walltime-seconds", str(args.max_walltime_seconds)]
    if args.max_iter_override is not None:
        cmd += ["--max-iter-override", str(args.max_iter_override)]
    if args.case in ("example2", "example6", "all"):
        cmd += ["--rho-init", str(args.rho_init), "--seed", str(args.seed)]

    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    with stdout_path.open("a", encoding="utf-8") as stdout, stderr_path.open("a", encoding="utf-8") as stderr:
        proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, text=True)

    payload = {
        "pid": proc.pid,
        "command": cmd,
        "cwd": str(ROOT),
        "run_dir": str(run_dir),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "started_at": time.time(),
    }
    launch_file(run_dir).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


def status(args: argparse.Namespace) -> None:
    run_dir = run_dir_for(args.run_root, args.run_name)
    launch = read_launch(run_dir)
    run_status = collect_run_status(run_dir)
    payload: dict[str, Any] = {
        "run_dir": str(run_dir),
        "launch": launch,
        "process_running": None,
        "run_status": run_status,
    }
    if launch and launch.get("pid") is not None:
        payload["process_running"] = process_exists(int(launch["pid"]))
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    print(format_status(run_status))
    if launch:
        print("")
        print(f"Background PID: {launch.get('pid')}")
        print(f"Process running: {payload['process_running']}")
        print(f"Background stdout: {launch.get('stdout')}")
        print(f"Background stderr: {launch.get('stderr')}")
    else:
        print("")
        print("No background launch metadata found.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    start_parser = sub.add_parser("start")
    start_parser.add_argument("--case", choices=["example2", "example3", "example4", "example6", "example5", "all"], default="all")
    start_parser.add_argument("--data-source", type=Path, default=Path(r"C:\Users\12412\Documents\Lei_code"))
    start_parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    start_parser.add_argument("--run-name", required=True)
    start_parser.add_argument("--max-walltime-seconds", type=float, default=0.0)
    start_parser.add_argument("--max-iter-override", type=int, default=None)
    start_parser.add_argument("--rho-init", type=float, default=1.0)
    start_parser.add_argument("--seed", type=int, default=12)
    start_parser.add_argument("--allow-existing-run", action="store_true")
    start_parser.set_defaults(func=start)

    status_parser = sub.add_parser("status")
    status_parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    status_parser.add_argument("--run-name", required=True)
    status_parser.add_argument("--json", action="store_true")
    status_parser.set_defaults(func=status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
