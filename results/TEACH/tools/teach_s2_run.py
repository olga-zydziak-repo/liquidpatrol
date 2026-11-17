#!/usr/bin/env python3
"""results/TEACH/tools/teach_s2_run.py — kolejka bootów lotnych S2 nogi TEACH (PROMPT_TEACH_S2 §3–§5) = wzór results/NAD3/tools/nad3_s2_run.py
(nietknięty): strażniki stanowiska z kont_s2_campaign_g.py (zegar, sieroty, /dev/shm; import READ-ONLY, ścieżki na results/TEACH/s2),
bramka zdrowia przyrządem A (nadir_s4_bramka READ-ONLY, katalog results/TEACH/s2/bramka; A, NO-GO ⇒ 3 min ⇒ C; trzecie NO-GO ⇒ STOP
stanowiskowy), telemetria hosta w tle. Boot: results/TEACH/tools/teach_boot.sh (TEACH_ETAP=s2, NM=1 KM=1 PT=0).
Jeden lot na wywołanie (kolejność wiążąca: C1 → C2 → SM; SM tylko po dwóch cieniach z bramką obrazu — pilnuje wykonawca przed
wywołaniem i strażnik niżej na księdze):
  C1 — cień, łata S, epizod 5 (c05_s01), nominał bez cięcia, BOOT_T_CIEN 173.6;
  C2 — cień, łata J, epizod 10 (c10_s01), nominał bez cięcia, BOOT_T_CIEN 176.5;
  SM — smoke, łata S, cięcie c05 (epizod 5, KONT_INJECT_T 30, kontynuacja 110.5 s).
Pasywny rejestrator kadrów kamery w dół (results/TEACH/tools/teach_rejestrator.py, co 1 s sim) w tle bootu; kadry na stanowisku
(~/teach_stanowisko/<nazwa>/, poza repo). Po boocie: wyciąg ULG (results/NAD2/tools/nad2_ulg — READ-ONLY) i analizator teach_analyze.
Boot nieważny stanowiskowo przed startem epizodu (bramka zdrowia NO-GO, bramka tempa) nie liczy się; jedna powtórka na lot.
Kody 41–45 (osłona), 4–6 (strażnik), 8–9 (driver: tryb / producent) ⇒ STOP. Licznik bootów nogi: ST1, ST2 (2) + loty z księgi.
Użycie: teach_s2_run.py C1|C2|SM [--sucho]. Wyjście: results/TEACH/s2/kampania_s2.log, kampania_ksiega.jsonl.
"""
import json
import os
import subprocess
import sys
import time

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [os.path.join(ROOT, "results/KONT/tools"), os.path.join(ROOT, "results/NADIR/tools"),
                os.path.join(ROOT, "results/NAD2/tools"), os.path.join(ROOT, "results/TEACH/tools"), ROOT]
import kont_s2_campaign_g as G                     # READ-ONLY
import nadir_s4_tel as TL                          # READ-ONLY

S2 = os.path.join(ROOT, "results/TEACH/s2")
G.S2 = S2
G.LOG = os.path.join(S2, "kampania_s2.log")
G.SKRYPTY = G.SKRYPTY | {"kont_s4_flight", "nadir_s4_flight", "nad2_flight", "nad3_flight", "teach_flight", "intruder_motion",
                         "nadir_obs", "teach_rejestrator"}
log = G.log
BOOT = os.path.join(ROOT, "results/TEACH/tools/teach_boot.sh")
KSIEGA = os.path.join(S2, "kampania_ksiega.jsonl")
STANOWISKO = os.path.expanduser("~/teach_stanowisko")
BOOTY_STATYCZNE = 2                                # ST1, ST2 (results/TEACH/s2/st_porownanie.json)
BUDZET = 7
BAZA = {"BOOT_NADIR_MODE": "1", "BOOT_KONT_MODE": "1", "BOOT_PASSTHROUGH": "0", "TEACH_ETAP": "s2"}
LOTY = {"C1": {"nazwa": "c1_cien_S_c05", "epizody": "5", "inject": "-", "lata": "S",
               "env": {**BAZA, "BOOT_LATA": "S", "BOOT_CIEN": "1", "BOOT_T_CIEN": "173.6"}},
        "C2": {"nazwa": "c2_cien_J_c10", "epizody": "10", "inject": "-", "lata": "J",
               "env": {**BAZA, "BOOT_LATA": "J", "BOOT_CIEN": "1", "BOOT_T_CIEN": "176.5"}},
        "SM": {"nazwa": "sm_smoke_S_c05", "epizody": "5", "inject": "30", "lata": "S",
               "env": {**BAZA, "BOOT_LATA": "S", "BOOT_CIEN": "0"}}}
