#!/usr/bin/env python3
"""tools/w_tilt.py — W B5: przechył (kąt od pionu) w oknie hoveru, offline z boot.ulg.

Źródło: vehicle_attitude (kwaternion q=[w,x,y,z]). Przechył od pionu:
  tilt = acos(R[2][2]),  R[2][2] = 1 - 2*(qx^2 + qy^2)   [kąt między osią -Z body a pionem].
Okno hoveru: z trace.jsonl (eventy hover_start/hover_end, pole 'mono') mostkowane do px4-ts przez
rzędy EKF (mono↔ts). Brak okna ⇒ całość ulogu (z notą). Wyjście: json per boot (mean/median/p95 deg).

Użycie:  w_tilt.py <OUTDIR>   (katalog z boot.ulg + trace.jsonl)  [--out plik.json]
"""
import os, sys, json, math, argparse


def _load_trace_window(outdir):
    """(ts_lo_us, ts_hi_us) okna hoveru w jednostkach ulogu (us od bootu) albo None.
    Most: ulog timestamp (hrt us od bootu) ≈ gz sim time (lockstep SITL) → używamy pola 'sim'
    eventów hover_start/hover_end (sekundy) × 1e6. EKF trace 'ts' to czas ABSOLUTNY (≠ ulog) — nie do mostu."""
    tp = os.path.join(outdir, "trace.jsonl")
    if not os.path.exists(tp):
        return None, "brak trace.jsonl"
    hs_sim, he_sim = None, None
    for ln in open(tp, errors="replace"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if r.get("t") == "event":
            if r.get("ev") == "hover_start":
                hs_sim = r.get("sim")
            elif r.get("ev") == "hover_end":
                he_sim = r.get("sim")
    if hs_sim is None or he_sim is None:
        return None, "brak eventów hover_start/hover_end (sim)"
    return (hs_sim * 1e6, he_sim * 1e6), None


def tilt_series(ulog_path):
    from pyulog import ULog
    ul = ULog(ulog_path, ["vehicle_attitude"])
    for d in ul.data_list:
        if d.name != "vehicle_attitude":
            continue
        ts = list(d.data.get("timestamp", []))
        qw = list(d.data.get("q[0]", [])); qx = list(d.data.get("q[1]", []))
        qy = list(d.data.get("q[2]", [])); qz = list(d.data.get("q[3]", []))
        out = []
        for i in range(min(len(ts), len(qx), len(qy))):
            r22 = 1.0 - 2.0 * (qx[i] * qx[i] + qy[i] * qy[i])
            r22 = max(-1.0, min(1.0, r22))
            out.append((ts[i], math.degrees(math.acos(r22))))
        return out
    return []


def _stats(vals):
    if not vals:
        return {"n": 0, "mean_deg": None, "median_deg": None, "p95_deg": None, "max_deg": None}
    s = sorted(vals); n = len(s)
    mean = sum(s) / n
    med = s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])
    p95 = s[min(n - 1, int(math.ceil(0.95 * n)) - 1)]
    return {"n": n, "mean_deg": round(mean, 3), "median_deg": round(med, 3),
            "p95_deg": round(p95, 3), "max_deg": round(max(s), 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    ulog = os.path.join(a.outdir, "boot.ulg")
    res = {"outdir": a.outdir, "ulog": ulog}
    if not os.path.exists(ulog):
        res["error"] = "brak boot.ulg"
        print(json.dumps(res, indent=2));
        if a.out: open(a.out, "w").write(json.dumps(res, indent=2))
        return
    series = tilt_series(ulog)
    win, note = _load_trace_window(a.outdir)
    if win is not None:
        lo, hi = win
        seg = [t for (ts, t) in series if lo <= ts <= hi]
        res["window_us"] = [lo, hi]; res["window_src"] = "hover (event sim→ulog us)"
    else:
        seg = [t for (_ts, t) in series]
        res["window_us"] = None; res["window_src"] = f"cały ulog ({note})"
    res["tilt_hover"] = _stats(seg)
    res["tilt_full_ulog"] = _stats([t for (_ts, t) in series])
    s = json.dumps(res, indent=2)
    print(s)
    if a.out:
        open(a.out, "w").write(s)


if __name__ == "__main__":
    main()
