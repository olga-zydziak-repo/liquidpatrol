#!/usr/bin/env python3
"""results/KONT/tools/kont_s4_campaign_c.py — kolejka S4 po ANEKS_KONT-4c = kopia kont_s4_campaign_b.py (oryginał nietknięty)
ze zmianami wyłącznie: budżet z argumentu (17 bez ratyfikacji 4c, 20 z „ratyfikuję 4c") z 3 użytymi, dolecenia do wyczerpania
budżetu (4c §4: 2 rezerwy przy 20), nowy STOP 4c §3: 2 kolejne booty nieważne na asercji yaw MIMO mitygacji ⇒
STOP-KONT4-STANOWISKO, wpis mitygacji (kont_ekf_preflight.json) w manifeście, wyjście kampania_s4c.json.
Nagłówek oryginału: results/KONT/tools/kont_s4_campaign_b.py — kolejka S4 po ANEKS_KONT-4b (ratyfikowane: S4 ≤ 17 bootów). Kopia pętli
kont_s4_campaign.py (oryginał nietknięty — wyprodukował boot nom_b1); siatka, stan, zdarzenia, strażniki i twarde STOPy
importem bez zmian. Zmiany wyłącznie: budżet 17 z 1 użytym (nom_b1, STOP-KONT4-DRIVER), kolejność §CO (nom_b1 dolecenie,
nom_b2, nom_b3, potem 12 cięć wg siatki), jedno dolecenie w całej serii (rezerwa 4b), wyjście kampania_s4c.json."""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kont_s4_campaign as K
from kont_s4_campaign import G, ROOT, T, PROFIL, S4, NOGA_PRZED, log, zegar, sprzataj_sieroty, shm_krok, wolna_nazwa, wpis_manifest

BUDZET, UZYTE = int(sys.argv[1]), 3


def main():
    pl, sel = K.plan()
    nom = [x for x in pl if x[2] == "-"]
    ciecia = [x for x in pl if x[2] != "-"]
    kolejka = nom + ciecia
    assert BUDZET in (17, 20), BUDZET
    assert not os.path.exists(os.path.join(S4, "kampania_s4c.json")), "kampania_s4c.json istnieje"
    log(f"=== S4 (ANEKS_KONT-4c) start: kolejka {[k[0] for k in kolejka]}, budżet {UZYTE}/{BUDZET}, noga {NOGA_PRZED + UZYTE}/45, "
        f"uptime {open('/proc/uptime').read().split()[0]} s")
    env = {**os.environ, "PERC2_FASTDDS_PROFILE": PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
    with open(os.path.join(S4, "zegar_stan_przed_c.txt"), "w") as f:
        subprocess.run("timedatectl status; systemctl is-active systemd-timesyncd; cat /sys/devices/system/clocksource/clocksource0/current_clocksource",
                       shell=True, stdout=f, stderr=subprocess.STDOUT)
    subprocess.run(["sudo", "-n", "systemctl", "stop", "systemd-timesyncd"], check=True)
    stop, booty, wyniki, faza_streak, fail_streak, yaw_streak = None, UZYTE, {}, 0, 0, 0
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
            s, e = K.stan(d), K.zdarzenia(d)
            try:
                kp = json.load(open(os.path.join(d, "kont_ekf_preflight.json")))
            except (OSError, ValueError):
                kp = None
            wpis_manifest(d, {"aneks": "ANEKS_KONT-4c + PROMPT_KONT_S4", "boot_s4": booty, "pozycja": nm, "epizody": epids,
                              "inject_t": inj, "shm": shm, "sieroty_term": {str(k): v for k, v in znal.items()},
                              "ekf_preflight": kp})
            wyniki[name] = {"pozycja": nm, "rc": r.returncode, "ekf_preflight": kp, **s, **e}
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
                    yaw_streak += 1
                    if yaw_streak >= 2:
                        stop = "STOP-KONT4-STANOWISKO"
                        log(f"ALARM {stop}: 2 kolejne booty nieważne na asercji yaw mimo mitygacji 4c")
                        break
                elif not s["uzb"]:
                    fail_streak += 1
                    niewazny = "sonda pod podłogą"
                    if fail_streak >= 2:
                        stop = "STOP-KONT4-SONDA"
                        break
                else:
                    fail_streak = 0
                    yaw_streak = 0
                    want = len(epids.split(","))
                    if e["episode_end"] < want or (inj != "-" and not (e["cut"] and e["przyziemienie"])):
                        niewazny = f"epizody {e['episode_end']}/{want}, cięcie {e['cut']}, przyziemienie {e['przyziemienie']}"
            wyniki[name]["niewazny_kampania"] = niewazny
            if niewazny:
                log(f"ALARM: {name} nieważny ({niewazny})")
                if booty + len(kolejka) < BUDZET:
                    kolejka.append((nm, epids, inj))
                    log(f"{name}: dolecenie {nm} na końcu kolejki (rezerwa 4c)")
                else:
                    stop = "STOP-KONT4-BUDZET"
                    log(f"ALARM {stop}: nieważny boot, rezerwa wyczerpana")
                    break
        if stop is None and kolejka:
            stop = "STOP-KONT4-BUDZET"
    except Exception as ex:
        stop = "STOP-KONT4-WYJATEK"
        log(f"ALARM {stop}: {ex!r}")
        raise
    finally:
        subprocess.run(["sudo", "-n", "systemctl", "start", "systemd-timesyncd"])
        with open(os.path.join(S4, "zegar_stan_po_c.txt"), "w") as f:
            subprocess.run("timedatectl status; systemctl is-active systemd-timesyncd", shell=True, stdout=f, stderr=subprocess.STDOUT)
        log(f"KONIEC booty={booty}/{BUDZET} noga={NOGA_PRZED + booty}/45 stop={stop} pozostało={[k[0] for k in kolejka]}")
        json.dump({"booty": booty, "noga": NOGA_PRZED + booty, "siatka": sel, "wyniki": wyniki, "stop": stop,
                   "pozostalo": kolejka}, open(os.path.join(S4, "kampania_s4c.json"), "w"), ensure_ascii=False, indent=1)
    print("KONIEC", booty, stop)


if __name__ == "__main__":
    main()
