#!/usr/bin/env python3
"""results/TEACH/tools/teach_s3_run.py — kolejka bramki S3 TEACH (PROMPT_TEACH_S3 §1–§4, ANEKS_TEACH-4 §3; ≤ 17 bootów, noga ≤ 22 z 24)
= wzór results/TEACH/tools/teach_s2_run.py i results/NAD3/tools/nad3_s3_run.py (oba nietknięte): strażniki stanowiska
kont_s2_campaign_g (READ-ONLY, ścieżki na results/TEACH/s3), bramka zdrowia przyrządem A w procesie potomnym (katalog results/TEACH/s3/bramka;
A, NO-GO ⇒ 3 min ⇒ C, trzecie NO-GO ⇒ STOP-TEACH-3-STANOWISKO, nic nie zużyte), telemetria hosta w tle, pasywny rejestrator kadrów kamery
w dół (teach_rejestrator, kadry na stanowisku ~/teach_stanowisko/<nazwa>/), boot results/TEACH/tools/teach_boot.sh (TEACH_ETAP=s3, tryb
1/1/0, manifest NAD3 v2, ziarno s01).
Plan: 14 pozycji w kolejności wiążącej (teach_s3_lot.PLAN): cięcia S (c05 a, c10 a, c05 b, c10 b), N1 (S, c10, cień 176.5), cięcia M,
N2 (J, c05, cień 173.6), cięcia J. Przed każdym bootem: asercja pozycja = numer (manifest: episode_id = indeks, 120/120; plan: pozycja
w kolejności = numer), lista procesów Windows (tasklist.exe: Chrome, ChatGPT ⇒ STOP-TEACH-3-PROCESY, bez bootu), sieroty, zegar.
Po każdym locie, przed następnym: wyciąg ULG (nad2_ulg, READ-ONLY), sędzia teach_s3_lot (analizator, sprawdzian 100%, meta, litera, D1,
odmowy, kadry do repo). Reguły §4 (funkcje `status_lotu` i `po_pozycji`, sprawdzane na sucho):
  - naruszenie B1–B5 (litera) ⇒ STOP-TEACH-3-VC natychmiast;
  - sprawdzian lotu < 100% albo meta niezgodna ⇒ STOP-TEACH-3-PRZYRZAD (wada przyrządu, nie rezerwa);
  - detekcja zgodna z manifestem, kadr mapy po fladze albo drugie zamknięcie ⇒ STOP-TEACH-3-SWIAT-KOD (lot nieważny, nie rezerwa);
  - cięcie bez wejścia ⇒ boot liczony, lot nieważny dla bramki, powtórka z rezerwy;
  - boot nieważny stanowiskowo w locie (bramka tempa drivera, epizod nie wystartował) ⇒ powtórka z rezerwy; NO-GO bramki zdrowia przed
    startem nie jest bootem;
  - rezerwa 3 łącznie, czwarta potrzeba ⇒ STOP-TEACH-3-REZERWA; budżet 17 ⇒ STOP-TEACH-3-BUDZET; noga > 22 ⇒ STOP-TEACH-3-NOGA;
  - po pozycji 4: mniej niż 3 z 4 cięć łaty S dostępnych ⇒ STOP-TEACH-3-S przed pozycją 5;
  - nominał bez akwizycji: pusty dla (B5), nazwany, bez powtórki;
  - breach ⇒ STOP-TEACH-3-BREACH; kody drivera 41–45 ⇒ STOP-TEACH-3-OSLONA-<kod>; 8–9 ⇒ STOP-TEACH-3-DRIVER-<kod>; strażnik 4–6 ⇒
    STOP-TEACH-3-GUARD.
Stan w księdze results/TEACH/s3/kampania_ksiega.jsonl (wiersz per zużyty boot z wynikiem sędziego); kolejka wznawia się od pierwszej
pozycji bez lotu ważnego. timesyncd: musi być nieaktywny (zatrzymany na sesję); kolejka go nie uruchamia — po sesji akcja Olgi.
Użycie: teach_s3_run.py [--sucho] [--do POZYCJA]. Wyjście: results/TEACH/s3/kampania_s3.log, kampania_s3.json.
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
import teach_s3_lot as LOT

S3 = os.path.join(ROOT, "results/TEACH/s3")
G.S2 = S3
G.LOG = os.path.join(S3, "kampania_s3.log")
G.SKRYPTY = G.SKRYPTY | {"kont_s4_flight", "nadir_s4_flight", "nad2_flight", "nad3_flight", "teach_flight", "intruder_motion",
                         "nadir_obs", "teach_rejestrator"}
log = G.log
BOOT = os.path.join(ROOT, "results/TEACH/tools/teach_boot.sh")
KSIEGA = os.path.join(S3, "kampania_ksiega.jsonl")
MANIFEST = os.path.join(ROOT, "results/NAD3/s1/scenario_manifest_nad3_v2.json")
STANOWISKO = os.path.expanduser("~/teach_stanowisko")
BUDZET, REZERWA, NOGA_PRZED, NOGA_MAX = 17, 3, 5, 22
TASKLIST = "/mnt/c/Windows/System32/tasklist.exe"
ZAKAZANE = ("chrome.exe", "chatgpt.exe")
SCEN = {5: "c05_s01", 10: "c10_s01"}


def nazwa(poz):
    P = LOT.POZ[poz]
    kom = "c05" if P["epizod"] == 5 else "c10"
    return f"p{poz:02d}_{P['lata']}_{kom}_{P['powt']}" if P["rodzaj"] == "ciecie" else f"p{poz:02d}_{P['powt']}_{P['lata']}_{kom}_cien"


def env_poz(poz):
    P = LOT.POZ[poz]
    e = {"BOOT_NADIR_MODE": "1", "BOOT_KONT_MODE": "1", "BOOT_PASSTHROUGH": "0", "TEACH_ETAP": "s3", "BOOT_LATA": P["lata"],
         "BOOT_CIEN": "1" if P["rodzaj"] == "nominal" else "0"}
    if P["rodzaj"] == "nominal":
        e["BOOT_T_CIEN"] = str(P["t_cien"])
    return e


def args_poz(poz):
    P = LOT.POZ[poz]
    return str(P["epizod"]), ("30" if P["rodzaj"] == "ciecie" else "-")


def niezmiennik(poz, plan):
    eps = json.load(open(MANIFEST))["episodes"]
    ep = LOT.POZ[poz]["epizod"]
    return (len(eps) == 120 and all(i == e["episode_id"] for i, e in enumerate(eps)) and eps[ep]["scenario_id"] == SCEN[ep]
            and plan and plan[0] == poz and sorted(LOT.POZ) == list(range(1, 15)))


def procesy():
    try:
        out = subprocess.run([TASKLIST, "/FO", "CSV"], capture_output=True, timeout=30).stdout.decode("utf-8", errors="replace").lower()
    except (OSError, subprocess.TimeoutExpired) as ex:
        return False, repr(ex)
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


def status_lotu(rc, rodzaj, names, kt, sd):
    """Reguły §4 po locie ⇒ (status, stop | None). sd = sędzia (None, gdy nie sądzony)."""
    started = "episode_start" in names
    if rc in (41, 42, 43, 44, 45):
        return "oslona", f"STOP-TEACH-3-OSLONA-{rc}"
    if rc in (8, 9):
        return "driver", f"STOP-TEACH-3-DRIVER-{rc}"
    if any(n in ("breach", "breach_gt") for n in names):
        return "breach", "STOP-TEACH-3-BREACH"
    if not started:
        return ("niewazny_stanowisko", None) if (kt is not None and not kt.get("ok")) else ("bez_epizodu", "STOP-TEACH-3-BEZ-EPIZODU")
    if sd is None:
        return "bez_sedziego", "STOP-TEACH-3-SEDZIA"
    if not sd["litera_ok"]:
        return "naruszenie", "STOP-TEACH-3-VC"
    nw = sd.get("niewaznosc") or []
    if "przyrzad" in nw:
        return "niewazny_przyrzad", "STOP-TEACH-3-PRZYRZAD"
    if "swiat_kod" in nw:
        return "niewazny_swiat_kod", "STOP-TEACH-3-SWIAT-KOD"
    if "wejscie" in nw:
        return "bez_wejscia", None
    if not sd["wazny"]:
        return "niewazny_inny", "STOP-TEACH-3-NIEWAZNY"
    return "wazny", None


def po_pozycji(poz, ks, rezerwa, zuzyte):
    """Reguły §4 po zakończonym boocie ⇒ stop | None (rezerwa, budżet, noga, próg łaty S)."""
    if rezerwa > REZERWA:
        return "STOP-TEACH-3-REZERWA"
    if NOGA_PRZED + zuzyte > NOGA_MAX:
        return "STOP-TEACH-3-NOGA"
    if poz == 4 and all(any(w.get("status") == "wazny" and w["pozycja"] == p for w in ks) for p in (1, 2, 3, 4)):
        dost = sum(1 for w in ks if w.get("status") == "wazny" and w["pozycja"] in (1, 2, 3, 4) and (w.get("sedzia") or {}).get("D1_dostepne"))
        log(f"łata S: dostępne wg D1 {dost}/4 (próg 3)")
        if dost < 3:
            return "STOP-TEACH-3-S"
    return None


BRAMKA_PY = """
import json, os, sys
sys.path[:0] = {sciezki!r}
import nadir_s4_bramka as B
B.OUT = {out!r}
B.zegar_ok()
r = B.przyrzad_a({tag!r}, tel={tel!r})
print("WYNIK " + json.dumps({{k: r.get(k) for k in ("wariant", "tempo", "GO", "czolowka_operatora")}}, ensure_ascii=False, default=str))
"""


def bramka_zdrowia(name):
    proby = []
    for k in range(3):
        if k:
            time.sleep(180)
        tag = f"{name}_g{k + 1}"
        kod = BRAMKA_PY.format(sciezki=[os.path.join(ROOT, "results/NADIR/tools"), os.path.join(ROOT, "results/KONT/tools"), ROOT],
                               out=os.path.join(S3, "bramka"), tag=tag, tel=bool(k))
        w = subprocess.run([sys.executable, "-c", kod], cwd=ROOT, capture_output=True, text=True)
        line = next((l for l in w.stdout.splitlines() if l.startswith("WYNIK ")), None)
        if w.returncode != 0 or line is None:
            log(f"{name}: bramka zdrowia błąd rc={w.returncode}: {(w.stdout + w.stderr)[-600:]}")
            return None, proby
        r = json.loads(line[6:])
        p = {"tag": tag, "wariant": r["wariant"], "tempo": r["tempo"], "GO": r["GO"], "czolowka_operatora": r.get("czolowka_operatora"),
             "t": time.strftime("%F %T")}
        proby.append(p)
        with open(os.path.join(S3, "bramka_ksiega.jsonl"), "a") as f:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
        log(f"{name}: bramka zdrowia {tag} ({p['wariant']}) GO={p['GO']} tempo={p['tempo']}")
        if r["GO"]:
            return True, proby
    return False, proby


def boot(poz, bn, plan):
    """Zwraca (stop | None, wpis | None). wpis = zużyty boot (zapisany w księdze)."""
    if not niezmiennik(poz, plan):
        return "STOP-TEACH-3-POZYCJA", None
    ok, zn = procesy()
    log(f"poz {poz}: procesy Windows {zn}")
    if not ok:
        return "STOP-TEACH-3-PROCESY", None
    if subprocess.run(["systemctl", "is-active", "--quiet", "systemd-timesyncd"]).returncode == 0:
        return "STOP-TEACH-3-TIMESYNCD", None
    name = wolna(nazwa(poz))
    go, proby = bramka_zdrowia(name)
    if go is None:
        return "STOP-TEACH-3-BRAMKA", None
    if not go:
        return "STOP-TEACH-3-STANOWISKO", None
    ok, z = G.zegar(name)
    log(f"{name}: próbnik zegara {z['skoki']} skoków ok={ok}")
    if not ok:
        return "STOP-TEACH-3-ZEGAR", None
    znal, zywe = G.sprzataj_sieroty()
    if zywe:
        return "STOP-TEACH-3-SIEROTY", None
    shm = G.shm_krok(name, False)
    eps, inj = args_poz(poz)
    env = {**os.environ, **env_poz(poz), "PERC2_FASTDDS_PROFILE": G.PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
    tp = os.path.join(S3, f"{name}_host_telemetria.jsonl")
    tl = TL.Telemetria2(tp, 3600)
    kad = os.path.join(STANOWISKO, name)
    rej = subprocess.Popen([sys.executable, os.path.join(ROOT, "results/TEACH/tools/teach_rejestrator.py"), "--world",
                            f"world_teach_{LOT.POZ[poz]['lata']}", "--model", "x500_teach_flow_0", "--out", kad],
                           stdout=open(os.path.join(S3, f"{name}_rejestrator.log"), "w"), stderr=subprocess.STDOUT,
                           env={**os.environ, "GZ_IP": "127.0.0.1"}, start_new_session=True)
    log(f"=== TEACH S3 poz {poz} {name} boot nogi {bn}/{NOGA_MAX} env={env_poz(poz)} epizod={eps} inject={inj}")
    t0 = time.time()
    try:
        for _ in range(4):
            r = subprocess.run(["bash", BOOT, str(bn), name, eps, inj], cwd=ROOT, env=env, capture_output=True, text=True)
            open(os.path.join(S3, f"{name}_driver.log"), "a").write(r.stdout + r.stderr)
            if r.returncode != 3:
                break
            log(f"{name}: env-block rc=3, nie boot, czekam 120 s"); time.sleep(120)
        else:
            return "STOP-TEACH-3-ENV", None
    finally:
        tl.close()
        rej.terminate()
        try:
            rej.wait(timeout=15)
        except subprocess.TimeoutExpired:
            rej.kill()
    if r.returncode in (4, 5, 6):
        log(f"{name}: guard rc={r.returncode}, stos nie ruszył, nie boot")
        return "STOP-TEACH-3-GUARD", None
    d = os.path.join(S3, name)
    if os.path.isdir(d) and os.path.exists(tp):
        os.replace(tp, os.path.join(d, "host_telemetria.jsonl"))
    try:
        kt = json.load(open(os.path.join(d, "kont_tempo.json")))
    except (OSError, ValueError):
        kt = None
    trp = os.path.join(d, "trace.jsonl")
    ev = [json.loads(l) for l in open(trp) if '"event"' in l] if os.path.exists(trp) else []
    names = [e.get("ev") for e in ev]
    wpis = {"boot_nogi": bn, "pozycja": poz, "nazwa": name, "rc": r.returncode, "czas_s": round(time.time() - t0, 1), "tempo": kt,
            "bramka_zdrowia": proby, "shm": shm, "procesy": zn, "epizod_wystartowal": "episode_start" in names,
            "breach": any(n in ("breach", "breach_gt") for n in names), "wejscie_denial": "denial" in names,
            "teach_producent": next((e for e in ev if e.get("ev") == "teach_producent"), None),
            "kadry_stanowisko": kad, "n_kadrow": len(os.listdir(kad)) if os.path.isdir(kad) else 0, "t": time.strftime("%F %T")}
    sd = None
    if "episode_start" in names and r.returncode not in (8, 9, 41, 42, 43, 44, 45):
        import nad2_ulg
        log(f"{name}: wyciąg ULG {nad2_ulg.wyciag(d)}")
        sd = LOT.sedzia(d, poz, kad)
        wpis["sedzia"] = {k: sd.get(k) for k in ("wazny", "niewaznosc", "litera_ok", "wejscie", "D1_dostepne", "b1_nieocenione_w_misji",
                                                 "tempo")}
        wpis["sedzia"]["sprawdzian"] = sd["sprawdzian"]["procent"]
        wpis["sedzia"]["meta_ok"] = sd["meta"]["ok"]
        wpis["sedzia"]["B"] = [e["B"] for e in sd["epizody"]]
        wpis["sedzia"]["odmowy"] = [e.get("odmowa_w_misji") for e in sd["epizody"] if e.get("ciecie")]
        wpis["sedzia"]["max_blad_poprawki"] = (sd["zrodlo"].get("blad_poprawki") or {}).get("max")
    wpis["status"], stop = status_lotu(r.returncode, LOT.POZ[poz]["rodzaj"], names, kt, sd)
    with open(KSIEGA, "a") as f:
        f.write(json.dumps(wpis, ensure_ascii=False, default=str) + "\n")
    log(f"{name} poz {poz} rc={r.returncode} boot nogi {bn} tempo={(kt or {}).get('dsim_dwall_settle')} status={wpis['status']} "
        f"sędzia={wpis.get('sedzia')}")
    return stop, wpis


def main():
    sucho = "--sucho" in sys.argv[1:]
    do = int(sys.argv[sys.argv.index("--do") + 1]) if "--do" in sys.argv else 14
    os.makedirs(S3, exist_ok=True)
    zuzyte, zrobione, rezerwa, plan = stan(ksiega())
    log(f"=== TEACH S3 {'(na sucho) ' if sucho else ''}start: zużyte {zuzyte}/{BUDZET}, rezerwa {rezerwa}/{REZERWA}, "
        f"noga {NOGA_PRZED + zuzyte}/{NOGA_MAX}, zrobione {sorted(zrobione)}, plan {plan}, do {do}")
    if sucho:
        print(json.dumps({"plan": plan, "uzyte": zuzyte, "rezerwa": rezerwa, "budzet": BUDZET,
                          "pozycje": {p: {"nazwa": nazwa(p), "env": env_poz(p), "args": args_poz(p), **LOT.POZ[p]} for p in plan}},
                         ensure_ascii=False))
        return
    stop = None
    try:
        while plan and plan[0] <= do:
            if zuzyte >= BUDZET:
                stop = "STOP-TEACH-3-BUDZET"; break
            if NOGA_PRZED + zuzyte + 1 > NOGA_MAX:
                stop = "STOP-TEACH-3-NOGA"; break
            poz = plan[0]
            st, w = boot(poz, NOGA_PRZED + zuzyte + 1, plan)
            if w is not None:
                zuzyte += 1
            if st:
                stop = st; break
            if w["status"] in ("bez_wejscia", "niewazny_stanowisko"):
                rezerwa += 1
                log(f"poz {poz}: {w['status']} — boot zużyty, powtórka z rezerwy ({rezerwa}/{REZERWA})")
                stop = po_pozycji(poz, ksiega(), rezerwa, zuzyte)
                if stop:
                    break
                continue
            plan.pop(0)
            zrobione.add(poz)
            stop = po_pozycji(poz, ksiega(), rezerwa, zuzyte)
            if stop:
                break
    except Exception as ex:
        stop = "STOP-TEACH-3-WYJATEK"; log(f"ALARM {stop}: {ex!r}"); raise
    finally:
        log(f"KONIEC booty={zuzyte}/{BUDZET} noga={NOGA_PRZED + zuzyte}/{NOGA_MAX} rezerwa={rezerwa}/{REZERWA} stop={stop} pozostało={plan}")
        p = os.path.join(S3, "kampania_s3.json")
        prev = json.load(open(p)) if os.path.exists(p) else {"przebiegi": []}
        prev["przebiegi"].append({"booty": zuzyte, "rezerwa": rezerwa, "stop": stop, "pozostalo": plan, "t": time.strftime("%F %T")})
        json.dump(prev, open(p, "w"), ensure_ascii=False, indent=1, default=str)
    print("KONIEC", zuzyte, stop)


if __name__ == "__main__":
    main()
