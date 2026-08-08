#!/usr/bin/env python3
"""r02/analyze_persistence.py — run-length TOP-1 boxa między klatkami (do derywacji k ENTRY).

Modeluje DOKŁADNIE bramkę ENTRY (kanał bierze TOP-1 box; ENTRY = k kolejnych spójnych top-1).
Śledzi top-1 (najwyższy conf) klatka-po-klatce: run rośnie gdy top-1 w spójnej lokalizacji
(ruch środka ≤ move_thr) względem poprzedniej. Run „szumowy" = top-1 sklasyfikowany false.
Wyprowadza: max run-length SZUMU → k musi go PRZEKRACZAĆ (by szum nigdy nie osiągnął ENTRY);
run-length SYGNAŁU (musi >> k, inaczej k zabije detekcję). Uruchom: python3 -m r02.analyze_persistence <char.jsonl> [move_thr]
"""
from __future__ import annotations
import json, math, sys


def runs(frames, move_thr):
    """Zwraca listę runów top-1: (dlugosc, czy_true). Run = kolejne klatki ze spójnym top-1."""
    out = []
    cur_len = 0; cur_true = None; prev = None
    for fr in frames:
        boxes = fr.get("boxes", [])
        top = boxes[0] if boxes else None      # char.jsonl: boxy sortowane malejąco po conf
        if top is None:
            if cur_len > 0: out.append((cur_len, cur_true)); cur_len = 0; prev = None
            continue
        c = (top["cx"], top["cy"])
        if prev is not None and math.hypot(c[0]-prev[0], c[1]-prev[1]) <= move_thr:
            cur_len += 1
            cur_true = cur_true and top["true"]   # run true tylko jeśli WSZYSTKIE klatki true
        else:
            if cur_len > 0: out.append((cur_len, cur_true))
            cur_len = 1; cur_true = top["true"]
        prev = c
    if cur_len > 0: out.append((cur_len, cur_true))
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/r02/CHAR/char.jsonl"
    move_thr = float(sys.argv[2]) if len(sys.argv) > 2 else 0.15
    frames = [json.loads(l) for l in open(path) if l.strip() and "SCENARIO_RESULT" not in l]
    rs = runs(frames, move_thr)
    noise_runs = [n for n, t in rs if not t]
    sig_runs = [n for n, t in rs if t]
    res = {"char_log": path, "move_thr": move_thr, "n_frames": len(frames),
           "n_runs": len(rs),
           "SZUM_run_lengths": sorted(noise_runs, reverse=True)[:10],
           "SZUM_max_run": max(noise_runs) if noise_runs else 0,
           "SZUM_runs_ge_3": sum(1 for n in noise_runs if n >= 3),
           "SYGNAL_run_lengths": sorted(sig_runs, reverse=True)[:10],
           "SYGNAL_max_run": max(sig_runs) if sig_runs else 0,
           "SYGNAL_runs_ge_5": sum(1 for n in sig_runs if n >= 5)}
    res["derywacja_k"] = {"k_min_by_szum": (res["SZUM_max_run"] + 1),
                          "sygnal_wytrzyma_k?": res["SYGNAL_max_run"] >= (res["SZUM_max_run"] + 1)}
    print(json.dumps(res, indent=2, ensure_ascii=False))
    if len(sys.argv) > 3:
        json.dump(res, open(sys.argv[3], "w"), indent=2, ensure_ascii=False)
    return res


if __name__ == "__main__":
    main()
