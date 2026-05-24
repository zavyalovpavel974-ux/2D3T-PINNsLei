#!/usr/bin/env python
"""Recalculate Example 5 metrics with per-time reference text files.

This script is intentionally read-only with respect to ``runs/overnight_current``.
It reconstructs the final Example 5 network from the frozen checkpoint, verifies
that the t=1 metrics match the frozen metrics, and writes corrected metrics to a
separate output directory.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np


PROTECTED_RUN = Path("runs/overnight_current")
DEFAULT_OUT_DIR = Path("reference_solver_outputs/example5_static_recalc")
TIME_REFERENCES = {
    "1e-5": ("1e-5", "sol1_wei_aei700_wer_krartr_1e-5.txt"),
    "0.3": (0.3, "sol1_wei_aei700_wer_krartr_0p3.txt"),
    "0.5": (0.5, "sol1_wei_aei700_wer_krartr_0p5.txt"),
    "0.7": (0.7, "sol1_wei_aei700_wer_krartr_0p7.txt"),
    "1.0": (1.0, "sol1_wei_aei700_wer_krartr_1.txt"),
}
LEGACY_T1_REFERENCE = "sol1_wei_aei700_wer_krartr_80_1.txt"
VARIABLES = ("Te", "Ti", "Tr")


def resolve(path: Path) -> Path:
    return path.expanduser().resolve()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def refuse_protected_output(out_dir: Path, protected: Path) -> None:
    out_resolved = resolve(out_dir)
    protected_resolved = resolve(protected)
    if out_resolved == protected_resolved or is_relative_to(out_resolved, protected_resolved):
        raise SystemExit(f"Refusing to write inside protected run directory: {out_resolved}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_author_txt(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fp:
        dim, num_t, _ = eval(fp.readline())
        if int(dim) != 2 or int(num_t) != 3:
            raise ValueError(f"Unexpected header in {path}: dim={dim}, num_t={num_t}")
        (imin, jmin), (imax, jmax), _ = eval(fp.readline())
        ny = int(imax - imin + 1)
        nx = int(jmax - jmin + 1)
        data = np.zeros((ny, nx, int(num_t)), dtype=np.float64)
        x_mesh = np.zeros((ny, nx), dtype=np.float64)
        y_mesh = np.zeros((ny, nx), dtype=np.float64)
        for _line in range(ny * nx * int(num_t)):
            raw = fp.readline()
            if not raw:
                raise ValueError(f"Unexpected EOF in {path}")
            i, j, k, value = (
                float(token)
                for token in re.split(r",| |\[|\]|\(|\)", raw.strip())
                if token
            )
            ii, jj, kk = int(i), int(j), int(k)
            data[ii, jj, kk] = value
            x_mesh[ii, jj] = (imin + i + 0.5) / ny
            y_mesh[ii, jj] = (jmin + j + 0.5) / nx

    # Author text files store photon/electron/ion. The training scripts remap
    # them to electron/ion/photon before computing Te/Ti/Tr metrics.
    mapped = data[:, :, (1, 2, 0)].reshape(-1, 3)
    meta = {
        "path": str(path),
        "shape": [ny, nx, int(num_t)],
        "raw_order": ["Tr", "Te", "Ti"],
        "mapped_order": list(VARIABLES),
        "sha256": sha256_file(path),
        "finite": bool(np.isfinite(mapped).all()),
    }
    return mapped, x_mesh.reshape(-1, 1), y_mesh.reshape(-1, 1), meta


def verify_reference_mapping(repo_root: Path) -> tuple[dict[str, Any], dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]]:
    mapping: dict[str, Any] = {}
    arrays: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    base_shape = None
    for label, (time_value, filename) in TIME_REFERENCES.items():
        path = repo_root / filename
        if not path.exists():
            raise SystemExit(f"Reference mapping cannot be confirmed, missing file: {path}")
        ref, x, y, meta = read_author_txt(path)
        if not meta["finite"]:
            raise SystemExit(f"Reference mapping cannot be confirmed, non-finite data in: {path}")
        if base_shape is None:
            base_shape = tuple(meta["shape"])
        elif tuple(meta["shape"]) != base_shape:
            raise SystemExit(f"Reference mapping cannot be confirmed, shape mismatch in: {path}")
        mapping[label] = {"time": time_value, "file": filename, **meta}
        arrays[label] = (ref, x, y)

    legacy_path = repo_root / LEGACY_T1_REFERENCE
    if not legacy_path.exists():
        raise SystemExit(f"Reference mapping cannot be confirmed, missing legacy t=1 file: {legacy_path}")
    legacy_hash = sha256_file(legacy_path)
    t1_hash = mapping["1.0"]["sha256"]
    if legacy_hash != t1_hash:
        raise SystemExit(
            "Reference mapping cannot be confirmed, legacy _80_1 file differs from t=1 file"
        )
    mapping["legacy_80_1"] = {
        "file": LEGACY_T1_REFERENCE,
        "sha256": legacy_hash,
        "equals_1.0_file": True,
    }
    return mapping, arrays


def metrics_for(reference: np.ndarray, prediction: np.ndarray) -> dict[str, dict[str, float]]:
    error = np.abs(reference - prediction)
    result: dict[str, dict[str, float]] = {}
    for idx, name in enumerate(VARIABLES):
        result[name] = {
            "L2": float(np.sqrt(np.mean(np.square(error[:, idx]))) / np.sqrt(np.mean(np.square(reference[:, idx])))),
            "L1": float(np.mean(error[:, idx])),
            "Linf": float(np.max(error[:, idx])),
        }
    return result


def aggregate_metrics(references: list[np.ndarray], predictions: list[np.ndarray]) -> dict[str, dict[str, float]]:
    ustar = np.stack(references, axis=1)
    upred = np.stack(predictions, axis=1)
    error = np.abs(ustar - upred)
    result: dict[str, dict[str, float]] = {}
    for idx, name in enumerate(VARIABLES):
        result[name] = {
            "L2": float(np.sqrt(np.mean(np.square(error[:, :, idx]))) / np.sqrt(np.mean(np.square(ustar[:, :, idx])))),
            "L1": float(np.mean(error[:, :, idx])),
            "Linf": float(np.max(error[:, :, idx])),
        }
    return result


def import_model_module(device: str):
    original_argv = sys.argv[:]
    sys.argv = [original_argv[0]]
    try:
        module = importlib.import_module("sub_2D3T_wei_aei700_wer_krartr_time")
    finally:
        sys.argv = original_argv
    module.DeviceDtype = {"device": device, "dtype": module.torch.float64}
    return module


def build_model(module, device: str):
    torch = module.torch
    np.random.seed(12)
    torch.manual_seed(12)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(12)
    torch.backends.cudnn.deterministic = True
    if device == "cuda":
        torch.backends.cudnn.enabled = True
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False

    dummy = np.zeros((1, 3), dtype=np.float64)
    layers = [[3] + [60] * 6 + [3]]
    return module.PhysicsInformedNN(
        dummy,
        dummy,
        dummy,
        dummy,
        dummy,
        dummy,
        layers,
        1.1,
        1.5 * 45,
        1.5 * 70,
        0.25 * 0.007568,
        3,
        81,
        0.02,
        2.1e2 / (1.1 * 1.1),
        700,
        79,
        lrin=1e-4,
    )


def load_checkpoint_model(model, module, checkpoint_path: Path, device: str) -> dict[str, Any]:
    checkpoint = module.torch.load(
        checkpoint_path,
        map_location=device,
        weights_only=False,
    )
    if checkpoint.get("Aei") not in (700, 700.0):
        raise SystemExit(f"Expected Example 5 stage Aei=700 checkpoint, got Aei={checkpoint.get('Aei')}")
    if checkpoint.get("phase") != "completed":
        raise SystemExit(f"Expected completed checkpoint, got phase={checkpoint.get('phase')}")
    model.net_u.load_state_dict(checkpoint["model"])
    model.net_u.eval()
    return checkpoint


def predict_all(model, module, arrays: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]) -> dict[str, np.ndarray]:
    predictions: dict[str, np.ndarray] = {}
    with module.torch.no_grad():
        for label, (time_value, _filename) in TIME_REFERENCES.items():
            _ref, x, y = arrays[label]
            t = np.full((x.shape[0], 1), float(time_value), dtype=np.float64)
            points = np.concatenate([x, y, t], axis=1)
            predictions[label] = model.predict(points).numpy().reshape(-1, 3)
    return predictions


def compare_t1(original_metrics: dict[str, Any], recalculated: dict[str, Any], tolerance: float) -> dict[str, Any]:
    diffs: dict[str, Any] = {}
    max_abs_diff = 0.0
    for variable in VARIABLES:
        diffs[variable] = {}
        for norm_name in ("L2", "L1", "Linf"):
            old = float(original_metrics["times"]["1.0"][variable][norm_name])
            new = float(recalculated["times"]["1.0"][variable][norm_name])
            diff = abs(new - old)
            max_abs_diff = max(max_abs_diff, diff)
            diffs[variable][norm_name] = {
                "original": old,
                "recalculated": new,
                "abs_diff": diff,
            }
    return {
        "tolerance": tolerance,
        "max_abs_diff": max_abs_diff,
        "passed": bool(max_abs_diff <= tolerance),
        "details": diffs,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_comparison_markdown(path: Path, original: dict[str, Any], corrected: dict[str, Any], t1_check: dict[str, Any]) -> None:
    lines = [
        "# Example 5 Per-Time Reference Metrics Recalculation",
        "",
        "## Self Check",
        "",
        f"- t=1 max abs diff: `{t1_check['max_abs_diff']:.12e}`",
        f"- tolerance: `{t1_check['tolerance']:.12e}`",
        f"- passed: `{t1_check['passed']}`",
        "",
        "## Aggregate Metrics",
        "",
        "| Variable | Norm | Original | Corrected | Delta |",
        "|---|---:|---:|---:|---:|",
    ]
    for variable in VARIABLES:
        for norm_name in ("L2", "L1", "Linf"):
            old = float(original["aggregate"][variable][norm_name])
            new = float(corrected["aggregate"][variable][norm_name])
            lines.append(f"| {variable} | {norm_name} | {old:.12e} | {new:.12e} | {new - old:.12e} |")
    lines.extend(["", "## Per-Time Metrics", ""])
    for label in TIME_REFERENCES:
        lines.extend([f"### t = {label}", "", "| Variable | Norm | Original | Corrected | Delta |", "|---|---:|---:|---:|---:|"])
        for variable in VARIABLES:
            for norm_name in ("L2", "L1", "Linf"):
                old = float(original["times"][label][variable][norm_name])
                new = float(corrected["times"][label][variable][norm_name])
                lines.append(f"| {variable} | {norm_name} | {old:.12e} | {new:.12e} | {new - old:.12e} |")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=PROTECTED_RUN)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--require-t1-match", action="store_true")
    parser.add_argument("--t1-tolerance", type=float, default=1e-8)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser.parse_args()


def main() -> None:
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    args = parse_args()
    repo_root = resolve(args.repo_root)
    run_dir = resolve(args.run_dir)
    out_dir = resolve(args.out_dir)
    refuse_protected_output(out_dir, run_dir)

    expected_run = resolve(repo_root / PROTECTED_RUN)
    if run_dir != expected_run:
        raise SystemExit(f"Expected frozen run-dir {expected_run}, got {run_dir}")
    if not run_dir.exists():
        raise SystemExit(f"Frozen run-dir does not exist: {run_dir}")

    mapping, arrays = verify_reference_mapping(repo_root)
    check_report = {
        "status": "ok",
        "run_dir": str(run_dir),
        "out_dir": str(out_dir),
        "reference_mapping": mapping,
        "protected_output_refused": True,
    }
    write_json(out_dir / "example5_reference_mapping_check.json", check_report)
    if args.check_only:
        print(json.dumps(check_report, indent=2, ensure_ascii=False))
        return

    import torch

    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but torch.cuda.is_available() is false")

    module = import_model_module(device)
    model = build_model(module, device)
    checkpoint_path = run_dir / "checkpoints" / "example5" / "latest.pt"
    if not checkpoint_path.exists():
        raise SystemExit(f"Missing frozen checkpoint: {checkpoint_path}")
    checkpoint = load_checkpoint_model(model, module, checkpoint_path, device)

    original_metrics_path = run_dir / "reports" / "example5_metrics.json"
    original_metrics = json.loads(original_metrics_path.read_text(encoding="utf-8"))
    started = time.time()
    predictions = predict_all(model, module, arrays)
    references = [arrays[label][0] for label in TIME_REFERENCES]
    predicted = [predictions[label] for label in TIME_REFERENCES]
    per_time = {
        label: metrics_for(arrays[label][0], predictions[label])
        for label in TIME_REFERENCES
    }
    corrected = {
        "case": "example5_transfer",
        "reference": "per_time_reference_txt",
        "source_run_dir": str(run_dir),
        "checkpoint": str(checkpoint_path),
        "checkpoint_meta": {
            "Aei": float(checkpoint.get("Aei")),
            "phase": checkpoint.get("phase"),
            "it": int(checkpoint.get("it", -1)),
            "adam_iter": int(checkpoint.get("adam_iter", -1)),
            "rho": float(checkpoint.get("rho", np.nan)),
        },
        "reference_mapping": mapping,
        "aggregate": aggregate_metrics(references, predicted),
        "times": per_time,
        "recalc_elapsed_seconds": time.time() - started,
        "device": device,
    }
    t1_check = compare_t1(original_metrics, corrected, args.t1_tolerance)
    comparison = {
        "original_metrics": str(original_metrics_path),
        "corrected_metrics": str(out_dir / "example5_metrics_per_time_reference.json"),
        "t1_self_check": t1_check,
        "aggregate_delta": {
            variable: {
                norm_name: float(corrected["aggregate"][variable][norm_name])
                - float(original_metrics["aggregate"][variable][norm_name])
                for norm_name in ("L2", "L1", "Linf")
            }
            for variable in VARIABLES
        },
    }

    if args.require_t1_match and not t1_check["passed"]:
        failure = {
            "status": "failed_t1_self_check",
            "message": "Reconstructed t=1 metrics do not match frozen metrics; corrected metrics were not written.",
            "t1_self_check": t1_check,
            "reference_mapping": mapping,
        }
        write_json(out_dir / "example5_recalc_failure.json", failure)
        raise SystemExit(f"t=1 self-check failed, max_abs_diff={t1_check['max_abs_diff']:.6e}")

    write_json(out_dir / "example5_metrics_per_time_reference.json", corrected)
    write_json(out_dir / "example5_metrics_comparison.json", comparison)
    write_comparison_markdown(
        out_dir / "example5_metrics_comparison.md",
        original_metrics,
        corrected,
        t1_check,
    )
    print(json.dumps({"status": "ok", **comparison}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
