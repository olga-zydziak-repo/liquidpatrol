#!/usr/bin/env python3
"""results/KONT/tools/kont_s2_campaign_g.py — kolejka S2′ (ANEKS_KONT-1b §2.3, §3, §4). Kopia kont_s2_campaign.py, oryginał nietknięty. Zmiany: budżet 12 przy zaliczonym c08_s02a_r2 (1/8); 2 kolejne FAIL sondy przed uzbrojeniem ⇒ STOP-KONT2-SONDA,
pierwszy FAIL ⇒ wiersz ALARM w kampania.log (dopisywany); przed każdym bootem sieroty po PID z inwentarza /proc: TERM, 10 s, powtórna kontrola, żywa ⇒ STOP-KONT2-SIEROTY; diagnoza: D1 = pusty /dev/shm bez sprzątania, od D2 sprzątanie fastrtps_* i sem.fastrtps_*
przed każdym bootem (stan przed/po w shm_<nazwa>.txt, wpis kont_s2g w manifeście); FAIL D1 albo D2 ⇒ STOP-KONT2b bez trzeciej próby. Nazwy: pierwszy wolny katalog (REPO-2). Wyjście: kampania_g.json; kampania.json z S2 zostaje. Pozostałe STOPy jak w oryginale."""
import glob
import json
import os
import signal
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
S2 = os.path.join(ROOT, "results/KONT/s2")
T = os.path.join(ROOT, "results/KONT/tools")
PLAN = [("c11_s02", 23), ("c02_s01", 2), ("c08_s04", 44), ("c11_s03", 35), ("c00_s02", 12), ("c11_s04", 47), ("c08_s02b", 20)]
LOT_1 = "c08_s02a_r2"
BUDZET, CEL, BOOTY_S2 = 12, 8, 14
LOG = os.path.join(S2, "kampania.log")
PROFIL = os.path.join(ROOT, "results/PERC2/tools/perc2_fastdds_profile.xml")
SKRYPTY = {"infra2_ekf_watchdog", "rtf_sampler", "percep_proc"}
BINARIA = {"MicroXRCEAgent", "gz", "px4"}
TERM_WAIT_S = 10


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


def sierota(argv):
    """Nazwa z listy aneksu albo None. Tylko pozycja programu w argv, nigdy podciąg, żeby powłoka z tą nazwą w poleceniu nie była sierotą."""
    if not argv or not argv[0]:
        return None
    prog = os.path.basename(argv[0].split()[0])
    if prog in BINARIA:
        return prog
    if prog.startswith(("python", "ruby")):
        for a in argv[1:4]:
            b = os.path.basename(a)
            b = b[:-3] if b.endswith(".py") else b
            b = b.rsplit(".", 1)[-1]
            if b in SKRYPTY or (prog.startswith("ruby") and b in BINARIA):
                return b
    return None


def inwentarz():
    out = {}
    for d in os.listdir("/proc"):
        if not d.isdigit() or int(d) == os.getpid():
            continue
        try:
            argv = open(f"/proc/{d}/cmdline", "rb").read().decode(errors="replace").split("\0")
            stan = open(f"/proc/{d}/stat").read().rsplit(")", 1)[1].split()[0]
        except OSError:
            continue
        n = sierota(argv)
        if n and stan != "Z":
            out[int(d)] = n
    return out


def sprzataj_sieroty(wait_s=TERM_WAIT_S):
    """Zwraca (znalezione, żywe po TERM). Sygnał wyłącznie po PID z inwentarza."""
    inw = inwentarz()
    for pid in inw:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    if inw:
        time.sleep(wait_s)
    return inw, inwentarz()


def shm_pliki():
    return sorted(glob.glob("/dev/shm/fastrtps_*") + glob.glob("/dev/shm/sem.fastrtps_*"))


def shm_trzymane():
    out = {}
    for m in glob.glob("/proc/[0-9]*/maps"):
        try:
            if "/dev/shm/fastrtps" in open(m).read():
                out[m.split("/")[2]] = open(m.replace("maps", "comm")).read().strip()
        except OSError:
            continue
    return out


def shm_krok(name, sprzataj):
    """Stan /dev/shm przed i po do pliku. Zwraca wpis do manifestu."""
    p = os.path.join(S2, f"shm_{name}.txt")
    przed = shm_pliki()
    trzym = shm_trzymane()
    with open(p, "w") as f:
        f.write(f"# {time.strftime('%F %T')} {name} sprzatanie={sprzataj} uptime={open('/proc/uptime').read().split()[0]} s\n# PRZED, trzymane przez: {trzym}\n")
        f.flush()
        subprocess.run(["ls", "-la", "--time-style=full-iso", "/dev/shm"], stdout=f, stderr=subprocess.STDOUT)
        if sprzataj:
            for x in przed:
                os.remove(x)
        f.write("# PO\n")
        f.flush()
        subprocess.run(["ls", "-la", "--time-style=full-iso", "/dev/shm"], stdout=f, stderr=subprocess.STDOUT)
    return {"sprzatanie": sprzataj, "plikow_przed": len(przed), "plikow_po": len(shm_pliki()), "trzymane_przed": trzym, "stan": os.path.basename(p)}


def wolna_nazwa(nm):
    n = 1
    while os.path.exists(os.path.join(S2, nm if n == 1 else f"{nm}_r{n}")):
        n += 1
    return nm if n == 1 else f"{nm}_r{n}"


