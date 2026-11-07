#!/usr/bin/env python3
"""results/KONT/s3/tools/kont_mutants.py — M-krok P5_kont: mutanty LUSTRA nakładki vs produkcja (wzorzec
r01/proofs/tests_fv_mutants.py; ANEKS_KONT-3b §1.6).

Adekwatność różnicówki: dla KAŻDEGO mutanta z katalogu MUTANTS (prereg, niżej) istnieje ≥ 1 rozbieżność
mutant-lustro ↔ produkcja (r03/kont_shield.KontShield) na siatce prereg ∪ fiksturze S2 ∪ fuzz (ziarno 1,
2000 epizodów). Mutacja = podmiana tekstu w źródle funkcji lustra w pamięci (dokładnie jedno wystąpienie,
asercja); p9_kont_verify.py na dysku NIETKNIĘTY. Wyjątek mutanta liczy się jako wykrycie.

Uruchom: PYTHONPATH=.:.certdeps python3 results/KONT/s3/tools/kont_mutants.py [wyjście.json]
"""
from __future__ import annotations
import inspect
import json
import os
import random
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from r01.proofs import p9_kont_verify as P

# (nazwa, funkcja lustra, tekst, zamiennik) — katalog prereg
MUTANTS = [
    ("g_debounce_minus_1", "g_monitor_step", 'g["g_bad"] >= deb', 'g["g_bad"] >= deb - 1'),
    ("g_hyst_minus_1", "g_monitor_step", 'g["g_healthy"] >= hyst', 'g["g_healthy"] >= hyst - 1'),
    ("g_no_backdate", "g_monitor_step", 'g["kont_t0"] = g["run_t0"]', 'g["kont_t0"] = now'),
    ("g_polarity", "mirror_step", "None if cs is None else (not cs)", "None if cs is None else cs"),
    ("g_exit_keeps_kref", "g_monitor_step", 'g["kref"] = False\n', 'g["kref"] = g["kref"]\n'),
    ("g_flicker_no_reset", "g_monitor_step", '        g["g_healthy"] = 0\n        if g["g_bad"] >= deb',
     '        if g["g_bad"] >= deb'),
    ("b_tstar_strict", "g_barrier_step", "t >= tstar", "t > tstar"),
    ("b_tstar_minus_1", "g_barrier_step", "t >= tstar", "t >= tstar - 1"),
    ("b_not_sticky", "g_barrier_step", 'if g["kref"]:\n        return g', 'if False:\n        return g'),
    ("b_bucket_round", "mirror_step", 'C["R_k"][int(math.floor(t))]', 'C["R_k"][min(int(round(t)), C["tstar"] - 1)]'),
    ("b_bar_ge", "mirror_step", 'r_est > C["R_k"]', 'r_est >= C["R_k"]'),
    ("n_rnom_old", "mirror_step", 'r_est > C["r_nom"]', 'r_est > 27.51'),
    ("n_rnom_ge", "mirror_step", 'r_est > C["r_nom"]', 'r_est >= C["r_nom"]'),
    ("n_outward_sign", "mirror_step", "m_outward(pos, target) > 0.0", "m_outward(pos, target) < 0.0"),
    ("n_no_strip", "mirror_step", "ax, ay = m_strip(", "ax, ay = (lambda vx, vy, p: (vx, vy))("),
    ("n_state_patrol", "mirror_step", '"state": st["state"], "decision": REFUSE, "reason": GEOFENCE, "rule": "R-G-NOM"',
     '"state": PATROL, "decision": REFUSE, "reason": GEOFENCE, "rule": "R-G-NOM"'),
    ("n_latching", "mirror_step", '"rule": "R-G-NOM",', '"rule": "R-G-NOM", "_": st.update(terminal=(GEOFENCE, "R-G-NOM")),'),
    ("p_kont_below_geo", "mirror_step", 'if g["kref"]:\n        st["state"] = POSDEG',
     'if g["kref"] and not FM.geofence_violation(pos, vel, target, C["r_e"], C["v_e"], C["v_max"], C["a_brake"])[0]:\n        st["state"] = POSDEG'),
    ("p_nom_above_geo", "mirror_step", "    if viol:\n", "    if viol and not (r_est > C[\"r_nom\"] and m_outward(pos, target) > 0.0):\n"),
    ("p_pos_disarmed_in_kont", "mirror_step", 'if st["pos"]["pos_refuse"]:', 'if st["pos"]["pos_refuse"] and not g["kont"]:'),
    ("a_kont_action_plain", "mirror_step", '"action": "VELOCITY_DESCENT_YAW_HOLD"', '"action": "VELOCITY_DESCENT"'),
]


