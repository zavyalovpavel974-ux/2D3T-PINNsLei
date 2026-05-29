"""Ex3 coordinate sanity check: compare (x,y,t) vs (y,x,t) evaluation."""
import json, os, re, sys
from pathlib import Path
import numpy as np
import torch

sys.argv = [
    "sanity_check.py",
    "--transfer-stages", "70,400",
    "--kr-mode", "constant",
    "--no-use-ff",
    "--use-log-loss",
    "--lambda-brd", "20",
    "--lambda-init", "10",
]

WORKDIR = Path("runs/ex3_transfer_clean_20260528/workdir")
sys.path.insert(0, str(WORKDIR))

from sub_2D3T_wei_aei700_wer_krartr_time import PhysicsInformedNN

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
    return x_mesh, y_mesh, data[:, :, (1, 2, 0)]

def compute_errors(ref, pred):
    error = np.abs(ref - pred)
    result = {}
    for idx, name in enumerate(("Te", "Ti", "Tr")):
        result[name] = {
            "L2": float(np.sqrt(np.mean(np.square(error[:, idx]))) / np.sqrt(np.mean(np.square(ref[:, idx])))),
            "L1": float(np.mean(error[:, idx])),
            "Linf": float(np.max(error[:, idx])),
        }
    return result

def main():
    checkpoint_path = "runs/ex3_transfer_clean_20260528/checkpoints/example3/latest.pt"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    print(f"Checkpoint: phase={checkpoint.get('phase')}, Aei={checkpoint.get('Aei')}, it={checkpoint.get('it')}")
    
    NN_layers = [[3] + [60] * 6 + [3]]
    model = PhysicsInformedNN.__new__(PhysicsInformedNN)
    model.__init__(
        np.zeros((800, 3)), np.zeros((800, 3)), np.zeros((800, 3)), np.zeros((800, 3)),
        np.zeros((800, 3)), np.zeros((4000, 3)), NN_layers,
        1.1, 67.5, 105.0, 0.001892, 3.0, 81.0, 0.02, 173.55, 79.0, 400.0,
    )
    model.net_u.load_state_dict(checkpoint["model"])
    model.net_u.to(device)
    model.net_u.eval()

    ref_file = WORKDIR / "sol1_wei_aei400_wer_krar_1.txt"
    x_mesh, y_mesh, data = read_reference(str(ref_file))
    ny, nx = x_mesh.shape
    
    # Standard evaluation: (x, y, t)
    X_std = np.column_stack([x_mesh.reshape(-1), y_mesh.reshape(-1), np.full(nx * ny, 1.0)])
    with torch.no_grad():
        pred_std = model.predict(X_std).cpu().numpy()
    
    # Swapped evaluation: (y, x, t)
    X_swap = np.column_stack([y_mesh.reshape(-1), x_mesh.reshape(-1), np.full(nx * ny, 1.0)])
    with torch.no_grad():
        pred_swap = model.predict(X_swap).cpu().numpy()
    
    ref = data.reshape(-1, 3)
    
    err_std = compute_errors(ref, pred_std)
    err_swap = compute_errors(ref, pred_swap)
    
    print("\n=== Coordinate Sanity Check (t=1.0) ===")
    print("\nStandard (x, y, t):")
    for name in ("Te", "Ti", "Tr"):
        print(f"  {name}: L2={err_std[name]['L2']:.4e}, L1={err_std[name]['L1']:.4e}, Linf={err_std[name]['Linf']:.4e}")
    
    print("\nSwapped (y, x, t):")
    for name in ("Te", "Ti", "Tr"):
        print(f"  {name}: L2={err_swap[name]['L2']:.4e}, L1={err_swap[name]['L1']:.4e}, Linf={err_swap[name]['Linf']:.4e}")
    
    print("\nRatio (swapped/standard):")
    for name in ("Te", "Ti", "Tr"):
        ratio = err_swap[name]['L2'] / max(err_std[name]['L2'], 1e-15)
        print(f"  {name} L2: {ratio:.2f}x")
    
    # Determine correct convention
    std_total = sum(err_std[n]['L2'] for n in ("Te", "Ti", "Tr"))
    swap_total = sum(err_swap[n]['L2'] for n in ("Te", "Ti", "Tr"))
    if swap_total < std_total:
        print(f"\n=> Swapped (y,x,t) is BETTER (ratio={swap_total/std_total:.2f})")
        print("   Use coordinate_evaluation=swapped_xy")
    else:
        print(f"\n=> Standard (x,y,t) is BETTER (ratio={std_total/swap_total:.2f})")
        print("   Use coordinate_evaluation=standard_xy")

if __name__ == "__main__":
    main()
