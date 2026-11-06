#!/usr/bin/env python3
"""results/KONT/tools/kont_s2_campaign_d.py — kolejka po ANEKS_KONT-1c (§3, §4). Strażniki 1b bez zmian, import z kont_s2_campaign_g.py (oryginał nietknięty). Boot: kont_s2d_boot.sh. Pierwszy boot = D3 (c11_s03, sesja po bootach, stan /dev/shm jak zastany, bez sprzątania, bo D2 obalił SHM):
PASS ⇔ initial absolute time ≥ 500 000 µs ∧ sensor_combined płynie (ulog) ∧ sonda PASS; FAIL ⇒ STOP-KONT2c. Faza < 500 000 µs poza D3: boot przerwany, liczy się do budżetu, to nie FAIL sondy; dwa z rzędu ⇒ STOP-KONT2-FAZA. Budżet 12 z 2 użytymi, loty 1–2 zaliczone.
Plan: §4 aneksu + c02_s01 na końcu, bo §4 wymienia 5 lotów, co z dwoma zaliczonymi daje 7, a PRE §3 wymaga 8 (c02_s01 z planu 1b §4 nie poleciał w D2). Wyjście: kampania_d.json."""
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kont_s2_campaign_g as G
from kont_s2_campaign_g import S2, T, ROOT, LOG, PROFIL, log, zegar, sprzataj_sieroty, shm_krok, wolna_nazwa, wpis_manifest

PLAN = [("c11_s03", 35), ("c08_s04", 44), ("c00_s02", 12), ("c11_s04", 47), ("c08_s02b", 20), ("c02_s01", 2)]
ZALICZONE = ["c08_s02a_r2", "c11_s02_r3"]
BUDZET, CEL, BOOTY_S2, UZYTE = 12, 8, 14, 2
T0_MIN = 500000
SC_MIN = 1000
RS = os.path.join(ROOT, "PX4-Autopilot/build/px4_sitl_default/rootfs")


def stan(d):
    """Z plików bootu: uzbrojony, werdykt sondy, n_frames, faza, initial time, próbki sensor_combined."""
    out = {"uzb": False, "werdykt": None, "nf": None, "faza": False, "t0": None, "sc": None}
    try:
        m = json.load(open(os.path.join(d, "manifest.json")))
        out["uzb"] = bool(m["kont_s2"].get("uzbrojony"))
        out["werdykt"] = (m["kont_s2"].get("sonda") or {}).get("werdykt")
        out["faza"] = bool(m["kont_s2d"].get("faza_ok"))
        out["t0"] = m["kont_s2d"].get("initial_absolute_time_us")
    except (OSError, ValueError, KeyError):
        pass
    try:
        out["nf"] = json.load(open(os.path.join(d, "percep_feed.jsonl.summary.json"))).get("n_frames")
    except (OSError, ValueError):
        pass
    try:
        from pyulog import ULog
        x = re.search(r"Opened full log file: \./(log/\S+\.ulg)", open(os.path.join(d, "px4.log"), errors="replace").read())
        u = ULog(os.path.join(RS, x.group(1)), ["sensor_combined"])
        out["sc"] = sum(len(q.data["timestamp"]) for q in u.data_list)
    except Exception as e:
        out["sc_blad"] = repr(e)[:120]
    return out


