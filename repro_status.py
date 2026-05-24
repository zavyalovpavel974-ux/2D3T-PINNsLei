#!/usr/bin/env python
"""Read-only status view for reproduction runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from repro_runner import DEFAULT_RUN_ROOT, collect_run_status, format_status, run_dir_for


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    status = collect_run_status(run_dir_for(args.run_root, args.run_name))
    if args.json:
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        print(format_status(status))


if __name__ == "__main__":
    main()