def sonda_stan(d):
    """(uzbrojony, n_frames, werdykt sondy) z plików bootu; brak manifestu = nieuzbrojony."""
    uzb, nf, wer = False, None, None
    try:
        m = json.load(open(os.path.join(d, "manifest.json")))["kont_s2"]
        uzb = bool(m.get("uzbrojony"))
        wer = (m.get("sonda") or {}).get("verdict")
    except (OSError, ValueError, KeyError):
        pass
    try:
        nf = json.load(open(os.path.join(d, "percep_feed.jsonl.summary.json"))).get("n_frames")
    except (OSError, ValueError):
        pass
    return uzb, nf, wer


def wpis_manifest(d, wpis):
    p = os.path.join(d, "manifest.json")
    if os.path.exists(p):
        m = json.load(open(p))
        m["kont_s2g"] = wpis
        json.dump(m, open(p, "w"), indent=2, ensure_ascii=False)


def main():
    os.makedirs(S2, exist_ok=True)
    assert json.load(open(os.path.join(S2, LOT_1, "wyniki.json")))["wazny"] is True
    assert not os.path.exists(os.path.join(S2, "kampania_g.json")), "kampania_g.json istnieje"
    if shm_pliki():
        log(f"ALARM D1: /dev/shm nie jest pusty ({len(shm_pliki())} plików), potrzebny wsl --shutdown, 0 bootów")
        sys.exit(7)
    log(f"=== S2′ ANEKS_KONT-1b start: lot 1/8 {LOT_1}, budżet {BUDZET}, uptime {open('/proc/uptime').read().split()[0]} s")
    env = {**os.environ, "PERC2_FASTDDS_PROFILE": PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
    with open(os.path.join(S2, "zegar_stan_przed_g.txt"), "w") as f:
        subprocess.run("timedatectl status; systemctl is-active systemd-timesyncd; cat /sys/devices/system/clocksource/clocksource0/current_clocksource", shell=True, stdout=f, stderr=subprocess.STDOUT)
    subprocess.run(["sudo", "-n", "systemctl", "stop", "systemd-timesyncd"], check=True)
    stop, booty, wazne, kolejka, fail_streak = None, 0, 1, list(PLAN), 0
    import kont_s2_analyze as A
    try:
        while kolejka and booty < BUDZET:
            nm, ep = kolejka.pop(0)
            name = wolna_nazwa(nm)
            dg = {0: "D1", 1: "D2"}.get(booty)
            ok, z = zegar(name)
            log(f"{name}: próbnik {z['skoki']} skoków ok={ok}")
            if not ok:
                stop = "STOP-KONT2-ZEGAR"
                break
            znal, zywe = sprzataj_sieroty()
            if znal:
                log(f"{name}: sieroty TERM {znal}, żywe po {TERM_WAIT_S} s: {zywe}")
            if zywe:
                stop = "STOP-KONT2-SIEROTY"
                log(f"ALARM {stop}: {zywe}")
                break
            shm = shm_krok(name, booty >= 1)
            log(f"{name}: {dg or 'lot'} /dev/shm sprzątanie={shm['sprzatanie']} przed={shm['plikow_przed']} po={shm['plikow_po']} trzymane={shm['trzymane_przed']}")
            for _ in range(4):
                r = subprocess.run(["bash", os.path.join(T, "kont_s2_boot.sh"), str(BOOTY_S2 + booty + 1), name, str(ep)], cwd=ROOT, env=env, capture_output=True, text=True)
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
            uzb, nf, wer = sonda_stan(d)
            wpis_manifest(d, {"aneks": "ANEKS_KONT-1b", "boot_s2p": booty, "diagnoza": dg, "shm": shm, "sieroty_term": {str(k): v for k, v in znal.items()}})
            w = A.analyze(d)
            log(f"{name} rc={r.returncode} boot {booty}/{BUDZET}: uzbrojony={uzb} n_frames={nf} sonda={wer} ważny={w.get('wazny')} ({w.get('powod_niewazny')}) V2p={w.get('v2p')} eps60={w.get('eps_60')} eps70={w.get('eps_70')} delta={w.get('delta_max')} p95={w.get('eps0_p95_nominal')} rmax={w.get('r_gt_max')} xy={w.get('xy_valid_cale_okno')} flipy={w.get('przeskoki_cs_gnss')} zejscie={w.get('powod_zejscia')} t_entry={w.get('t_entry')}")
            if w.get("breach"):
                stop = "STOP-KONT2-BREACH"
                break
            if w.get("refuse_nominal"):
                stop = "STOP-KONT2-REFUSE"
                break
            if w.get("przeskoki_cs_gnss"):
                stop = "STOP-KONT2-PRZESKOK"
                break
            if not uzb:
                fail_streak += 1
                log(f"ALARM FAIL sondy przed uzbrojeniem: {name} n_frames={nf} sonda={wer}, seria {fail_streak}")
                if dg:
                    stop = "STOP-KONT2b"
                    log(f"ALARM {stop}: FAIL {dg} ({'kandydat 1 obalony' if dg == 'D2' else 'czysty host'})")
                    break
                if fail_streak >= 2:
                    stop = "STOP-KONT2-SONDA"
                    break
            else:
                fail_streak = 0
                if dg == "D2":
                    log("D2 PASS: kandydat 1 (SHM) przyjęty roboczo, sprzątanie przed każdym bootem")
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
        with open(os.path.join(S2, "zegar_stan_po_g.txt"), "w") as f:
            subprocess.run("timedatectl status; systemctl is-active systemd-timesyncd", shell=True, stdout=f, stderr=subprocess.STDOUT)
        log(f"KONIEC booty={booty} ważne={wazne} stop={stop}")
        json.dump({"booty": booty, "wazne": wazne, "stop": stop}, open(os.path.join(S2, "kampania_g.json"), "w"))
    print("KONIEC", booty, wazne, stop)


if __name__ == "__main__":
    main()
