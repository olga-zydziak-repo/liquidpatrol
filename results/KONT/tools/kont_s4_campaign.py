#!/usr/bin/env python3
"""results/KONT/tools/kont_s4_campaign.py — kolejka S4 (PROMPT_KONT_S4 §0–§2). Strażniki ANEKS_KONT-1b (sieroty po PID z inwentarza,
/dev/shm, próbnik zegara 60 s, nazwy REPO-2) importem z kont_s2_campaign_g.py (oryginał nietknięty; ścieżki modułu przestawione
na results/KONT/s4 w tym procesie). Boot: kont_s4_boot.sh (launcher s2y). timesyncd stop na sesję, start zawsze na końcu.

Siatka (z pliku, nie z pamięci): results/KONT_RECON/r4_margin.json, margines komórki = min m po jej scenariuszach (ten sam zbiór
daje min po ziarnach s01/s02); 4 komórki o najmniejszym m + 2 najbliżej mediany m p50; ziarna s01 i s02 jak kampania K2
(results/K2/k2_campaign.json). Cięcie: KONT_INJECT_T = 30 s (t_entry + 30, jak K2). Nominał: 3 booty × 4 epizody c00–c11_s01
(wzór K4b, results/K2/RAPORT_K4b.md). Kolejność: nominał b1, 12 cięć, nominał b2, b3.

Twarde STOPy (§2): breach (GT albo r_est > R_E) ⇒ STOP; REFUSE(POS) w nominale (boot nominalny albo faza przed cięciem) ⇒ STOP;
REFUSE(GEOFENCE) z reguły R-G (nie R-G-NOM) ⇒ STOP; budżet 16 ⇒ STOP. Strażniki stanowiska: zegar, sieroty, env-block ×4, guard
rc 4/5/6, faza < 0.5 s dwa razy z rzędu, sonda pod podłogą dwa razy z rzędu. Boot nieważny (asercja yaw, faza, sonda, brak
epizodu) ⇒ jedno dolecenie tej pozycji w budżecie. Wyjście: results/KONT/s4/kampania_s4.json, kampania_s4.log."""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kont_s2_campaign_g as G

ROOT, T, PROFIL = G.ROOT, G.T, G.PROFIL
S4 = os.path.join(ROOT, "results/KONT/s4")
G.S2 = S4                                         # zegar/shm_krok/wolna_nazwa piszą do s4 (ten proces)
G.LOG = os.path.join(S4, "kampania_s4.log")
G.SKRYPTY = G.SKRYPTY | {"kont_s4_flight", "intruder_motion"}
from kont_s2_campaign_g import log, zegar, sprzataj_sieroty, shm_krok, wolna_nazwa, wpis_manifest

BUDZET, NOGA_PRZED = 16, 24
EPID = lambda sc: (int(sc[5:7]) - 1) * 12 + int(sc[1:3])


def siatka():
    d = json.load(open(os.path.join(ROOT, "results/KONT_RECON/r4_margin.json")))
    tab, p50 = d["tabela_scenariuszy"], d["m"]["p50"]
    kom = {}
    for sc, v in tab.items():
        kom[sc[:3]] = min(kom.get(sc[:3], 1e9), v["m"])
    low = sorted(kom, key=lambda c: (kom[c], c))[:4]
    med = sorted((c for c in kom if c not in low), key=lambda c: (abs(kom[c] - p50), c))[:2]
    return low, med, kom, p50


def plan():
    low, med, kom, p50 = siatka()
    ciecia = [(f"{c}_{s}", str(EPID(f"{c}_{s}")), "30") for c in low + med for s in ("s01", "s02")]
    nom = [(f"nom_b{i + 1}", ",".join(str(4 * i + j) for j in range(4)), "-") for i in range(3)]
    return [nom[0]] + ciecia + nom[1:], {"komorki_niski_m": low, "komorki_mediana": med, "m_komorki": kom, "m_p50": p50}


