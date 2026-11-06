#!/usr/bin/env python3
"""results/KONT/tools/kont_s2_campaign_y.py — kolejka sondy Y (ANEKS_KONT-2b §2, §3.4). Strażniki 1b bez zmian (import z kont_s2_campaign_g.py), faza jak kont_s2_campaign_d.py. Boot: kont_s2y_boot.sh. Przeskoki liczone od startu (1e §2): STOP tylko w powietrzu, zdarzenie na ziemi = wiersz „restart estymatora na ziemi”.
Asercja yaw naruszona (kont_yaw.json): boot nieważny, dolecenie, bez serii FAIL sondy. Po każdym locie reguła Y z kont_d4_y.py do logu; lot Y-b nie zatrzymuje kolejki, bo 3 loty uzupełniają n = 8 (§2). Wyjście: kampania_y.json."""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kont_s2_campaign_g as G
import kont_s2_campaign_d as CD
from kont_s2_campaign_g import ROOT, T, PROFIL, log, zegar, sprzataj_sieroty, shm_krok, wolna_nazwa, wpis_manifest

S2 = G.S2
PLAN = [("c11_s04", 47), ("c08_s02b", 20), ("c02_s01", 2)]
ZALICZONE = ["c08_s02a_r2", "c11_s02_r3", "c11_s03_r4", "c08_s04_r3", "c00_s02_r3"]
BUDZET, CEL, BOOTY_S2, UZYTE = 12, 8, 14, 5


def przeskoki(w):
    """(w powietrzu, na ziemi) z listy analizy; cs_in_air = t_cut − nominal_powietrze_s."""
    lista = w.get("przeskoki_lista") or []
    if w.get("nominal_powietrze_s") is None or w.get("t_cut") is None:
        return list(lista), []
    t_air = w["t_cut"] - w["nominal_powietrze_s"]
    return [x for x in lista if x[0] >= t_air], [x for x in lista if x[0] < t_air]


def yaw_stan(d):
    try:
        return json.load(open(os.path.join(d, "kont_yaw.json")))
    except (OSError, ValueError):
        return None