def main():
    for z in ZALICZONE:
        assert json.load(open(os.path.join(S2, z, "wyniki.json")))["wazny"] is True
    assert not os.path.exists(os.path.join(S2, "kampania_d.json")), "kampania_d.json istnieje"
    log(f"=== S2′ ANEKS_KONT-1c start: zaliczone {ZALICZONE}, budżet {UZYTE}/{BUDZET}, uptime {open('/proc/uptime').read().split()[0]} s, /dev/shm fastrtps {len(G.shm_pliki())}")
    env = {**os.environ, "PERC2_FASTDDS_PROFILE": PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
    with open(os.path.join(S2, "zegar_stan_przed_d.txt"), "w") as f:
        subprocess.run("timedatectl status; systemctl is-active systemd-timesyncd; cat /sys/devices/system/clocksource/clocksource0/current_clocksource", shell=True, stdout=f, stderr=subprocess.STDOUT)
    subprocess.run(["sudo", "-n", "systemctl", "stop", "systemd-timesyncd"], check=True)
    stop, booty, wazne, kolejka, fail_streak, faza_streak = None, UZYTE, len(ZALICZONE), list(PLAN), 0, 0
    d3_czeka = True
    import kont_s2_analyze as A
    try:
        while kolejka and booty < BUDZET:
            nm, ep = kolejka.pop(0)
            name = wolna_nazwa(nm)
            dg = "D3" if d3_czeka else None
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
            log(f"{name}: {dg or 'lot'} /dev/shm sprzątanie=False przed={shm['plikow_przed']}")
            for _ in range(4):
                r = subprocess.run(["bash", os.path.join(T, "kont_s2d_boot.sh"), str(BOOTY_S2 + booty + 1), name, str(ep)], cwd=ROOT, env=env, capture_output=True, text=True)
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
            s = stan(d)
            wpis_manifest(d, {"aneks": "ANEKS_KONT-1c", "boot_s2p": booty, "diagnoza": dg, "shm": shm, "sieroty_term": {str(k): v for k, v in znal.items()}, "sensor_combined_n": s["sc"]})
            w = A.analyze(d)
            log(f"{name} rc={r.returncode} boot {booty}/{BUDZET}: t0_us={s['t0']} sc={s['sc']} uzbrojony={s['uzb']} n_frames={s['nf']} sonda={s['werdykt']} ważny={w.get('wazny')} ({w.get('powod_niewazny')}) V2p={w.get('v2p')} eps60={w.get('eps_60')} eps70={w.get('eps_70')} delta={w.get('delta_max')} p95={w.get('eps0_p95_nominal')} rmax={w.get('r_gt_max')} xy={w.get('xy_valid_cale_okno')} flipy={w.get('przeskoki_cs_gnss')} zejscie={w.get('powod_zejscia')} t_entry={w.get('t_entry')}")
            if w.get("breach"):
                stop = "STOP-KONT2-BREACH"
                break
            if w.get("refuse_nominal"):
                stop = "STOP-KONT2-REFUSE"
                break
            if w.get("przeskoki_cs_gnss"):
                stop = "STOP-KONT2-PRZESKOK"
                break
            if dg:
                d3 = (s["t0"] or 0) >= T0_MIN and (s["sc"] or 0) >= SC_MIN and s["uzb"] and s["werdykt"] == "PASS"
                d3_czeka = False
                if not d3:
                    stop = "STOP-KONT2c"
                    log(f"ALARM {stop}: FAIL D3 t0_us={s['t0']} sc={s['sc']} sonda={s['werdykt']} {s.get('sc_blad', '')}")
                    break
                log("D3 PASS: launcher s2d wchodzi do dalszych bootów")
            if not s["faza"]:
                faza_streak += 1
                log(f"ALARM FAZA: {name} t0_us={s['t0']} < {T0_MIN}, boot przerwany, seria {faza_streak}")
                if faza_streak >= 2:
                    stop = "STOP-KONT2-FAZA"
                    break
            else:
                faza_streak = 0
                if not s["uzb"]:
                    fail_streak += 1
                    log(f"ALARM FAIL sondy przed uzbrojeniem: {name} n_frames={s['nf']} sonda={s['werdykt']}, seria {fail_streak}")
                    if fail_streak >= 2:
                        stop = "STOP-KONT2-SONDA"
                        break
                else:
                    fail_streak = 0
            if w.get("wazny"):
                wazne += 1
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
        with open(os.path.join(S2, "zegar_stan_po_d.txt"), "w") as f:
            subprocess.run("timedatectl status; systemctl is-active systemd-timesyncd", shell=True, stdout=f, stderr=subprocess.STDOUT)
        log(f"KONIEC booty={booty} ważne={wazne} stop={stop}")
        json.dump({"booty": booty, "wazne": wazne, "stop": stop}, open(os.path.join(S2, "kampania_d.json"), "w"))
    print("KONIEC", booty, wazne, stop)


if __name__ == "__main__":
    main()