MIRROR_FNS = ("m_outward", "m_strip", "g_monitor_step", "g_barrier_step", "mirror_step")


def _mutate(name, fn, old, new):
    """Wszystkie funkcje lustra kompilowane w przestrzeni mutanta (inaczej mirror_step woła oryginały z modułu)."""
    ns = dict(vars(P))
    for f in MIRROR_FNS:
        src = inspect.getsource(getattr(P, f))
        if f == fn:
            assert src.count(old) == 1, (name, fn, src.count(old))
            src = src.replace(old, new)
        exec(compile(src, f"<mutant {name}:{f}>", "exec"), ns)
    return ns


def _episodes(C):
    grid = json.load(open(P.GRID))
    eps = [(e["ticks"], e["hyst"], tuple(e["latch"]) if e["latch"] else None) for e in grid["episodes"]]
    # brzeg równości (r_est = R(k), r_est = R_nom) — brak w siatce prereg (luka nazwana w RAPORT_KONT_S3)
    for k in (0, 9, 21):
        r = C["R_k"][k]
        eps.append(([P._tick((r, 0.0, -10.0), cs_gnss_pos=False, now=0.0),
                     P._tick((r, 0.0, -10.0), cs_gnss_pos=False, now=k + 0.5)], None, None))
    eps.append(([P._tick((C["r_nom"], 0.0, -10.0), target=(C["r_nom"] + 1.0, 0.0, -10.0), cs_gnss_pos=True,
                         now=0.0)], None, None))
    for fl in P.s2_flights():
        eps.append((P.s2_fixture(fl)[0], None, None))
    rng = random.Random(1)
    for _ in range(2000):
        t, h = P.fuzz_episode(rng, C)
        eps.append((t, h, None))
    return eps


def _detect(ns, eps, C):
    """Pierwsza rozbieżność produkcja ↔ mutant-lustro (mirror_step z przestrzeni mutanta)."""
    for ticks, hyst, latch in eps:
        sh = P._new_prod(C, hyst)
        Cm = dict(C)
        if hyst is not None:
            Cm["hyst_ticks"] = hyst
        st = P.new_mirror_state()
        if latch is not None:
            sh.latch_refuse(*latch); st["terminal"] = latch; st["state"] = P.DONE
        for k, inp in enumerate(ticks):
            d = sh.step(k, inp["pos"], inp["vel"], inp["target"], mode=inp.get("mode", P.M_PATROL),
                        pos_flag=inp.get("pos_flag"), auth_ok=inp.get("auth_ok", True),
                        cs_gnss_pos=inp.get("cs_gnss_pos"), now=inp.get("now"), r_est=inp.get("r_est"))
            try:
                m = ns["mirror_step"](st, k, inp, Cm)
            except Exception as e:
                return f"wyjątek {type(e).__name__}"
            if P.prod_core(d, sh) != P.mir_core(m):
                return f"tick {k}"
    return None


def main():
    C = P.mirror_consts()
    eps = _episodes(C)
    clean = _detect(dict(vars(P)), eps, C)
    assert clean is None, f"lustro czyste ma rozbieżność: {clean}"
    rows = []
    for name, fn, old, new in MUTANTS:
        ns = _mutate(name, fn, old, new)
        det = _detect(ns, eps, C)
        rows.append({"mutant": name, "funkcja": fn, "wykryty": det is not None, "gdzie": det})
        print(f"  {'WYKRYTY ' if det else 'PRZEŻYŁ '} {name:24s} {det}")
    n = sum(r["wykryty"] for r in rows)
    print(f"WERDYKT mutanty: {n}/{len(rows)} wykryte (lustro czyste: 0 rozbieżności, {len(eps)} epizodów)")
    if len(sys.argv) > 1:
        json.dump({"epizody": len(eps), "lustro_czyste_rozbieznosci": 0, "mutanty": rows,
                   "wykryte": n, "razem": len(rows)}, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)
    sys.exit(0 if n == len(rows) else 1)


if __name__ == "__main__":
    main()
