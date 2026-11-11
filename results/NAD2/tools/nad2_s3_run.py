#!/usr/bin/env python3
"""results/NAD2/tools/nad2_s3_run.py — kolejka bramki S3 NADIR-II (PROMPT_NAD2_S3 §0.3, §R, §1; ≤ 19 bootów). Wzór
results/NAD2/tools/nad2_s2_run.py (stanowisko) i results/NADIR/tools/nadir_s4_campaign.py (siatka, kolejność, ważność) — oba
nietknięte; strażniki z kont_s2_campaign_g.py, stan/zdarzenia z kont_s4_campaign.py, bramka zdrowia nadir_s4_bramka.przyrzad_a,
telemetria nadir_s4_tel — import READ-ONLY, ścieżki przestawione na results/NAD2/s3 w tym procesie.

Kod lotu bez zmian (§0.2): boot = results/NAD2/tools/nad2_boot.sh z bd975df5 (katalog results/NAD2/s2 wpisany w skrypt) wołany
z nazwą „../s3/<pozycja>” ⇒ OUTDIR = results/NAD2/s2/../s3/<pozycja> = results/NAD2/s3/<pozycja>; dopiski bootu do
results/NAD2/s2/nad2_s2_monitor.log (artefakt smoke) kolejka przenosi po każdym boocie do results/NAD2/s3/nad2_s3_monitor.log
i przywraca plik smoke do długości sprzed bootu.
Siatka (§R): nom_b1, 12 cięć (c01_s01 … c11_s02, epizod (s−1)·12 + c, KONT_INJECT_T 30), nom_b2–nom_b4 (epizody 4i…4i+3) —
kolejność jak NADIR S4; wszystkie booty BOOT_NADIR_MODE=1, BOOT_KONT_MODE=1, BOOT_PASSTHROUGH=0, BOOT_LITERA=NAD2. Kolejka =
siatka minus pozycje z bootem ważnym (księga results/NAD2/s3/kampania_ksiega.jsonl, wiersz per zużyty boot).
Stanowisko (§0.3): przed każdym bootem bramka zdrowia (A, GO ⇔ tempo ≥ 0.90; NO-GO ⇒ 3 min ⇒ C; trzecie NO-GO z rzędu ⇒
STOP-NAD2-3-STANOWISKO, nic nie zużyte), timesyncd zatrzymany na starcie i wznawiany na końcu, telemetria w tle; bramka tempa
bootu 0.93 (przerwanie = boot zużyty, nieważny).
Ważność bootu jak NADIR S4: bramka tempa, faza, asercja yaw, sonda, komplet epizodów (cięcie: denial + przyziemienie), analizator.
Boot nieważny ⇒ dolecenie pozycji z rezerwy, dopóki siatka mieści się w budżecie; inaczej STOP-NAD2-3-BUDZET.
Po każdym boocie: wyciąg ULG (nad2_ulg), analizator (nad2_analyze: B1–B5, D1), sprawdziany (nad2_s3_spr: (s1), (s2) — poniżej
100% ⇒ STOP-NAD2-3-PRZYRZAD). STOPy globalne verbatim: breach ⇒ STOP; REFUSE(POS) fałszywy ⇒ STOP; budżet ⇒ STOP (breach =
zdarzenie breach drivera albo B2 margines ≤ 0; REFUSE(POS) fałszywy = przed cięciem / w nominale, z trace albo analizatora).
Naruszenie litery B1–B5 / D1 nie jest STOPem: zapis, kampania dolatuje siatkę.
Po STOP-NAD2-3-GUARD (decyzja Olgi 12.11): env-block (rc 3, nie boot) ⇒ kolejna próba pod wolną nazwą (stub launchera zostaje), ≤ 4.
Użycie: nad2_s3_run.py [--sucho]   (--sucho: plan i stan księgi, 0 bootów). Wyjście: kampania_s3.log, kampania_s3.json.
"""
import json
import os
import subprocess
import sys
import time

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [os.path.join(ROOT, "results/KONT/tools"), os.path.join(ROOT, "results/NADIR/tools"), os.path.join(ROOT, "results/NAD2/tools"), ROOT]
import kont_s4_campaign as K                       # READ-ONLY: stan, zdarzenia (import przestawia G — niżej z powrotem)
import kont_s2_campaign_g as G                     # READ-ONLY
import nadir_s4_tel as TL                          # READ-ONLY

