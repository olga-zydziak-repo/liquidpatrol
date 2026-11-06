#!/usr/bin/env python3
"""results/KONT/tools/kont_s2_campaign_r.py — wznowienie po przerwanym biegu z 6.11 01:44 (c08_s02a padł po 6.7 s przed startem stosu, nie boot; katalog zostaje jako dowód, pierwszy lot = c08_s02a_r2). Kopia kont_s2_campaign.py, jedyna zmiana: licznik prób. Oryginał: kolejka lotów S2 (PROMPT_KONT_S2 §S2.2). Przed każdym bootem próbnik 60 s (ANEKS_SKAN2-0b): FAIL ⇒ STOP-KONT2-ZEGAR. Po każdym locie analiza i twarde STOPy
(breach; REFUSE(POS) poza scenariuszem; przeskok cs_gnss_pos w nominale, R-5; budżet 14). Nieważne loty dolatywane do ≥ 8 ważnych. Env-block rc=3 nie liczy się jako boot. timesyncd stop na sesję, start zawsze na końcu."""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
S2 = os.path.join(ROOT, "results/KONT/s2")
T = os.path.join(ROOT, "results/KONT/tools")
PLAN = [("c08_s02a", 20), ("c11_s02", 23), ("c02_s01", 2), ("c08_s04", 44), ("c11_s03", 35), ("c00_s02", 12), ("c11_s04", 47), ("c08_s02b", 20)]
BUDZET, CEL = 14, 8
LOG = os.path.join(S2, "kampania.log")
PROFIL = os.path.join(ROOT, "results/PERC2/tools/perc2_fastdds_profile.xml")


def log(s):
    line = f"[kampania {time.strftime('%H:%M:%S')}] {s}"
    print(line, flush=True)
    open(LOG, "a").write(line + "\n")


def zegar(name):
    p = os.path.join(S2, f"zegar_przed_{name}.jsonl")
    subprocess.run([sys.executable, os.path.join(ROOT, "results/SKAN2/tools/skan2_zegar.py"), p, "--seconds", "60"], check=True)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "results/SKAN2/tools/skan2_zegar.py"), "--check", p], capture_output=True, text=True)
    z = json.loads(r.stdout)
    return z["skoki"] <= 3 and all(abs(j["skok_s"]) <= 1.2 for j in z["lista"]), z


def main():
    os.makedirs(S2, exist_ok=True)
    env = {**os.environ, "PERC2_FASTDDS_PROFILE": PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
    with open(os.path.join(S2, "zegar_stan_przed.txt"), "w") as f:
        subprocess.run("timedatectl status; systemctl is-active systemd-timesyncd; cat /sys/devices/system/clocksource/clocksource0/current_clocksource", shell=True, stdout=f, stderr=subprocess.STDOUT)
    subprocess.run(["sudo", "-n", "systemctl", "stop", "systemd-timesyncd"], check=True)
    stop, booty, wazne, kolejka, proby = None, 0, 0, list(PLAN), {"c08_s02a": 1}
    import kont_s2_analyze as A
    try:
        while kolejka and booty < BUDZET:
            nm, ep = kolejka.pop(0)
            proby[nm] = proby.get(nm, 0) + 1
            name = nm if proby[nm] == 1 else f"{nm}_r{proby[nm]}"
            ok, z = zegar(name)
            log(f"{name}: próbnik {z['skoki']} skoków ok={ok}")
            if not ok:
                stop = "STOP-KONT2-ZEGAR"
                break
            for _ in range(4):
                r = subprocess.run(["bash", os.path.join(T, "kont_s2_boot.sh"), str(booty + 1), name, str(ep)], cwd=ROOT, env=env, capture_output=True, text=True)
                open(os.path.join(S2, f"{name}_driver.log"), "a").write(r.stdout + r.stderr)
                if r.returncode != 3:
                    break
                log(f"{name}: env-block rc=3, nie boot, czekam 120 s")
                time.sleep(120)
            else:
                stop = "STOP-KONT2-ENV"
                break
            booty += 1
            w = A.analyze(os.path.join(S2, name))
            log(f"{name} rc={r.returncode} boot {booty}/{BUDZET}: ważny={w.get('wazny')} ({w.get('powod_niewazny')}) V2p={w.get('v2p')} eps60={w.get('eps_60')} eps70={w.get('eps_70')} delta={w.get('delta_max')} p95={w.get('eps0_p95_nominal')} rmax={w.get('r_gt_max')} xy={w.get('xy_valid_cale_okno')} flipy={w.get('przeskoki_cs_gnss')} zejscie={w.get('powod_zejscia')} t_entry={w.get('t_entry')}")
            if w.get("breach"):
                stop = "STOP-KONT2-BREACH"
                break
            if w.get("refuse_nominal"):
                stop = "STOP-KONT2-REFUSE"
                break
            if w.get("przeskoki_cs_gnss"):
                stop = "STOP-KONT2-PRZESKOK"
                break
            if w.get("wazny"):
                wazne += 1
            elif wazne + len(kolejka) < CEL and booty + len(kolejka) < BUDZET:
                kolejka.append((nm, ep))
        if stop is None and wazne < CEL:
            stop = "STOP-KONT2-BUDZET"
    finally:
        subprocess.run(["sudo", "-n", "systemctl", "start", "systemd-timesyncd"])
        with open(os.path.join(S2, "zegar_stan_po.txt"), "w") as f:
            subprocess.run("timedatectl status; systemctl is-active systemd-timesyncd", shell=True, stdout=f, stderr=subprocess.STDOUT)
    log(f"KONIEC booty={booty} ważne={wazne} stop={stop}")
    json.dump({"booty": booty, "wazne": wazne, "stop": stop}, open(os.path.join(S2, "kampania.json"), "w"))
    print("KONIEC", booty, wazne, stop)


main()
