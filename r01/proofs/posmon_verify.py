"""r01/proofs/posmon_verify.py — O2 (histereza `_pos_monitor`), cert P7_posmon (PRE_FV §3/O2, PROMPT_FV_S2 §3).

Dowód NA GRAFIE osiągalnym FSM monitora pozycji, transitions z LUSTRA (fv_mirror.pos_monitor_step ≡
produkcja r01/shield.py:76-94; różnicówka S1 + M-krok 27/27). Metoda podstawowa: wyczerpująca enumeracja
(BFS), z3-indukcja jako duplikat kroku (O2d).

ABSTRAKCJA (jawna, sound): w kodzie `pos_bad += 1` NIE jest capowane (shield.py:83) — surowy stan
nieskończony. Ale `pos_bad` czytane WYŁĄCZNIE przez `pos_bad >= debounce_ticks` (shield.py:85 /
fv_mirror.py:66). Zatem saturacja `pos_bad := min(pos_bad, debounce)` PO każdym kroku jest
ZACHOWUJĄCA ZACHOWANIE (decyzja i przyszłość zależą tylko od `>=debounce` i resetu do 0 na False,
shield.py:89). `pos_healthy` bounded z natury: rośnie tylko w refuse na False, reset przy `>=hyst`
(shield.py:91-94) ⇒ h ∈ {0..hyst-1}. Stan abstrakcyjny = (min(pos_bad,deb), pos_healthy, pos_refuse).
Alfabet Σ={True,False}; None = no-op (shield.py:80-81) — pętla własna, nie zmienia grafu ani liczników
(pomijana w BFS, odnotowana).

Twierdzenia (PRE §3/O2), sprawdzane algorytmicznie na CAŁYM grafie:
  (a) każde wejście w REFUSE(POS) (krawędź r:False→True) jest na wejściu True i ze stanu pos_bad=deb−1;
      minimalny bieg True do wejścia = debounce (F resetuje pos_bad → potrzeba deb kolejnych True).
  (b) każde wyjście (krawędź r:True→False) jest na wejściu False i ze stanu pos_healthy=hyst−1;
      minimalny bieg False do wyjścia = hyst (True resetuje pos_healthy).
  (c) dolne ograniczenie cyklu zdegradowany→czysty→zdegradowany = hyst + debounce
      (wyjście wymaga hyst czystych, ponowne wejście deb bad — brak trzepotania szybszego niż histereza).

Uruchom: PYTHONPATH=.certdeps python3 -m r01.proofs.posmon_verify
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
from collections import deque

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from r01.proofs import fv_mirror as M

CERT = os.path.join(_HERE, "certs", "P7_posmon.json")


def _self_sha() -> str:
    return hashlib.sha256(open(__file__, "rb").read()).hexdigest()


def _step_abstract(state, flag, deb, hyst):
    """Krok LUSTRA na stanie abstrakcyjnym; zwraca (nowy_stan_abstrakcyjny, enter_event).
    Wykorzystuje fv_mirror.pos_monitor_step (semantyka z kodu), potem saturuje pos_bad do deb."""
    a, h, r = state
    st = {"pos_bad": a, "pos_healthy": h, "pos_refuse": r, "n_pos_enter": 0}
    M.pos_monitor_step(st, flag, deb, hyst)
    enter = (not r) and st["pos_refuse"]         # krawędź r:False→True
    a2 = min(st["pos_bad"], deb)                  # saturacja (sound — patrz docstring)
    return (a2, st["pos_healthy"], st["pos_refuse"]), enter


def build_graph(deb, hyst):
    """BFS pełnego osiągalnego grafu ze stanu init (0,0,False). Σ={True,False}."""
    init = (0, 0, False)
    nodes = {init}
    edges = []                       # (src, flag, dst, enter)
    q = deque([init])
    while q:
        s = q.popleft()
        for flag in (True, False):
            d, enter = _step_abstract(s, flag, deb, hyst)
            edges.append((s, flag, d, enter))
            if d not in nodes:
                nodes.add(d)
                q.append(d)
    return nodes, edges


def _bfs_dist(edges, src, pred):
    """Najkrótsza liczba krawędzi z src do stanu spełniającego pred(state). None gdy nieosiągalne."""
    adj = {}
    for s, f, d, e in edges:
        adj.setdefault(s, []).append(d)
    if pred(src):
        return 0
    seen = {src}
    q = deque([(src, 0)])
    while q:
        s, dist = q.popleft()
        for d in adj.get(s, []):
            if d not in seen:
                if pred(d):
                    return dist + 1
                seen.add(d)
                q.append((d, dist + 1))
    return None


def _bfs_dist_to_enter_edge(edges, src):
    """Najkrótsza liczba krawędzi z src do PRZEJŚCIA krawędzią enter (r:False→True)."""
    adj = {}
    enter_src = set()
    for s, f, d, e in edges:
        adj.setdefault(s, []).append(d)
        if e:
            enter_src.add(s)
    # dystans do stanu będącego źródłem krawędzi enter, +1 (sama krawędź enter)
    if src in enter_src:
        return 1
    seen = {src}
    q = deque([(src, 0)])
    while q:
        s, dist = q.popleft()
        for d in adj.get(s, []):
            if d not in seen:
                if d in enter_src:
                    return dist + 2
                seen.add(d)
                q.append((d, dist + 1))
    return None


def prove():
    th = M.shield_thresholds()
    deb, hyst = th["debounce_ticks"], th["hyst_ticks"]
    nodes, edges = build_graph(deb, hyst)
    res = {}

    # (a) enter-edges
    enter_edges = [(s, f, d) for (s, f, d, e) in edges if e]
    a_ok = all(f is True and s[0] == deb - 1 for (s, f, d) in enter_edges)
    res["a_enter_only_True_and_bad_eq_deb_minus_1"] = "PASS" if a_ok else "FAIL"
    a_min_run = _bfs_dist(edges, (0, 0, False), lambda st: st[2] is True)
    res["a_min_True_run_to_enter"] = a_min_run

    # (b) exit-edges (r True→False)
    exit_edges = [(s, f, d) for (s, f, d, e) in edges if s[2] and not d[2]]
    b_ok = all(f is False and s[1] == hyst - 1 for (s, f, d) in exit_edges)
    res["b_exit_only_False_and_healthy_eq_hyst_minus_1"] = "PASS" if b_ok else "FAIL"
    post_enter = (deb, 0, True)      # stan po wejściu (pos_bad saturowany, r=True)
    b_min_run = _bfs_dist(edges, post_enter, lambda st: st[2] is False)
    res["b_min_False_run_to_exit"] = b_min_run

    # (c) dolne ograniczenie cyklu re-enter
    c_cycle = _bfs_dist_to_enter_edge(edges, post_enter)
    res["c_min_reenter_cycle"] = c_cycle

    checks = {
        "a_ok": a_ok,
        "a_min_run_eq_deb": (a_min_run == deb),
        "b_ok": b_ok,
        "b_min_run_eq_hyst": (b_min_run == hyst),
        "c_cycle_eq_hyst_plus_deb": (c_cycle == hyst + deb),
    }
    return res, checks, nodes, edges, deb, hyst


# ------------------------- z3 duplikat (O2d, krok) --------------------------
def z3_step_invariants(deb, hyst):
    """z3-indukcja kroku: (a-step) enter ⇒ input=True ∧ pos_bad≥deb−1; (b-step) exit ⇒ input=False
    ∧ pos_healthy≥hyst−1. Transition zakodowany 1:1 z fv_mirror.pos_monitor_step (T/F)."""
    try:
        import z3
    except Exception as e:
        return {"z3_a_step": f"brak z3: {type(e).__name__}", "z3_b_step": "-"}
    b, h = z3.Ints("b h")
    r = z3.Bool("r")
    f = z3.Bool("f")           # True⇒pos_flag True, False⇒pos_flag False
    D, H = z3.IntVal(deb), z3.IntVal(hyst)
    dom = z3.And(b >= 0, h >= 0, b <= D, h <= H - 1)   # dziedzina stanu abstrakcyjnego

    # transition (pos_monitor_step, gałąź T / F)
    bT = b + 1
    enterT = z3.And(bT >= D, z3.Not(r))
    rT = z3.Or(r, enterT)
    # gałąź F
    h1 = h + 1
    exitF = z3.And(r, h1 >= H)
    rF = z3.If(r, z3.If(h1 >= H, z3.BoolVal(False), z3.BoolVal(True)), r)
    r_next = z3.If(f, rT, rF)

    def holds(neg):
        s = z3.Solver(); s.add(dom); s.add(neg)
        return "unsat" if s.check() == z3.unsat else "sat"

    out = {}
    # (a-step): (¬r ∧ r_next) ⇒ f ∧ b ≥ D−1
    out["z3_a_step"] = holds(z3.And(z3.Not(r), r_next, z3.Not(z3.And(f, b >= D - 1))))
    # (b-step): (r ∧ ¬r_next) ⇒ ¬f ∧ h ≥ H−1
    out["z3_b_step"] = holds(z3.And(r, z3.Not(r_next), z3.Not(z3.And(z3.Not(f), h >= H - 1))))
    return out


EXPECT_CHECKS = ["a_ok", "a_min_run_eq_deb", "b_ok", "b_min_run_eq_hyst", "c_cycle_eq_hyst_plus_deb"]


def main():
    res, checks, nodes, edges, deb, hyst = prove()
    z3res = z3_step_invariants(deb, hyst)
    graph_ok = all(checks[k] for k in EXPECT_CHECKS)
    print("=== O2 dowód histerezy (enumeracja grafu + z3-duplikat) ===")
    print(f"  debounce={deb} hyst={hyst}  |  n_stanów={len(nodes)} n_krawędzi={len(edges)}")
    for k, v in res.items():
        print(f"  {k}: {v}")
    print(f"  checks: {checks}")
    print(f"  z3: {z3res}")
    verdict = "PROVED" if graph_ok else "UNPROVEN"
    print(f"WERDYKT O2 (P7_posmon): {verdict}")
    if not graph_ok:
        sys.exit(1)
    cert = {
        "property": "P7_posmon",
        "verdict": "PROVED",
        "method": "wyczerpująca enumeracja osiągalnego grafu FSM (BFS) na lustrze ≡ produkcja "
                  "(fv_mirror.pos_monitor_step; różnicówka S1 + M-krok 27/27); z3-indukcja kroku jako duplikat",
        "obligations": res,
        "checks": {k: bool(checks[k]) for k in checks},
        "z3_duplicate": z3res,
        "graph": {"n_states": len(nodes), "n_edges": len(edges), "alphabet": ["True", "False"],
                  "none_input": "no-op (shield.py:80-81) — pętla własna, poza grafem"},
        "theorem": "(a) r:False→True tylko na True ∧ pos_bad=debounce−1; min bieg True do wejścia = debounce; "
                   "(b) r:True→False tylko na False ∧ pos_healthy=hyst−1; min bieg False do wyjścia = hyst; "
                   "(c) min cykl zdegradowany→czysty→zdegradowany = hyst+debounce",
        "constants": {
            "debounce_ticks": deb, "hyst_ticks": hyst,
            "debounce_source": "r01/shield.py:72 (pos_debounce_ticks=2) == r03/config.py:30 DEBOUNCE_TICKS",
            "hyst_source": "r01/shield.py:73-74 (int(round(5.0/dt))) ; dt=0.05 (r01/config.py:41) ⇒ 100; "
                           "HYST_M_S=5.0 (r03/config.py:31)",
            "min_reenter_cycle": hyst + deb,
        },
        "abstraction": "pos_bad saturowany do debounce (min(pos_bad,deb)) — SOUND: pos_bad czytany wyłącznie "
                       "przez `>=debounce` (shield.py:85) i resetowany do 0 na False (shield.py:89); "
                       "wartość powyżej debounce nie wpływa na decyzję ani przyszłość. pos_healthy∈{0..hyst-1} "
                       "z natury (reset przy >=hyst, shield.py:91-94).",
        "assumptions": [
            "Semantyka wg LUSTRA ≡ produkcja: fv_mirror.pos_monitor_step bit-w-bit z r01/shield.py:76-94 "
            "(różnicówka tests_fv_diff.py: siatka+fuzz 4×10⁵+fikstura, 0 rozbieżności; M-krok: 27/27 mutantów wykrytych).",
            "None ⇒ monitor nieaktywny (bez zmian, shield.py:80-81) — no-op, poza alfabetem grafu.",
            "Stałe debounce/hyst z config (V5, cytaty w 'constants').",
        ],
        "code_refs": {
            "mirror": "r01/proofs/fv_mirror.py:pos_monitor_step",
            "production": "r01/shield.py:76-94 (_pos_monitor)",
            "config": "r01/shield.py:72-74 + r03/config.py:30-31 + r01/config.py:41",
        },
        "model_sha256": _self_sha(),
    }
    os.makedirs(os.path.dirname(CERT), exist_ok=True)
    if os.path.exists(CERT):
        old = json.load(open(CERT))
        print(f"cert istnieje — zgodność sha: {'TAK' if old.get('model_sha256')==cert['model_sha256'] else 'NIE'}")
    json.dump(cert, open(CERT, "w"), indent=2, ensure_ascii=False)
    print(f"zapisano {CERT} (sha={cert['model_sha256'][:16]}…)")


if __name__ == "__main__":
    main()
