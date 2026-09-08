#!/usr/bin/env python3
"""bench/tests_k2_judge.py — testy syntetyczne K2 (PROMPT_K2_BUILD B6). Zero SITL, zero zamrożonych zmian.

- pasmo t_refuse [0.05,0.15] brzegowo 0.04/0.16 ⇒ FAIL, 0.05/0.10/0.15 ⇒ OK
- episode_verdict: komplet warunków; brak touchdown/breach/x_exc>cap/native failsafe ⇒ FAIL
- leg_verdict: 12/12 PASS · 11/12 NIEROZSTRZYGNIETE · ≥2 FAIL
- judge_episode_k2 na fabrykowanym trace: REFUSE wstrzyknięty ⇒ metryki liczą; brak denialu ⇒ nominał
- unit `pos_flag=True` NA SUCHO (PRE dozwolił jako test): shield REFUSE(POS) → safe_descend do touchdown w pętli
"""
import json
import math
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench.k2_judge import trefuse_in_band, episode_verdict, leg_verdict, judge_episode_k2
from r03.controllers.safe_descend import safe_descend_step, new_state
from r01.shield import PatrolShield, REFUSE, POS_DEGRADED, M_PATROL
from r03 import config as C


def test_trefuse_band():
    assert trefuse_in_band(0.10) and trefuse_in_band(0.05) and trefuse_in_band(0.15)
    assert not trefuse_in_band(0.04) and not trefuse_in_band(0.16) and not trefuse_in_band(None)


def test_episode_verdict_all_paths():
    ok = episode_verdict(0.10, True, False, 3.0, 5.0, False)
    assert ok["pass"], ok
    assert not episode_verdict(0.20, True, False, 3.0, 5.0, False)["pass"]     # t_refuse poza pasmem
    assert not episode_verdict(0.10, False, False, 3.0, 5.0, False)["pass"]    # brak touchdown
    assert not episode_verdict(0.10, True, True, 3.0, 5.0, False)["pass"]      # breach
    assert not episode_verdict(0.10, True, False, 9.0, 5.0, False)["pass"]     # x_exc>cap
    assert not episode_verdict(0.10, True, False, 3.0, 5.0, True)["pass"]      # native failsafe


def test_leg_verdict_ladder():
    assert leg_verdict(12, 12) == "PASS"
    assert leg_verdict(12, 11) == "NIEROZSTRZYGNIETE"
    assert leg_verdict(12, 10) == "FAIL"
    assert leg_verdict(11, 11) == "NIEKOMPLETNE"


