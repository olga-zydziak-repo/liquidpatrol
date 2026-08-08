#!/usr/bin/env python3
"""r02/analyze_char.py — analiza pasa charakteryzacyjnego (EKSPLORACJA, poza pre-rejestracją).

Wejście: char.jsonl (z r02.gate_run_r02 scenario_CHAR) — per klatka detektora: wszystkie boxy z
klasyfikacją true/false (vs projekcja GT intruza), conf, edge_dist. Wyjście: rozkłady conf i
przestrzenne (krawędź vs środek) dla szumu (false) vs sygnału (true) + ocena separacji progiem
(conf i geometrycznym) na CAŁYM locie. NIE zmienia werdyktu G1 (FAIL/SR-5) — dane do sekcji EKSPLORACJA.
Uruchom: python3 -m r02.analyze_char <char.jsonl> [out.json]
"""
from __future__ import annotations
import json, sys


def pct(xs, p):
    if not xs:
        return None
    s = sorted(xs)
    i = min(len(s) - 1, max(0, int(round(p / 100.0 * (len(s) - 1)))))
    return s[i]


def stats(xs):
    if not xs:
        return {"n": 0}
    return {"n": len(xs), "min": round(min(xs), 5), "p5": round(pct(xs, 5), 5),
            "p50": round(pct(xs, 50), 5), "p90": round(pct(xs, 90), 5),
            "p95": round(pct(xs, 95), 5), "p99": round(pct(xs, 99), 5), "max": round(max(xs), 5)}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/r02/CHAR/char.jsonl"
    out = sys.argv[2] if len(sys.argv) > 2 else None
    frames = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                frames.append(json.loads(line))
    n_frames = len(frames)
    n_infov = sum(1 for fr in frames if fr.get("in_fov"))
    true_conf, false_conf, true_edge, false_edge = [], [], [], []
    n_true = n_false = 0
    for fr in frames:
        for b in fr.get("boxes", []):
            if b["true"]:
                true_conf.append(b["conf"]); true_edge.append(b["edge"]); n_true += 1
            else:
                false_conf.append(b["conf"]); false_edge.append(b["edge"]); n_false += 1

    # separacja conf: próg = p99 szumu; ile sygnału powyżej
    tau_conf = pct(false_conf, 99) if false_conf else None
    true_above = (sum(1 for c in true_conf if tau_conf is not None and c > tau_conf) / len(true_conf)
                  if true_conf else None)
    # separacja geometryczna: szum blisko krawędzi (edge mały)? próg edge = p95 sygnału-od-dołu...
    # ile szumu ma edge < 0.10 (przy krawędzi); ile sygnału ma edge >= 0.10 (środek)
    false_edgey = sum(1 for e in false_edge if e < 0.10) / len(false_edge) if false_edge else None
    true_central = sum(1 for e in true_edge if e >= 0.10) / len(true_edge) if true_edge else None
    # move-gating i persistencja są w kanale (ENTRY k=3) — tu mierzymy surowe boxy per klatka

    res = {
        "char_log": path, "n_frames": n_frames, "n_infov_frames": n_infov,
        "n_true_boxes": n_true, "n_false_boxes": n_false,
        "conf_false(szum)": stats(false_conf), "conf_true(sygnał)": stats(true_conf),
        "edge_false(szum)": stats(false_edge), "edge_true(sygnał)": stats(true_edge),
        "separacja_conf": {"tau=p99_szumu": round(tau_conf, 5) if tau_conf is not None else None,
                            "frac_sygnał_powyżej_tau": round(true_above, 3) if true_above is not None else None,
                            "rozdziela": (true_above is not None and true_above >= 0.9
                                          and tau_conf is not None)},
        "separacja_geometryczna": {"frac_szum_przy_krawędzi(edge<0.10)": round(false_edgey, 3) if false_edgey is not None else None,
                                    "frac_sygnał_centralny(edge>=0.10)": round(true_central, 3) if true_central is not None else None},
    }
    print(json.dumps(res, indent=2, ensure_ascii=False))
    if out:
        json.dump(res, open(out, "w"), indent=2, ensure_ascii=False)
    return res


if __name__ == "__main__":
    main()
