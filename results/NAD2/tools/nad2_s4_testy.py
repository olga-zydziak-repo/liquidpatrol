#!/usr/bin/env python3
"""results/NAD2/tools/nad2_s4_testy.py — testy przed lotem długim (ANEKS_NAD2-3 §2), 0 bootów.

T1 prefiks: pierwsze 200 s nowego wzoru = wzór bramki (siatka 0.1 s, |Δ| ≤ 1e-6 m) — c10_s01 i wszystkie 120 epizodów.
T2 ciągłość: max krok pozycji między próbkami 0.1 s ≤ v·0.1 + 1e-6 m na 0–800 s (zero skoków).
T3 prędkość stała = v komórki (wszystkie odcinki), tor w dysku r ≤ DISK_R.
T4 na sucho: IntruderMotion.run_episode (harness, nietknięty) na nowym manifeście z zegarem syntetycznym — prowadzi intruza
   ≥ 700 s bez zatrzymania; kontrast: manifest bramki zatrzymuje się po 200 s.
T5 domyślne: bez env ścieżka i suma manifestu, T_CONT_S, WALL_MAX_CUT_S i LIMIT = wartości bramki; z env = wartości lotu.
T6 diff: bd975df5 → drzewo pusty dla zamrożonych poza 3 plikami z listy ANEKS_NAD2-3 §2; w nich tylko linie env.
Użycie: nad2_s4_testy.py [manifest] [wyjście] (dom. scenario_manifest_s4L.json → testy_s4.json; pozycja 1: *_poz1).
T4: max krok komendy w przebiegu na sucho jest informacyjny (cmd_ned zaokrąglone do 1e-4 m); bramkuje „bez zatrzymania”
i ruch w 600–700 s — ciągłość bramkuje T2. (Pierwsza wersja bramkowała też krok komendy z progiem v·0.02 + 1e-4; pozycja 1
miała 0.020123 m.)
Wyjście: results/NAD2/s4/testy_s4.json.
"""
import ast
import hashlib
import json
import math
import os
import subprocess
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
from bench import scenarios as S
from harness.intruder_motion import IntruderMotion

BRAMKA = "results/NADIR/s4/scenario_manifest_s4.json"
NOWY = sys.argv[1] if len(sys.argv) > 1 else "results/NAD2/s4/scenario_manifest_s4L.json"
SHA_BRAMKI = "090af08bc9a1ef1c6f024a1bb81a816b1f4231e1d0407783466f1dfe322909c0"
EPID = 10                                                  # c10_s01
OUT = os.path.join(ROOT, sys.argv[2] if len(sys.argv) > 2 else "results/NAD2/s4/testy_s4.json")
ZMIENIONE = ["results/NAD2/tools/nad2_flight.py", "results/NAD2/tools/nad2_boot.sh", "results/NAD2/tools/nad2_ulg.py"]
ZAMROZONE = ["harness", "r01", "r03", "results/NAD2/s1/freeze_U.json", "results/NAD2/tools/nad2_krok.py",
             "results/NAD2/tools/nad2_launch.sh", "results/NAD2/tools/nad2_analyze.py", "results/NAD2/tools/nad2_s2_spr.py",
             "results/NAD2/tools/nad2_certs_selfcheck.py", BRAMKA, "bench/scenarios.py"]


def sha(p):
    return hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()


def siatka(T, dt=0.1):
    return [round(i * dt, 6) for i in range(int(round(T / dt)) + 1)]


def t1(bra, now):
    worst = 0.0; worst_c10 = 0.0
    for a, b in zip(bra["episodes"], now["episodes"]):
        for t in siatka(200.0):
            pa, pb = S.position_at(a, t), S.position_at(b, t)
            d = math.dist(pa, pb)
            worst = max(worst, d)
            if a["episode_id"] == EPID:
                worst_c10 = max(worst_c10, d)
    return {"max_delta_c10_s01_m": worst_c10, "max_delta_120_ep_m": worst, "PASS": worst_c10 <= 1e-6 and worst <= 1e-6}


def t2_t3(now):
    ep = now["episodes"][EPID]
    v = ep["cell"]["v_intr"]
    pts = [S.position_at(ep, t) for t in siatka(800.0)]
    kroki = [math.dist(p, q) for p, q in zip(pts, pts[1:])]
    rmax = max(math.hypot(x, y) for x, y, _ in pts)
    vs = sorted({s["v"] for s in ep["segments"]})
    zakres = [ep["segments"][0]["t0"], ep["segments"][-1]["t1"]]
    # kontrast: wzór bramki po 200 s (position_at trzyma koniec ostatniego odcinka) — nie dotyczy lotu; tylko ciągłość
    return ({"v": v, "max_krok_m": max(kroki), "prog_m": v * 0.1 + 1e-6, "n_probek": len(pts),
             "PASS": max(kroki) <= v * 0.1 + 1e-6},
            {"v_odcinkow": vs, "n_odcinkow": len(ep["segments"]), "zakres_s": zakres, "r_max_m": round(rmax, 4),
             "disk_r_m": S.DISK_R, "PASS": vs == [v] and rmax <= S.DISK_R + 1e-6 and zakres[1] >= 700.0})


def na_sucho(ep, dur):
    zegar = [0.0]
    rows = []
    im = IntruderMotion(set_pose_fn=lambda x, y, z: None, clock_fn=lambda: zegar[0])

    def krok():
        zegar[0] = round(zegar[0] + 0.02, 6)
    im.run_episode(ep, 0.0, dur, rows.append, step_fn=krok)
    return rows


