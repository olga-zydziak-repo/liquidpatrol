#!/usr/bin/env python3
"""results/NAD3/tools/nad3_s3_run.py — kolejka bramki S3 NADIR-III (PROMPT_NAD3_S3 §1–§4, ANEKS_NAD3-3 §3; ≤ 17 bootów) = wzór
results/NAD3/tools/nad3_s2_run.py: strażniki stanowiska kont_s2_campaign_g (READ-ONLY, ścieżki na results/NAD3/s3), bramka zdrowia
przyrządem A (results/NADIR/tools/nadir_s4_bramka — katalog results/NAD3/s3/bramka; A, NO-GO ⇒ 3 min ⇒ C, trzecie NO-GO z rzędu ⇒
STOP-NAD3-3-STANOWISKO, nic nie zużyte), telemetria w tle bootu, boot results/NAD3/tools/nad3_boot.sh (NAD3_ETAP=s3, tryb 1/1/0/NAD2,
manifest v2, ziarno 1).
Plan: 14 pozycji w kolejności wiążącej (nad3_s3_lot.PLAN): cięcia P1 (c05/c10 × na zewnątrz/do środka), nominał NA (P1, na zewnątrz,
0,1,5,10), cięcia P2, nominał NB (P1, do środka, 1,2,5,10), cięcia P3. Epizody numerem kanonu; przed każdym bootem asercja manifestu
(pozycja = episode_id 120/120) i lista procesów Windows (tasklist.exe: Chrome, ChatGPT ⇒ STOP-NAD3-3-PROCESY, bez bootu).
Po każdym locie, przed następnym: wyciąg ULG (nad2_ulg, READ-ONLY), nad3_analyze, sędzia nad3_s3_lot (ważność, litera, D1, odmowy).
Reguły §4:
  - naruszenie B1–B5 (litera) ⇒ STOP-NAD3-3-VC natychmiast;
  - lot nieważny (replay < 100%, meta niezgodna, decymacja) ⇒ STOP-NAD3-3-PRZYRZAD (wada przyrządu, nie rezerwa);
  - cięcie bez wejścia (brak „denial”) ⇒ boot liczony, lot nieważny dla bramki, powtórka z rezerwy;
  - boot nieważny stanowiskowo (bramka tempa w driverze — kont_tempo.json ok = false) ⇒ boot liczony, powtórka z rezerwy;
  - rezerwa 3 booty łącznie; czwarta potrzeba ⇒ STOP-NAD3-3-REZERWA;
  - po pozycji 4: mniej niż 3 z 4 cięć P1 dostępnych wg D1 ⇒ STOP-NAD3-3-P1 przed pozycją 5;
  - breach ⇒ STOP-NAD3-3-BREACH; kody drivera 41–45 ⇒ STOP-NAD3-3-OSLONA-<kod>; niezgodność degradacji (zdarzenie nad3_degradacja
    zgodna = false) ⇒ STOP-NAD3-3-DEGRAD; strażnik boota 4–6 ⇒ STOP-NAD3-3-GUARD; budżet 17 ⇒ STOP-NAD3-3-BUDZET.
Stan w księdze results/NAD3/s3/kampania_ksiega.jsonl (wiersz per zużyty boot z wynikiem sędziego); kolejka wznawia się od pierwszej
pozycji bez lotu ważnego. timesyncd: stop na starcie, start na końcu.
Użycie: nad3_s3_run.py [--sucho]. Wyjście: results/NAD3/s3/kampania_s3.log, kampania_s3.json.
"""
import json
import os
import subprocess
import sys
import time

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [os.path.join(ROOT, "results/KONT/tools"), os.path.join(ROOT, "results/NADIR/tools"),
                os.path.join(ROOT, "results/NAD2/tools"), os.path.join(ROOT, "results/NAD3/tools"), ROOT]
import kont_s2_campaign_g as G                     # READ-ONLY
import nadir_s4_tel as TL                          # READ-ONLY
import nad3_s3_lot as LOT