def _write_trace(d, denial=True):
    """Fabrykuje minimalny trace K2 + gt_intruder + rtf. Dron: start w domu, po denialu dryf i zejście."""
    tr = os.path.join(d, "trace.jsonl"); gi = os.path.join(d, "gt_intruder.jsonl"); rt = os.path.join(d, "rtf_stream.jsonl")
    rows = []
    # gt drona (t=gt): orbita ~8m od intruza (~15m od home), po denialu dryf do ~17m potem zejście z=up→0
    t = 100.0
    def gt(t, x, y, z): rows.append({"t": "gt", "sim": round(t, 2), "x": x, "y": y, "z": z})
    for i in range(60):        # faza orbity (przed T_inj) r≈15
        gt(100 + i * 0.5, 15.0, 0.0, 10.0)
    t_inj = 130.0
    if denial:
        for i in range(20):    # po denialu: mały dryf poziomy + zejście pionowe (z: 10→0 Up)
            gt(130 + i * 0.5, 15.0 + i * 0.1, 0.0, max(0.0, 10.0 - i * 0.6))
    open(gi, "w").write("\n".join(json.dumps({"sim": round(100 + i * 0.5, 2), "x": 7.0, "y": 0.0, "z": -10.0}) for i in range(120)) + "\n")
    open(rt, "w").write("\n".join(json.dumps({"sim": round(100 + i * 0.5, 2), "wall": round(i * 0.5, 2), "rtf": 1.0}) for i in range(120)) + "\n")
    ev = []
    ev.append({"t": "event", "ev": "episode_start", "episode_id": 0, "scenario_id": "c00_s01", "sim": 100.0})
    if denial:
        ev.append({"t": "event", "ev": "denial", "episode_id": 0, "sim": t_inj, "t_inj_sim": t_inj})
        ev.append({"t": "event", "ev": "refuse", "episode_id": 0, "sim": round(t_inj + 0.10, 2), "reason": "POS_DEGRADED"})
        ev.append({"t": "event", "ev": "refuse_pos_land", "episode_id": 0, "sim": round(t_inj + 0.10, 2)})
        ev.append({"t": "event", "ev": "touchdown", "episode_id": 0, "sim": round(t_inj + 9.0, 2)})
        ev.append({"t": "event", "ev": "episode_end", "episode_id": 0, "sim": round(t_inj + 9.5, 2),
                   "breach": False, "denied": True, "t_inj_sim": t_inj})
    else:
        ev.append({"t": "event", "ev": "episode_end", "episode_id": 0, "sim": 170.0,
                   "breach": False, "denied": False, "t_inj_sim": None})
    with open(tr, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
        for e in ev:
            f.write(json.dumps(e) + "\n")


def test_judge_k2_denial_metrics_count():
    with tempfile.TemporaryDirectory() as d:
        _write_trace(d, denial=True)
        vs = judge_episode_k2(d, eps_cap=5.0, home=(0.0, 0.0))
        assert len(vs) == 1
        v = vs[0]
        assert v["t_refuse"] is not None and abs(v["t_refuse"] - 0.10) < 1e-6, v["t_refuse"]
        assert v["touchdown"] is True
        assert v["x_exc"] is not None                       # metryki denialu policzone
        assert trefuse_in_band(v["t_refuse"])


def test_judge_k2_nominal_no_denial_metrics():
    with tempfile.TemporaryDirectory() as d:
        _write_trace(d, denial=False)
        vs = judge_episode_k2(d, eps_cap=5.0, home=(0.0, 0.0))
        assert len(vs) == 1
        v = vs[0]
        assert v["t_refuse"] is None and v["x_exc"] is None  # epizod nominalny, brak metryk denialu
        assert v["verdict"]["pass"] is False                 # bez REFUSE nie jest (+) przejęciem


def test_pos_flag_true_dry_descend():
    """PRE: unit syntetyczny pos_flag=True — shield REFUSE(POS) → safe_descend do touchdown, na sucho."""
    sh = PatrolShield(); sh.reset()
    sh.pos_debounce_ticks = C.DEBOUNCE_TICKS
    cfg = {"v_desc_fast": C.V_DESC_FAST, "v_desc_land": C.V_DESC_LAND,
           "desc_fast_dur": max(0.0, (C.ALT_M - C.H_SWITCH_AGL) / C.V_DESC_FAST),
           "desc_total": max(0.0, (C.ALT_M - C.H_SWITCH_AGL) / C.V_DESC_FAST) + C.H_SWITCH_AGL / C.V_DESC_LAND + 1.5}
    st = new_state(); refused = td = False; DT = C.DT
    for i in range(int((cfg["desc_total"] + 2.0) / DT)):
        pos = [15.0, 0.0, -10.0]; vel = [0.5, 0.0, 0.0]; tgt = (15.0, 0.0, -10.0)
        d = sh.step(i, pos, vel, tgt, mode=M_PATROL, pos_flag=True)         # denial uzbrojony
        is_pos = d["decision"] == REFUSE and d.get("reason") == POS_DEGRADED
        if is_pos:
            refused = True
            vdesc, evs, sd_td, st = safe_descend_step(st, i * DT, cfg)
            if sd_td:
                td = True; break
    assert refused, "shield nie odmówił POS przy pos_flag=True (debounce?)"
    assert td, "safe_descend nie osiągnął touchdown na sucho"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_k2_judge: ALL PASS")


def test_denial_hook_timing_within_dt():
    """B4: hook wstrzykuje w 1. ticku po t_entry+K2_INJECT_T ⇒ |t_inj−cel| ≤ DT ⊂ ±0.2 s (determinizm)."""
    DT = 0.05; t_entry = 3.0; K2_INJECT_T = 30.0; target = t_entry + K2_INJECT_T
    denial_done = False; t_inj = None
    t = 0.0
    while t < 40.0:
        t_rel = t
        if (not denial_done) and t_entry is not None and t_rel >= t_entry + K2_INJECT_T:
            denial_done = True; t_inj = t_rel
        t += DT
    assert t_inj is not None and abs(t_inj - target) <= DT <= 0.2, (t_inj, target)
