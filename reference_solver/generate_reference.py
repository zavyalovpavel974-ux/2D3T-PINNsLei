#!/usr/bin/env python
"""Generate and export reference solutions for the 2D 3T PINNs paper.

The public 2D3T-PINNs repository does not include the numerical reference
solutions read by the author scripts. This utility provides a reproducible
replacement path:

1. solve the 2-D 3-T heat-conduction equations with a NumPy/SciPy JFNK solver;
2. save multi-time snapshots in ``reference_snapshots.npz``;
3. export the text files expected by the author code.

The text export intentionally stores variables in the order used by the author
reader: photon, electron, ion. The author scripts then remap ``(1, 2, 0)`` to
obtain ``Te, Ti, Tr``.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, Sequence, Tuple

import numpy as np
from scipy.sparse.linalg import LinearOperator, gmres


DEFAULT_TIMES = (1e-5, 0.3, 0.5, 0.7, 1.0)


@dataclass
class PhysicalParams:
    rho: float = 1.1
    Ae: float = 81.0
    Ai: float = 0.02
    Ar: float = 210.0 / (1.1 * 1.1)
    Aer: float = 79.0
    Aei: float = 700.0
    Gammae: float = 45.0
    Gammai: float = 70.0
    Gammar: float = 0.007568
    t0: float = 3e-4
    kr_power: float = 1.0

    @property
    def cve(self) -> float:
        return 1.5 * self.Gammae

    @property
    def cvi(self) -> float:
        return 1.5 * self.Gammai


@dataclass
class ReferenceConfig:
    nx: int = 80
    ny: int = 80
    grid_convention: str = "cell_center"
    dt_init: float = 5e-3
    dt_min: float = 1e-6
    dt_max: float = 2e-2
    newton_tol: float = 1e-3
    newton_max: int = 8
    gmres_tol: float = 1e-5
    gmres_restart: int = 40
    gmres_maxiter: int = 120
    line_search_max: int = 8
    temp_floor: float = 1e-10
    log_every_step: bool = False
    log_rejected_steps: bool = False
    debug_on_failure: bool = False
    detailed_diagnostics: bool = False


def tr_surface(t: float, nx: int, t0: float) -> np.ndarray:
    return np.full((nx,), t0 + 2.0 * t, dtype=np.float64)


def make_grid(n: int, convention: str) -> np.ndarray:
    if convention == "endpoint":
        return np.linspace(0.0, 1.0, n, dtype=np.float64)
    if convention == "cell_center":
        return (np.arange(n, dtype=np.float64) + 0.5) / n
    raise ValueError(f"unknown grid convention: {convention}")


def infer_grid_convention(values: np.ndarray) -> str:
    if len(values) < 2:
        return "unknown"
    if np.allclose(values, make_grid(len(values), "cell_center"), rtol=0.0, atol=1e-12):
        return "cell_center"
    if np.allclose(values, make_grid(len(values), "endpoint"), rtol=0.0, atol=1e-12):
        return "endpoint"
    return "custom"


def pack(Te: np.ndarray, Ti: np.ndarray, Tr: np.ndarray) -> np.ndarray:
    return np.concatenate([Te.ravel(), Ti.ravel(), Tr.ravel()])


def unpack(U: np.ndarray, ny: int, nx: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = nx * ny
    return U[:n].reshape(ny, nx), U[n : 2 * n].reshape(ny, nx), U[2 * n :].reshape(ny, nx)


def diffusion(T: np.ndarray, K: np.ndarray, dx: float, dy: float, top_dirichlet: np.ndarray | None = None) -> np.ndarray:
    T_left = np.concatenate([T[:, :1], T[:, :-1]], axis=1)
    T_right = np.concatenate([T[:, 1:], T[:, -1:]], axis=1)
    K_left = np.concatenate([K[:, :1], K[:, :-1]], axis=1)
    K_right = np.concatenate([K[:, 1:], K[:, -1:]], axis=1)
    flux_x = (K_right * (T_right - T) - K_left * (T - T_left)) / (dx * dx)

    T_bottom = np.concatenate([T[:1, :], T[:-1, :]], axis=0)
    K_bottom = np.concatenate([K[:1, :], K[:-1, :]], axis=0)
    if top_dirichlet is None:
        T_top = np.concatenate([T[1:, :], T[-1:, :]], axis=0)
        K_top = np.concatenate([K[1:, :], K[-1:, :]], axis=0)
    else:
        T_top = T.copy()
        T_top[-1, :] = top_dirichlet
        T_top[:-1, :] = T[1:, :]
        K_top = K
    flux_y = (K_top * (T_top - T) - K_bottom * (T - T_bottom)) / (dy * dy)
    return flux_x + flux_y


def residual(
    U: np.ndarray,
    U_old: np.ndarray,
    dt: float,
    x: np.ndarray,
    y: np.ndarray,
    t_new: float,
    p: PhysicalParams,
    cfg: ReferenceConfig,
) -> np.ndarray:
    nx, ny = len(x), len(y)
    dx, dy = float(x[1] - x[0]), float(y[1] - y[0])
    Te, Ti, Tr = unpack(U, ny, nx)
    Te0, Ti0, Tr0 = unpack(U_old, ny, nx)

    Te = np.maximum(Te, cfg.temp_floor)
    Ti = np.maximum(Ti, cfg.temp_floor)
    Tr = np.maximum(Tr, cfg.temp_floor)

    cvr = 0.25 * p.Gammar * (Tr**3)
    Ke = p.Ae * (Te**2.5)
    Ki = p.Ai * (Ti**2.5)
    Kr = p.Ar * (Tr**p.kr_power)
    wei = p.Aei * p.rho * (Te ** (-2.0 / 3.0))
    wer = p.Aer * p.rho * (Te ** (-0.5))

    de = diffusion(Te, Ke, dx, dy)
    di = diffusion(Ti, Ki, dx, dy)
    dr = diffusion(Tr, Kr, dx, dy, top_dirichlet=tr_surface(t_new, nx, p.t0))

    Re = p.cve * (Te - Te0) / dt - de / p.rho - (wei * (Ti - Te) + wer * (Tr - Te))
    Ri = p.cvi * (Ti - Ti0) / dt - di / p.rho - wei * (Te - Ti)
    Rr = cvr * (Tr - Tr0) / dt - dr / p.rho - wer * (Te - Tr)
    Rr[-1, :] = Tr[-1, :] - tr_surface(t_new, nx, p.t0)
    return pack(Re, Ri, Rr)


def build_preconditioner(U: np.ndarray, nx: int, ny: int, dt: float, dx: float, dy: float, p: PhysicalParams, cfg: ReferenceConfig) -> LinearOperator:
    Te, Ti, Tr = unpack(U, ny, nx)
    Te = np.maximum(Te, cfg.temp_floor)
    Ti = np.maximum(Ti, cfg.temp_floor)
    Tr = np.maximum(Tr, cfg.temp_floor)

    cvr = 0.25 * p.Gammar * (Tr**3)
    Ke = p.Ae * (Te**2.5)
    Ki = p.Ai * (Ti**2.5)
    Kr = p.Ar * (Tr**p.kr_power)
    wei = p.Aei * p.rho * (Te ** (-2.0 / 3.0))
    wer = p.Aer * p.rho * (Te ** (-0.5))

    eps = 1e-10
    diag_e = (p.cve / dt + 2 * Ke / (dx * dx) + 2 * Ke / (dy * dy)) / p.rho + wei + wer + eps
    diag_i = (p.cvi / dt + 2 * Ki / (dx * dx) + 2 * Ki / (dy * dy)) / p.rho + wei + eps
    diag_r = (cvr / dt + 2 * Kr / (dx * dx) + 2 * Kr / (dy * dy)) / p.rho + wer + eps
    diag = np.concatenate([diag_e.ravel(), diag_i.ravel(), diag_r.ravel()])
    n = 3 * nx * ny
    return LinearOperator((n, n), matvec=lambda v: v / diag, dtype=np.float64)


def gmres_callback_summary(values: list[float], callback_type: str) -> dict:
    finite = [float(v) for v in values if np.isfinite(v)]
    summary = {
        "callback_type": callback_type,
        "iterations": len(values),
        "finite_iterations": len(finite),
        "tail": [float(v) for v in values[-10:]],
    }
    if finite:
        summary.update({
            "first": finite[0],
            "last": finite[-1],
            "min": min(finite),
            "max": max(finite),
        })
    return summary


def solve_gmres(A: LinearOperator, b: np.ndarray, M: LinearOperator, cfg: ReferenceConfig):
    residuals: list[float] = []

    def record_callback(value) -> None:
        try:
            residuals.append(float(value) if np.isscalar(value) else float(np.linalg.norm(value)))
        except (TypeError, ValueError, FloatingPointError):
            residuals.append(float("nan"))

    try:
        x, info = gmres(
            A,
            b,
            M=M,
            restart=cfg.gmres_restart,
            maxiter=cfg.gmres_maxiter,
            atol=0.0,
            rtol=cfg.gmres_tol,
            callback=record_callback,
            callback_type="pr_norm",
        )
        return x, info, gmres_callback_summary(residuals, "pr_norm")
    except TypeError:
        residuals.clear()
        x, info = gmres(
            A,
            b,
            M=M,
            restart=cfg.gmres_restart,
            maxiter=cfg.gmres_maxiter,
            atol=0.0,
            tol=cfg.gmres_tol,
            callback=record_callback,
        )
        return x, info, gmres_callback_summary(residuals, "legacy")


def gmres_log_text(summary) -> str:
    if not summary:
        return "gmres_iterations=None gmres_last=None"
    return f"gmres_iterations={summary.get('iterations')} gmres_last={summary.get('last')}"


def vector_summary(v: np.ndarray) -> dict:
    finite = np.isfinite(v)
    summary = {
        "finite": bool(finite.all()),
        "size": int(v.size),
        "nonfinite_count": int(v.size - finite.sum()),
    }
    if finite.any():
        vf = v[finite]
        summary.update({
            "norm": float(np.linalg.norm(vf)),
            "max_abs": float(np.max(np.abs(vf))),
            "min": float(np.min(vf)),
            "max": float(np.max(vf)),
        })
    return summary


def values_summary(values: list[float]) -> dict:
    finite = [float(v) for v in values if np.isfinite(v)]
    summary = {
        "count": len(values),
        "finite_count": len(finite),
    }
    if finite:
        summary.update({
            "first": finite[0],
            "last": finite[-1],
            "min": min(finite),
            "max": max(finite),
        })
    return summary


def state_summary(U: np.ndarray, ny: int, nx: int, cfg: ReferenceConfig) -> dict:
    Te, Ti, Tr = unpack(U, ny, nx)
    out = {}
    for name, arr in (("Te", Te), ("Ti", Ti), ("Tr", Tr)):
        finite = np.isfinite(arr)
        item = {
            "finite": bool(finite.all()),
            "nonfinite_count": int(arr.size - finite.sum()),
            "below_floor_count": int(np.sum(arr < cfg.temp_floor)),
            "nonpositive_count": int(np.sum(arr <= 0.0)),
        }
        if finite.any():
            af = arr[finite]
            item.update({
                "min": float(np.min(af)),
                "max": float(np.max(af)),
                "mean": float(np.mean(af)),
            })
        out[name] = item
    return out


def jfnk_step(U: np.ndarray, F, nx: int, ny: int, dt: float, dx: float, dy: float, p: PhysicalParams, cfg: ReferenceConfig):
    n = U.size
    u = U.copy()
    last_norm = np.inf
    last_gmres_info = None
    last_gmres_summary = None
    collect_details = cfg.debug_on_failure or cfg.detailed_diagnostics
    newton_diagnostics = []
    for k in range(cfg.newton_max):
        R = F(u)
        norm_R = float(np.linalg.norm(R) / np.sqrt(R.size))
        last_norm = norm_R
        iteration_details = None
        if collect_details:
            iteration_details = {
                "iteration": k + 1,
                "norm_R": norm_R,
                "state": state_summary(u, ny, nx, cfg),
            }
        if norm_R < cfg.newton_tol:
            if collect_details:
                newton_diagnostics.append(iteration_details)
            return u, True, last_norm, k + 1, {
                "reason": "converged",
                "gmres_info": last_gmres_info,
                "gmres_summary": last_gmres_summary,
                "newton_diagnostics": newton_diagnostics if collect_details else None,
            }

        jv_eps_values = []

        def Jv(v: np.ndarray) -> np.ndarray:
            norm_v = np.linalg.norm(v)
            if norm_v < 1e-14:
                return np.zeros_like(v)
            eps = np.sqrt(np.finfo(u.dtype).eps) * (1.0 + np.linalg.norm(u)) / norm_v
            if collect_details:
                jv_eps_values.append(float(eps))
            return (F(u + eps * v) - R) / eps

        A = LinearOperator((n, n), matvec=Jv, dtype=np.float64)
        M = build_preconditioner(u, nx, ny, dt, dx, dy, p, cfg)
        dU, info, gmres_summary = solve_gmres(A, -R, M, cfg)
        last_gmres_info = int(info) if np.isscalar(info) else info
        last_gmres_summary = gmres_summary

        alpha, ok = 1.0, False
        trial_norm = np.inf
        accepted_alpha = None
        line_search_trials = []
        for _ in range(cfg.line_search_max):
            u_try = u + alpha * dU
            trial_norm = float(np.linalg.norm(F(u_try)) / np.sqrt(R.size))
            accepted = trial_norm < norm_R
            if collect_details:
                line_search_trials.append({
                    "alpha": alpha,
                    "trial_norm": trial_norm,
                    "accepted": bool(accepted),
                    "state": state_summary(u_try, ny, nx, cfg),
                })
            if accepted:
                u = u_try
                ok = True
                accepted_alpha = alpha
                break
            alpha *= 0.5
        if collect_details:
            iteration_details.update({
                "gmres_info": last_gmres_info,
                "gmres_summary": gmres_summary,
                "jv_eps_summary": values_summary(jv_eps_values),
                "dU_summary": vector_summary(dU),
                "line_search_trials": line_search_trials,
                "accepted_alpha": accepted_alpha,
            })
            newton_diagnostics.append(iteration_details)
        if not ok:
            return u, False, last_norm, k + 1, {
                "reason": "line_search_failed",
                "gmres_info": last_gmres_info,
                "gmres_summary": last_gmres_summary,
                "alpha": alpha,
                "trial_norm": trial_norm,
                "newton_diagnostics": newton_diagnostics if collect_details else None,
            }
    return u, False, last_norm, cfg.newton_max, {
        "reason": "newton_max",
        "gmres_info": last_gmres_info,
        "gmres_summary": last_gmres_summary,
        "newton_diagnostics": newton_diagnostics if collect_details else None,
    }


def snapshot_from_state(U: np.ndarray, ny: int, nx: int, t: float, p: PhysicalParams) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    Te, Ti, Tr = unpack(U.copy(), ny, nx)
    Tr[-1, :] = tr_surface(t, nx, p.t0)
    return Te, Ti, Tr


def _save_reference_checkpoint(path: Path, x: np.ndarray, y: np.ndarray, U: np.ndarray, t: float, dt: float, step: int, snapshots, history, diagnostics=None, grid_convention: str = "unknown") -> None:
    data = {
        "x": x,
        "y": y,
        "grid_convention": np.array([grid_convention], dtype=object),
        "U": U,
        "t": np.array([t], dtype=np.float64),
        "dt": np.array([dt], dtype=np.float64),
        "step": np.array([step], dtype=np.int64),
        "history_json": np.array([json.dumps(history)], dtype=object),
    }
    if diagnostics is not None:
        data["diagnostics_json"] = np.array([json.dumps(diagnostics)], dtype=object)
    for ts, (Te, Ti, Tr) in sorted(snapshots.items()):
        tag = f"{ts:.10f}"
        data[f"Te_{tag}"] = Te
        data[f"Ti_{tag}"] = Ti
        data[f"Tr_{tag}"] = Tr
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **data)


def _load_reference_checkpoint(path: Path):
    d = np.load(path, allow_pickle=True)
    x = np.asarray(d["x"])
    y = np.asarray(d["y"])
    snapshots = {}
    for key in d.files:
        if key.startswith("Te_"):
            tag = key[3:]
            snapshots[float(tag)] = (np.asarray(d[f"Te_{tag}"]), np.asarray(d[f"Ti_{tag}"]), np.asarray(d[f"Tr_{tag}"]))
    history_raw = d["history_json"][0]
    history = json.loads(str(history_raw)) if str(history_raw) else []
    grid_convention = str(d["grid_convention"][0]) if "grid_convention" in d.files else infer_grid_convention(x)
    return x, y, np.asarray(d["U"]), float(d["t"][0]), float(d["dt"][0]), int(d["step"][0]), snapshots, history, grid_convention


def solve_reference(
    p: PhysicalParams,
    cfg: ReferenceConfig,
    snapshot_times: Sequence[float],
    checkpoint_path: Path | None = None,
    resume_checkpoint: Path | None = None,
    checkpoint_interval_steps: int = 25,
    max_walltime_seconds: float = 0.0,
):
    x = make_grid(cfg.nx, cfg.grid_convention)
    y = make_grid(cfg.ny, cfg.grid_convention)
    dx, dy = float(x[1] - x[0]), float(y[1] - y[0])
    X, _Y = np.meshgrid(x, y)
    U = pack(np.full_like(X, p.t0), np.full_like(X, p.t0), np.full_like(X, p.t0))

    targets = sorted(set(float(t) for t in snapshot_times if 0.0 <= t <= 1.0))
    snapshots: Dict[float, Tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    history = []
    diagnostics = []
    t, dt, step = 0.0, cfg.dt_init, 0
    active_grid_convention = cfg.grid_convention
    if resume_checkpoint:
        x, y, U, t, dt, step, snapshots, history, loaded_grid_convention = _load_reference_checkpoint(resume_checkpoint)
        if loaded_grid_convention != "unknown":
            active_grid_convention = loaded_grid_convention
        dx, dy = float(x[1] - x[0]), float(y[1] - y[0])
        print(f"[reference] resumed {resume_checkpoint} at step={step} t={t:.6f} dt={dt:.2e}", flush=True)
    start = time.time()
    while t < 1.0 - 1e-14:
        dt = min(dt, 1.0 - t)
        U_old = U.copy()
        F = lambda U_new: residual(U_new, U_old, dt, x, y, t + dt, p, cfg)
        U_new, ok, res, nit, details = jfnk_step(U_old, F, cfg.nx, cfg.ny, dt, dx, dy, p, cfg)
        if not ok:
            attempted_dt = dt
            dt *= 0.5
            event = {
                "type": "rejected_step",
                "step": step + 1,
                "time": t,
                "attempted_dt": attempted_dt,
                "next_dt": dt,
                "newton_iters": nit,
                "residual_norm": res,
                **details,
            }
            diagnostics.append(event)
            if cfg.log_rejected_steps:
                print(
                    "[reference] reject "
                    f"step={step + 1} t={t:.6f} attempted_dt={attempted_dt:.3e} "
                    f"next_dt={dt:.3e} newton={nit} residual={res:.3e} "
                    f"reason={details.get('reason')} gmres_info={details.get('gmres_info')} "
                    f"{gmres_log_text(details.get('gmres_summary'))}",
                    flush=True,
                )
            if dt < cfg.dt_min:
                debug_path = None
                if checkpoint_path and cfg.debug_on_failure:
                    debug_path = checkpoint_path.with_suffix(".failed.npz")
                    _save_reference_checkpoint(debug_path, x, y, U, t, dt, step, snapshots, history, diagnostics, active_grid_convention)
                    print(f"[reference] wrote failure debug checkpoint {debug_path}", flush=True)
                suffix = f"; debug_checkpoint={debug_path}" if debug_path else ""
                raise RuntimeError(f"Reference solve failed: dt<{cfg.dt_min} at t={t:.6f}; last residual={res:.3e}{suffix}")
            continue

        t_prev, t = t, t + dt
        U = U_new
        step += 1
        history.append({
            "step": step,
            "time": t,
            "dt": dt,
            "newton_iters": nit,
            "residual_norm": res,
            "gmres_info": details.get("gmres_info"),
            "gmres_summary": details.get("gmres_summary"),
            "newton_diagnostics": details.get("newton_diagnostics"),
        })
        if cfg.log_every_step or step % 25 == 0 or t >= 1.0 - 1e-14:
            print(
                f"[reference] step={step} t={t:.6f} dt={dt:.2e} "
                f"newton={nit} residual={res:.3e} gmres_info={details.get('gmres_info')} "
                f"{gmres_log_text(details.get('gmres_summary'))}",
                flush=True,
            )

        for ts in targets:
            if ts in snapshots:
                continue
            if t_prev - 1e-14 <= ts <= t + 1e-14:
                a = (ts - t_prev) / max(dt, 1e-15)
                snapshots[ts] = snapshot_from_state(U_old + a * (U - U_old), cfg.ny, cfg.nx, ts, p)
        if nit <= 3 and dt < cfg.dt_max:
            dt = min(cfg.dt_max, dt * 1.2)
        if checkpoint_path and checkpoint_interval_steps > 0 and step % checkpoint_interval_steps == 0:
            _save_reference_checkpoint(checkpoint_path, x, y, U, t, dt, step, snapshots, history, diagnostics, active_grid_convention)
        if checkpoint_path and max_walltime_seconds > 0.0 and time.time() - start >= max_walltime_seconds:
            _save_reference_checkpoint(checkpoint_path, x, y, U, t, dt, step, snapshots, history, diagnostics, active_grid_convention)
            raise TimeoutError(f"reference solve reached walltime at step={step} t={t:.6f}; checkpoint={checkpoint_path}")

    print(f"[reference] done in {time.time()-start:.1f}s, steps={step}", flush=True)
    if checkpoint_path:
        _save_reference_checkpoint(checkpoint_path, x, y, U, t, dt, step, snapshots, history, diagnostics, active_grid_convention)
    return x, y, snapshots, history


def save_npz(path: Path, x: np.ndarray, y: np.ndarray, snapshots: Dict[float, Tuple[np.ndarray, np.ndarray, np.ndarray]], grid_convention: str = "unknown") -> None:
    data = {"x": x, "y": y, "grid_convention": np.array([grid_convention], dtype=object)}
    for t, (Te, Ti, Tr) in sorted(snapshots.items()):
        tag = f"{t:.10f}"
        data[f"Te_{tag}"] = Te
        data[f"Ti_{tag}"] = Ti
        data[f"Tr_{tag}"] = Tr
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **data)


def load_npz(path: Path):
    d = np.load(path)
    x = np.asarray(d["x"], dtype=np.float64)
    y = np.asarray(d["y"], dtype=np.float64)
    snapshots = {}
    for key in d.files:
        if key.startswith("Te_"):
            tag = key[3:]
            t = float(tag)
            snapshots[t] = (np.asarray(d[f"Te_{tag}"]), np.asarray(d[f"Ti_{tag}"]), np.asarray(d[f"Tr_{tag}"]))
    return x, y, snapshots


def resample_field(field: np.ndarray, x_old: np.ndarray, y_old: np.ndarray, x_new: np.ndarray, y_new: np.ndarray) -> np.ndarray:
    along_x = np.vstack([np.interp(x_new, x_old, row) for row in field])
    return np.vstack([np.interp(y_new, y_old, along_x[:, j]) for j in range(len(x_new))]).T


def resample_npz(src: Path, dst: Path, nx: int, ny: int, grid_convention: str = "cell_center") -> None:
    x_old, y_old, snapshots = load_npz(src)
    x_new = make_grid(nx, grid_convention)
    y_new = make_grid(ny, grid_convention)
    resampled = {}
    for t, (Te, Ti, Tr) in sorted(snapshots.items()):
        Te_new = resample_field(Te, x_old, y_old, x_new, y_new)
        Ti_new = resample_field(Ti, x_old, y_old, x_new, y_new)
        Tr_new = resample_field(Tr, x_old, y_old, x_new, y_new)
        Tr_new[-1, :] = tr_surface(t, nx, PhysicalParams.t0)
        resampled[t] = (Te_new, Ti_new, Tr_new)
    save_npz(dst, x_new, y_new, resampled, grid_convention)


def time_label(t: float) -> str:
    if abs(t - 1e-5) < 1e-12:
        return "1e-5"
    if abs(t - round(t)) < 1e-12:
        return str(int(round(t)))
    return str(t).replace(".", "p")


def write_author_txt(path: Path, Te: np.ndarray, Ti: np.ndarray, Tr: np.ndarray) -> None:
    if not (Te.shape == Ti.shape == Tr.shape):
        raise ValueError("Te, Ti, Tr shapes differ")
    ny, nx = Te.shape
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("(2, 3, 0)\n")
        f.write(f"((0, 0), ({ny - 1}, {nx - 1}), 0)\n")
        # Author readers remap Data[:, :, (1, 2, 0)] => Te, Ti, Tr.
        fields = (Tr, Te, Ti)
        for i in range(ny):
            for j in range(nx):
                for k, arr in enumerate(fields):
                    f.write(f"({i}, {j}, {k}, {float(arr[i, j]):.16e})\n")


def export_author_files(npz_path: Path, out_dir: Path, case: str) -> list[Path]:
    x, _y, snapshots = load_npz(npz_path)
    grid_convention = infer_grid_convention(x)
    with np.load(npz_path, allow_pickle=True) as d:
        if "grid_convention" in d.files:
            grid_convention = str(d["grid_convention"][0])
    written: list[Path] = []
    if case == "aei70_krar":
        for t, (Te, Ti, Tr) in sorted(snapshots.items()):
            filename = f"sol1_wei_aei70_wer_krar_{time_label(t)}.txt"
            path = out_dir / filename
            write_author_txt(path, Te, Ti, Tr)
            written.append(path)
    elif case == "aei700_krartr":
        if not snapshots:
            raise ValueError("no snapshots found")
        # The public author script reads only t=1 filenames for Example 5 diagnostics.
        Te, Ti, Tr = snapshots[min(snapshots, key=lambda t: abs(t - 1.0))]
        seen: set[Path] = set()
        for filename in ("sol1_wei_aei700_wer_krartr_1.txt", "sol1_wei_aei700_wer_krartr_80_1.txt"):
            path = out_dir / filename
            write_author_txt(path, Te, Ti, Tr)
            written.append(path)
            seen.add(path)
        # Keep per-time exports for independent validation and future script cleanup.
        for t, (Te, Ti, Tr) in sorted(snapshots.items()):
            path = out_dir / f"sol1_wei_aei700_wer_krartr_{time_label(t)}.txt"
            if path in seen:
                continue
            write_author_txt(path, Te, Ti, Tr)
            written.append(path)
            seen.add(path)
    else:
        raise ValueError(f"unknown case: {case}")
    metadata = {
        "case": case,
        "source_npz": str(npz_path),
        "grid_convention": grid_convention,
        "author_reader_coordinate_convention": "cell_center",
        "coordinate_consistency": grid_convention == "cell_center",
        "note": "Author txt files store indices only; existing readers map them to cell-center coordinates.",
        "written_files": [str(path) for path in written],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "reference_export_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return written


def validate_npz(path: Path) -> dict:
    d = np.load(path, allow_pickle=True)
    x, y, snapshots = load_npz(path)
    grid_convention = str(d["grid_convention"][0]) if "grid_convention" in d.files else infer_grid_convention(x)
    report = {"path": str(path), "nx": int(len(x)), "ny": int(len(y)), "grid_convention": grid_convention, "times": []}
    for t, (Te, Ti, Tr) in sorted(snapshots.items()):
        arrays = {"Te": Te, "Ti": Ti, "Tr": Tr}
        item = {"time": float(t)}
        for name, arr in arrays.items():
            item[name] = {
                "shape": list(arr.shape),
                "finite": bool(np.isfinite(arr).all()),
                "min": float(np.nanmin(arr)),
                "max": float(np.nanmax(arr)),
            }
        item["top_Tr_expected"] = float(3e-4 + 2.0 * t)
        item["top_Tr_max_abs_error"] = float(np.max(np.abs(Tr[-1, :] - item["top_Tr_expected"])))
        report["times"].append(item)
    return report


def parse_times(text: str) -> tuple[float, ...]:
    return tuple(float(x.strip()) for x in text.split(",") if x.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    solve_p = sub.add_parser("solve", help="solve a reference case and save an npz")
    solve_p.add_argument("--case", choices=["aei70_krar", "aei700_krartr"], required=True)
    solve_p.add_argument("--out", type=Path, required=True)
    solve_p.add_argument("--nx", type=int, default=80)
    solve_p.add_argument("--ny", type=int, default=80)
    solve_p.add_argument("--grid-convention", choices=["cell_center", "endpoint"], default="cell_center")
    solve_p.add_argument("--times", default="1e-5,0.3,0.5,0.7,1.0")
    solve_p.add_argument("--dt-init", type=float, default=5e-3)
    solve_p.add_argument("--dt-min", type=float, default=1e-6)
    solve_p.add_argument("--dt-max", type=float, default=2e-2)
    solve_p.add_argument("--newton-max", type=int, default=8)
    solve_p.add_argument("--gmres-maxiter", type=int, default=120)
    solve_p.add_argument("--checkpoint", type=Path)
    solve_p.add_argument("--resume-checkpoint", type=Path)
    solve_p.add_argument("--checkpoint-interval-steps", type=int, default=25)
    solve_p.add_argument("--max-walltime-seconds", type=float, default=0.0)
    solve_p.add_argument("--log-every-step", action="store_true")
    solve_p.add_argument("--log-rejected-steps", action="store_true")
    solve_p.add_argument("--debug-on-failure", action="store_true")
    solve_p.add_argument("--detailed-diagnostics", action="store_true")

    export_p = sub.add_parser("export", help="export author txt files from an npz")
    export_p.add_argument("--case", choices=["aei70_krar", "aei700_krartr"], required=True)
    export_p.add_argument("--npz", type=Path, required=True)
    export_p.add_argument("--out-dir", type=Path, required=True)

    val_p = sub.add_parser("validate", help="validate a reference npz")
    val_p.add_argument("--npz", type=Path, required=True)
    val_p.add_argument("--json-out", type=Path)

    res_p = sub.add_parser("resample", help="resample an npz for pipeline smoke tests")
    res_p.add_argument("--npz", type=Path, required=True)
    res_p.add_argument("--out", type=Path, required=True)
    res_p.add_argument("--nx", type=int, required=True)
    res_p.add_argument("--ny", type=int, required=True)
    res_p.add_argument("--grid-convention", choices=["cell_center", "endpoint"], default="cell_center")

    args = parser.parse_args()
    if args.cmd == "solve":
        if args.case == "aei70_krar":
            params = PhysicalParams(Aei=70.0, kr_power=0.0)
        else:
            params = PhysicalParams(Aei=700.0, kr_power=1.0)
        cfg = ReferenceConfig(
            nx=args.nx,
            ny=args.ny,
            grid_convention=args.grid_convention,
            dt_init=args.dt_init,
            dt_min=args.dt_min,
            dt_max=args.dt_max,
            newton_max=args.newton_max,
            gmres_maxiter=args.gmres_maxiter,
            log_every_step=args.log_every_step,
            log_rejected_steps=args.log_rejected_steps,
            debug_on_failure=args.debug_on_failure,
            detailed_diagnostics=args.detailed_diagnostics,
        )
        x, y, snapshots, history = solve_reference(
            params,
            cfg,
            parse_times(args.times),
            checkpoint_path=args.checkpoint,
            resume_checkpoint=args.resume_checkpoint,
            checkpoint_interval_steps=args.checkpoint_interval_steps,
            max_walltime_seconds=args.max_walltime_seconds,
        )
        save_npz(args.out, x, y, snapshots, infer_grid_convention(x))
        meta = {"case": args.case, "params": asdict(params), "config": asdict(cfg), "history": history}
        args.out.with_suffix(".history.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"[ok] wrote {args.out}")
    elif args.cmd == "export":
        written = export_author_files(args.npz, args.out_dir, args.case)
        for path in written:
            print(path)
    elif args.cmd == "validate":
        report = validate_npz(args.npz)
        text = json.dumps(report, indent=2, ensure_ascii=False)
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(text + "\n", encoding="utf-8")
        print(text)
    elif args.cmd == "resample":
        resample_npz(args.npz, args.out, args.nx, args.ny, args.grid_convention)
        print(f"[ok] wrote {args.out}")


if __name__ == "__main__":
    main()
