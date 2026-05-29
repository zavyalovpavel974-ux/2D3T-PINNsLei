#!/usr/bin/env python
"""Compute Example 3 (Aei=400, Kr=Ar) metrics from a completed checkpoint.
Run from the workdir directory."""
import json, os, re, sys, time
from pathlib import Path
import numpy as np
import torch

# Set sys.argv before importing sub module
sys.argv = [
    "compute_ex3_metrics.py",
    "--transfer-stages", "70,400",
    "--kr-mode", "constant",
    "--no-use-ff",
    "--use-log-loss",
    "--lambda-brd", "20",
    "--lambda-init", "10",
]

# Add workdir to path
WORKDIR = Path(__file__).resolve().parent.parent / "runs" / "ex3_transfer_clean_20260528" / "workdir"
sys.path.insert(0, str(WORKDIR))

from sub_2D3T_wei_aei700_wer_krartr_time import PhysicsInformedNN

TIME_LABELS = {"1e-5": "1e-5", "0.3": "0p3", "0.5": "0p5", "0.7": "0p7", "1.0": "1"}
REFERENCE_FILES = {label: f"sol1_wei_aei400_wer_krar_{tag}.txt" for label, tag in TIME_LABELS.items()}

def read_reference(path):
    with open(path, "r", encoding="utf-8") as fp:
        dim, num_t, _ = eval(fp.readline())
        (imin, jmin), (imax, jmax), _ = eval(fp.readline())
        data = np.zeros((imax - imin + 1, jmax - jmin + 1, num_t))
        x_mesh = np.zeros((imax - imin + 1, jmax - jmin + 1))
        y_mesh = np.zeros((imax - imin + 1, jmax - jmin + 1))
        for _ in range((imax - imin + 1) * (jmax - jmin + 1) * num_t):
            i, j, k, value = (float(p) for p in re.split(r",| |\[|\]|\(|\)", fp.readline()[:-1]) if p)
            data[int(i), int(j), int(k)] = value
            x_mesh[int(i), int(j)] = (imin + i + 0.5) / (imax - imin + 1)
            y_mesh[int(i), int(j)] = (jmin + j + 0.5) / (jmax - jmin + 1)
    return x_mesh, y_mesh, data[:, :, (1, 2, 0)]  # remap photon,electron,ion -> Te,Ti,Tr

def main():
    checkpoint_path = WORKDIR.parent / "checkpoints" / "example3" / "latest.pt"
    data_dir = WORKDIR
    output_json = WORKDIR.parent / "reports" / "example3_metrics.json"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading checkpoint: {checkpoint_path}")
    checkpoint = torch.load(str(checkpoint_path), map_location=device, weights_only=False)
    print(f"  phase={checkpoint.get('phase')}, Aei={checkpoint.get('Aei')}, it={checkpoint.get('it')}")

    NN_layers = [[3] + [60] * 6 + [3]]
    model = PhysicsInformedNN.__new__(PhysicsInformedNN)
    rho, ce, ci, cr, Aer, Aei = 1.1, 67.5, 105.0, 173.55, 79.0, 400.0
    # PhysicalParams: rho=1.1, Gammae=45, Gammai=70, Gammar=0.007568
    # ce = 1.5*45=67.5, ci = 1.5*70=105, cr = 0.25*0.007568=0.001892
    # But the checkpoint uses cr in the Kr sense: Ar=210/1.1^2=173.55
    # Actually from the forward script: Ar = 210/(rou*rou) = 210/1.21 = 173.55
    # ce=1.5*45=67.5, ci=1.5*70=105, cr=0.25*0.007568=0.001892
    
    # Recreate with same params as the training
    model.__init__(
        np.zeros((800, 3)),  # Xlbtrain placeholder
        np.zeros((800, 3)),  # Xubtrain placeholder
        np.zeros((800, 3)),  # Ylbtrain placeholder
        np.zeros((800, 3)),  # Yubtrain placeholder
        np.zeros((800, 3)),  # T0train placeholder
        np.zeros((4000, 3)), # X_f_train placeholder
        NN_layers,
        rho, 67.5, 105.0, 0.001892, 3.0,  # rou, ce, ci, cr, beta
        81.0, 0.02, 173.55,  # Ae, Ai, Ar
        79.0, 400.0,  # Aer, Aei
    )
    model.net_u.load_state_dict(checkpoint["model"])
    model.net_u.to(device)
    model.net_u.eval()

    results = {}
    all_refs, all_preds = [], []

    for time_label, ref_file in REFERENCE_FILES.items():
        ref_path = data_dir / ref_file
        if not ref_path.exists():
            print(f"  [warn] missing: {ref_path}")
            continue
        x_mesh, y_mesh, data = read_reference(str(ref_path))
        ny, nx = x_mesh.shape
        t_val = float(time_label)
        X = np.column_stack([x_mesh.reshape(-1), y_mesh.reshape(-1), np.full(nx * ny, t_val)])
        with torch.no_grad():
            pred = model.predict(X).cpu().numpy()
        ref = data.reshape(-1, 3)
        error = np.abs(ref - pred)
        all_refs.append(ref)
        all_preds.append(pred)
        time_metrics = {}
        for idx, name in enumerate(("Te", "Ti", "Tr")):
            time_metrics[name] = {
                "L2": float(np.sqrt(np.mean(np.square(error[:, idx]))) / np.sqrt(np.mean(np.square(ref[:, idx])))),
                "L1": float(np.mean(error[:, idx])),
                "Linf": float(np.max(error[:, idx])),
            }
        results[time_label] = time_metrics
        print(f"  t={time_label}: Te L2={time_metrics['Te']['L2']:.4f}, Ti L2={time_metrics['Ti']['L2']:.4f}, Tr L2={time_metrics['Tr']['L2']:.4f}")

    all_refs = np.concatenate(all_refs, axis=0)
    all_preds = np.concatenate(all_preds, axis=0)
    error = np.abs(all_refs - all_preds)
    aggregate = {}
    for idx, name in enumerate(("Te", "Ti", "Tr")):
        aggregate[name] = {
            "L2": float(np.sqrt(np.mean(np.square(error[:, idx]))) / np.sqrt(np.mean(np.square(all_refs[:, idx])))),
            "L1": float(np.mean(error[:, idx])),
            "Linf": float(np.max(error[:, idx])),
        }

    metrics = {
        "case": "example3",
        "reference": "interpolated_80x80_from20",
        "reference_source": "aei400_krar_20",
        "transfer_stages": [70, 400],
        "final_stage": 400,
        "kr_mode": "constant",
        "metrics_available": True,
        "aggregate": aggregate,
        "times": results,
    }
    os.makedirs(os.path.dirname(str(output_json)), exist_ok=True)
    with open(str(output_json), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n[ok] wrote {output_json}")
    print(f"\nAggregate:")
    for name in ("Te", "Ti", "Tr"):
        print(f"  {name}: L2={aggregate[name]['L2']:.4f}, L1={aggregate[name]['L1']:.4f}, Linf={aggregate[name]['Linf']:.4f}")

if __name__ == "__main__":
    main()
