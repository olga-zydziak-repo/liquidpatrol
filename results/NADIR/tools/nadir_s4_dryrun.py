#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s4_dryrun.py — PROMPT_NADIR_S4 §0.1: próba na sucho skryptów S4 (0 bootów), wzór nadir_s3_dryrun.py.

(1) main() drivera results/NADIR/tools/nadir_s4_flight.py przez atrapy results/KONT/tools/kont_s4_dryrun_c.py (import READ-ONLY,
    podmieniona ścieżka DRIVER), scenariusz „zdrowy”, do uzbrojenia: konfiguracja S4 (NADIR_MODE=1, KONT_MODE=1, manifest S4)
    ⇒ arm_retry + selfcheck certów NADIR PASS + meta s4n (T_CONT_S 110, manifest S4); konfiguracja NADIR_MODE=0 ⇒ odmowa kod 8.
(2) Bloki S4N wywołane DOSŁOWNYM tekstem z pliku drivera na stanie syntetycznym: planowe zejście (od `is_pos = (d_dec` do
    `out = None`) — przed 110 s brak, ≥ 110 s od t_inj zejście + zdarzenie, tick REFUSE(POS) nie jest zejściem planowym, bez
    cięcia brak; warunek końca (`done = (`) — boot cięcia nie kończy się na T_entry + T_ORB, nominał tak.
(3) shellcheck (-S warning) nadir_s4_boot.sh / nadir_s4_launch.sh vs oryginały S3: zero nowych ostrzeżeń; ROOT absolutny, pipefail;
    sha manifestu S4 w strażniku bootu = sha pliku; generator manifestu deterministyczny (drugi przebieg do pliku tymczasowego).
(4) Analiza nadir_s4_analyze.analyze na kopii bootu S2 c08_s02 (REFUSE T* po 22 s): (a) FAIL (brak zejścia planowego,
    kontynuacja < 110 s), ważność PASS, u = 2.429 (koszyk najgorszy — dane S2 bez pola kosz), okna g_3d policzone.
Wyjście: results/NADIR/s4/dryrun/dryrun_s4.json. Uruchamiany pod `set -uo pipefail` (nadir_s4_dryrun.sh nie istnieje — wywołanie
w raporcie).
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap

ROOT = "/home/olga/projects/liquidpatrol"
T = os.path.join(ROOT, "results/NADIR/tools")
OUT = os.path.join(ROOT, "results/NADIR/s4/dryrun")
DRV = os.path.join(T, "nadir_s4_flight.py")
MAN = "results/NADIR/s4/scenario_manifest_s4.json"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/KONT/tools"), T]


def czesc1(tag, nm):
    sock = os.path.join(tempfile.mkdtemp(), "drv.sock")
    out = os.path.join(OUT, tag)
    r = subprocess.run([sys.executable, "-c", f"""
import os, sys, json
os.environ.update(NADIR_MODE={nm!r}, NADIR_S3_PASSTHROUGH="0", NADIR_SOCK_DRIVER={sock!r}, BENCH_MANIFEST={MAN!r})
sys.path[:0] = [{ROOT!r}, {os.path.join(ROOT, 'results/KONT/tools')!r}]
import kont_s4_dryrun_c as D
D.DRIVER = {DRV!r}
res = D.run({out!r}, "zdrowy")
print("WYNIK", json.dumps({{k: res[k] for k in ("wynik", "kroki")}}, ensure_ascii=False))
"""], capture_output=True, text=True, timeout=600, cwd=ROOT)
    line = next((l for l in r.stdout.splitlines() if l.startswith("WYNIK ")), None)
    w = json.loads(line[6:]) if line else None
    cs = open(os.path.join(out, "certs_selfcheck.log")).read() if os.path.exists(os.path.join(out, "certs_selfcheck.log")) else ""
    nadir_sc = "WERDYKT nadir_certs_selfcheck: PASS" in cs
    odmowa = "NADIR_MODE != 1 — ODMOWA" in (r.stdout + r.stderr)
    if nm == "1":
        ok = r.returncode == 0 and w is not None and w["wynik"] == "zatrzymane: uzbrojenie" and nadir_sc and not odmowa
    else:
        ok = r.returncode == 8 and odmowa
    return {"rc": r.returncode, "wynik": w, "nadir_selfcheck_pass": nadir_sc, "odmowa_nadir0": odmowa, "PASS": ok,
            "stdout_ogon": r.stdout[-400:], "stderr_ogon": r.stderr[-400:]}


