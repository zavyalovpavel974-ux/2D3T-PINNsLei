#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PAPER_EXAMPLE2 = {
    "Te": {"L2": 1.446e-2, "L1": 5.388e-3, "Linf": 1.684e-2},
    "Ti": {"L2": 7.902e-3, "L1": 1.153e-3, "Linf": 3.742e-3},
    "Tr": {"L2": 1.588e-2, "L1": 1.436e-2, "Linf": 4.834e-2},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute Example 2 forward metrics from a completed checkpoint.")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--comparison-md", required=True)
    parser.add_argument("--data-dir", default=".")
    parser.add_argument("--swap-xy", action="store_true", help="evaluate the model at (y, x, t) for author text-grid coordinates")
    return parser.parse_args()


def configure_forward_module() -> None:
    sys.argv = [
        sys.argv[0],
        "--transfer-stages",
        "70",
        "--kr-mode",
        "constant",
        "--no-use-ff",
        "--no-use-log-loss",
        "--lambda-brd",
        "1000",
        "--lambda-init",
        "10",
    ]


def read_reference(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with path.open("r", encoding="utf-8") as fp:
        dim, num_t, _ = eval(fp.readline())
        (imin, jmin), (imax, jmax), _ = eval(fp.readline())
        data = np.zeros((imax - imin + 1, jmax - jmin + 1, num_t))
        x_mesh = np.zeros((imax - imin + 1, jmax - jmin + 1))
        y_mesh = np.zeros((imax - imin + 1, jmax - jmin + 1))
        for _line in range((imax - imin + 1) * (jmax - jmin + 1) * num_t):
            i, j, k, value = (
                float(part)
                for part in re.split(r",| |\[|\]|\(|\)", fp.readline()[:-1])
                if part
            )
            data[int(i), int(j), int(k)] = value
            x_mesh[int(i), int(j)] = (imin + i + 0.5) / (imax - imin + 1)
            y_mesh[int(i), int(j)] = (jmin + j + 0.5) / (jmax - jmin + 1)
    if dim != 2:
        raise ValueError(f"unexpected dimension in {path}: {dim}")
    return np.column_stack((x_mesh.reshape(-1), y_mesh.reshape(-1))), data[:, :, (1, 2, 0)].reshape(-1, 3)


def compute_errors(reference: np.ndarray, prediction: np.ndarray) -> dict[str, dict[str, float]]:
    error = np.abs(reference - prediction)
    names = ("Te", "Ti", "Tr")
    metrics = {}
    for idx, name in enumerate(names):
        metrics[name] = {
            "L2": float(np.sqrt(np.mean(np.square(error[:, idx]))) / np.sqrt(np.mean(np.square(reference[:, idx])))),
            "L1": float(np.mean(error[:, idx])),
            "Linf": float(np.max(error[:, idx])),
        }
    return metrics


def relative_delta(value: float, target: float) -> float:
    return abs(value - target) / abs(target)


def main() -> None:
    cli = parse_args()
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    configure_forward_module()
    from sub_2D3T_wei_aei700_wer_krartr_time import DeviceDtype, PhysicsInformedNN

    checkpoint_path = Path(cli.checkpoint)
    data_dir = Path(cli.data_dir)
    ckpt = torch.load(checkpoint_path, map_location=DeviceDtype["device"], weights_only=False)

    gamme_e_ch = 45
    gamme_i_ch = 70
    gamme_r_ch = 0.007568
    rou = 1.1
    ae = 81
    ai = 0.02
    ar = 2.1e2 / (rou * rou)
    ce = 1.5 * gamme_e_ch
    ci = 1.5 * gamme_i_ch
    cr = 0.25 * gamme_r_ch
    beta = 3
    aer = 79
    aei = float(ckpt.get("Aei", 70.0))

    dummy = np.zeros((1, 3), dtype=np.float64)
    layers = [[3] + [60] * 6 + [3]]
    model = PhysicsInformedNN(dummy, dummy, dummy, dummy, dummy, dummy, layers, rou, ce, ci, cr, beta, ae, ai, ar, aei, aer)
    model.net_u.load_state_dict(ckpt["model"])
    model.net_u.eval()

    time_files = {
        "1e-5": "sol1_wei_aei70_wer_krar_1e-5.txt",
        "0.3": "sol1_wei_aei70_wer_krar_0p3.txt",
        "0.5": "sol1_wei_aei70_wer_krar_0p5.txt",
        "0.7": "sol1_wei_aei70_wer_krar_0p7.txt",
        "1.0": "sol1_wei_aei70_wer_krar_1.txt",
    }
    predictions = []
    references = []
    per_time = {}
    infer_start = time.time()
    for label, filename in time_files.items():
        coords, reference = read_reference(data_dir / filename)
        eval_coords = coords[:, [1, 0]] if cli.swap_xy else coords
        xyt = np.column_stack((eval_coords, np.full((coords.shape[0],), float(label))))
        with torch.no_grad():
            prediction = model.predict(xyt).reshape(-1, 3).numpy()
        references.append(reference)
        predictions.append(prediction)
        per_time[label] = compute_errors(reference, prediction)
    inference_seconds = time.time() - infer_start

    aggregate = compute_errors(np.stack(references, axis=1).reshape(-1, 3), np.stack(predictions, axis=1).reshape(-1, 3))
    metrics = {
        "case": "example2_forward",
        "reference": "sol1_wei_aei70_wer_krar",
        "metrics_available": True,
        "coordinate_evaluation": "swapped_xy" if cli.swap_xy else "as_written_xy",
        "checkpoint": str(checkpoint_path),
        "checkpoint_phase": ckpt.get("phase"),
        "final_stage": int(aei),
        "kr_mode": "constant",
        "use_ff": False,
        "use_log_loss": False,
        "lambda_brd": 1000.0,
        "lambda_init": 10.0,
        "lbfgs_func_evals": int(ckpt.get("lbfgs", {}).get("state", {}).get(0, {}).get("func_evals", -1)),
        "lbfgs_n_iter": int(ckpt.get("lbfgs", {}).get("state", {}).get(0, {}).get("n_iter", -1)),
        "checkpoint_elapsed_seconds": float(ckpt.get("elapsed_seconds", 0.0)),
        "inference_time_seconds": float(inference_seconds),
        "aggregate": aggregate,
        "times": per_time,
    }

    output_json = Path(cli.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    lines = [
        "# Example 2 Forward Metrics vs Paper",
        "",
        f"- Checkpoint: `{checkpoint_path}`",
        f"- Reference files: `{data_dir / 'sol1_wei_aei70_wer_krar_*.txt'}`",
        f"- Coordinate evaluation: `{'swapped_xy' if cli.swap_xy else 'as_written_xy'}`",
        f"- Metrics JSON: `{output_json}`",
        "",
        "| Variable | Metric | This run | Paper Example 2 | Relative difference |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for var in ("Te", "Ti", "Tr"):
        for metric_name in ("L2", "L1", "Linf"):
            value = aggregate[var][metric_name]
            target = PAPER_EXAMPLE2[var][metric_name]
            lines.append(f"| {var} | {metric_name} | {value:.3e} | {target:.3e} | {100 * relative_delta(value, target):.1f}% |")
    comparison_md = Path(cli.comparison_md)
    comparison_md.parent.mkdir(parents=True, exist_ok=True)
    comparison_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote metrics: {output_json}")
    print(f"wrote comparison: {comparison_md}")


if __name__ == "__main__":
    main()
