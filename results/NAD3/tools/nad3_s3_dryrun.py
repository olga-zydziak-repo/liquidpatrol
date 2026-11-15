#!/usr/bin/env python3
"""results/NAD3/tools/nad3_s3_dryrun.py — PROMPT_NAD3_S3 §1: próba na sucho bramki S3 (0 bootów).

(1) plan kolejki nad3_s3_run --sucho: 14 pozycji w kolejności ANEKS_NAD3-3 §3.3 (punkt, rodzaj, kierunek, epizody, cięcie / nominał).
(2) strażnik boota dla każdej z 14 pozycji (env z kolejki, bez profilu FastDDS): wszystkie strażniki trybu, punktu, tabeli, degradacji,
    etapu przechodzą i boot staje dopiero na profilu (kod 5, komunikat profilu); NAD3_DEGRAD budowany przez boot (blok wycięty dosłownie)
    = {bias_rad, kierunek pozycji, E_max = E tabeli punktu, f 1, K 0, ziarno 1}.
(3) driver ↔ proces intruza dla każdego epizodu planu (0, 1, 2, 5, 10) na manifeście v2: _resolve_episodes wycięta dosłownie z drivera
    i `manifest["episodes"][episode_id]` (wyrażenie sprawdzone w harness/intruder_motion.py) — ten sam scenario_id i odcinki.
(4) odczyt listy procesów Windows na żywo (tasklist.exe, strona kodowa) i scenariusze reguł §4 na kolejce z atrapą bootu (księga w katalogu tymczasowym): wszystko ważne ⇒ 14 bootów bez STOP; naruszenie ⇒
    STOP-NAD3-3-VC natychmiast; replay < 100% ⇒ STOP-NAD3-3-PRZYRZAD; cięcie bez wejścia ⇒ powtórka z rezerwy; czwarta potrzeba
    rezerwy ⇒ STOP-NAD3-3-REZERWA; P1 dostępne 2/4 ⇒ STOP-NAD3-3-P1 przed pozycją 5; P1 3/4 ⇒ dalej; procesy Windows ⇒ STOP bez bootu.
(5) sędzia nad3_s3_lot na lotach S2 (kopie dowiązaniami): B4 jako pozycja 1 ⇒ ważny, litera, D1; B3 jako pozycja 3 ⇒ nieważny (bez
    degradacji ≠ pozycja planu).
Wyjście: results/NAD3/s3/dryrun/dryrun_s3.json.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types

ROOT = "/home/olga/projects/liquidpatrol"
T = os.path.join(ROOT, "results/NAD3/tools")
OUT = os.path.join(ROOT, "results/NAD3/s3/dryrun")
MAN = os.path.join(ROOT, "results/NAD3/s1/scenario_manifest_nad3_v2.json")
sys.path[:0] = [ROOT, T, os.path.join(ROOT, "results/KONT/tools"), os.path.join(ROOT, "results/NADIR/tools"), os.path.join(ROOT, "results/NAD2/tools")]
import nad3_s3_lot as LOT


def czesc1():
    r = subprocess.run([sys.executable, os.path.join(T, "nad3_s3_run.py"), "--sucho"], capture_output=True, text=True, cwd=ROOT, timeout=120)
    line = next((l for l in r.stdout.splitlines() if l.startswith("{")), None)
    plan = json.loads(line) if line else {}
    oczek = [(1, "P1", "na_zewnatrz", "5", "30"), (2, "P1", "na_zewnatrz", "10", "30"), (3, "P1", "do_srodka", "5", "30"),
             (4, "P1", "do_srodka", "10", "30"), (5, "P1", "na_zewnatrz", "0,1,5,10", "-"), (6, "P2", "na_zewnatrz", "5", "30"),
             (7, "P2", "na_zewnatrz", "10", "30"), (8, "P2", "do_srodka", "5", "30"), (9, "P2", "do_srodka", "10", "30"),
             (10, "P1", "do_srodka", "1,2,5,10", "-"), (11, "P3", "na_zewnatrz", "5", "30"), (12, "P3", "na_zewnatrz", "10", "30"),
             (13, "P3", "do_srodka", "5", "30"), (14, "P3", "do_srodka", "10", "30")]
    poz = plan.get("pozycje", {})
    got = [(int(p), v["env"]["BOOT_PUNKT"], v["env"]["BOOT_DEGRAD"], v["args"][0], v["args"][1]) for p, v in poz.items()]
    return {"rc": r.returncode, "plan": plan.get("plan"), "pozycje": got, "PASS": r.returncode == 0 and got == oczek and plan.get("plan") == list(range(1, 15))
            and all(v["env"]["NAD3_ETAP"] == "s3" and v["env"]["BOOT_ZIARNO"] == "1" for v in poz.values())}


def czesc2():
    import nad3_s3_run as Q
    out = {}
    src = open(os.path.join(T, "nad3_boot.sh")).read()
    a, b = src.index('E3=$(python3'), src.index('N3ENV=();')
    blok = src[a:b]
    for p in sorted(LOT.POZ):
        env = {k: v for k, v in os.environ.items() if k != "PERC2_FASTDDS_PROFILE"}
        env.update(Q.env_poz(p))
        eps, inj = Q.args_poz(p)
        r = subprocess.run(["bash", "-uo", "pipefail", os.path.join(T, "nad3_boot.sh"), "99", "dryrun_guard_s3", eps, inj], env=env,
                           capture_output=True, text=True, timeout=60)
        P = LOT.POZ[p]
        E = json.load(open(os.path.join(ROOT, f"results/NAD3/s1/freeze_U_{P['punkt']}.json")))["tabela"]["E"]
        rb = subprocess.run(["bash", "-uo", "pipefail", "-c", f'ROOT={ROOT}; TAB=results/NAD3/s1/freeze_U_{P["punkt"]}.json; DEG={P["kierunek"]}; '
                             f'ZIA=1; MONLOG=/dev/null; NAME=x\n{blok}\nN3ENV=(); [ -n "$N3DEG" ] && N3ENV=(NAD3_DEGRAD="$N3DEG")\n'
                             'printf "%s\\n" "${N3ENV[@]}"'], capture_output=True, text=True, cwd=ROOT)
        ln = rb.stdout.strip().splitlines()
        cfg = json.loads(ln[0].split("=", 1)[1]) if ln and ln[0].startswith("NAD3_DEGRAD=") else None
        ok_cfg = cfg == {"model": "bias_rad", "kierunek": P["kierunek"], "E_max": E, "f": 1, "K": 0, "ziarno": 1}
        out[p] = {"rc": r.returncode, "do_profilu": "brak PERC2_FASTDDS_PROFILE" in r.stdout, "NAD3_DEGRAD": cfg, "cfg_ok": ok_cfg,
                  "ok": r.returncode == 5 and "brak PERC2_FASTDDS_PROFILE" in r.stdout and ok_cfg}
    shutil.rmtree(os.path.join(ROOT, "results/NAD3/s3/dryrun_guard_s3"), ignore_errors=True)
    out["PASS"] = all(v["ok"] for v in out.values())
    return out


def czesc3():
    drv = os.path.join(T, "nad3_flight.py")
    src = open(drv, encoding="utf8").read()
    i = src.index("def _resolve_episodes(manifest):")
    fn = src[i:src.index("\n\n\n", i)]
    im = open(os.path.join(ROOT, "harness/intruder_motion.py"), encoding="utf8").read()
    assert 'ep = manifest["episodes"][this_id]' in im
    man = json.load(open(MAN))
    w = {}
    for p in sorted(LOT.POZ):
        ns = {"os": types.SimpleNamespace(environ={"BENCH_QUEUE": ""}), "EP_IDS": ",".join(map(str, LOT.POZ[p]["epizody"])), "N_EP": 99}
        exec(compile(fn, drv + ":_resolve_episodes", "exec"), ns)
        for e in ns["_resolve_episodes"](man):
            ie = man["episodes"][e["episode_id"]]
            w[f"{p}/{e['episode_id']}"] = {"driver": e["scenario_id"], "intruz": ie["scenario_id"],
                                            "zgodne": ie["scenario_id"] == e["scenario_id"] and ie["segments"] == e["segments"]}
    sc = {k: v["driver"] for k, v in w.items()}
    ok_sc = all(v.endswith("_s01") for v in sc.values()) and {v for v in sc.values()} == {"c00_s01", "c01_s01", "c02_s01", "c05_s01", "c10_s01"}
    return {"pary": w, "PASS": all(v["zgodne"] for v in w.values()) and ok_sc}


def czesc4():
    import nad3_s3_run as Q
    wyniki = {}

    def scen(nazwa, zachowanie, procesy_ok=True):
        tmp = tempfile.mkdtemp()
        Q.S3, Q.KSIEGA, Q.G.LOG = tmp, os.path.join(tmp, "k.jsonl"), os.path.join(tmp, "log")
        Q.subprocess = types.SimpleNamespace(run=lambda *a, **k: None)
        calls = []

        def fboot(poz, bn):
            if not procesy_ok:
                return "STOP-NAD3-3-PROCESY", None
            n = sum(1 for c in calls if c[0] == poz)
            st = zachowanie(poz, n)
            calls.append((poz, bn, st))
            w = {"pozycja": poz, "boot_s3": bn, "status": st, "sedzia": {"D1_dostepne": not (st == "wazny_bez_D1")}}
            if st == "wazny_bez_D1":
                w["status"] = "wazny"
            with open(Q.KSIEGA, "a") as f:
                f.write(json.dumps(w) + "\n")
            stop = {"naruszenie": "STOP-NAD3-3-VC", "niewazny_przyrzad": "STOP-NAD3-3-PRZYRZAD"}.get(st)
            return stop, w
        Q.boot = fboot
        sys.argv = ["x"]
        Q.main()
        st = json.load(open(os.path.join(tmp, "kampania_s3.json")))["przebiegi"][-1]
        shutil.rmtree(tmp)
        wyniki[nazwa] = {"stop": st["stop"], "booty": st["booty"], "rezerwa": st["rezerwa"], "loty": [c[0] for c in calls]}
        return wyniki[nazwa]
    ok = {}
    r = scen("wszystko_wazne", lambda p, n: "wazny")
    ok["wszystko_wazne"] = r["stop"] is None and r["booty"] == 14 and r["loty"] == list(range(1, 15))
    r = scen("naruszenie_poz2", lambda p, n: "naruszenie" if p == 2 else "wazny")
    ok["naruszenie_poz2"] = r["stop"] == "STOP-NAD3-3-VC" and r["loty"] == [1, 2]
    r = scen("przyrzad_poz6", lambda p, n: "niewazny_przyrzad" if p == 6 else "wazny")
    ok["przyrzad_poz6"] = r["stop"] == "STOP-NAD3-3-PRZYRZAD" and r["loty"][-1] == 6 and r["booty"] == 6
    r = scen("bez_wejscia_poz1_raz", lambda p, n: "bez_wejscia" if (p == 1 and n == 0) else "wazny")
    ok["bez_wejscia_poz1_raz"] = r["stop"] is None and r["booty"] == 15 and r["rezerwa"] == 1 and r["loty"][:2] == [1, 1]
    r = scen("rezerwa_czwarta", lambda p, n: ("bez_wejscia" if (p in (2, 7) and n == 0) or (p == 12 and n < 2) else "wazny"))
    ok["rezerwa_czwarta"] = r["stop"] == "STOP-NAD3-3-REZERWA" and r["rezerwa"] == 4
    r = scen("stanowisko_w_locie", lambda p, n: "niewazny_stanowisko" if (p == 9 and n == 0) else "wazny")
    ok["stanowisko_w_locie"] = r["stop"] is None and r["booty"] == 15 and r["rezerwa"] == 1
    r = scen("P1_2_z_4", lambda p, n: "wazny_bez_D1" if p in (1, 3) else "wazny")
    ok["P1_2_z_4"] = r["stop"] == "STOP-NAD3-3-P1" and r["loty"] == [1, 2, 3, 4]
    r = scen("P1_3_z_4", lambda p, n: "wazny_bez_D1" if p == 2 else "wazny")
    ok["P1_3_z_4"] = r["stop"] is None and r["booty"] == 14
    r = scen("procesy", lambda p, n: "wazny", procesy_ok=False)
    ok["procesy"] = r["stop"] == "STOP-NAD3-3-PROCESY" and r["booty"] == 0
    import importlib
    importlib.reload(Q)                                               # prawdziwa funkcja procesy() (bez atrapy) — odczyt tasklist.exe na żywo
    pr = Q.procesy()
    ok["procesy_na_zywo_odczyt"] = isinstance(pr[1], dict) and set(pr[1]) == {"chrome.exe", "chatgpt.exe"}
    return {"scenariusze": wyniki, "procesy_na_zywo": pr, "ok": ok, "PASS": all(ok.values())}


def czesc5():
    tmp = tempfile.mkdtemp()
    out = {}
    for b, poz, oczek in (("b4_c05_p1_na_zewnatrz", 1, True), ("b3_c05_bez_degradacji", 3, False)):
        d = os.path.join(tmp, b); os.makedirs(d)
        src = os.path.join(ROOT, "results/NAD3/s2", b)
        for f in os.listdir(src):
            if f not in ("sprawdziany_s2_nad3.json", "sedzia_s3.json"):
                os.symlink(os.path.join(src, f), os.path.join(d, f))
        s = LOT.sedzia(d, poz)
        out[b] = {k: s.get(k) for k in ("wazny", "replay_ok", "meta_ok", "decymacja_ok", "litera_ok", "wejscie", "D1_dostepne")}
        out[b]["ok"] = (s["wazny"] is oczek) and s["litera_ok"] and (not oczek or s["D1_dostepne"])
    shutil.rmtree(tmp)
    out["PASS"] = all(v["ok"] for v in out.values() if isinstance(v, dict))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    w = {"czesc1_plan": czesc1()}
    print("czesc1", w["czesc1_plan"]["PASS"], flush=True)
    w["czesc2_straznik"] = czesc2()
    print("czesc2", w["czesc2_straznik"]["PASS"], flush=True)
    w["czesc3_intruz"] = czesc3()
    print("czesc3", w["czesc3_intruz"]["PASS"], flush=True)
    w["czesc4_reguly"] = czesc4()
    print("czesc4", w["czesc4_reguly"]["PASS"], w["czesc4_reguly"]["ok"], flush=True)
    w["czesc5_sedzia"] = czesc5()
    print("czesc5", w["czesc5_sedzia"]["PASS"], flush=True)
    w["PASS"] = all(v["PASS"] for v in w.values() if isinstance(v, dict))
    json.dump(w, open(os.path.join(OUT, "dryrun_s3.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: (v["PASS"] if isinstance(v, dict) else v) for k, v in w.items()}))


if __name__ == "__main__":
    main()