def main():
    for z in ZALICZONE:
        assert json.load(open(os.path.join(S2, z, "wyniki.json")))["wazny"] is True
    assert not os.path.exists(os.path.join(S2, "kampania_y.json")), "kampania_y.json istnieje"
    log(f"=== S2′ ANEKS_KONT-2b sonda Y start: zaliczone {len(ZALICZONE)}, budżet {UZYTE}/{BUDZET}, uptime {open('/proc/uptime').read().split()[0]} s")
    env = {**os.environ, "PERC2_FASTDDS_PROFILE": PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
    with open(os.path.join(S2, "zegar_stan_przed_y.txt"), "w") as f:
        subprocess.run("timedatectl status; systemctl is-active systemd-timesyncd; cat /sys/devices/system/clocksource/clocksource0/current_clocksource", shell=True, stdout=f, stderr=subprocess.STDOUT)
    subprocess.run(["sudo", "-n", "systemctl", "stop", "systemd-timesyncd"], check=True)
    stop, booty, wazne, kolejka, fail_streak, faza_streak = None, UZYTE, len(ZALICZONE), list(PLAN), 0, 0
    loty_y, reguly = [], {}
    import kont_s2_analyze as A
    import kont_d4_y as DY
    try:
        while kolejka and booty < BUDZET:
            nm, ep = kolejka.pop(0)
            name = wolna_nazwa(nm)
            ok, z = zegar(name)
            log(f"{name}: próbnik {z['skoki']} skoków ok={ok}")
            if not ok:
                stop = "STOP-KONT2-ZEGAR"
                break
            znal, zywe = sprzataj_sieroty()
            if znal:
                log(f"{name}: sieroty TERM {znal}, żywe po {G.TERM_WAIT_S} s: {zywe}")
            if zywe:
                stop = "STOP-KONT2-SIEROTY"
                log(f"ALARM {stop}: {zywe}")
                break
            shm = shm_krok(name, False)
            for _ in range(4):
                r = subprocess.run(["bash", os.path.join(T, "kont_s2y_boot.sh"), str(BOOTY_S2 + booty + 1), name, str(ep)], cwd=ROOT, env=env, capture_output=True, text=True)
                open(os.path.join(S2, f"{name}_driver.log"), "a").write(r.stdout + r.stderr)
                if r.returncode != 3:
                    break
                log(f"{name}: env-block rc=3, nie boot, czekam 120 s")
                time.sleep(120)
            else:
                stop = "STOP-KONT2-ENV"
                break
            if r.returncode in (4, 5, 6):
                stop = "STOP-KONT2-GUARD"
                log(f"ALARM {stop}: {name} rc={r.returncode}, stos nie ruszył, nie boot")
                break
            booty += 1
            d = os.path.join(S2, name)
            s = CD.stan(d)
            y = yaw_stan(d)
            wpis_manifest(d, {"aneks": "ANEKS_KONT-2b", "boot_s2p": booty, "sonda": "Y", "shm": shm, "sieroty_term": {str(k): v for k, v in znal.items()}, "sensor_combined_n": s["sc"], "yaw_assert": y})
            w = A.analyze(d)
            pow_, zie = przeskoki(w)
            log(f"{name} rc={r.returncode} boot {booty}/{BUDZET}: t0_us={s['t0']} sc={s['sc']} uzbrojony={s['uzb']} n_frames={s['nf']} sonda={s['werdykt']} yaw={y} ważny={w.get('wazny')} ({w.get('powod_niewazny')}) V2p={w.get('v2p')} eps60={w.get('eps_60')} eps70={w.get('eps_70')} delta={w.get('delta_max')} p95={w.get('eps0_p95_nominal')} rmax={w.get('r_gt_max')} xy={w.get('xy_valid_cale_okno')} flipy_powietrze={len(pow_)} zejscie={w.get('powod_zejscia')} t_entry={w.get('t_entry')}")
            if zie:
                log(f"{name}: restart estymatora na ziemi {zie}, watchdog: {open(os.path.join(d, 'ekf_watchdog.log')).read().splitlines()[:1]}")
            if w.get("breach"):
                stop = "STOP-KONT2-BREACH"
                break
            if w.get("refuse_nominal"):
                stop = "STOP-KONT2-REFUSE"
                break
            if pow_:
                stop = "STOP-KONT2-PRZESKOK"
                log(f"ALARM {stop}: {name} w powietrzu {pow_}")
                break
            if not s["faza"]:
                faza_streak += 1
                log(f"ALARM FAZA: {name} t0_us={s['t0']}, boot przerwany, seria {faza_streak}")
                if faza_streak >= 2:
                    stop = "STOP-KONT2-FAZA"
                    break
            else:
                faza_streak = 0
                if y is not None and not y.get("ok"):
                    log(f"ALARM YAW: {name} {y}, boot nieważny, dolecenie")
                elif not s["uzb"]:
                    fail_streak += 1
                    log(f"ALARM FAIL sondy przed uzbrojeniem: {name} n_frames={s['nf']} sonda={s['werdykt']}, seria {fail_streak}")
                    if fail_streak >= 2:
                        stop = "STOP-KONT2-SONDA"
                        break
                else:
                    fail_streak = 0
            if w.get("t_descent") is not None:
                q = DY.ocen(name)
                reguly[name] = {**q["regula_y"], **q["yaw"], "delta": w.get("delta_max"), "wazny": w.get("wazny")}
                log(f"REGUŁA Y {name}: {reguly[name]}")
                if q["yaw"]["obrot_3s_deg"] > 20:
                    log(f"ALARM TRZYMANIE YAW: {name} obrót {q['yaw']['obrot_3s_deg']}°, zejście nie testuje czynnika")
            if w.get("wazny"):
                wazne += 1
                loty_y.append(name)
            elif wazne + len(kolejka) < CEL and booty + len(kolejka) < BUDZET:
                kolejka.append((nm, ep))
        if stop is None and wazne < CEL:
            stop = "STOP-KONT2-BUDZET"
    except Exception as e:
        stop = "STOP-KONT2-WYJATEK"
        log(f"ALARM {stop}: {e!r}")
        raise
    finally:
        subprocess.run(["sudo", "-n", "systemctl", "start", "systemd-timesyncd"])
        with open(os.path.join(S2, "zegar_stan_po_y.txt"), "w") as f:
            subprocess.run("timedatectl status; systemctl is-active systemd-timesyncd", shell=True, stdout=f, stderr=subprocess.STDOUT)
        log(f"KONIEC booty={booty} ważne={wazne} loty_y={loty_y} stop={stop}")
        json.dump({"booty": booty, "wazne": wazne, "loty_y": loty_y, "reguly": reguly, "stop": stop}, open(os.path.join(S2, "kampania_y.json"), "w"), ensure_ascii=False, indent=1)
    print("KONIEC", booty, wazne, stop)


if __name__ == "__main__":
    main()
