#!/usr/bin/env python3
"""
tools/infra2_imu_forensics.py — ANEKS_INFRA2-4 Z1: forensyka strumienia IMU w klasie FAIL vs PASS.
OFFLINE, zero bootów. Read-only na ulogach + rtf_stream z I3.

Z1(a) Δt sensor_combined: luki (>Δt+tol), duplikaty stempli, odcinki poza 4000±100 µs.
Z1(b) sample-and-hold: kolejne próbki bitowo identyczne (gyro+accel 6 wartości) — długość i pozycja vs stalle.
Z1(c) wariancja gyro w oknach 1 s: okna zerowej wariancji vs stalle (1:1?).
Z1(d) kontrast FAIL vs PASS na tych samych miarach.

Werdykt drukowany + JSON: strumień IMU zdrowy / zamrożony-pod-stallami / inny defekt — z liczbami.
"""
import os, sys, json
import numpy as np
from pyulog import ULog

DT_NOM = 4000.0      # µs (IMU_INTEG_RATE 250)
DT_TOL = 100.0       # ±100 µs okno „normalne"
DEEP_RTF = 0.5       # rtf < 0.5 = głęboki stall
VAR_EPS = 1e-12      # próg „zerowej wariancji" gyro (rad/s)^2


def load_stalls(d):
    """Interwały sim [s] gdzie rtf<0.5. Zwraca listę (lo,hi) sklejonych sąsiadów + surowe punkty."""
    pts = []
    try:
        for line in open(os.path.join(d, "rtf_stream.jsonl"), errors="replace"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            s = r.get("sim"); rtf = r.get("rtf")
            if s is None or rtf is None:
                continue
            pts.append((s, rtf))
    except Exception:
        pass
    pts.sort()
    deep = [s for s, rtf in pts if rtf < DEEP_RTF]
    # interwały: każdy deep punkt reprezentuje próbkę ~co 0.084s; skleja przylegające
    intervals = []
    if pts:
        # mediana odstępu próbkowania rtf
        ss = np.array([s for s, _ in pts])
        dts = np.diff(ss)
        step = float(np.median(dts)) if len(dts) else 0.1
        for s in deep:
            lo, hi = s - step / 2, s + step / 2
            if intervals and lo <= intervals[-1][1] + step:
                intervals[-1] = (intervals[-1][0], max(intervals[-1][1], hi))
            else:
                intervals.append((lo, hi))
    return intervals, deep, len(pts)


def in_any(t, intervals):
    for lo, hi in intervals:
        if lo <= t <= hi:
            return True
    return False


def analyze(d):
    u = ULog(os.path.join(d, "boot.ulg"), ["sensor_combined"])
    ds = u.get_dataset("sensor_combined")
    ts = ds.data["timestamp"].astype(np.float64)  # µs, sim axis (start=0)
    sim = ts / 1e6
    gx, gy, gz = ds.data["gyro_rad[0]"], ds.data["gyro_rad[1]"], ds.data["gyro_rad[2]"]
    ax, ay, az = ds.data["accelerometer_m_s2[0]"], ds.data["accelerometer_m_s2[1]"], ds.data["accelerometer_m_s2[2]"]
    n = len(ts)

    intervals, deep_pts, n_rtf = load_stalls(d)

    # --- (a) Δt stempli ---
    dt = np.diff(ts)  # µs
    dup = int(np.sum(dt == 0))
    gaps = int(np.sum(dt > DT_NOM + DT_TOL))
    short = int(np.sum((dt < DT_NOM - DT_TOL) & (dt > 0)))
    outside = int(np.sum(np.abs(dt - DT_NOM) > DT_TOL))
    dt_ok = n - 1 - outside
    max_gap = float(dt.max()) if len(dt) else 0.0
    # kilka największych luk z pozycją sim
    big_idx = np.argsort(dt)[::-1][:5] if len(dt) else []
    big_gaps = [{"sim_s": round(float(sim[i]), 3), "dt_us": float(dt[i])} for i in big_idx]

    # --- (b) sample-and-hold: bitowo identyczne kolejne próbki (6 wartości) ---
    same = (gx[1:] == gx[:-1]) & (gy[1:] == gy[:-1]) & (gz[1:] == gz[:-1]) & \
           (ax[1:] == ax[:-1]) & (ay[1:] == ay[:-1]) & (az[1:] == az[:-1])
    # runy identyczności
    runs = []
    i = 0
    m = len(same)
    while i < m:
        if same[i]:
            j = i
            while j < m and same[j]:
                j += 1
            # run od próbki i do j (włącznie j jako ostatnia identyczna); długość = liczba powtórzonych próbek
            lo_s, hi_s = float(sim[i]), float(sim[j])
            runs.append((i, j, lo_s, hi_s, j - i + 1))
            i = j
        else:
            i += 1
    hold_samples = int(same.sum())
    # ile hold-próbek leży w oknie stalla
    hold_idx = np.where(same)[0] + 1  # indeks „powtarzającej" próbki
    hold_in_stall = sum(1 for k in hold_idx if in_any(float(sim[k]), intervals))
    frac_hold_in_stall = (hold_in_stall / len(hold_idx)) if len(hold_idx) else 0.0
    # największe runy
    runs_sorted = sorted(runs, key=lambda r: r[4], reverse=True)[:8]
    top_runs = [{"sim_lo": round(r[2], 3), "sim_hi": round(r[3], 3),
                 "len_samples": r[4], "dur_s": round(r[3] - r[2], 3),
                 "in_stall": in_any((r[2] + r[3]) / 2, intervals)} for r in runs_sorted]

    # --- (c) wariancja gyro w oknach 1 s ---
    gmag = np.sqrt(gx**2 + gy**2 + gz**2)
    t0, t1 = float(sim[0]), float(sim[-1])
    win = []
    w = int(np.floor(t0))
    zero_var_wins = 0
    zero_var_in_stall = 0
    total_wins = 0
    while w < t1:
        mask = (sim >= w) & (sim < w + 1)
        if mask.sum() >= 2:
            total_wins += 1
            # wariancja per-oś, bierzemy max (najczulsze)
            v = max(float(np.var(gx[mask])), float(np.var(gy[mask])), float(np.var(gz[mask])))
            zv = v < VAR_EPS
            stall_here = any(in_any(t, intervals) for t in (w, w + 0.5, w + 0.999))
            if zv:
                zero_var_wins += 1
                if stall_here:
                    zero_var_in_stall += 1
            win.append((w, v, zv, stall_here))
        w += 1

    # --- (d-content) treść wartości gyro/accel: offset, szum, piki + pozycja piku vs stall ---
    gmax_i = int(np.argmax(gmag))
    amag = np.sqrt(ax**2 + ay**2 + az**2)
    # piki gyro poza spoczynkiem: |gyro|>0.05 rad/s (~2.9°/s) i czy w oknie stalla
    spike_thr = 0.05
    spike_idx = np.where(gmag > spike_thr)[0]
    spike_in_stall = sum(1 for k in spike_idx if in_any(float(sim[k]), intervals))
    content = {
        "gyro_mean_xyz": [round(float(np.mean(gx)), 6), round(float(np.mean(gy)), 6), round(float(np.mean(gz)), 6)],
        "gyro_std_xyz": [round(float(np.std(gx)), 6), round(float(np.std(gy)), 6), round(float(np.std(gz)), 6)],
        "gyro_absmax": round(float(gmag.max()), 5),
        "gyro_absmax_sim_s": round(float(sim[gmax_i]), 3),
        "gyro_absmax_in_stall": in_any(float(sim[gmax_i]), intervals),
        "accel_mean_z": round(float(np.mean(az)), 4),
        "accel_std_mag": round(float(np.std(amag)), 5),
        "n_spikes_gt_0p05": int(len(spike_idx)),
        "spikes_in_stall": int(spike_in_stall),
        "frac_spikes_in_stall": round(spike_in_stall / max(1, len(spike_idx)), 3),
    }

    return {
        "dir": d, "n_samples": n, "n_rtf_pts": n_rtf, "n_deep_stall_pts": len(deep_pts),
        "n_stall_intervals": len(intervals),
        "d_content": content,
        "a_dt": {"dup_stamps": dup, "gaps_gt_tol": gaps, "short_lt_tol": short,
                 "outside_4000pm100": outside, "within_tol": dt_ok,
                 "pct_within": round(100.0 * dt_ok / max(1, n - 1), 3),
                 "max_gap_us": max_gap, "top_gaps": big_gaps},
        "b_hold": {"hold_samples": hold_samples, "pct_hold": round(100.0 * hold_samples / max(1, n), 3),
                   "n_runs": len(runs), "hold_in_stall": hold_in_stall,
                   "frac_hold_in_stall": round(frac_hold_in_stall, 3), "top_runs": top_runs},
        "c_var": {"total_1s_windows": total_wins, "zero_var_windows": zero_var_wins,
                  "zero_var_in_stall": zero_var_in_stall,
                  "frac_zerovar_in_stall": round(zero_var_in_stall / max(1, zero_var_wins), 3),
                  "var_eps": VAR_EPS},
    }


def main():
    fails = sys.argv[1].split(",") if len(sys.argv) > 1 else ["1", "3", "5"]
    passes = sys.argv[2].split(",") if len(sys.argv) > 2 else ["4", "7"]
    out = {"FAIL": {}, "PASS": {}}
    for b in fails:
        d = f"results/K1/E/p0_0/boot{b}"
        try:
            out["FAIL"][b] = analyze(d)
        except Exception as e:
            out["FAIL"][b] = {"err": str(e)}
    for b in passes:
        d = f"results/K1/E/p0_0/boot{b}"
        try:
            out["PASS"][b] = analyze(d)
        except Exception as e:
            out["PASS"][b] = {"err": str(e)}

    os.makedirs("results/K1/INFRA1", exist_ok=True)
    with open("results/K1/INFRA1/Z1_imu_forensics.json", "w") as f:
        json.dump(out, f, indent=2)

    # --- podsumowanie tabelaryczne ---
    def row(cls, b, r):
        if "err" in r:
            return f"{cls} boot{b}: ERR {r['err']}"
        a = r["a_dt"]; h = r["b_hold"]; c = r["c_var"]; ct = r["d_content"]
        return (f"{cls} boot{b}: n={r['n_samples']} | Δt within±100µs={a['pct_within']}% "
                f"dup={a['dup_stamps']} gaps={a['gaps_gt_tol']} maxgap={a['max_gap_us']:.0f}µs | "
                f"hold={h['hold_samples']} zerovar={c['zero_var_windows']}/{c['total_1s_windows']} | "
                f"gyro_std={ct['gyro_std_xyz']} absmax={ct['gyro_absmax']}@{ct['gyro_absmax_sim_s']}s(stall={ct['gyro_absmax_in_stall']}) "
                f"spikes>0.05={ct['n_spikes_gt_0p05']}(in_stall={ct['frac_spikes_in_stall']}) | stalls={r['n_stall_intervals']}")
    print("=" * 100)
    for b, r in out["FAIL"].items():
        print(row("FAIL", b, r))
    for b, r in out["PASS"].items():
        print(row("PASS", b, r))
    print("=" * 100)
    print("JSON → results/K1/INFRA1/Z1_imu_forensics.json")


if __name__ == "__main__":
    main()
