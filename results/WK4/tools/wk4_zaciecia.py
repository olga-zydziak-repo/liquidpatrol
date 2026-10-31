#!/usr/bin/env python3
"""results/WK4/tools/wk4_zaciecia.py — próbnik zacięć symulacji (PROMPT_WK4_S1 §1.5, PRE_WK4 §2 B0).

DEFINICJA (FROZEN przed B0): zacięcie = maksymalny odcinek ≥ 1.0 s czasu ŚCIENNEGO, w którym przyrost
czasu SYMULACJI < 0.1 s. Liczone na szeregu próbek (wall, sim): dla każdego i najdalsze j z
sim[j] − sim[i] < 0.1; jeśli wall[j] − wall[i] ≥ 1.0 ⇒ odcinek [i, j]; nachodzące odcinki łączone.
Raport: liczba, suma [s ściany], odstępy między zacięciami w czasie symulacji, t_sim początku każdego.
Obok: liczba linii „time jump detected" w px4.log (sygnatura PX4 timesync).

Tryby:
  stream <rtf_stream.jsonl> [--px4 px4.log]     — szereg z acts/rtf_sampler (boot)
  live <świat> <czas_ściany_s> <out.jsonl>      — własny subskrybent /world/<W>/clock (goły gz; GZ_PARTITION
                                                  z env), zapis każdej wiadomości (wall, sim)
  analiza <out.jsonl>                           — jak stream, na pliku z trybu live
"""
import json
import sys
import time


def stalls(W, S, min_wall=1.0, max_dsim=0.1):
    out = []
    j = 0
    n = len(S)
    for i in range(n):
        if j < i:
            j = i
        while j + 1 < n and S[j + 1] - S[i] < max_dsim:
            j += 1
        if W[j] - W[i] >= min_wall:
            if out and i <= out[-1][1]:
                out[-1][1] = max(out[-1][1], j)
            else:
                out.append([i, j])
    res = [{"t_sim": round(S[a], 3), "wall_s": round(W[b] - W[a], 3), "dsim": round(S[b] - S[a], 4)}
           for a, b in out]
    gaps = [round(res[k + 1]["t_sim"] - res[k]["t_sim"], 2) for k in range(len(res) - 1)]
    return {"n": len(res), "suma_wall_s": round(sum(r["wall_s"] for r in res), 2),
            "odstepy_t_sim": gaps, "zaciecia": res,
            "wall_total_s": round(W[-1] - W[0], 2) if W else 0, "sim_total_s": round(S[-1] - S[0], 2) if S else 0,
            "dsim_dwall": round((S[-1] - S[0]) / (W[-1] - W[0]), 4) if W and W[-1] > W[0] else None}


def load(p):
    W, S = [], []
    for ln in open(p):
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if isinstance(r, dict) and "wall" in r and "sim" in r:
            W.append(float(r["wall"])); S.append(float(r["sim"]))
    return W, S


def time_jumps(px4):
    try:
        return sum(1 for ln in open(px4, errors="replace") if "time jump detected" in ln)
    except FileNotFoundError:
        return None


def live(world, secs, outp):
    from gz.msgs10.clock_pb2 import Clock
    from gz.transport13 import Node
    f = open(outp, "w", buffering=1)
    node = Node()
    node.subscribe(Clock, f"/world/{world}/clock",
                   lambda m: f.write(json.dumps({"wall": round(time.time(), 4),
                                                 "sim": round(m.sim.sec + m.sim.nsec * 1e-9, 4)}) + "\n"))
    time.sleep(secs)
    f.close()


def main():
    mode = sys.argv[1]
    if mode in ("stream", "analiza"):
        W, S = load(sys.argv[2])
        r = stalls(W, S)
        if "--px4" in sys.argv:
            r["px4_time_jump_detected"] = time_jumps(sys.argv[sys.argv.index("--px4") + 1])
        print(json.dumps(r, ensure_ascii=False))
    elif mode == "live":
        live(sys.argv[2], float(sys.argv[3]), sys.argv[4])


if __name__ == "__main__":
    main()
