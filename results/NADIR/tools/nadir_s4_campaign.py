#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s4_campaign.py — kolejka S4 NADIR (PROMPT_NADIR_S4 §R, §1, §2). Wzór kont_s4_campaign_f.py (nietknięty);
strażniki stanowiska importem z kont_s2_campaign_g.py (zegar 60 s, sieroty po PID, /dev/shm; ścieżki modułu przestawione na
results/NADIR/s4 w tym procesie), stan/zdarzenia bootu z kont_s4_campaign.py (READ-ONLY). Boot: nadir_s4_boot.sh (NADIR_MODE=1).

Siatka (PROMPT_NADIR_S4 §R): 12 cięć 1/boot — c01_s01, c01_s03, c02_s01, c02_s03, c05_s01, c05_s02, c08_s01, c08_s02, c10_s01,
c10_s02, c11_s01, c11_s02 (KONT_INJECT_T = 30 s po t_entry, jak KONT S4) + 4 nominały nom_b1…nom_b4 = epizody 4i…4i+3 (i = 0…3;
nom_b1–b3 = ramię (−) KONT S4, nom_b4 = c00–c03_s02, ta sama reguła). Kolejność jak KONT S4: nom_b1, 12 cięć, nom_b2–b4.
Kolejka = siatka minus pozycje z bootem ważnym (z dysku: results/NADIR/s4/kampania_ksiega.jsonl, append-only, wiersz per zużyty
boot) — lekcja kolejki f. Budżet S4 ≤ 16 bootów z księgi, zero rezerwy etapu; po STOP-NADIR4-BUDZET (5eb4c14c) sygnałem Olgi
+2 z luzu nogi ⇒ BUDZET 18 (noga ≤ 30): boot nieważny ⇒ dolecenie tej pozycji, dopóki siatka mieści się w budżecie;
2 kolejne przerwania bramką tempa ⇒ STOP-NADIR4-STANOWISKO (wzór kolejki f).

