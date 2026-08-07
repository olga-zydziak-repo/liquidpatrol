#!/usr/bin/env python3
"""r02/sample_intruder_pose.py — próbnik pozy aktora-intruza (R1 dowód determinizmu).

Czyta gz topic /world/<world>/dynamic_pose/info (Pose_V: header.stamp = SIM-TIME + pozy encji),
wyciąga (sim_time, intruder.y) i porównuje z ANALITYCZNYM skryptem trajektorii y(t) z intruder_actor.sdf:
  y(t) = -15 + 3*τ  dla τ=t mod 20 ∈[0,10];  y(t) = 15 - 3*(τ-10) dla τ∈[10,20]  (v=3 m/s, okres 20 s).
Zgodność (poza = f(sim_time)) ⇒ ruch deterministyczny → powtarzalny między biegami (bez fizyki/losu).

Uruchom: python3 -m r02.sample_intruder_pose <world> <n_msgs> [out.json]
"""
import json
import re
import subprocess
import sys

WP = [(0.0, -15.0), (10.0, 15.0), (20.0, -15.0)]  # (time, y) — lustro intruder_actor.sdf


def analytic_y(t):
    tau = t % 20.0
    for (t0, y0), (t1, y1) in zip(WP[:-1], WP[1:]):
        if t0 <= tau <= t1:
            return y0 + (y1 - y0) * (tau - t0) / (t1 - t0)
    return None


def parse(text):
    """Zwraca listę (sim_time_s, intruder_pos) z tekstu Pose_V (może wiele wiadomości)."""
    out = []
    # rozbij po blokach 'header {' rozpoczynających wiadomość
    for block in re.split(r'(?=header\s*{)', text):
        ms = re.search(r'stamp\s*{\s*sec:\s*(-?\d+)\s*nsec:\s*(\d+)', block)
        if not ms:
            continue
        t = int(ms.group(1)) + int(ms.group(2)) * 1e-9
        # znajdź pozę o name: "intruder"
        for pm in re.finditer(r'pose\s*{(.*?)}\s*(?=pose\s*{|$)', block, re.S):
            body = pm.group(1)
            nm = re.search(r'name:\s*"([^"]+)"', body)
            if nm and nm.group(1) == "intruder":
                pos = re.search(r'position\s*{\s*x:\s*(-?[\d.eE+-]+)\s*y:\s*(-?[\d.eE+-]+)\s*z:\s*(-?[\d.eE+-]+)', body)
                if pos:
                    out.append((t, [float(pos.group(1)), float(pos.group(2)), float(pos.group(3))]))
    return out


def main():
    world = sys.argv[1] if len(sys.argv) > 1 else "default"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    out = sys.argv[3] if len(sys.argv) > 3 else None
    topic = f"/world/{world}/dynamic_pose/info"
    try:
        r = subprocess.run(["gz", "topic", "-e", "-t", topic, "-n", str(n)],
                           capture_output=True, text=True, timeout=40)
    except subprocess.TimeoutExpired as e:
        r = type("X", (), {"stdout": e.stdout.decode() if e.stdout else "", "stderr": ""})()
    samples = parse(r.stdout)
    rows, max_err = [], 0.0
    for t, p in samples:
        ay = analytic_y(t)
        err = abs(p[1] - ay) if ay is not None else None
        if err is not None:
            max_err = max(max_err, err)
        rows.append({"sim_t": round(t, 3), "y_meas": round(p[1], 3),
                     "y_analytic": round(ay, 3) if ay is not None else None,
                     "err": round(err, 3) if err is not None else None,
                     "pos": [round(v, 2) for v in p]})
    res = {"topic": topic, "n_samples": len(rows), "max_abs_err_y_m": round(max_err, 3),
           "deterministic_match": (len(rows) > 0 and max_err < 0.5), "rows": rows}
    print(json.dumps(res, indent=2))
    if out:
        json.dump(res, open(out, "w"), indent=2)
    sys.exit(0 if res["deterministic_match"] else 1)


if __name__ == "__main__":
    main()
