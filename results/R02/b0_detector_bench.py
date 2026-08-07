#!/usr/bin/env python3
"""results/R02/b0_detector_bench.py — B0: pomiar latencji/Hz/VRAM detektora (bramka wczesna R0.2).

Mierzy L_det (med, p95), osiągalny Hz i ślad VRAM detektora (YOLO-World) na TYM sprzęcie.
NIE mierzy jakości detekcji (to G1/G2) — latencja jest content-niezależna, więc klatka syntetyczna
320×240 mono jest metodologicznie wystarczająca. Reżim ustawiany etykietą (--regime): 'idle' (bez symu)
vs 'sim' (run_stack.sh żywy → kontencja render D3D12 ↔ inferencja CUDA).

VRAM z nvidia-smi (GLOBALNY): idle → after_load = ślad detektora; sim → baseline=sim, peak=sim+detektor.

Kryteria §4 (dwustronne): PASS L_det p95 ≤ 800 ms; FAIL > 1000 ms. VRAM PASS peak ≤ 11 GB; FAIL > 12 GB.
Uruchom (venv): .b0deps/bin/python results/R02/b0_detector_bench.py --regime idle
"""
from __future__ import annotations
import argparse, json, os, statistics, subprocess, time
import numpy as np


def vram_used_mib() -> int:
    r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True)
    return int(r.stdout.strip().splitlines()[0])


def make_frame(w=320, h=240):
    """Deterministyczna klatka mono→3ch: gradient + jasny blob (imitacja celu)."""
    base = np.tile(np.linspace(20, 120, w, dtype=np.uint8), (h, 1))
    base[100:140, 150:190] = 220
    return np.stack([base, base, base], axis=-1)  # HxWx3 uint8


def pct(sorted_vals, p):
    k = int(round((p / 100.0) * (len(sorted_vals) - 1)))
    return sorted_vals[k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default=".b0deps/weights/yolov8s-worldv2.pt")
    ap.add_argument("--phrase", default="drone")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--cadence", type=float, default=1.0)   # 1 Hz
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--regime", default="idle")
    ap.add_argument("--out", default="results/R02/b0_latency.json")
    args = ap.parse_args()

    os.environ.setdefault("YOLO_VERBOSE", "False")
    import torch
    cuda = torch.cuda.is_available()
    dev_name = torch.cuda.get_device_name(0) if cuda else "CPU"
    torch_ver = torch.__version__
    cap = tuple(torch.cuda.get_device_capability(0)) if cuda else None
    vram_base = vram_used_mib()

    from ultralytics import YOLOWorld
    os.makedirs(os.path.dirname(args.weights), exist_ok=True)
    model = YOLOWorld(args.weights)            # pobiera przy braku pliku
    dev = 0 if cuda else "cpu"
    if cuda:
        model.to("cuda")
    model.set_classes([args.phrase])
    frame = make_frame()

    # warmup (kompilacja kerneli/alokacja) — NIE liczony
    for _ in range(args.warmup):
        model.predict(frame, verbose=False, device=dev, imgsz=args.imgsz, conf=0.001)
    if cuda:
        torch.cuda.synchronize()
    vram_after_load = vram_used_mib()

    lat_ms, vram_peak = [], vram_after_load
    for _ in range(args.n):
        t0 = time.perf_counter()
        model.predict(frame, verbose=False, device=dev, imgsz=args.imgsz, conf=0.001)
        if cuda:
            torch.cuda.synchronize()
        lat_ms.append((time.perf_counter() - t0) * 1000.0)
        vram_peak = max(vram_peak, vram_used_mib())
        rem = args.cadence - (time.perf_counter() - t0)
        if rem > 0:
            time.sleep(rem)

    s = sorted(lat_ms)
    res = {
        "regime": args.regime, "device": dev_name, "cuda": cuda, "torch": torch_ver,
        "compute_cap": cap, "imgsz": args.imgsz, "phrase": args.phrase,
        "n": args.n, "warmup": args.warmup, "cadence_s": args.cadence,
        "lat_ms": {"med": round(statistics.median(lat_ms), 1), "p95": round(pct(s, 95), 1),
                   "mean": round(statistics.mean(lat_ms), 1), "min": round(min(lat_ms), 1),
                   "max": round(max(lat_ms), 1)},
        "achievable_hz_single": round(1000.0 / statistics.median(lat_ms), 2),
        "vram_mib": {"baseline": vram_base, "after_load": vram_after_load, "peak": vram_peak,
                     "detector_footprint_vs_baseline": vram_after_load - vram_base},
        "vram_total_mib": 12227,
        "headroom_mib_at_peak": 12227 - vram_peak,
    }
    print(json.dumps(res, indent=2))
    prev = []
    if os.path.exists(args.out):
        try:
            prev = json.load(open(args.out))
        except Exception:
            prev = []
    prev.append(res)
    json.dump(prev, open(args.out, "w"), indent=2)
    print(f"[b0] zapisano do {args.out} (regime={args.regime})")


if __name__ == "__main__":
    main()
