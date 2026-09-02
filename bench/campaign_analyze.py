#!/usr/bin/env python3
"""bench/campaign_analyze.py — analiza kampanii blok1/48 (ANEKS_BENCH-1 §3 + ANEKS_BENCH-1a §2 R1).

D9 = V2′ (ROZSTRZYGNIĘCIE ANEKS_BENCH-1a §2 R1): epizod WAŻNY ⇔ najdłuższy pojedynczy deep-stall
(rtf<0.5) ≤ 1.5 s wall ∧ Δsim/Δwall ≥ 0.90 ∧ timejump=0. LICZBA zdarzeń deep raportowana per epizod,
NIEBRAMKUJĄCA (cap „≤3" z V2 zdjęty — jednopróbkowe blipy 4×0.05 s to szum próbnika, nie choroba mostu;
przed patologią wielu stalli chroni Δ).

Realizowane WARSTWĄ ANALIZY przez override slotu „V2" params sędziego `bench_judge` (frozen 8ec0fcfb…
NIETKNIĘTY): V2′ = {dsw_min:0.90, max_deep_stall:∞, longest_stall_s:1.5, timejump:0} → judge liczy
valid_V2 z tych progów, tu czytane jako `valid_campaign_V2p`. Sędzia liczy V1/V2/V3 i tak; bramkowanie
robi TA agregacja.

Strażnik (R1): kampania raportuje sukces D6 vs liczba deep-stalli (tabela); korelacja ujemna ⇒ rewizja
V2′ dokumentem, nie cicho.

`judge_boot(outdir)` — per epizod z trace+gt_intruder+rtf. `wilson(k,n)` — przedział Wilsona.
`blok1_episode_ids(manifest)` — 48 id (bloki seed 1-4 × 12 komórek) w kolejności manifestu.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench.bench_judge import judge_episode, _load_drone_ned, _load_intr_ned, _load_rtf, _interp_ned

# D9 = V2′ (ANEKS_BENCH-1a §2 R1): ważny ⇔ najdłuższy deep-stall ≤ 1.5 s wall ∧ Δsim/Δwall ≥ 0.90 ∧ timejump=0.
# Override slotu „V2" sędziego frozen: max_deep_stall=∞ ⇒ LICZBA stalli NIE bramkuje; longest 1.5 s NADAL bramkuje.
D9_V2P_PARAMS = {"V2": {"dsw_min": 0.90, "max_deep_stall": 10 ** 9, "longest_stall_s": 1.5, "timejump": 0}}


def blok1_episode_ids(manifest):
    return [e["episode_id"] for e in manifest["episodes"] if e["block"] == 1]


def wilson(k, n, z=1.96):
    """Przedział ufności Wilsona dla proporcji k/n (dom. 95%). Zwraca (p, lo, hi)."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / d
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (round(p, 4), round(max(0.0, center - half), 4), round(min(1.0, center + half), 4))


def judge_boot(outdir, params=None):
    """Zwraca listę werdyktów epizodów w boocie (trace+gt_intruder+rtf). D9=V2′ (valid_campaign_V2p) = ważność kampanii."""
    p = dict(D9_V2P_PARAMS)
    if params:
        p.update(params)
    trace = os.path.join(outdir, "trace.jsonl")
    drone = _load_drone_ned(trace)
    intr = _load_intr_ned(os.path.join(outdir, "gt_intruder.jsonl"))
    rtf = _load_rtf(os.path.join(outdir, "rtf_stream.jsonl"))
    tj = 0
    for fn in ("timejump_pre.txt", "timejump_post.txt"):
        fp = os.path.join(outdir, fn)
        if os.path.exists(fp):
            tj += int(open(fp).read().strip() or 0)
    evs = [json.loads(l) for l in open(trace) if '"event"' in l]
    eps = []; cur = None
    for e in evs:
        if e.get("ev") == "episode_start":
            cur = {"id": e["episode_id"], "sid": e["scenario_id"], "lo": e["t0_sim"]}
        elif e.get("ev") == "invalid_start":
            cur = None
        elif e.get("ev") == "episode_end" and cur:
            cur["hi"] = e["sim"]; cur["refuse"] = e.get("refuse", 0); cur["breach"] = e.get("breach", False)
            eps.append(cur); cur = None
    out = []
    for ep in eps:
        dg = [(t, q) for t, q in drone if ep["lo"] <= t <= ep["hi"]]
        v = judge_episode(dg, intr, rtf=rtf, refuse_count=ep["refuse"], breach=ep["breach"],
                          timejump=tj, params=p)
        # d_min po 3 s (faza orbity) — diagnostyka
        dm3 = 1e9
        for t, q in dg:
            if t - ep["lo"] >= 3.0:
                ip = _interp_ned(intr, t)
                if ip:
                    dm3 = min(dm3, math.sqrt(sum((ip[k] - q[k]) ** 2 for k in range(3))))
        v["episode_id"] = ep["id"]; v["scenario_id"] = ep["sid"]
        v["d_min_orbit"] = round(dm3, 3) if dm3 < 1e9 else None
        v["valid_campaign_V2p"] = v["valid_V2"]         # D9 = V2′ (slot V2 nadpisany progami V2′)
        v["n_deep_stall"] = v["stalls"]["n_deep"]       # LICZBA raportowana, NIEBRAMKUJĄCA (R1)
        out.append(v)
    return out


