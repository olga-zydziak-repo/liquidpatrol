#!/usr/bin/env python3
"""results/NAD3/tools/nad3_s2_run.py — kolejka smoke S2 NADIR-III (PROMPT_NAD3_S2 §2–§4; ≤ 4 booty) = wzór
results/NAD2/tools/nad2_s2_run.py (nietknięty): strażniki stanowiska z kont_s2_campaign_g.py (zegar, sieroty, /dev/shm; import
READ-ONLY, ścieżki przestawione na results/NAD3/s2), bramka zdrowia przyrządem A (results/NADIR/tools/nadir_s4_bramka — READ-ONLY,
katalog wyjścia results/NAD3/s2/bramka; A, NO-GO ⇒ 3 min ⇒ C; trzecie NO-GO z rzędu ⇒ STOP-NAD3-2-STANOWISKO), telemetria w tle
bootu. Boot: results/NAD3/tools/nad3_boot.sh (NAD3_ETAP=s2, tryb NM=1 KM=1 PT=0 LIT=NAD2, BOOT_PUNKT=P1).
Kolejność wiążąca (§2): N1 (nominał, epizody c00, c01, c05, c10) → bramka geometrii → N2 (c02, c03, c05, c10) → bramka geometrii →
B3 (cięcie c05, bez degradacji) → B4 (cięcie c05, P1, bias na zewnątrz). Epizody podawane INDEKSEM listy manifestu NAD3
(driver: manifest["episodes"][i]): c00 0, c01 1, c02 2, c03 3, c05 4, c10 5. Cięcia KONT_INJECT_T 30, kontynuacja 110.5 s.
Po każdym boocie: wyciąg ULG (results/NAD2/tools/nad2_ulg — READ-ONLY), analizator nad3_analyze; po N1/N2 nad3_s2_geom (bramka
r_max ≤ 19.5 m — przekroczenie ⇒ STOP-NAD3-2-GEOM; kryterium nominału niespełnione w > 1 z 8 ⇒ STOP-NAD3-2-SMIERC-GEOM); po B3/B4
nad3_s2_spr (replay < 100% ⇒ STOP-NAD3-2-REPLAY; B1–B4 naruszone ⇒ STOP-NAD3-2-FAIL; B4: r_max GT > 19.5 m ⇒ STOP-NAD3-2-RMAX).
Boot nieważny stanowiskowo przed startem epizodu (bramka zdrowia NO-GO, bramka tempa w driverze — kont_tempo.json ok = false) nie
liczy się; jedna powtórka; drugi nieważny ⇒ STOP-NAD3-2-STANOWISKO. Kod 9 drivera jest wspólny dla bramki tempa (KONT) i niezgodności
degradacji (NAD3) — rozróżnienie: kont_tempo.json vs zdarzenie „nad3_degradacja” (zgodna = false ⇒ STOP-NAD3-2-DEGRAD). Kody
41–45 (odmowa startu osłony) i 4–6 (strażnik boota) ⇒ STOP bez zużycia. timesyncd: stop na starcie, start na końcu.
Użycie: nad3_s2_run.py [--sucho]. Wyjście: results/NAD3/s2/kampania_s2.log, kampania_s2.json, kampania_ksiega.jsonl.
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

S2 = os.path.join(ROOT, "results/NAD3/s2")
G.S2 = S2
G.LOG = os.path.join(S2, "kampania_s2.log")
G.SKRYPTY = G.SKRYPTY | {"kont_s4_flight", "nadir_s4_flight", "nad2_flight", "nad3_flight", "intruder_motion", "nadir_obs"}
log = G.log
BOOT = os.path.join(ROOT, "results/NAD3/tools/nad3_boot.sh")
KSIEGA = os.path.join(S2, "kampania_ksiega.jsonl")
BUDZET = 4
NOGA_PRZED = 0                                     # NADIR-III: pierwszy boot nogi (budżet nogi ≤ 22)
BAZA = {"BOOT_NADIR_MODE": "1", "BOOT_KONT_MODE": "1", "BOOT_PASSTHROUGH": "0", "BOOT_LITERA": "NAD2", "BOOT_PUNKT": "P1",
        "BOOT_ZIARNO": "1", "NAD3_ETAP": "s2"}
LOTY = {"N1": {"nazwa": "n1_nominal", "epizody": "0,1,4,5", "inject": "-", "env": {**BAZA, "BOOT_DEGRAD": "0"}},
        "N2": {"nazwa": "n2_nominal", "epizody": "2,3,4,5", "inject": "-", "env": {**BAZA, "BOOT_DEGRAD": "0"}},
        "B3": {"nazwa": "b3_c05_bez_degradacji", "epizody": "4", "inject": "30", "env": {**BAZA, "BOOT_DEGRAD": "0"}},
        "B4": {"nazwa": "b4_c05_p1_na_zewnatrz", "epizody": "4", "inject": "30", "env": {**BAZA, "BOOT_DEGRAD": "na_zewnatrz"}}}
KOLEJNOSC = ("N1", "N2", "B3", "B4")


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
        try:
            r = B.przyrzad_a(tag, tel=bool(k))
        except Exception as ex:
            log(f"{name}: bramka zdrowia błąd {ex!r}")
            return None, proby
        p = {"tag": tag, "wariant": r["wariant"], "tempo": r["tempo"], "GO": r["GO"], "czolowka_operatora": r.get("czolowka_operatora"),
             "t": time.strftime("%F %T")}
        proby.append(p)
        with open(os.path.join(S2, "bramka_ksiega.jsonl"), "a") as f:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
        log(f"{name}: bramka zdrowia {tag} ({p['wariant']}) GO={p['GO']} tempo={p['tempo']}"
            + (f" — do zamknięcia: {p['czolowka_operatora']}" if p["czolowka_operatora"] else ""))
        if r["GO"]:
            return True, proby
    return False, proby


def boot(lot, bn):
    L = LOTY[lot]
    name = wolna(L["nazwa"])
    go, proby = bramka_zdrowia(name)
    if go is None:
        return "STOP-NAD3-2-BRAMKA", None
    if not go:
        return "NIEWAZNY-BRAMKA-ZDROWIA", {"nazwa": name, "lot": lot, "bramka_zdrowia": proby}
    ok, z = G.zegar(name)
    log(f"{name}: próbnik {z['skoki']} skoków ok={ok}")
    if not ok:
        return "STOP-NAD3-2-ZEGAR", None
    znal, zywe = G.sprzataj_sieroty()
    if zywe:
        return "STOP-NAD3-2-SIEROTY", None
    shm = G.shm_krok(name, False)
    env = {**os.environ, **L["env"], "PERC2_FASTDDS_PROFILE": G.PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
    tp = os.path.join(S2, f"{name}_host_telemetria.jsonl")
    tl = TL.Telemetria2(tp, 3600)
    t0 = time.time()
    try:
        for _ in range(4):
            r = subprocess.run(["bash", BOOT, str(bn), name, L["epizody"], L["inject"]], cwd=ROOT, env=env, capture_output=True, text=True)
            open(os.path.join(S2, f"{name}_driver.log"), "a").write(r.stdout + r.stderr)
            if r.returncode != 3:
                break
            log(f"{name}: env-block rc=3, nie boot, czekam 120 s"); time.sleep(120)
        else:
            return "STOP-NAD3-2-ENV", None
    finally:
        tl.close()
    if r.returncode in (4, 5, 6):
        log(f"{name}: guard rc={r.returncode}, stos nie ruszył, nie boot")
        return "STOP-NAD3-2-GUARD", None
    d = os.path.join(S2, name)
    if os.path.isdir(d) and os.path.exists(tp):
        os.replace(tp, os.path.join(d, "host_telemetria.jsonl"))
    try:
        kt = json.load(open(os.path.join(d, "kont_tempo.json")))
    except (OSError, ValueError):
        kt = None
    ev = []
    if os.path.exists(os.path.join(d, "trace.jsonl")):
        ev = [json.loads(l) for l in open(os.path.join(d, "trace.jsonl")) if '"event"' in l]
    names = [e.get("ev") for e in ev]
    n3 = next((e for e in ev if e.get("ev") == "nad3_degradacja"), None)
    wpis = {"boot_s2": bn, "lot": lot, "nazwa": name, "rc": r.returncode, "czas_s": round(time.time() - t0, 1), "tempo": kt,
            "bramka_tempa": kt is not None and not kt.get("ok"), "bramka_zdrowia": proby, "shm": shm,
            "epizod_wystartowal": "episode_start" in names,
            "breach": any(n in ("breach", "breach_gt") for n in names), "nad2_litera": next((e for e in ev if e.get("ev") == "nad2_litera"), None),
            "nad3_degradacja": n3, "t": time.strftime("%F %T")}
    with open(KSIEGA, "a") as f:
        f.write(json.dumps(wpis, ensure_ascii=False, default=str) + "\n")
    log(f"{name} rc={r.returncode} boot {bn} tempo={(kt or {}).get('dsim_dwall_settle')} breach={wpis['breach']} "
        f"litera={wpis['nad2_litera']} nad3={n3}")
    if r.returncode in (41, 42, 43, 44, 45):
        return f"STOP-NAD3-2-OSLONA-{r.returncode}", wpis
    if n3 is not None and not n3.get("zgodna"):
        return "STOP-NAD3-2-DEGRAD", wpis
    if wpis["bramka_tempa"] and not wpis["epizod_wystartowal"]:
        return "NIEWAZNY-TEMPO", wpis
    return None, wpis


def po_boocie(lot, name):
    d = os.path.join(S2, name)
    import nad2_ulg, nad3_analyze, nad3_s2_geom, nad3_s2_spr
    w = nad2_ulg.wyciag(d)
    log(f"{name}: wyciąg ULG {w}")
    a = nad3_analyze.analyze(d)
    wyn = {"analiza_bezpieczenstwo_ok": a.get("bezpieczenstwo_ok"), "wazny": a.get("wazny")}
    log(f"{name}: analizator ważny={a.get('wazny')} bezpieczeństwo_ok={a.get('bezpieczenstwo_ok')}")
    if lot in ("N1", "N2"):
        g = nad3_s2_geom.geometria(d)
        wyn["geometria"] = {"bramka_ok": g["bramka_ok"], "niespelnione": g["nominaly_niespelnione"],
                            "r_max": {e["scenario_id"]: e.get("r_max_gt") for e in g["epizody"]}}
        log(f"{name}: geometria {wyn['geometria']}")
    else:
        s = nad3_s2_spr.sprawdz(d, lot, "na_zewnatrz" if lot == "B4" else None)
        wyn["sprawdziany"] = {k: v.get("ok") for k, v in s.items() if isinstance(v, dict) and "ok" in v}
        wyn["b1_nieocenione"] = s["b1_nieocenione"]
        try:
            g = nad3_s2_geom.geometria(d)
            wyn["r_max_gt"] = {e["scenario_id"]: e.get("r_max_gt") for e in g["epizody"]}
        except Exception as ex:                            # noqa: BLE001 — obserwabla, nie bramka
            wyn["r_max_gt"] = repr(ex)
        log(f"{name}: sprawdziany {wyn['sprawdziany']} r_max {wyn['r_max_gt']}")
    return wyn


def main():
    sucho = "--sucho" in sys.argv[1:]
    os.makedirs(S2, exist_ok=True)
    ks = ksiega()
    zuzyte = [w for w in ks if w.get("epizod_wystartowal")]
    zrobione = {w["lot"] for w in zuzyte}
    niewazne = sum(1 for w in ks if not w.get("epizod_wystartowal"))
    plan = [l for l in KOLEJNOSC if l not in zrobione]
    log(f"=== NAD3 S2 {'(na sucho) ' if sucho else ''}start: zużyte {len(zuzyte)}/{BUDZET}, nieważne {niewazne}, plan {plan}")
    if sucho:
        print(json.dumps({"plan": plan, "uzyte": len(zuzyte), "budzet": BUDZET, "loty": LOTY}, ensure_ascii=False))
        return
    subprocess.run(["sudo", "-n", "systemctl", "stop", "systemd-timesyncd"], check=True)
    stop, wyniki, uzyte = None, {}, len(zuzyte)
    powtorki = {}
    nieocenione_geom = {}
    try:
        while plan:
            if uzyte >= BUDZET:
                stop = "STOP-NAD3-2-BUDZET"; break
            lot = plan[0]
            st, w = boot(lot, NOGA_PRZED + uzyte + 1)
            if st and st.startswith("NIEWAZNY"):
                powtorki[lot] = powtorki.get(lot, 0) + 1
                log(f"{lot}: boot nieważny stanowiskowo ({st}) — nie liczy się; powtórka {powtorki[lot]}/1")
                if powtorki[lot] > 1:
                    stop = "STOP-NAD3-2-STANOWISKO"; break
                continue
            if st:
                stop = st; break
            uzyte += 1
            wyniki[w["nazwa"]] = w
            if w["breach"]:
                stop = "STOP-NAD3-2-BREACH"; break
            plan.pop(0)
            p = po_boocie(lot, w["nazwa"])
            wyniki[w["nazwa"]]["po_boocie"] = p
            if lot in ("N1", "N2"):
                nieocenione_geom[lot] = p["geometria"]["niespelnione"]
                if not p["geometria"]["bramka_ok"]:
                    stop = "STOP-NAD3-2-GEOM"; break
                if sum(nieocenione_geom.values()) > 1:
                    stop = "STOP-NAD3-2-SMIERC-GEOM"; break
            else:
                s = p["sprawdziany"]
                if not s.get("replay", False):
                    stop = "STOP-NAD3-2-REPLAY"; break
                if not p["analiza_bezpieczenstwo_ok"]:
                    stop = "STOP-NAD3-2-FAIL"; break
                if not all(s.values()):
                    stop = "STOP-NAD3-2-SPRAWDZIAN"; break
                if lot == "B4" and isinstance(p["r_max_gt"], dict) and any((v or 0) > 19.5 for v in p["r_max_gt"].values()):
                    stop = "STOP-NAD3-2-RMAX"; break
    except Exception as ex:
        stop = "STOP-NAD3-2-WYJATEK"; log(f"ALARM {stop}: {ex!r}"); raise
    finally:
        subprocess.run(["sudo", "-n", "systemctl", "start", "systemd-timesyncd"])
        log(f"KONIEC booty={uzyte}/{BUDZET} stop={stop} pozostało={plan}")
        p = os.path.join(S2, "kampania_s2.json")
        prev = json.load(open(p)) if os.path.exists(p) else {"przebiegi": []}
        prev["przebiegi"].append({"booty": uzyte, "stop": stop, "wyniki": wyniki, "pozostalo": plan, "powtorki": powtorki})
        json.dump(prev, open(p, "w"), ensure_ascii=False, indent=1, default=str)
    print("KONIEC", uzyte, stop)


if __name__ == "__main__":
    main()
