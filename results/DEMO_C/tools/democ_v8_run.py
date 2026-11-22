#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_v8_run.py — kolejka ujęć AKTU 8 „Bez GPS, bez znaczników" (PROMPT_DEMOC_V8 §3; ≤ 3 booty, łańcuch DEMOC).
KOPIA results/TEACH/tools/teach_s3_run.py (nietknięty) z podmianami (hunki oznaczone „# (V8)”):
  (V8-a) katalog results/DEMO_C/s8_mapa, log democ_v8.log, księga s8_mapa/kampania_ksiega.jsonl, boot democ_v8_boot.sh;
  (V8-b) plan = jedna pozycja bramki S3: 12 (łata J, c10, wariant a — ten sam lot co p12_J_c10_a), nazwa take<k>_J_c10_a;
  (V8-c) budżet 3 booty (łańcuch DEMOC, poza budżetem nogi TEACH), sygnały STOP-DEMOC-8-*;
  (V8-d) ujęcie VALID ⇔ status „wazny” (sędzia teach_s3_lot: litera B1–B4, sprawdzian 100%, meta, wejście, warunki ważności sędziego)
         ∧ odmowa w misji brak ∧ D1 kontynuacja ≥ 110 s ∧ komplet klatek obu kamer w oknie aktu (od początku fazy mapy do zejścia
         planowego + 4 s; przerwa ≤ 1.0 s, pokrycie obu końców) — ujęcie nieważne zapisane jawnie w ujecia.jsonl, następny take
         w identycznych warunkach (§3), progi bez zmian;
  (V8-e) reguła łaty S po pozycji 4 i liczniki nogi usunięte (nie dotyczą łańcucha DEMOC).
Reszta (strażniki stanowiska, procesy Windows, timesyncd, bramka zdrowia A/C w procesie potomnym, zegar, sieroty, telemetria hosta,
rejestrator kadrów, wyciąg ULG, sędzia, reguły STOP po locie) bez zmian.
Użycie: democ_v8_run.py [--sucho]. Wyjście: s8_mapa/democ_v8.log, democ_v8.json, kampania_ksiega.jsonl, ujecia.jsonl.
--- docstring kopii (teach_s3_run.py) ---
results/TEACH/tools/teach_s3_run.py — kolejka bramki S3 TEACH (PROMPT_TEACH_S3 §1–§4, ANEKS_TEACH-4 §3; ≤ 17 bootów, noga ≤ 22 z 24)
= wzór results/TEACH/tools/teach_s2_run.py i results/NAD3/tools/nad3_s3_run.py (oba nietknięte): strażniki stanowiska
kont_s2_campaign_g (READ-ONLY, ścieżki na results/TEACH/s3), bramka zdrowia przyrządem A w procesie potomnym (katalog results/TEACH/s3/bramka;
A, NO-GO ⇒ 3 min ⇒ C, trzecie NO-GO ⇒ STOP-DEMOC-8-STANOWISKO, nic nie zużyte), telemetria hosta w tle, pasywny rejestrator kadrów kamery
w dół (teach_rejestrator, kadry na stanowisku ~/teach_stanowisko/<nazwa>/), boot results/TEACH/tools/teach_boot.sh (TEACH_ETAP=s3, tryb
1/1/0, manifest NAD3 v2, ziarno s01).
Plan: 14 pozycji w kolejności wiążącej (teach_s3_lot.PLAN): cięcia S (c05 a, c10 a, c05 b, c10 b), N1 (S, c10, cień 176.5), cięcia M,
N2 (J, c05, cień 173.6), cięcia J. Przed każdym bootem: asercja pozycja = numer (manifest: episode_id = indeks, 120/120; plan: pozycja
w kolejności = numer), lista procesów Windows (tasklist.exe: Chrome, ChatGPT ⇒ STOP-DEMOC-8-PROCESY, bez bootu), sieroty, zegar.
Po każdym locie, przed następnym: wyciąg ULG (nad2_ulg, READ-ONLY), sędzia teach_s3_lot (analizator, sprawdzian 100%, meta, litera, D1,
odmowy, kadry do repo). Reguły §4 (funkcje `status_lotu` i `po_pozycji`, sprawdzane na sucho):
  - naruszenie B1–B5 (litera) ⇒ STOP-DEMOC-8-VC natychmiast;
  - sprawdzian lotu < 100% albo meta niezgodna ⇒ STOP-DEMOC-8-PRZYRZAD (wada przyrządu, nie rezerwa);
  - detekcja zgodna z manifestem, kadr mapy po fladze albo drugie zamknięcie ⇒ STOP-DEMOC-8-SWIAT-KOD (lot nieważny, nie rezerwa);
  - cięcie bez wejścia ⇒ boot liczony, lot nieważny dla bramki, powtórka z rezerwy;
  - boot nieważny stanowiskowo w locie (bramka tempa drivera, epizod nie wystartował) ⇒ powtórka z rezerwy; NO-GO bramki zdrowia przed
    startem nie jest bootem;
  - rezerwa 3 łącznie, czwarta potrzeba ⇒ STOP-DEMOC-8-REZERWA; budżet 17 ⇒ STOP-DEMOC-8-BUDZET; noga > 22 ⇒ STOP-DEMOC-8-NOGA;
  - po pozycji 4: mniej niż 3 z 4 cięć łaty S dostępnych ⇒ STOP-DEMOC-8-S przed pozycją 5;
  - nominał bez akwizycji: pusty dla (B5), nazwany, bez powtórki;
  - breach ⇒ STOP-DEMOC-8-BREACH; kody drivera 41–45 ⇒ STOP-DEMOC-8-OSLONA-<kod>; 8–9 ⇒ STOP-DEMOC-8-DRIVER-<kod>; strażnik 4–6 ⇒
    STOP-DEMOC-8-GUARD.
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

S3 = os.path.join(ROOT, "results/DEMO_C/s8_mapa")                                   # (V8-a)
G.S2 = S3
G.LOG = os.path.join(S3, "democ_v8.log")
G.SKRYPTY = G.SKRYPTY | {"kont_s4_flight", "nadir_s4_flight", "nad2_flight", "nad3_flight", "teach_flight", "intruder_motion",
                         "nadir_obs", "teach_rejestrator"}
log = G.log
BOOT = os.path.join(ROOT, "results/DEMO_C/tools/democ_v8_boot.sh")      # (V8-a)
KSIEGA = os.path.join(S3, "kampania_ksiega.jsonl")
MANIFEST = os.path.join(ROOT, "results/NAD3/s1/scenario_manifest_nad3_v2.json")
STANOWISKO = os.path.expanduser("~/teach_stanowisko")
BUDZET, REZERWA, NOGA_PRZED, NOGA_MAX = 3, 2, 0, 3                  # (V8-c)
POZYCJA = 12                                                         # (V8-b)
UJECIA = os.path.join(S3, "ujecia.jsonl")
TASKLIST = "/mnt/c/Windows/System32/tasklist.exe"
ZAKAZANE = ("chrome.exe", "chatgpt.exe")
SCEN = {5: "c05_s01", 10: "c10_s01"}


def nazwa(poz, take=1):                                               # (V8-b)
    P = LOT.POZ[poz]
    kom = "c05" if P["epizod"] == 5 else "c10"
    return f"take{take}_{P['lata']}_{kom}_{P['powt']}"


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
    zrobione = {w["pozycja"] for w in ks if w.get("VALID")}                                  # (V8-d)
    rezerwa = max(0, zuzyte - 1)
    plan = [p for p in [POZYCJA] if p not in zrobione]                                    # (V8-b)
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
        return "oslona", f"STOP-DEMOC-8-OSLONA-{rc}"
    if rc in (8, 9):
        return "driver", f"STOP-DEMOC-8-DRIVER-{rc}"
    if any(n in ("breach", "breach_gt") for n in names):
        return "breach", "STOP-DEMOC-8-BREACH"
    if not started:
        return ("niewazny_stanowisko", None) if (kt is not None and not kt.get("ok")) else ("bez_epizodu", "STOP-DEMOC-8-BEZ-EPIZODU")
    if sd is None:
        return "bez_sedziego", "STOP-DEMOC-8-SEDZIA"
    if not sd["litera_ok"]:
        return "naruszenie", "STOP-DEMOC-8-VC"
    nw = sd.get("niewaznosc") or []
    if "przyrzad" in nw:
        return "niewazny_przyrzad", "STOP-DEMOC-8-PRZYRZAD"
    if "swiat_kod" in nw:
        return "niewazny_swiat_kod", "STOP-DEMOC-8-SWIAT-KOD"
    if "wejscie" in nw:
        return "bez_wejscia", None
    if not sd["wazny"]:
        return "niewazny_inny", "STOP-DEMOC-8-NIEWAZNY"
    return "wazny", None


def _ciaglosc(p, t0, t1, przerwa=1.0):
    """Indeks klatek zrzutnika: (pokrycie obu końców okna, największa przerwa w oknie, liczba klatek w oknie)."""
    if not os.path.exists(p):
        return False, None, 0
    ts = sorted(json.loads(l)["sim"] for l in open(p) if l.strip())
    w = [x for x in ts if t0 <= x <= t1]
    if not w:
        return False, None, 0
    gaps = [b - a for a, b in zip([t0] + w, w + [t1])]
    return (ts[0] <= t0 + przerwa and ts[-1] >= t1 - przerwa and max(gaps) <= przerwa), round(max(gaps), 3), len(w)


def ujecie(d, sd, status):                                                                  # (V8-d)
    """VALID ujęcia: status ważny ∧ brak odmowy w misji ∧ D1 kontynuacja ≥ 110 s ∧ komplet klatek obu kamer w oknie aktu."""
    u = {"status_wazny": status == "wazny"}
    if sd is None:
        return False, u
    ec = next((e for e in sd["epizody"] if e.get("ciecie")), None) or {}
    u["odmowa_w_misji"] = ec.get("odmowa_w_misji")
    u["D1"] = ec.get("D1")
    kont = (ec.get("D1") or {}).get("kontynuacja_od_t_inj_s")
    u["kontynuacja_ok"] = kont is not None and kont >= 110.0
    t0 = None
    for l in open(os.path.join(d, "nadir_obs.jsonl")):
        try:
            r = json.loads(l)
        except ValueError:
            continue
        te = r.get("teach") or {} if r.get("t") == "nf" else {}
        if te.get("faza") == "mapa" and "bufor" in te:
            t0 = r["sim"]; break
    ev = [json.loads(l) for l in open(os.path.join(d, "trace.jsonl")) if '"event"' in l]
    zp = next((e["sim"] for e in ev if e.get("ev") == "zejscie_planowe"), None)
    u["okno_aktu"] = [t0, (zp + 4.0) if zp is not None else None]
    if t0 is None or zp is None:
        u["klatki_ok"] = False
    else:
        c = _ciaglosc(os.path.join(d, "cam", "frames_index.jsonl"), t0, zp + 4.0)
        n = _ciaglosc(os.path.join(d, "nadir", "frames_index.jsonl"), t0, zp + 4.0)
        u["klatki_cam"] = {"ok": c[0], "max_przerwa_s": c[1], "n": c[2]}
        u["klatki_nadir"] = {"ok": n[0], "max_przerwa_s": n[1], "n": n[2]}
        u["klatki_ok"] = c[0] and n[0]
    ok = u["status_wazny"] and u["odmowa_w_misji"] is None and u["kontynuacja_ok"] and u["klatki_ok"]
    return bool(ok), u


def po_pozycji(poz, ks, rezerwa, zuzyte):
    """Reguły §4 po zakończonym boocie ⇒ stop | None (rezerwa, budżet, noga, próg łaty S)."""
    if rezerwa > REZERWA:
        return "STOP-DEMOC-8-REZERWA"
    if NOGA_PRZED + zuzyte > NOGA_MAX:
        return "STOP-DEMOC-8-NOGA"
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
        return "STOP-DEMOC-8-POZYCJA", None
    ok, zn = procesy()
    log(f"poz {poz}: procesy Windows {zn}")
    if not ok:
        return "STOP-DEMOC-8-PROCESY", None
    if subprocess.run(["systemctl", "is-active", "--quiet", "systemd-timesyncd"]).returncode == 0:
        return "STOP-DEMOC-8-TIMESYNCD", None
    name = wolna(nazwa(poz, len(ksiega()) + 1))                                          # (V8-b)
    go, proby = bramka_zdrowia(name)
    if go is None:
        return "STOP-DEMOC-8-BRAMKA", None
    if not go:
        return "STOP-DEMOC-8-STANOWISKO", None
    ok, z = G.zegar(name)
    log(f"{name}: próbnik zegara {z['skoki']} skoków ok={ok}")
    if not ok:
        return "STOP-DEMOC-8-ZEGAR", None
    znal, zywe = G.sprzataj_sieroty()
    if zywe:
        return "STOP-DEMOC-8-SIEROTY", None
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
    log(f"=== DEMOC v8 poz {poz} {name} boot nogi {bn}/{NOGA_MAX} env={env_poz(poz)} epizod={eps} inject={inj}")
    t0 = time.time()
    try:
        for _ in range(4):
            r = subprocess.run(["bash", BOOT, str(bn), name, eps, inj], cwd=ROOT, env=env, capture_output=True, text=True)
            open(os.path.join(S3, f"{name}_driver.log"), "a").write(r.stdout + r.stderr)
            if r.returncode != 3:
                break
            log(f"{name}: env-block rc=3, nie boot, czekam 120 s"); time.sleep(120)
        else:
            return "STOP-DEMOC-8-ENV", None
    finally:
        tl.close()
        rej.terminate()
        try:
            rej.wait(timeout=15)
        except subprocess.TimeoutExpired:
            rej.kill()
    if r.returncode in (4, 5, 6):
        log(f"{name}: guard rc={r.returncode}, stos nie ruszył, nie boot")
        return "STOP-DEMOC-8-GUARD", None
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
    wpis["VALID"], wpis["ujecie"] = ujecie(d, sd, wpis["status"])                       # (V8-d)
    with open(UJECIA, "a") as f:
        f.write(json.dumps({"take": len(ksiega()) + 1, "nazwa": name, "VALID": wpis["VALID"], "status": wpis["status"], **wpis["ujecie"],
                            "t": time.strftime("%F %T")}, ensure_ascii=False, default=str) + "\n")
    log(f"{name}: ujęcie VALID={wpis['VALID']} {wpis['ujecie']}")
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
    log(f"=== DEMOC v8 {'(na sucho) ' if sucho else ''}start: zużyte {zuzyte}/{BUDZET}, rezerwa {rezerwa}/{REZERWA}, "
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
                stop = "STOP-DEMOC-8-BUDZET"; break
            if NOGA_PRZED + zuzyte + 1 > NOGA_MAX:
                stop = "STOP-DEMOC-8-NOGA"; break
            poz = plan[0]
            st, w = boot(poz, NOGA_PRZED + zuzyte + 1, plan)
            if w is not None:
                zuzyte += 1
            if st:
                stop = st; break
            if not w.get("VALID") and w["status"] in ("bez_wejscia", "niewazny_stanowisko", "wazny"):        # (V8-d)
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
        stop = "STOP-DEMOC-8-WYJATEK"; log(f"ALARM {stop}: {ex!r}"); raise
    finally:
        log(f"KONIEC booty={zuzyte}/{BUDZET} noga={NOGA_PRZED + zuzyte}/{NOGA_MAX} rezerwa={rezerwa}/{REZERWA} stop={stop} pozostało={plan}")
        p = os.path.join(S3, "democ_v8.json")                                 # (V8-a)
        prev = json.load(open(p)) if os.path.exists(p) else {"przebiegi": []}
        prev["przebiegi"].append({"booty": zuzyte, "rezerwa": rezerwa, "stop": stop, "pozostalo": plan, "t": time.strftime("%F %T")})
        json.dump(prev, open(p, "w"), ensure_ascii=False, indent=1, default=str)
    print("KONIEC", zuzyte, stop)


if __name__ == "__main__":
    main()