def wytnij(src, start, stop):
    i = src.rfind("\n", 0, src.index(start)) + 1
    j = src.index(stop, i)
    j = src.rfind("\n", 0, j) + 1
    return textwrap.dedent(src[i:j])


def czesc2():
    src = open(DRV, encoding="utf8").read()
    blk = wytnij(src, "is_pos = (d_dec[\"decision\"] == REFUSE", "out = None")
    assert "zejscie_planowe" in blk and "T_CONT_S" in blk
    i = src.index("done = ((t_entry is not None")
    blk_done = textwrap.dedent(src[src.rfind("\n", 0, i) + 1:src.index("\n", src.index("(breach and not descending))", i)) + 1])
    stale = {}
    exec("T_CONT_S = " + src.split("T_CONT_S = ")[1].split()[0], stale)
    exec("T_ORB = " + src.split("T_ORB = ")[1].split()[0], stale)
    REFUSE, POS = "REFUSE", "POS_DEGRADED"
    evs = []

    def run(now_sim, t_inj, denial_done, dec="ALLOW", reason=None, descending=False):
        ns = {"REFUSE": REFUSE, "POS_DEGRADED": POS, "T_CONT_S": stale["T_CONT_S"], "time": __import__("time"),
              "d_dec": {"decision": dec, "reason": reason, "rule": None, "nadir": {"tau": 0.1, "j": 1}},
              "denial_done": denial_done, "descending": descending, "now_sim": now_sim, "t_inj_sim": t_inj, "t_rel": now_sim - 50,
              "r_est": 12.0, "r_gt": lambda: 12.3, "round": round, "ep": {"episode_id": 5}, "t_desc_wall": None, "zejscie_plan": None,
              "ev": lambda s, **kw: evs.append((s, kw))}
        exec(compile(blk, DRV + ":S4N-zejscie", "exec"), ns)
        return ns
    w = {}
    a = run(100.0 + 109.95, 100.0, True); w["przed_110"] = not a["descending"]
    b = run(100.0 + 110.0, 100.0, True); w["po_110"] = b["descending"] and b["zejscie_plan"]["od_ciecia_s"] == 110.0 and evs[-1][0] == "zejscie_planowe"
    c = run(100.0 + 115.0, 100.0, True, dec=REFUSE, reason=POS); w["refuse_pos_nie_planowe"] = not c["descending"]
    dd = run(500.0, None, False); w["bez_ciecia"] = not dd["descending"]
    n_ev = len(evs)
    e = run(100.0 + 120.0, 100.0, True, descending=True); w["juz_w_zejsciu"] = len(evs) == n_ev and e["zejscie_plan"] is None

    def done(K2, t_rel, descending=False, denied=False):
        ns = {"t_entry": 10.0, "t_rel": t_rel, "T_ORB": stale["T_ORB"], "descending": descending, "denied": denied, "breach": False,
              "K2_INJECT_T": K2}
        exec(compile(blk_done, DRV + ":S4N-done", "exec"), ns)
        return ns["done"]
    w["ciecie_nie_konczy_T_ORB"] = done(30.0, 10.0 + 70.0 + 5) is False
    w["nominal_konczy_T_ORB"] = done(None, 10.0 + 70.0) is True
    w["ciecie_konczy_przyziemienie"] = done(30.0, 160.0, descending=True, denied=True) is True
    w["T_CONT_S"], w["T_ORB"] = stale["T_CONT_S"], stale["T_ORB"]
    w["PASS"] = all(v for k, v in w.items() if k not in ("T_CONT_S", "T_ORB")) and stale["T_CONT_S"] == 110.0
    return w