S3 = os.path.join(ROOT, "results/NAD3/s3")
G.S2 = S3
G.LOG = os.path.join(S3, "kampania_s3.log")
G.SKRYPTY = G.SKRYPTY | {"kont_s4_flight", "nadir_s4_flight", "nad2_flight", "nad3_flight", "intruder_motion", "nadir_obs"}
log = G.log
BOOT = os.path.join(ROOT, "results/NAD3/tools/nad3_boot.sh")
KSIEGA = os.path.join(S3, "kampania_ksiega.jsonl")
MANIFEST = os.path.join(ROOT, "results/NAD3/s1/scenario_manifest_nad3_v2.json")
BUDZET, REZERWA = 17, 3
NOGA_PRZED = 4                                     # NADIR-III: 4 booty S2
TASKLIST = "/mnt/c/Windows/System32/tasklist.exe"
ZAKAZANE = ("chrome.exe", "chatgpt.exe")


def nazwa(poz):
    P = LOT.POZ[poz]
    ep = "c05" if P["epizody"] == [5] else ("c10" if P["epizody"] == [10] else "nom")
    return f"p{poz:02d}_{P['punkt'].lower()}_{ep}_{'zew' if P['kierunek'] == 'na_zewnatrz' else 'srod'}" + \
        ("" if P["rodzaj"] == "ciecie" else ("_NA" if poz == 5 else "_NB"))


def env_poz(poz):
    P = LOT.POZ[poz]
    return {"BOOT_NADIR_MODE": "1", "BOOT_KONT_MODE": "1", "BOOT_PASSTHROUGH": "0", "BOOT_LITERA": "NAD2", "BOOT_PUNKT": P["punkt"],
            "BOOT_DEGRAD": P["kierunek"], "BOOT_ZIARNO": "1", "NAD3_ETAP": "s3"}


def args_poz(poz):
    P = LOT.POZ[poz]
    return ",".join(str(x) for x in P["epizody"]), ("30" if P["rodzaj"] == "ciecie" else "-")


def niezmiennik(poz):
    eps = json.load(open(MANIFEST))["episodes"]
    ids = LOT.POZ[poz]["epizody"]
    return len(eps) == 120 and all(i == e["episode_id"] for i, e in enumerate(eps)) and all(eps[i]["episode_id"] == i for i in ids)


def procesy():
    try:
        out = subprocess.run([TASKLIST, "/FO", "CSV"], capture_output=True, text=True, timeout=30).stdout.lower()
    except (OSError, subprocess.TimeoutExpired) as ex:
        return None, repr(ex)
    zn = {z: out.count(f'"{z}"') for z in ZAKAZANE}
    return all(v == 0 for v in zn.values()), zn


def ksiega():
    return [json.loads(l) for l in open(KSIEGA) if l.strip()] if os.path.exists(KSIEGA) else []


def stan(ks):
    zuzyte = len(ks)
    zrobione = {w["pozycja"] for w in ks if w.get("status") == "wazny"}
    rezerwa = sum(1 for w in ks if w.get("status") in ("bez_wejscia", "niewazny_stanowisko"))
    plan = [p for p in sorted(LOT.POZ) if p not in zrobione]
    return zuzyte, zrobione, rezerwa, plan


def wolna(nm):
    n = 1
    while True:
        c = nm if n == 1 else f"{nm}_r{n}"
        if not any(f == c or f.startswith(c + "_") or f.startswith(c + ".") for f in os.listdir(S3)):
            return c
        n += 1


def bramka_zdrowia(name):
    import nadir_s4_bramka as B
    B.OUT = os.path.join(S3, "bramka")
    proby = []
    for k in range(3):
        if k:
            time.sleep(180)
        B.zegar_ok()
        tag = f"{name}_g{k + 1}"
        try:
            r = B.przyrzad_a(tag, tel=bool(k))
        except Exception as ex:
            log(f"{name}: bramka zdrowia błąd {ex!r}")
            return None, proby
        p = {"tag": tag, "wariant": r["wariant"], "tempo": r["tempo"], "GO": r["GO"], "czolowka_operatora": r.get("czolowka_operatora"),
             "t": time.strftime("%F %T")}
        proby.append(p)
        with open(os.path.join(S3, "bramka_ksiega.jsonl"), "a") as f:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
        log(f"{name}: bramka zdrowia {tag} ({p['wariant']}) GO={p['GO']} tempo={p['tempo']}"
            + (f" — do zamknięcia: {p['czolowka_operatora']}" if p["czolowka_operatora"] else ""))
        if r["GO"]:
            return True, proby
    return False, proby


