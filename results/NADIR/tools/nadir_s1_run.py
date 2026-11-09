#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s1_run.py — jeden boot epizodowy S1 NADIR (PROMPT_NADIR_S1 §2.2/§2.3) w reżimie KONT S4:
timesyncd zatrzymany (ANEKS_SKAN2-0b), próbnik zegara 60 s ze świeżą nazwą pliku (lekcja STOP-KONT4-ZEGAR), sprzątanie
sierot i /dev/shm (kont_s2_campaign_g — import READ-ONLY, katalog przekierowany na results/NADIR/s1 w tym procesie),
boot results/NADIR/tools/nadir_s1_boot.sh z profilem FastDDS PERC2, stan /dev/shm po. Bez kolejki: jeden boot na wywołanie,
decyzja o następnym po analizie (budżet S1 ≤ 4).
Użycie: nadir_s1_run.py <BOOT_N> <NAZWA> <EPIZODY csv>
"""
import json
import os
import subprocess
import sys
import time

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/KONT/tools"))
import kont_s2_campaign_g as G

S1 = os.path.join(ROOT, "results/NADIR/s1")
G.S2 = S1
G.LOG = os.path.join(S1, "nadir_s1_run.log")
G.SKRYPTY = G.SKRYPTY | {"kont_s4_flight", "intruder_motion", "nadir_obs"}


def main():
    bn, name, epids = sys.argv[1], sys.argv[2], sys.argv[3]
    assert not os.path.exists(os.path.join(S1, name)), f"{name} istnieje"
    assert not any(f.startswith(name) for f in os.listdir(S1)), f"pliki {name}* istnieją"
    ts = subprocess.run(["systemctl", "is-active", "systemd-timesyncd"], capture_output=True, text=True).stdout.strip()
    if ts == "active":
        subprocess.run(["sudo", "-n", "systemctl", "stop", "systemd-timesyncd"], check=True)
    G.log(f"=== NADIR S1 boot {bn} {name} epizody {epids}; timesyncd przed: {ts}")
    ok, z = G.zegar(name)
    G.log(f"zegar {name}: ok={ok} skoki={z['skoki']}")
    if not ok:
        G.log("STOP: zegar — boot nie startuje")
        sys.exit(7)
    sier, zywe = G.sprzataj_sieroty()
    shm0 = G.shm_krok(name, True)
    G.log(f"sieroty {sier} żywe {zywe}; shm {shm0}")
    env = dict(os.environ, PERC2_FASTDDS_PROFILE=G.PROFIL)
    t0 = time.time()
    r = subprocess.run(["bash", os.path.join(ROOT, "results/NADIR/tools/nadir_s1_boot.sh"), bn, name, epids, "-"], env=env)
    shm1 = G.shm_krok(name + "_po", False)
    tempo = None
    tp = os.path.join(S1, name, "kont_tempo.json")
    if os.path.exists(tp):
        tempo = json.load(open(tp))
    wpis = {"boot": int(bn), "nazwa": name, "epizody": epids, "rc": r.returncode, "czas_s": round(time.time() - t0, 1),
            "zegar": z, "shm_przed": shm0, "shm_po": shm1, "tempo_driver": tempo}
    json.dump(wpis, open(os.path.join(S1, f"run_{name}.json"), "w"), ensure_ascii=False, indent=1)
    G.log(f"=== koniec {name} rc={r.returncode} {round(time.time() - t0)} s tempo={tempo}")
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