def stan(d):
    out = {"uzb": False, "faza": False, "t0": None, "yaw": None}
    try:
        m = json.load(open(os.path.join(d, "manifest.json")))
        out["uzb"] = bool(m["kont_s4"].get("uzbrojony"))
        out["faza"] = bool(m["kont_s2d"].get("faza_ok"))
        out["t0"] = m["kont_s2d"].get("initial_absolute_time_us")
    except (OSError, ValueError, KeyError):
        pass
    try:
        out["yaw"] = json.load(open(os.path.join(d, "kont_yaw.json")))
    except (OSError, ValueError):
        pass
    return out


def zdarzenia(d):
    """Twarde STOPy i ważność z trace (zdarzenia driverów; pełne kryteria liczy kont_s4_analyze.py z GT i ulogu)."""
    ev = []
    p = os.path.join(d, "trace.jsonl")
    if os.path.exists(p):
        for l in open(p):
            if '"t": "event"' in l:
                try:
                    ev.append(json.loads(l))
                except ValueError:
                    pass
    cut_sim = next((e["sim"] for e in ev if e["ev"] == "denial"), None)
    out = {"breach": any(e["ev"] in ("breach", "breach_gt") for e in ev), "refuse_pos_nominal": [], "refuse_rg": [],
           "episode_start": sum(e["ev"] == "episode_start" for e in ev), "episode_end": sum(e["ev"] == "episode_end" for e in ev),
           "r_g_nom": sum(e["ev"] == "r_g_nom" for e in ev), "cut": cut_sim is not None,
           "przyziemienie": any(e["ev"] == "gt_przyziemienie" for e in ev)}
    for e in ev:
        if e["ev"] != "refuse":
            continue
        if e.get("reason") == "POS_DEGRADED" and (cut_sim is None or e["sim"] < cut_sim):
            out["refuse_pos_nominal"].append({k: e.get(k) for k in ("sim", "rule", "cause", "episode_id")})
        if e.get("reason") == "GEOFENCE" and e.get("rule") == "R-G":
            out["refuse_rg"].append({k: e.get(k) for k in ("sim", "episode_id", "r_est")})
    return out