def sc(path):
    r = subprocess.run(["shellcheck", "-S", "warning", "-f", "json", path], capture_output=True, text=True)
    return {(x["code"], x["message"]) for x in json.loads(r.stdout or "[]")}


def czesc3():
    out = {}
    for new, old in (("nadir_s4_boot.sh", "nadir_s3_boot.sh"), ("nadir_s4_launch.sh", "nadir_s3_launch.sh")):
        n, o = sc(os.path.join(T, new)), sc(os.path.join(T, old))
        head = open(os.path.join(T, new)).read()
        out[new] = {"ostrzezenia": len(n), "w_oryginale": len(o), "nowe": [f"SC{c}: {m}" for c, m in sorted(n - o)],
                    "root_absolutny": f'ROOT="{ROOT}"' in head, "pipefail": "set -o pipefail" in head,
                    "bash_n": subprocess.run(["bash", "-n", os.path.join(T, new)]).returncode == 0}
        out[new]["PASS"] = not out[new]["nowe"] and out[new]["root_absolutny"] and out[new]["pipefail"] and out[new]["bash_n"]
    boot = open(os.path.join(T, "nadir_s4_boot.sh")).read()
    sha_plik = hashlib.sha256(open(os.path.join(ROOT, MAN), "rb").read()).hexdigest()
    import nadir_s4_manifest as GM
    tmp = os.path.join(tempfile.mkdtemp(), "m.json")
    GM.OUT = tmp
    _o = sys.stdout; sys.stdout = open(os.devnull, "w")
    try:
        GM.main()
    finally:
        sys.stdout.close(); sys.stdout = _o
    sha2 = hashlib.sha256(open(tmp, "rb").read()).hexdigest()
    out["manifest"] = {"sha_plik": sha_plik, "w_straznik": f'S4MAN_SHA="{sha_plik}"' in boot, "drugi_przebieg": sha2,
                       "PASS": f'S4MAN_SHA="{sha_plik}"' in boot and sha2 == sha_plik}
    out["PASS"] = all(v["PASS"] for v in out.values() if isinstance(v, dict))
    return out


def czesc4():
    import nadir_s4_analyze as A
    tmp = os.path.join(tempfile.mkdtemp(), "c08_s02")
    shutil.copytree(os.path.join(ROOT, "results/NADIR/s2/c08_s02"), tmp)
    r = A.analyze(tmp)
    o = r["epizody"][0]
    w = {"wazny": r["wazny"], "a_ok": o["a_ok"], "kontynuacja_s": o["kontynuacja_s"], "zejscie_planowe": o["zejscie_planowe"],
         "refuse_misja": o["refuse_misja"], "u_max": o["u_max"], "g_3d_bez_GNSS_max": o["g_3d"]["bez_GNSS"]["max_inc_do_eps_b"],
         "g_2d_bez_GNSS_max": o["g_2d"]["bez_GNSS"]["max_inc_do_eps_b"], "litera": {k: o[k] for k in ("a_ok", "b_ok", "c_ok", "d_ok", "e_ok", "g_ok")}}
    w["PASS"] = (r["wazny"] and o["a_ok"] is False and o["zejscie_planowe"] is False and o["kontynuacja_s"] < 110
                 and o["refuse_misja"]["n"] > 0 and abs(o["u_max"] - 2.429) < 1e-6 and o["g_3d"]["bez_GNSS"]["n"] > 0)
    return w


def main():
    os.makedirs(OUT, exist_ok=True)
    res = {"opis": __doc__.split("\n\n")[0], "1_S4": czesc1("S4", "1"), "1_nadir0": czesc1("N0", "0"),
           "2_bloki_S4N": czesc2(), "3_skrypty": czesc3(), "4_analiza": czesc4()}
    res["PASS"] = all(res[k]["PASS"] for k in ("1_S4", "1_nadir0", "2_bloki_S4N", "3_skrypty", "4_analiza"))
    json.dump(res, open(os.path.join(OUT, "dryrun_s4.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str)[:5000])
    sys.exit(0 if res["PASS"] else 1)


if __name__ == "__main__":
    main()
