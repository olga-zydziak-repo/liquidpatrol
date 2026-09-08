#!/usr/bin/env python3
"""bench/tests_safe_descend.py — test bit-w-bit ekstrakcji D5 (PROMPT_K2_BUILD B2, wzór INFRA-3 A1.3).

(i) REFERENCJA `ref_descend` = LITERALNA transkrypcja bloku is_pos z pinu `gate_run_r03.py:275-289`
    (c3ccabe0), z jedyną zmianą monotonic→`now` (jak w ekstrakcie — chirurgia zachowuje zachowanie).
(ii) Wejścia = wiersze `tick` (pola `pos`, `descending`) ze WSZYSTKICH lotów S serii K1 z wierszami tick
     (`results/K1/S/**/trace.jsonl`) = 4221 ticków (1791 z descending) — ta sama fikstura co A1.3.
(iii) Asercja: dla KAŻDEGO ticka referencja i `safe_descend_step` dają IDENTYCZNE (bit-w-bit)
      (vdesc, events, touchdown, stan) — bez tolerancji (SR-4).
(iv) Test syntetyczny przejść faz: el rośnie przez desc_fast_dur (h_switch) i desc_total (touchdown).
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from r03.controllers.safe_descend import safe_descend_step, new_state

DT = 0.05
# cfg reprezentatywne (ALT=15: desc_fast_dur=(15-2)/1.5, desc_total=...+2/0.7+1.5); dowolne cfg dowodzi równoważności
CFG = {"v_desc_fast": 1.5, "v_desc_land": 0.7,
       "desc_fast_dur": (15.0 - 2.0) / 1.5, "desc_total": (15.0 - 2.0) / 1.5 + 2.0 / 0.7 + 1.5}


def ref_descend(st, now, cfg):
    """LITERALNA transkrypcja bloku is_pos (gate_run_r03.py:275-289 @ c3ccabe0), monotonic→now."""
    events = []
    if not st["descending"]:
        st["descending"] = True; st["desc_t0"] = now; events.append("refuse_pos_land")
    el = now - st["desc_t0"]
    if el < cfg["desc_fast_dur"]:
        vdesc = cfg["v_desc_fast"]
    else:
        if not st["h_switched"]:
            events.append("h_switch"); st["h_switched"] = True
        vdesc = cfg["v_desc_land"]
    touchdown = False
    if el >= cfg["desc_total"] and not st["td"]:
        events.append("touchdown"); st["td"] = True; touchdown = True
    return vdesc, events, touchdown, st


def _fixture():
    """Zwraca listę (plik, [descending_bool per tick]) z lotów S z wierszami tick."""
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "results/K1/S/**/trace.jsonl"), recursive=True)):
        seq = []
        for l in open(f):
            if '"t": "tick"' in l:
                try:
                    r = json.loads(l)
                except Exception:
                    continue
                seq.append(bool(r.get("descending")))
        if seq:
            out.append((f, seq))
    return out


def test_fixture_size_4221():
    fx = _fixture()
    tot = sum(len(s) for _, s in fx)
    desc = sum(sum(s) for _, s in fx)
    assert tot == 4221, tot
    assert desc == 1791, desc
    assert len(fx) == 11, len(fx)


def test_bit_exact_ref_vs_extract():
    """4221 ticków: referencja == safe_descend_step, bit-w-bit (vdesc, events, touchdown, stan)."""
    fx = _fixture()
    n_desc = 0
    for _, seq in fx:
        st_ref = new_state(); st_new = new_state()
        for idx, desc in enumerate(seq):
            if not desc:
                continue                       # tylko ticki fazy zejścia (is_pos) napędzają D5
            now = idx * DT
            n_desc += 1
            v_ref, e_ref, td_ref, st_ref = ref_descend(st_ref, now, CFG)
            v_new, e_new, td_new, st_new = safe_descend_step(st_new, now, CFG)
            assert v_ref == v_new, (idx, v_ref, v_new)
            assert e_ref == e_new, (idx, e_ref, e_new)
            assert td_ref == td_new, (idx, td_ref, td_new)
            assert st_ref == st_new, (idx, st_ref, st_new)
    assert n_desc == 1791, n_desc


def test_phase_transitions_synthetic():
    """Wszystkie gałęzie: V_DESC_FAST → h_switch → V_DESC_LAND → touchdown."""
    st = new_state()
    seen = {"refuse_pos_land": False, "h_switch": False, "touchdown": False}
    n = int((CFG["desc_total"] + 2.0) / DT)
    fast_seen = land_seen = False
    for idx in range(n):
        v, evs, td, st = safe_descend_step(st, idx * DT, CFG)
        for e in evs:
            seen[e] = True
        if v == CFG["v_desc_fast"]:
            fast_seen = True
        if v == CFG["v_desc_land"]:
            land_seen = True
    assert seen["refuse_pos_land"] and seen["h_switch"] and seen["touchdown"]
    assert fast_seen and land_seen
    assert st["td"] is True


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_safe_descend: ALL PASS")