S3 = os.path.join(ROOT, "results/NAD2/s3")
G.S2 = S3
G.LOG = os.path.join(S3, "kampania_s3.log")
G.SKRYPTY = G.SKRYPTY | {"kont_s4_flight", "nadir_s4_flight", "nad2_flight", "intruder_motion", "nadir_obs"}
log = G.log
BOOT = os.path.join(ROOT, "results/NAD2/tools/nad2_boot.sh")
MON_S2 = os.path.join(ROOT, "results/NAD2/s2/nad2_s2_monitor.log")
MON_S3 = os.path.join(S3, "nad2_s3_monitor.log")
KSIEGA = os.path.join(S3, "kampania_ksiega.jsonl")
BUDZET, NOGA_PRZED, NOGA_MAX = 19, 2, 22
ENV_BOOT = {"BOOT_NADIR_MODE": "1", "BOOT_KONT_MODE": "1", "BOOT_PASSTHROUGH": "0", "BOOT_LITERA": "NAD2"}
CIECIA = ["c01_s01", "c01_s03", "c02_s01", "c02_s03", "c05_s01", "c05_s02", "c08_s01", "c08_s02", "c10_s01", "c10_s02",
          "c11_s01", "c11_s02"]
EPID = lambda sc: (int(sc[5:7]) - 1) * 12 + int(sc[1:3])          # = kont_s4_campaign.EPID


def plan():
    man = json.load(open(os.path.join(ROOT, "results/NADIR/s4/scenario_manifest_s4.json")))["episodes"]
    ciecia = [(sc, str(EPID(sc)), "30") for sc in CIECIA]
    for sc, e, _ in ciecia:
        assert man[int(e)]["scenario_id"] == sc
    nom = [(f"nom_b{i + 1}", ",".join(str(4 * i + j) for j in range(4)), "-") for i in range(4)]
    return [nom[0]] + ciecia + nom[1:]


def ksiega():
    return [json.loads(l) for l in open(KSIEGA) if l.strip()] if os.path.exists(KSIEGA) else []


def wolna_nazwa(nm):
    """Jak nadir_s4_campaign.wolna_nazwa (w results/NAD2/s3)."""
    zajete = os.listdir(S3)
    n = 1
    while True:
        c = nm if n == 1 else f"{nm}_r{n}"
        if not any(f == c or f.startswith(c + "_") or f.startswith(c + ".") or f.endswith("_" + c + ".jsonl") or f.endswith("_" + c + ".txt")
                   for f in zajete):
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


def przenies_monitor(n0):
    """Dopiski nad2_boot.sh do monitora smoke ⇒ monitor S3; plik smoke wraca do długości n0."""
    if not os.path.exists(MON_S2) or os.path.getsize(MON_S2) <= n0:
        return
    with open(MON_S2, "rb") as f:
        f.seek(n0)
        nowe = f.read()
    with open(MON_S3, "ab") as f:
        f.write(nowe)
    os.truncate(MON_S2, n0)


def po_boocie(d, nominal):
    import nad2_ulg, nad2_analyze, nad2_s3_spr
    out = {}
    try:
        out["ulg"] = nad2_ulg.wyciag(d)
    except AssertionError as ex:
        out["ulg"] = {"ponad_limit": repr(ex), "plik": os.path.join(d, "ulg.jsonl.gz")}
    log(f"{os.path.basename(d)}: wyciąg ULG {out['ulg']}")
    out["an"] = nad2_analyze.analyze(d)
    out["spr"] = nad2_s3_spr.sprawdz(d, nominal)
    return out