def t4(bra, now):
    ep = now["episodes"][EPID]
    rows = na_sucho(ep, ep["ep_dur_s"])
    cmd = [r["cmd_ned"] for r in rows]
    kroki = [math.dist(p, q) for p, q in zip(cmd, cmd[1:])]
    t_end = rows[-1]["t_sim"]
    # ruch w ostatnich 100 s (intruz nie stoi): przemieszczenie skumulowane 600–700 s
    ruch = sum(k for r, k in zip(rows[1:], kroki) if 600.0 <= r["t_sim"] <= 700.0)
    bra_rows = na_sucho(bra["episodes"][EPID], bra["episodes"][EPID]["ep_dur_s"])
    v = ep["cell"]["v_intr"]
    return {"ep_dur_s": ep["ep_dur_s"], "t_ostatni_s": t_end, "n_setpose": rows and len(rows), "max_krok_cmd_m": round(max(kroki), 6),
            "droga_600_700_m": round(ruch, 3),
            "kontrast_bramka_t_ostatni_s": bra_rows[-1]["t_sim"],
            "PASS": t_end >= 700.0 and ruch >= 0.9 * v * 100.0}


def _py_stala(plik, nazwa, env):
    drzewo = ast.parse(open(os.path.join(ROOT, plik), encoding="utf-8").read())
    for n in drzewo.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == nazwa for t in n.targets):
            stare = dict(os.environ)
            try:
                os.environ.clear(); os.environ.update(env)
                return eval(compile(ast.Expression(n.value), plik, "eval"), {"os": os})
            finally:
                os.environ.clear(); os.environ.update(stare)
    raise KeyError(nazwa)


def _bash_man(env):
    linia = [l for l in open(os.path.join(ROOT, "results/NAD2/tools/nad2_boot.sh"), encoding="utf-8") if l.startswith("S4MAN=")][0]
    r = subprocess.run(["bash", "-c", linia + 'echo "$S4MAN|$S4MAN_SHA"'], env={"PATH": os.environ["PATH"], **env},
                       capture_output=True, text=True)
    return r.stdout.strip().split("|")


def t5():
    lot = {"NAD2_T_CONT_S": "600.5", "NAD2_WALL_MAX_CUT_S": "1000", "NAD2_ULG_LIMIT_MB": "10",
           "NAD2_MANIFEST": NOWY, "NAD2_MANIFEST_SHA": sha(NOWY)}
    dom = {"T_CONT_S": _py_stala("results/NAD2/tools/nad2_flight.py", "T_CONT_S", {}),
           "WALL_MAX_CUT_S": _py_stala("results/NAD2/tools/nad2_flight.py", "WALL_MAX_CUT_S", {}),
           "LIMIT": _py_stala("results/NAD2/tools/nad2_ulg.py", "LIMIT", {}),
           "manifest": _bash_man({})}
    zenv = {"T_CONT_S": _py_stala("results/NAD2/tools/nad2_flight.py", "T_CONT_S", lot),
            "WALL_MAX_CUT_S": _py_stala("results/NAD2/tools/nad2_flight.py", "WALL_MAX_CUT_S", lot),
            "LIMIT": _py_stala("results/NAD2/tools/nad2_ulg.py", "LIMIT", lot),
            "manifest": _bash_man(lot)}
    ok_dom = (dom["T_CONT_S"] == 110.5 and dom["WALL_MAX_CUT_S"] == 300.0 and dom["LIMIT"] == 3 * 1024 * 1024
              and dom["manifest"] == [BRAMKA, SHA_BRAMKI] and sha(BRAMKA) == SHA_BRAMKI)
    ok_env = (zenv["T_CONT_S"] == 600.5 and zenv["WALL_MAX_CUT_S"] == 1000.0 and zenv["LIMIT"] == 10 * 1024 * 1024
              and zenv["manifest"] == [NOWY, sha(NOWY)])
    skladnia = subprocess.run(["bash", "-n", os.path.join(ROOT, "results/NAD2/tools/nad2_boot.sh")]).returncode == 0
    for p in ("results/NAD2/tools/nad2_flight.py", "results/NAD2/tools/nad2_ulg.py"):
        compile(open(os.path.join(ROOT, p), encoding="utf-8").read(), p, "exec")
    return {"bez_env": dom, "z_env_lotu": zenv, "env_lotu": lot, "bash_n": skladnia, "PASS": ok_dom and ok_env and skladnia}


def t6():
    r = subprocess.run(["git", "diff", "--quiet", "bd975df5", "--", *ZAMROZONE], cwd=ROOT)
    d = subprocess.run(["git", "diff", "-U0", "bd975df5", "--", *ZMIENIONE], cwd=ROOT, capture_output=True, text=True).stdout
    zm = [l for l in d.splitlines() if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    return {"zamrozone_diff_rc": r.returncode, "n_linii_zmienionych": len(zm), "linie": zm,
            "PASS": r.returncode == 0 and len(zm) == 12}


def main():
    bra = json.load(open(os.path.join(ROOT, BRAMKA)))
    now = json.load(open(os.path.join(ROOT, NOWY)))
    w = {"manifest": NOWY, "sha256": sha(NOWY), "pozycja_aneksu": 1}
    w["T1_prefiks"] = t1(bra, now)
    w["T2_ciaglosc"], w["T3_predkosc_dysk"] = t2_t3(now)
    w["T4_na_sucho"] = t4(bra, now)
    w["T5_domyslne"] = t5()
    w["T6_diff"] = t6()
    w["PASS"] = all(v["PASS"] for k, v in w.items() if k.startswith("T"))
    json.dump(w, open(OUT, "w"), indent=1, ensure_ascii=False)
    for k, v in w.items():
        if k.startswith("T"):
            print(k, "PASS" if v["PASS"] else "FAIL", {a: b for a, b in v.items() if a not in ("linie", "PASS", "env_lotu")})
    print("PASS" if w["PASS"] else "FAIL")


if __name__ == "__main__":
    main()