SCEN = {"C1": "c05_s01", "C2": "c10_s01", "SM": "c05_s01"}
MANIFEST = os.path.join(ROOT, "results/NAD3/s1/scenario_manifest_nad3_v2.json")


def ksiega():
    return [json.loads(l) for l in open(KSIEGA) if l.strip()] if os.path.exists(KSIEGA) else []


def wolna(nm):
    n = 1
    while True:
        c = nm if n == 1 else f"{nm}_r{n}"
        if not any(f == c or f.startswith(c + "_") or f.startswith(c + ".") for f in os.listdir(S2)):
            return c
        n += 1


def bramka_zdrowia(name):
    import nadir_s4_bramka as B
    B.OUT = os.path.join(S2, "bramka")
    proby = []
    for k in range(3):
        if k:
            time.sleep(180)
        B.zegar_ok()
        tag = f"{name}_g{k + 1}"
        r = B.przyrzad_a(tag, tel=bool(k))
        p = {"tag": tag, "wariant": r["wariant"], "tempo": r["tempo"], "GO": r["GO"], "t": time.strftime("%F %T")}
        proby.append(p)
        with open(os.path.join(S2, "bramka_ksiega.jsonl"), "a") as f:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
        log(f"{name}: bramka zdrowia {tag} ({p['wariant']}) GO={p['GO']} tempo={p['tempo']}")
        if r["GO"]:
            return True, proby
    return False, proby