def main():
    kolejka, sel = plan()
    assert not os.path.exists(os.path.join(S4, "kampania_s4.json")), "kampania_s4.json istnieje"
    os.makedirs(S4, exist_ok=True)
    log(f"=== S4 start: siatka {sel}, kolejka {[k[0] for k in kolejka]}, budżet 0/{BUDZET}, noga {NOGA_PRZED}/45, "
        f"uptime {open('/proc/uptime').read().split()[0]} s")
    env = {**os.environ, "PERC2_FASTDDS_PROFILE": PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
    with open(os.path.join(S4, "zegar_stan_przed.txt"), "w") as f:
        subprocess.run("timedatectl status; systemctl is-active systemd-timesyncd; cat /sys/devices/system/clocksource/clocksource0/current_clocksource",
                       shell=True, stdout=f, stderr=subprocess.STDOUT)
    subprocess.run(["sudo", "-n", "systemctl", "stop", "systemd-timesyncd"], check=True)
    stop, booty, wyniki, faza_streak, fail_streak, dolecone = None, 0, {}, 0, 0, set()
    try:
        while kolejka:
            if booty >= BUDZET:
                stop = "STOP-KONT4-BUDZET"
                break
            nm, epids, inj = kolejka.pop(0)
            name = wolna_nazwa(nm)
            ok, z = zegar(name)
            log(f"{name}: próbnik {z['skoki']} skoków ok={ok}")
            if not ok:
                stop = "STOP-KONT4-ZEGAR"
                break
            znal, zywe = sprzataj_sieroty()
            if znal:
                log(f"{name}: sieroty TERM {znal}, żywe po {G.TERM_WAIT_S} s: {zywe}")
            if zywe:
                stop = "STOP-KONT4-SIEROTY"
                break
            shm = shm_krok(name, False)
            for _ in range(4):
                r = subprocess.run(["bash", os.path.join(T, "kont_s4_boot.sh"), str(NOGA_PRZED + booty + 1), name, epids, inj],
                                   cwd=ROOT, env=env, capture_output=True, text=True)
                open(os.path.join(S4, f"{name}_driver.log"), "a").write(r.stdout + r.stderr)
                if r.returncode != 3:
                    break
                log(f"{name}: env-block rc=3, nie boot, czekam 120 s")
                time.sleep(120)
            else:
                stop = "STOP-KONT4-ENV"
                break
            if r.returncode in (4, 5, 6):
                stop = "STOP-KONT4-GUARD"
                log(f"ALARM {stop}: {name} rc={r.returncode}, stos nie ruszył, nie boot")
                break
            booty += 1
            d = os.path.join(S4, name)
            s, e = stan(d), zdarzenia(d)
            wpis_manifest(d, {"aneks": "ANEKS_KONT-4 + PROMPT_KONT_S4", "boot_s4": booty, "pozycja": nm, "epizody": epids,
                              "inject_t": inj, "shm": shm, "sieroty_term": {str(k): v for k, v in znal.items()}})
            wyniki[name] = {"pozycja": nm, "rc": r.returncode, **s, **e}
            log(f"{name} rc={r.returncode} boot {booty}/{BUDZET} (noga {NOGA_PRZED + booty}/45): faza={s['faza']} t0_us={s['t0']} "
                f"uzbrojony={s['uzb']} yaw={s['yaw']} epizody {e['episode_start']}/{e['episode_end']} cięcie={e['cut']} "
                f"przyziemienie={e['przyziemienie']} R-G-NOM={e['r_g_nom']} breach={e['breach']} "
                f"REFUSE(POS)_nominal={e['refuse_pos_nominal']} R-G={e['refuse_rg']}")
            if e["breach"]:
                stop = "STOP-KONT4-BREACH"
                break
            if e["refuse_pos_nominal"]:
                stop = "STOP-KONT4-REFUSE-NOMINAL"
                break
            if e["refuse_rg"]:
                stop = "STOP-KONT4-REFUSE-RG"
                break
            niewazny = None
            if not s["faza"]:
                faza_streak += 1
                niewazny = "faza"
                if faza_streak >= 2:
                    stop = "STOP-KONT4-FAZA"
                    break
            else:
                faza_streak = 0
                if s["yaw"] is not None and not s["yaw"].get("ok"):
                    niewazny = "asercja yaw"
                elif not s["uzb"]:
                    fail_streak += 1
                    niewazny = "sonda pod podłogą"
                    if fail_streak >= 2:
                        stop = "STOP-KONT4-SONDA"
                        break
                else:
                    fail_streak = 0
                    want = len(epids.split(","))
                    if e["episode_end"] < want or (inj != "-" and not (e["cut"] and e["przyziemienie"])):
                        niewazny = f"epizody {e['episode_end']}/{want}, cięcie {e['cut']}, przyziemienie {e['przyziemienie']}"
            wyniki[name]["niewazny_kampania"] = niewazny
            if niewazny:
                log(f"ALARM: {name} nieważny ({niewazny})")
                if nm not in dolecone:
                    dolecone.add(nm)
                    kolejka.append((nm, epids, inj))
                    log(f"{name}: dolecenie {nm} na końcu kolejki")
        if stop is None and kolejka:
            stop = "STOP-KONT4-BUDZET"
    except Exception as ex:
        stop = "STOP-KONT4-WYJATEK"
        log(f"ALARM {stop}: {ex!r}")
        raise
    finally:
        subprocess.run(["sudo", "-n", "systemctl", "start", "systemd-timesyncd"])
        with open(os.path.join(S4, "zegar_stan_po.txt"), "w") as f:
            subprocess.run("timedatectl status; systemctl is-active systemd-timesyncd", shell=True, stdout=f, stderr=subprocess.STDOUT)
        log(f"KONIEC booty={booty}/{BUDZET} noga={NOGA_PRZED + booty}/45 stop={stop} pozostało={[k[0] for k in kolejka]}")
        json.dump({"booty": booty, "noga": NOGA_PRZED + booty, "siatka": sel, "wyniki": wyniki, "stop": stop,
                   "pozostalo": kolejka}, open(os.path.join(S4, "kampania_s4.json"), "w"), ensure_ascii=False, indent=1)
    print("KONIEC", booty, stop)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--plan":
        print(json.dumps(plan(), ensure_ascii=False, indent=1))
    else:
        main()