STOPy: breach ⇒ STOP-NADIR4-BREACH; REFUSE(POS) przed cięciem albo w nominale ⇒ STOP-NADIR4-REFUSE-NOMINAL; budżet ⇒
STOP-NADIR4-BUDZET — (przed rezerwą) każdy boot nieważny (bramka tempa, faza, asercja yaw, sonda, analiza: V2′/zegar/
selftest/xy_valid, niekompletne epizody) kończy kolejkę tym STOPem (rezerwa wyłącznie z luzu nogi za sygnałem Olgi); bramka
tempa w pierwszym boocie po restarcie WSL (uptime < 3600 s przy starcie kolejki) ⇒ STOP-NADIR4-STANOWISKO; strażniki: zegar,
sieroty, env-block ×4 (rc 3, nie boot), guard rc 4/5/6 (nie boot), wyjątek analizy ⇒ STOP-NADIR4-ANALIZA (boot zużyty, dane
zostają). Naruszenie litery (a)–(g) NIE jest STOPem (PROMPT_NADIR_S4 §2: FAIL nogi zapisany, kampania dolatuje siatkę).
ANEKS_NADIR-4 (po „ratyfikuję N3"): przed każdym bootem bramka zdrowia §3.1 = nadir_s4_bramka.py bramka (przyrząd A, GO ⇔ tempo
≥ 0.90; NO-GO ⇒ boot nie startuje, nic nie zużyte, po 3 min powtórka w wariancie C; trzecie NO-GO z rzędu ⇒ STOP-NADIR4-STANOWISKO;
błąd przyrządu ⇒ STOP-NADIR4-BRAMKA); próby w bramka_ksiega.jsonl. W tle każdego bootu telemetria §3.3 (nadir_s4_tel.Telemetria2)
⇒ <boot>/host_telemetria.jsonl, podsumowanie w wierszu księgi. Bramka tempa w boocie 0.93 bez zmian.
Użycie: nadir_s4_campaign.py [--sucho]  (--sucho: plan, księga, budżet; 0 bootów). Wyjście: kampania_s4.json, kampania_s4.log.
"""
import json
import os
import subprocess
import sys
import time

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [os.path.join(ROOT, "results/KONT/tools"), os.path.join(ROOT, "results/NADIR/tools"), ROOT]
import kont_s4_campaign as K                       # READ-ONLY: stan, zdarzenia (import przestawia G na KONT/s4 — niżej z powrotem)
import kont_s2_campaign_g as G
import nadir_s4_tel as TL                          # ANEKS_NADIR-4 §3.3

S4 = os.path.join(ROOT, "results/NADIR/s4")
G.S2 = S4
G.LOG = os.path.join(S4, "kampania_s4.log")
G.SKRYPTY = G.SKRYPTY | {"kont_s4_flight", "nadir_s2_flight", "nadir_s3_flight", "nadir_s4_flight", "intruder_motion", "nadir_obs"}
log, zegar, sprzataj_sieroty, shm_krok = G.log, G.zegar, G.sprzataj_sieroty, G.shm_krok
PROFIL = G.PROFIL
BOOT = os.path.join(ROOT, "results/NADIR/tools/nadir_s4_boot.sh")
KSIEGA = os.path.join(S4, "kampania_ksiega.jsonl")
BUDZET, NOGA_PRZED, NOGA_MAX = 24, 11, 35            # ANEKS_NADIR-3 §4.4 po „ratyfikuję N3" (10.11): 16 zużytych w nodze + 15 pozycji + 4 rezerwy; było 19/30
BRAMKA = os.path.join(ROOT, "results/NADIR/tools/nadir_s4_bramka.py")
BRAMKA_KSIEGA = os.path.join(S4, "bramka_ksiega.jsonl")
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
    if not os.path.exists(KSIEGA):
        return []
    return [json.loads(l) for l in open(KSIEGA) if l.strip()]


def wolna_nazwa(nm):
    """Jak kont_s4_campaign_f.wolna_nazwa: nazwa zajęta także przez pliki tej nazwy."""
    zajete = os.listdir(S4)
    n = 1
    while True:
        c = nm if n == 1 else f"{nm}_r{n}"
        if not any(f == c or f.startswith(c + "_") or f.startswith(c + ".") or f.endswith("_" + c + ".jsonl") or f.endswith("_" + c + ".txt")
                   for f in zajete):
            return c
        n += 1


def bramka_zdrowia(name):
    """ANEKS_NADIR-4 §3.1: A; NO-GO ⇒ 3 min ⇒ C; trzecie NO-GO z rzędu ⇒ False. Błąd przyrządu (rc 2) ⇒ None."""
    proby = []
    for k in range(3):
        if k:
            time.sleep(180)
        tag = f"{name}_g{k + 1}"
        r = subprocess.run([sys.executable, BRAMKA, "bramka", tag] + (["--tel"] if k else []), cwd=ROOT, capture_output=True, text=True)
        try:
            b = json.load(open(os.path.join(S4, "bramka", tag, "bramka.json")))
        except (OSError, ValueError):
            b = {}
        p = {"pozycja_nazwa": name, "tag": tag, "wariant": "C" if k else "A", "rc": r.returncode, "tempo": b.get("tempo"),
             "czolowka_operatora": b.get("czolowka_operatora"), "t": time.strftime("%F %T")}
        proby.append(p)
        with open(BRAMKA_KSIEGA, "a") as f:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
        log(f"{name}: bramka zdrowia {tag} ({p['wariant']}) rc={r.returncode} tempo={p['tempo']}"
            + (f" — do zamknięcia: GPU {p['czolowka_operatora']['gpu']} CPU {p['czolowka_operatora']['cpu']}" if p["czolowka_operatora"] else ""))
        if r.returncode == 0:
            return True, proby
        if r.returncode != 1:
            log(f"{name}: bramka zdrowia błąd: {(r.stdout + r.stderr)[-800:]}")
            return None, proby
    return False, proby


def tel_skrot(tp):
    try:
        t = TL.podsumuj(tp)
    except Exception as ex:
        return {"blad": repr(ex)}
    g = t.get("gpu", {})
    return {"gpu_n": g.get("n"), "pstate": g.get("pstate_udzial"), "sm_med": g.get("sm_med"), "moc_med": g.get("moc_med"),
            "flaga_0x4": g.get("flaga_0x4_udzial"), "gpuproc": t.get("gpuproc", {}).get("czolowka"), "win": t.get("win", {}).get("czolowka"),
            "kadencja_win_s": t.get("win", {}).get("kadencja_med_s")}


def wpis_manifest(d, wpis):
    p = os.path.join(d, "manifest.json")
    if os.path.exists(p):
        m = json.load(open(p))
        m["nadir_s4_kampania"] = wpis
        json.dump(m, open(p, "w"), indent=2, ensure_ascii=False)


def main():
    sucho = "--sucho" in sys.argv[1:]
    os.makedirs(S4, exist_ok=True)
    ks = ksiega()
    wazne = {w["pozycja"] for w in ks if w.get("wazny")}
    uzyte = len(ks)
    kolejka = [p for p in plan() if p[0] not in wazne]
    uptime0 = float(open("/proc/uptime").read().split()[0])
    log(f"=== S4 NADIR {'(na sucho) ' if sucho else ''}start: księga {uzyte} bootów, ważne {sorted(wazne)}; kolejka {[k[0] for k in kolejka]}; "
        f"budżet {uzyte}/{BUDZET}, noga {NOGA_PRZED + uzyte}/{NOGA_MAX}, uptime {uptime0:.0f} s")
    if sucho:
        print(json.dumps({"kolejka": kolejka, "uzyte": uzyte, "budzet": BUDZET, "wazne": sorted(wazne)}, ensure_ascii=False))
        return
    env = {**os.environ, "PERC2_FASTDDS_PROFILE": PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
    subprocess.run(["sudo", "-n", "systemctl", "stop", "systemd-timesyncd"], check=True)
    import nadir_s4_analyze as A
    stop, booty, wyniki, pierwszy, tempo_streak = None, uzyte, {}, True, 0
    try:
        while kolejka:
            if booty >= BUDZET:
                stop = "STOP-NADIR4-BUDZET"
                break
            if booty + len(kolejka) > BUDZET:
                stop = "STOP-NADIR4-BUDZET"
                log(f"ALARM {stop}: {len(kolejka)} pozycji, {BUDZET - booty} bootów w budżecie")
                break
            nm, epids, inj = kolejka[0]
            name = wolna_nazwa(nm)
            go, proby = bramka_zdrowia(name)
            if go is None:
                stop = "STOP-NADIR4-BRAMKA"
                break
            if not go:
                stop = "STOP-NADIR4-STANOWISKO"
                log(f"ALARM {stop}: {name} — trzecie NO-GO bramki zdrowia z rzędu (§3.1), boot nie startował, nic nie zużyte")
                break
            ok, z = zegar(name)
            log(f"{name}: próbnik {z['skoki']} skoków ok={ok}")
            if not ok:
                stop = "STOP-NADIR4-ZEGAR"
                break
            znal, zywe = sprzataj_sieroty()
            if znal:
                log(f"{name}: sieroty TERM {znal}, żywe po {G.TERM_WAIT_S} s: {zywe}")
            if zywe:
                stop = "STOP-NADIR4-SIEROTY"
                break
            shm = shm_krok(name, False)
            tp = os.path.join(S4, f"{name}_host_telemetria.jsonl")
            tl = TL.Telemetria2(tp, 3600)
            try:
                for _ in range(4):
                    r = subprocess.run(["bash", BOOT, str(NOGA_PRZED + booty + 1), name, epids, inj], cwd=ROOT, env=env,
                                       capture_output=True, text=True)
                    open(os.path.join(S4, f"{name}_driver.log"), "a").write(r.stdout + r.stderr)
                    if r.returncode != 3:
                        break
                    log(f"{name}: env-block rc=3, nie boot, czekam 120 s")
                    time.sleep(120)
                else:
                    stop = "STOP-NADIR4-ENV"
                    break
            finally:
                tl.close()
            if r.returncode in (4, 5, 6):
                stop = "STOP-NADIR4-GUARD"
                log(f"ALARM {stop}: {name} rc={r.returncode}, stos nie ruszył, nie boot")
                break
            booty += 1
            kolejka.pop(0)
            d = os.path.join(S4, name)
            if os.path.isdir(d):
                os.replace(tp, os.path.join(d, "host_telemetria.jsonl"))
                tp = os.path.join(d, "host_telemetria.jsonl")
            s, e = K.stan(d), K.zdarzenia(d)
            try:
                kt = json.load(open(os.path.join(d, "kont_tempo.json")))
            except (OSError, ValueError):
                kt = None
            an = None
            if e["episode_start"]:
                try:
                    an = A.analyze(d)
                except Exception as ex:
                    stop = "STOP-NADIR4-ANALIZA"
                    log(f"ALARM {stop}: {name} {ex!r}")
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
            elif e["episode_end"] < want or (inj != "-" and not (e["cut"] and e["przyziemienie"])):
                niewazny = f"epizody {e['episode_end']}/{want}, cięcie {e['cut']}, przyziemienie {e['przyziemienie']}"
            elif an is None or not an.get("wazny"):
                niewazny = f"analiza: {(an or {}).get('powod_niewazny')}"
            lit = {o["scenario_id"]: {k: o.get(k) for k in ("a_ok", "b_ok", "c_ok", "d_ok", "e_ok", "f_ok", "g_ok", "litera_ok")}
                   for o in (an or {}).get("epizody", [])}
            wpis = {"boot_s4": booty, "boot_noga": NOGA_PRZED + booty, "pozycja": nm, "nazwa": name, "epizody": epids, "inject_t": inj,
                    "rc": r.returncode, "tempo": kt, "wazny": niewazny is None, "niewazny": niewazny, "litera": lit,
                    "litera_ok": (an or {}).get("litera_ok"), "breach": e["breach"], "refuse_pos_nominal": e["refuse_pos_nominal"],
                    "shm": shm, "bramka_zdrowia": proby, "tel": tel_skrot(tp), "sieroty_term": {str(k): v for k, v in znal.items()}, "t": time.strftime("%F %T")}
            with open(KSIEGA, "a") as f:
                f.write(json.dumps(wpis, ensure_ascii=False) + "\n")
            wpis_manifest(d, wpis)
            wyniki[name] = {**wpis, **s, **e}
            log(f"{name} rc={r.returncode} boot {booty}/{BUDZET} (noga {NOGA_PRZED + booty}/{NOGA_MAX}): tempo={(kt or {}).get('dsim_dwall_settle')} "
                f"ważny={niewazny is None} ({niewazny}) litera={lit} epizody {e['episode_start']}/{e['episode_end']} cięcie={e['cut']} "
                f"przyziemienie={e['przyziemienie']} breach={e['breach']} REFUSE(POS)_nominal={e['refuse_pos_nominal']}")
            if stop:
                break
            if e["breach"]:
                stop = "STOP-NADIR4-BREACH"
                break
            if e["refuse_pos_nominal"]:
                stop = "STOP-NADIR4-REFUSE-NOMINAL"
                break
            tempo_streak = tempo_streak + 1 if (niewazny or "").startswith("bramka tempa") else 0
            if niewazny:
                kolejka.insert(0, (nm, epids, inj))
                if niewazny.startswith("bramka tempa") and pierwszy and uptime0 < 3600:
                    stop = "STOP-NADIR4-STANOWISKO"
                    log(f"ALARM {stop}: {name} {niewazny} — pierwszy boot po restarcie WSL")
                elif tempo_streak >= 2:
                    stop = "STOP-NADIR4-STANOWISKO"
                    log(f"ALARM {stop}: {name} — 2 kolejne przerwania bramką tempa")
                elif booty + len(kolejka) > BUDZET:
                    stop = "STOP-NADIR4-BUDZET"
                    log(f"ALARM {stop}: {name} nieważny ({niewazny}), budżet wyczerpany bez kompletu siatki")
                else:
                    log(f"{name} nieważny ({niewazny}) — dolecenie {nm} (rezerwa: {BUDZET - booty - len(kolejka)} po nim)")
                if stop:
                    break
            pierwszy = False
        if stop is None and kolejka:
            stop = "STOP-NADIR4-BUDZET"
    except Exception as ex:
        stop = "STOP-NADIR4-WYJATEK"
        log(f"ALARM {stop}: {ex!r}")
        raise
    finally:
        subprocess.run(["sudo", "-n", "systemctl", "start", "systemd-timesyncd"])
        log(f"KONIEC booty={booty}/{BUDZET} noga={NOGA_PRZED + booty}/{NOGA_MAX} stop={stop} pozostało={[k[0] for k in kolejka]}")
        p = os.path.join(S4, "kampania_s4.json")
        prev = json.load(open(p)) if os.path.exists(p) else {"przebiegi": []}
        prev["przebiegi"].append({"start_uptime_s": uptime0, "booty": booty, "noga": NOGA_PRZED + booty, "wyniki": wyniki, "stop": stop,
                                  "pozostalo": kolejka})
        json.dump(prev, open(p, "w"), ensure_ascii=False, indent=1, default=str)
    print("KONIEC", booty, stop)


if __name__ == "__main__":
    main()