def main():
    lot = sys.argv[1]
    sucho = "--sucho" in sys.argv[2:]
    L = LOTY[lot]
    eps = json.load(open(MANIFEST))["episodes"]
    assert eps[int(L["epizody"])]["scenario_id"] == SCEN[lot] and eps[int(L["epizody"])]["episode_id"] == int(L["epizody"])
    ks = ksiega()
    zuzyte = [w for w in ks if w.get("epizod_wystartowal")]
    nr = BOOTY_STATYCZNE + len(zuzyte) + 1
    if lot == "SM":
        def bramka_obrazu(w):                       # wynik oceny cienia (teach_s2_cien → <nazwa>/cien_s2.json); księga go nie niesie
            p = os.path.join(S2, w["nazwa"], "cien_s2.json")
            return os.path.exists(p) and json.load(open(p))["bramka_obrazu"]["ok"] is True
        cienie = {w["lot"] for w in zuzyte if w["lot"] in ("C1", "C2") and bramka_obrazu(w)}
        if cienie != {"C1", "C2"}:
            sys.exit(f"SM: bramka obrazu niespełniona w obu cieniach ({cienie}) — ODMOWA")
    if nr > BUDZET:
        sys.exit(f"budżet {BUDZET} wyczerpany — ODMOWA")
    name = wolna(L["nazwa"])
    log(f"=== TEACH S2 {lot} {name} boot nogi {nr}/{BUDZET} {'(na sucho)' if sucho else ''}")
    if sucho:
        print(json.dumps({"lot": lot, "nazwa": name, "boot": nr, "env": L["env"], "epizody": L["epizody"], "inject": L["inject"]},
                         ensure_ascii=False))
        return
    go, proby = bramka_zdrowia(name)
    if not go:
        wpis = {"lot": lot, "nazwa": name, "epizod_wystartowal": False, "powod": "bramka zdrowia NO-GO", "bramka_zdrowia": proby}
        open(KSIEGA, "a").write(json.dumps(wpis, ensure_ascii=False) + "\n")
        print("NIEWAZNY-BRAMKA-ZDROWIA"); return
    ok, z = G.zegar(name)
    log(f"{name}: próbnik zegara {z['skoki']} skoków ok={ok}")
    if not ok:
        print("STOP-TEACH-2-ZEGAR"); return
    znal, zywe = G.sprzataj_sieroty()
    if zywe:
        print("STOP-TEACH-2-SIEROTY", zywe); return
    shm = G.shm_krok(name, False)
    env = {**os.environ, **L["env"], "PERC2_FASTDDS_PROFILE": G.PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
    tp = os.path.join(S2, f"{name}_host_telemetria.jsonl")
    tl = TL.Telemetria2(tp, 3600)
    kad = os.path.join(STANOWISKO, name)
    rej = subprocess.Popen([sys.executable, os.path.join(ROOT, "results/TEACH/tools/teach_rejestrator.py"), "--world",
                            f"world_teach_{L['lata']}", "--model", "x500_teach_flow_0", "--out", kad],
                           stdout=open(os.path.join(S2, f"{name}_rejestrator.log"), "w"), stderr=subprocess.STDOUT,
                           env={**os.environ, "GZ_IP": "127.0.0.1"}, start_new_session=True)
    t0 = time.time()
    try:
        for _ in range(4):
            r = subprocess.run(["bash", BOOT, str(nr), name, L["epizody"], L["inject"]], cwd=ROOT, env=env, capture_output=True, text=True)
            open(os.path.join(S2, f"{name}_driver.log"), "a").write(r.stdout + r.stderr)
            if r.returncode != 3:
                break
            log(f"{name}: env-block rc=3, nie boot, czekam 120 s"); time.sleep(120)
        else:
            print("STOP-TEACH-2-ENV"); return
    finally:
        tl.close()
        rej.terminate()
        try:
            rej.wait(timeout=15)
        except subprocess.TimeoutExpired:
            rej.kill()
    d = os.path.join(S2, name)
    if os.path.isdir(d) and os.path.exists(tp):
        os.replace(tp, os.path.join(d, "host_telemetria.jsonl"))
    try:
        kt = json.load(open(os.path.join(d, "kont_tempo.json")))
    except (OSError, ValueError):
        kt = None
    ev = [json.loads(l) for l in open(os.path.join(d, "trace.jsonl")) if '"event"' in l] if os.path.exists(os.path.join(d, "trace.jsonl")) else []
    names = [e.get("ev") for e in ev]
    wpis = {"boot_nogi": nr, "lot": lot, "nazwa": name, "rc": r.returncode, "czas_s": round(time.time() - t0, 1), "tempo": kt,
            "bramka_zdrowia": proby, "shm": shm, "epizod_wystartowal": "episode_start" in names,
            "breach": any(n in ("breach", "breach_gt") for n in names), "teach_producent": next((e for e in ev if e.get("ev") == "teach_producent"), None),
            "wejscie": "denial" in names, "kadry_stanowisko": kad, "n_kadrow": len(os.listdir(kad)) if os.path.isdir(kad) else 0,
            "t": time.strftime("%F %T")}
    if r.returncode in (4, 5, 6, 8, 9, 41, 42, 43, 44, 45):
        wpis["epizod_wystartowal"] = wpis["epizod_wystartowal"] and r.returncode not in (4, 5, 6)
    with open(KSIEGA, "a") as f:
        f.write(json.dumps(wpis, ensure_ascii=False, default=str) + "\n")
    log(f"{name} rc={r.returncode} boot {nr} epizod={wpis['epizod_wystartowal']} wejście={wpis['wejscie']} breach={wpis['breach']} "
        f"producent={wpis['teach_producent']} kadrów={wpis['n_kadrow']}")
    if os.path.exists(os.path.join(d, "boot.ulg")):
        import nad2_ulg
        log(f"{name}: wyciąg ULG {nad2_ulg.wyciag(d)}")
    print("KONIEC", json.dumps({k: wpis[k] for k in ("lot", "nazwa", "rc", "boot_nogi", "epizod_wystartowal", "wejscie", "breach", "n_kadrow")},
                               ensure_ascii=False))


if __name__ == "__main__":
    main()