def boot(poz, bn):
    """Zwraca (stop | None, wpis | None). wpis = zużyty boot (zapisany w księdze)."""
    if not niezmiennik(poz):
        return "STOP-NAD3-3-MANIFEST", None
    ok, zn = procesy()
    log(f"poz {poz}: procesy Windows {zn}")
    if not ok:
        return "STOP-NAD3-3-PROCESY", None
    name = wolna(nazwa(poz))
    go, proby = bramka_zdrowia(name)
    if go is None:
        return "STOP-NAD3-3-BRAMKA", None
    if not go:
        return "STOP-NAD3-3-STANOWISKO", None
    ok, z = G.zegar(name)
    log(f"{name}: próbnik {z['skoki']} skoków ok={ok}")
    if not ok:
        return "STOP-NAD3-3-ZEGAR", None
    znal, zywe = G.sprzataj_sieroty()
    if zywe:
        return "STOP-NAD3-3-SIEROTY", None
    shm = G.shm_krok(name, False)
    eps, inj = args_poz(poz)
    env = {**os.environ, **env_poz(poz), "PERC2_FASTDDS_PROFILE": G.PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
    tp = os.path.join(S3, f"{name}_host_telemetria.jsonl")
    tl = TL.Telemetria2(tp, 3600)
    t0 = time.time()
    try:
        for _ in range(4):
            r = subprocess.run(["bash", BOOT, str(bn), name, eps, inj], cwd=ROOT, env=env, capture_output=True, text=True)
            open(os.path.join(S3, f"{name}_driver.log"), "a").write(r.stdout + r.stderr)
            if r.returncode != 3:
                break
            log(f"{name}: env-block rc=3, nie boot, czekam 120 s"); time.sleep(120)
        else:
            return "STOP-NAD3-3-ENV", None
    finally:
        tl.close()
    if r.returncode in (4, 5, 6):
        log(f"{name}: guard rc={r.returncode}, stos nie ruszył, nie boot")
        return "STOP-NAD3-3-GUARD", None
    d = os.path.join(S3, name)
    if os.path.isdir(d) and os.path.exists(tp):
        os.replace(tp, os.path.join(d, "host_telemetria.jsonl"))
    try:
        kt = json.load(open(os.path.join(d, "kont_tempo.json")))
    except (OSError, ValueError):
        kt = None
    ev = [json.loads(l) for l in open(os.path.join(d, "trace.jsonl")) if '"event"' in l] if os.path.exists(os.path.join(d, "trace.jsonl")) else []
    names = [e.get("ev") for e in ev]
    n3 = next((e for e in ev if e.get("ev") == "nad3_degradacja"), None)
    wpis = {"boot_s3": bn, "pozycja": poz, "nazwa": name, "rc": r.returncode, "czas_s": round(time.time() - t0, 1), "tempo": kt,
            "bramka_zdrowia": proby, "shm": shm, "epizod_wystartowal": "episode_start" in names,
            "breach": any(n in ("breach", "breach_gt") for n in names), "nad3_degradacja": n3, "procesy": zn, "t": time.strftime("%F %T")}
    stop = None
    if r.returncode in (41, 42, 43, 44, 45):
        wpis["status"], stop = "osłona", f"STOP-NAD3-3-OSLONA-{r.returncode}"
    elif n3 is not None and not n3.get("zgodna"):
        wpis["status"], stop = "degradacja_niezgodna", "STOP-NAD3-3-DEGRAD"
    elif kt is not None and not kt.get("ok") and not wpis["epizod_wystartowal"]:
        wpis["status"] = "niewazny_stanowisko"
    elif wpis["breach"]:
        wpis["status"], stop = "breach", "STOP-NAD3-3-BREACH"
    elif LOT.POZ[poz]["rodzaj"] == "ciecie" and "denial" not in names:
        wpis["status"] = "bez_wejscia"
    else:
        wpis["status"] = "do_sedziego"
    if wpis["status"] == "do_sedziego":
        import nad2_ulg, nad3_analyze
        w = nad2_ulg.wyciag(d)
        log(f"{name}: wyciąg ULG {w}")
        nad3_analyze.analyze(d)
        sd = LOT.sedzia(d, poz)
        wpis["sedzia"] = {k: sd.get(k) for k in ("wazny", "replay_ok", "meta_ok", "decymacja_ok", "litera_ok", "wejscie", "D1_dostepne",
                                                 "b1_nieocenione_w_misji", "tempo")}
        wpis["sedzia"]["odmowy"] = [e.get("odmowa_w_misji") for e in sd["epizody"] if e.get("ciecie")]
        if not sd["litera_ok"]:
            wpis["status"], stop = "naruszenie", "STOP-NAD3-3-VC"
        elif not sd["wazny"]:
            wpis["status"], stop = "niewazny_przyrzad", "STOP-NAD3-3-PRZYRZAD"
        else:
            wpis["status"] = "wazny"
    with open(KSIEGA, "a") as f:
        f.write(json.dumps(wpis, ensure_ascii=False, default=str) + "\n")
    log(f"{name} poz {poz} rc={r.returncode} boot {bn} tempo={(kt or {}).get('dsim_dwall_settle')} status={wpis['status']} "
        f"sędzia={wpis.get('sedzia')}")
    return stop, wpis


def main():
    sucho = "--sucho" in sys.argv[1:]
    os.makedirs(S3, exist_ok=True)
    zuzyte, zrobione, rezerwa, plan = stan(ksiega())
    log(f"=== NAD3 S3 {'(na sucho) ' if sucho else ''}start: zużyte {zuzyte}/{BUDZET}, rezerwa {rezerwa}/{REZERWA}, "
        f"zrobione {sorted(zrobione)}, plan {plan}")
    if sucho:
        print(json.dumps({"plan": plan, "uzyte": zuzyte, "rezerwa": rezerwa, "budzet": BUDZET,
                          "pozycje": {p: {"nazwa": nazwa(p), "env": env_poz(p), "args": args_poz(p)} for p in plan}}, ensure_ascii=False))
        return
    subprocess.run(["sudo", "-n", "systemctl", "stop", "systemd-timesyncd"], check=True)
    stop = None
    try:
        while plan:
            if zuzyte >= BUDZET:
                stop = "STOP-NAD3-3-BUDZET"; break
            poz = plan[0]
            st, w = boot(poz, NOGA_PRZED + zuzyte + 1)
            if w is not None:
                zuzyte += 1
            if st:
                stop = st; break
            if w["status"] in ("bez_wejscia", "niewazny_stanowisko"):
                rezerwa += 1
                log(f"poz {poz}: {w['status']} — boot zużyty, powtórka z rezerwy ({rezerwa}/{REZERWA})")
                if rezerwa > REZERWA:
                    stop = "STOP-NAD3-3-REZERWA"; break
                continue
            plan.pop(0)
            zrobione.add(poz)
            if poz == 4:
                ks = ksiega()
                dost = sum(1 for x in ks if x.get("status") == "wazny" and x["pozycja"] in (1, 2, 3, 4) and x["sedzia"].get("D1_dostepne"))
                log(f"P1: dostępne wg D1 {dost}/4 (próg 3)")
                if dost < 3:
                    stop = "STOP-NAD3-3-P1"; break
    except Exception as ex:
        stop = "STOP-NAD3-3-WYJATEK"; log(f"ALARM {stop}: {ex!r}"); raise
    finally:
        subprocess.run(["sudo", "-n", "systemctl", "start", "systemd-timesyncd"])
        log(f"KONIEC booty={zuzyte}/{BUDZET} rezerwa={rezerwa}/{REZERWA} stop={stop} pozostało={plan}")
        p = os.path.join(S3, "kampania_s3.json")
        prev = json.load(open(p)) if os.path.exists(p) else {"przebiegi": []}
        prev["przebiegi"].append({"booty": zuzyte, "rezerwa": rezerwa, "stop": stop, "pozostalo": plan, "t": time.strftime("%F %T")})
        json.dump(prev, open(p, "w"), ensure_ascii=False, indent=1, default=str)
    print("KONIEC", zuzyte, stop)


if __name__ == "__main__":
    main()