def main():
    sucho = "--sucho" in sys.argv[1:]
    os.makedirs(S3, exist_ok=True)
    ks = ksiega()
    wazne = {w["pozycja"] for w in ks if w.get("wazny")}
    uzyte = len(ks)
    kolejka = [p for p in plan() if p[0] not in wazne]
    log(f"=== NAD2 S3 {'(na sucho) ' if sucho else ''}start: księga {uzyte} bootów, ważne {sorted(wazne)}; kolejka {[k[0] for k in kolejka]}; "
        f"budżet {uzyte}/{BUDZET}, noga {NOGA_PRZED + uzyte}/{NOGA_MAX}")
    if sucho:
        print(json.dumps({"kolejka": kolejka, "uzyte": uzyte, "budzet": BUDZET, "wazne": sorted(wazne), "env": ENV_BOOT}, ensure_ascii=False))
        return
    subprocess.run(["sudo", "-n", "systemctl", "stop", "systemd-timesyncd"], check=True)
    stop, booty, wyniki = None, uzyte, {}
    try:
        while kolejka:
            if booty + len(kolejka) > BUDZET:
                stop = "STOP-NAD2-3-BUDZET"
                log(f"ALARM {stop}: {len(kolejka)} pozycji, {BUDZET - booty} bootów w budżecie")
                break
            nm, epids, inj = kolejka[0]
            nominal = inj == "-"
            name = wolna_nazwa(nm)
            go, proby = bramka_zdrowia(name)
            if go is None:
                stop = "STOP-NAD2-3-BRAMKA"; break
            if not go:
                stop = "STOP-NAD2-3-STANOWISKO"
                log(f"ALARM {stop}: {name} — trzecie NO-GO bramki zdrowia z rzędu, boot nie startował, nic nie zużyte")
                break
            ok, z = G.zegar(name)
            log(f"{name}: próbnik {z['skoki']} skoków ok={ok}")
            if not ok:
                stop = "STOP-NAD2-3-ZEGAR"; break
            znal, zywe = G.sprzataj_sieroty()
            if znal:
                log(f"{name}: sieroty TERM {znal}, żywe po {G.TERM_WAIT_S} s: {zywe}")
            if zywe:
                stop = "STOP-NAD2-3-SIEROTY"; break
            shm = G.shm_krok(name, False)
            env = {**os.environ, **ENV_BOOT, "PERC2_FASTDDS_PROFILE": G.PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
            tp = os.path.join(S3, f"{name}_host_telemetria.jsonl")
            tl = TL.Telemetria2(tp, 3600)
            t0 = time.time()
            try:
                for k in range(4):
                    if k:                              # env-block launchera zostawia stub manifestu ⇒ wolna nazwa (STOP-NAD2-3-GUARD)
                        name = wolna_nazwa(nm)
                        log(f"{nm}: po env-blocku próba {k + 1} pod nazwą {name}")
                    n0 = os.path.getsize(MON_S2) if os.path.exists(MON_S2) else 0
                    r = subprocess.run(["bash", BOOT, str(NOGA_PRZED + booty + 1), f"../s3/{name}", epids, inj], cwd=ROOT, env=env,
                                       capture_output=True, text=True)
                    przenies_monitor(n0)
                    open(os.path.join(S3, f"{name}_driver.log"), "a").write(r.stdout + r.stderr)
                    if r.returncode != 3:
                        break
                    log(f"{name}: env-block rc=3, nie boot, czekam 120 s"); time.sleep(120)
                else:
                    stop = "STOP-NAD2-3-ENV"; break
            finally:
                tl.close()
            if r.returncode in (4, 5, 6):
                stop = "STOP-NAD2-3-GUARD"
                log(f"ALARM {stop}: {name} rc={r.returncode}, stos nie ruszył, nie boot")
                break
            booty += 1
            kolejka.pop(0)
            d = os.path.join(S3, name)
            if os.path.isdir(d):
                os.replace(tp, os.path.join(d, "host_telemetria.jsonl"))
            s, e = K.stan(d), K.zdarzenia(d)
            try:
                kt = json.load(open(os.path.join(d, "kont_tempo.json")))
            except (OSError, ValueError):
                kt = None
            niewazny = None
            want = len(epids.split(","))
            if r.returncode == 9 or (kt is not None and not kt.get("ok")):
                niewazny = f"bramka tempa {(kt or {}).get('dsim_dwall_settle')}"
            elif not s["faza"]:
                niewazny = "faza"
            elif s["yaw"] is not None and not s["yaw"].get("ok"):
                niewazny = "asercja yaw"
            elif not s["uzb"]:
                niewazny = "sonda pod podłogą"
            elif e["episode_end"] < want or (not nominal and not (e["cut"] and e["przyziemienie"])):
                niewazny = f"epizody {e['episode_end']}/{want}, cięcie {e['cut']}, przyziemienie {e['przyziemienie']}"
            po, an, spr = None, None, None
            if e["episode_start"]:
                try:
                    po = po_boocie(d, nominal)
                    an, spr = po["an"], po["spr"]
                except Exception as ex:
                    stop = "STOP-NAD2-3-ANALIZA"
                    log(f"ALARM {stop}: {name} {ex!r}")
            if niewazny is None and (an is None or not an.get("wazny")):
                niewazny = f"analiza: {(an or {}).get('powod_niewazny')}"
            epi = [{k: o.get(k) for k in ("episode_id", "scenario_id", "bezpieczenstwo_ok", "D1")} |
                   {b: o[b]["ok"] for b in ("B1", "B2", "B3", "B4", "B5") if b in o} for o in (an or {}).get("epizody", [])]
            b2_breach = any(o.get("B2") is False for o in epi)
            pos_fals = sum(o["B4"]["refuse_pos_falszywe"] for o in (an or {}).get("epizody", []))
            wpis = {"boot_s3": booty, "boot_noga": NOGA_PRZED + booty, "pozycja": nm, "nazwa": name, "epizody": epids, "inject_t": inj,
                    "rc": r.returncode, "czas_s": round(time.time() - t0, 1), "tempo": kt, "wazny": niewazny is None, "niewazny": niewazny,
                    "epizody_wyniki": epi, "bezpieczenstwo_ok": (an or {}).get("bezpieczenstwo_ok"),
                    "sprawdziany": (spr or {}).get("ok"), "przyrzad_ok": (spr or {}).get("przyrzad_ok"),
                    "ulg": (po or {}).get("ulg"), "breach": e["breach"] or b2_breach, "refuse_pos_nominal": e["refuse_pos_nominal"],
                    "refuse_pos_falszywe_analizator": pos_fals, "shm": shm, "bramka_zdrowia": proby,
                    "sieroty_term": {str(k): v for k, v in znal.items()}, "t": time.strftime("%F %T")}
            with open(KSIEGA, "a") as f:
                f.write(json.dumps(wpis, ensure_ascii=False, default=str) + "\n")
            wyniki[name] = wpis
            log(f"{name} rc={r.returncode} boot {booty}/{BUDZET} (noga {NOGA_PRZED + booty}/{NOGA_MAX}): tempo={(kt or {}).get('dsim_dwall_settle')} "
                f"ważny={niewazny is None} ({niewazny}) epizody={epi} sprawdziany={wpis['sprawdziany']} breach={wpis['breach']} "
                f"REFUSE(POS) fałszywe={len(e['refuse_pos_nominal'])}/{pos_fals}")
            if stop:
                break
            if wpis["breach"]:
                stop = "STOP-NAD2-3-BREACH"; break
            if e["refuse_pos_nominal"] or pos_fals:
                stop = "STOP-NAD2-3-REFUSE-POS"; break
            if niewazny is None and not wpis["przyrzad_ok"]:
                stop = "STOP-NAD2-3-PRZYRZAD"
                log(f"ALARM {stop}: {name} sprawdziany {wpis['sprawdziany']} poniżej 100%")
                break
            if niewazny:
                kolejka.insert(0, (nm, epids, inj))
                log(f"{name} nieważny ({niewazny}) — dolecenie {nm} (rezerwa po nim: {BUDZET - booty - len(kolejka)})")
    except Exception as ex:
        stop = "STOP-NAD2-3-WYJATEK"; log(f"ALARM {stop}: {ex!r}"); raise
    finally:
        subprocess.run(["sudo", "-n", "systemctl", "start", "systemd-timesyncd"])
        log(f"KONIEC booty={booty}/{BUDZET} noga={NOGA_PRZED + booty}/{NOGA_MAX} stop={stop} pozostało={[k[0] for k in kolejka]}")
        p = os.path.join(S3, "kampania_s3.json")
        prev = json.load(open(p)) if os.path.exists(p) else {"przebiegi": []}
        prev["przebiegi"].append({"booty": booty, "noga": NOGA_PRZED + booty, "stop": stop, "wyniki": wyniki, "pozostalo": kolejka})
        json.dump(prev, open(p, "w"), ensure_ascii=False, indent=1, default=str)
    print("KONIEC", booty, stop)


if __name__ == "__main__":
    main()