def aggregate_p_exec(episode_verdicts):
    """p_exec = udane D6 / WAŻNE (D9=V2′). Zwraca dict z liczbami + Wilson + strażnik sukces-vs-stalle."""
    valid = [v for v in episode_verdicts if v["valid_campaign_V2p"]]
    succ = [v for v in valid if v["success_D6"]]
    p, lo, hi = wilson(len(succ), len(valid))
    # strażnik R1: rozkład sukcesu D6 wobec obecności deep-stalli (0 vs ≥1) na epizodach WAŻNYCH
    with0 = [v for v in valid if v["n_deep_stall"] == 0]
    with1 = [v for v in valid if v["n_deep_stall"] >= 1]
    guard = {"stall0_n": len(with0), "stall0_succ": sum(1 for v in with0 if v["success_D6"]),
             "stall1p_n": len(with1), "stall1p_succ": sum(1 for v in with1 if v["success_D6"])}
    return {"n_episodes": len(episode_verdicts), "n_valid": len(valid), "n_success": len(succ),
            "p_exec": p, "wilson95": [lo, hi],
            "n_invalid_V2p": len(episode_verdicts) - len(valid),
            "guard_success_vs_stall": guard}


def aggregate_campaign(manifests, queue_state=None):
    """Roll-up całej kampanii z manifestów bench_finalize (per boot). Liczy po PIERWSZEJ ważnej (V2′) próbie
    każdego scenariusza; scenariusze bez ważnej próby = UNRESOLVED (z kolejki jeśli podana), wykluczone z p_exec.
    manifests = lista dictów manifestu (kolejność bootów). queue_state = dict stanu kolejki (opc., autorytatywny
    dla UNRESOLVED)."""
    first_valid = {}                                     # scenario_id → {attempt, success_D6}
    seen = {}                                            # scenario_id → min attempt widziany (diag)
    for m in manifests:
        for ep in sorted(m.get("episodes", []), key=lambda e: e.get("attempt", 0)):
            sid = ep.get("scenario_id")
            seen[sid] = min(seen.get(sid, 10 ** 9), ep.get("attempt", 0))
            if ep.get("valid_V2p") and sid not in first_valid:
                first_valid[sid] = {"attempt": ep.get("attempt", 0), "success_D6": bool(ep.get("success_D6"))}
    if queue_state is not None:
        unresolved = [e["scenario_id"] for e in queue_state.get("unresolved", [])]
    else:
        unresolved = sorted(sid for sid in seen if sid not in first_valid)
    resolved = sorted(first_valid)
    succ = [sid for sid in resolved if first_valid[sid]["success_D6"]]
    p, lo, hi = wilson(len(succ), len(resolved))
    return {"n_resolved": len(resolved), "n_success": len(succ), "n_unresolved": len(unresolved),
            "p_exec": p, "wilson95": [lo, hi], "unresolved_ids": unresolved,
            "resolved_first_valid": {sid: first_valid[sid] for sid in resolved}}


def _stall_table(verdicts):
    """Tabela strażnika R1: per epizod sukces D6 vs liczba/najdłuższy deep-stall (tekst płaski, bez ramek)."""
    lines = ["scenario_id            valid  D6    n_deep  longest_s  dsim/dwall"]
    for v in verdicts:
        lines.append("{:<22} {:<6} {:<5} {:<7} {:<10} {}".format(
            str(v.get("scenario_id")), str(v.get("valid_campaign_V2p")), str(v["success_D6"]),
            v["stalls"]["n_deep"], v["stalls"]["longest_s"], v["stalls"]["dsim_dwall"]))
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("outdirs", nargs="+")
    a = ap.parse_args()
    allv = []
    for od in a.outdirs:
        vs = judge_boot(od)
        allv += vs
        for v in vs:
            print(f"{v['scenario_id']}: D6={v['success_D6']} valid(V2')={v['valid_campaign_V2p']} "
                  f"frac[6,10]={v['frac_band_6_10']} d_min={v['d_min_m']} dorb={v['d_min_orbit']} "
                  f"n_deep={v['n_deep_stall']} longest={v['stalls']['longest_s']}s REFUSE={v['refuse_count']} breach={v['breach']}")
    print("\n# strażnik R1 — sukces D6 vs deep-stalle")
    print(_stall_table(allv))
    print("\n" + json.dumps(aggregate_p_exec(allv)))
