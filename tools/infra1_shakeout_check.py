#!/usr/bin/env python3
"""
tools/infra1_shakeout_check.py — INFRA-1 ANEKS_INFRA1-2 N3: ZAMROŻONE kryterium shakeoutu po resecie.

Kryterium (ANEKS_INFRA1-3 W3, poprawka wynikająca z C1/C2):
  PASS ⟺ arm_ok ∧ (brak głębokiego stalla rtf<0.5 w oknie preflight→arm)
  FAIL ⟺ cokolwiek innego.
  n_timejumps: RAPORTOWANY, NIE bramkujący — C1 wykazał, że „time jump" to artefakt licznika uxrce
  Timesync (Timesync.cpp:69) referowanego do zegara ściennego; nie dotyka osi sim (Δt IMU 4000µs
  jednorodny) ani EKF. Dlatego przestaje bramkować (był fałszywym negatywem dla zdrowych bootów).
Interpretacja:
  PASS ⇒ maszyna armuje end-to-end → wracamy do I3 (dziesiątka) na harnessie po rewercie I2b (P0a).
  FAIL ⇒ dopiero wtedy wracamy do pytania o habitat, z S boot4/5/6 jako jedynym realnym trybem awarii.
Dokładnie JEDEN shakeout — brak powtórki (powtarzanie do skutku = selekcja).
Uwaga: poprzedni werdykt N3 (na harnessie I2b) WYCOFANY jako nieważny (mierzył deadlock, nie arm).

Użycie: python3 tools/infra1_shakeout_check.py --dir results/K1/E/p0_0/bootS
"""
import os, sys, json, argparse

TJ_MAX = 1              # n_timejumps ≤ 1
DEEP_STALL_RTF = 0.5    # rtf < 0.5 = głęboki stall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    a = ap.parse_args()
    d = a.dir

    # X1 (ANEKS_INFRA1-4): okno deep-stall = PX4 start → arm na OSI SIM, ŹRÓDŁO = ulog (nie trace).
    # Poprzednie okno [gt0_trace, arm] było ~3 s (trace startuje po 90 s settle) → mierzyło odcinek
    # start-modułu→arm, nie preflight. Nowe okno obejmuje pełny preflight (PX4 start → arm) na tej samej
    # osi sim co rtf_stream (lockstep gz clock, dowód C1). Fallback do trace gdy ulog niedostępny.
    armed_sim = None
    arm_ok = False
    px4_start_sim = None
    window_source = None
    try:
        from pyulog import ULog
        import numpy as np
        u = ULog(os.path.join(d, "boot.ulg"), ["actuator_armed"])
        px4_start_sim = float(u.start_timestamp) / 1e6
        ds = u.get_dataset("actuator_armed")
        ts = ds.data["timestamp"]; ar = ds.data["armed"]
        idx = np.where(ar == 1)[0]
        if len(idx):
            arm_ok = True
            armed_sim = float(ts[idx[0]]) / 1e6
        window_source = "ulog"
    except Exception as e:
        print(f"[shakeout] ulog read err ({e}) → fallback trace")

    if window_source is None:  # fallback: stare źródło (trace) gdy brak ulog/pyulog
        gt0 = None
        try:
            for line in open(os.path.join(d, "trace.jsonl"), errors="replace"):
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if r.get("t") == "gt" and gt0 is None:
                    gt0 = r.get("sim")
                if r.get("t") == "event" and r.get("ev") == "armed":
                    arm_ok = True
                    armed_sim = r.get("sim")
            px4_start_sim = gt0
            window_source = "trace(fallback)"
        except Exception as e:
            print(f"[shakeout] trace read err: {e}")

    # n_timejumps z px4.log (ta sama fraza co diagnoza)
    n_tj = 0
    try:
        for line in open(os.path.join(d, "px4.log"), errors="replace"):
            if "time jump detected" in line:
                n_tj += 1
    except Exception:
        n_tj = None

    # głębokie stalle rtf<0.5 w oknie preflight→arm (jeśli brak armed_sim, całe okno do końca rtf)
    deep_pre = None
    try:
        lo = px4_start_sim if px4_start_sim is not None else -1e18
        hi = armed_sim if armed_sim is not None else 1e18
        deep_pre = 0
        for line in open(os.path.join(d, "rtf_stream.jsonl"), errors="replace"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            s = r.get("sim"); rtf = r.get("rtf")
            if s is None or rtf is None:
                continue
            if lo <= s <= hi and rtf < DEEP_STALL_RTF:
                deep_pre += 1
    except Exception:
        deep_pre = None

    tj_ok = (n_tj is not None and n_tj <= TJ_MAX)  # RAPORTOWANE, już nie bramkuje (W3)
    stall_ok = (deep_pre is not None and deep_pre == 0)
    verdict = "PASS" if (arm_ok and stall_ok) else "FAIL"  # W3: timejump zdjęty z bramki (artefakt uxrce, C1)
    interp = ("maszyna armuje end-to-end → wracamy do I3 (10 liczonych) na harnessie po rewercie I2b"
              if verdict == "PASS" else
              "FAIL → pytanie o habitat, z S boot4/5/6 jako jedynym realnym trybem awarii")

    out = {"verdict": verdict, "arm_ok": arm_ok, "gate": "arm_ok ∧ deep_stalls==0 (timejump raportowany)",
           "n_timejumps": n_tj, "tj_reported_only": True, "tj_advisory_max": TJ_MAX, "tj_within_advisory": tj_ok,
           "deep_stalls_preflight_to_arm": deep_pre, "deep_stall_rtf_thr": DEEP_STALL_RTF,
           "window_sim": [px4_start_sim, armed_sim], "window_source": window_source,
           "interpretation": interp, "dir": d}
    with open(os.path.join(d, "shakeout_check.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
