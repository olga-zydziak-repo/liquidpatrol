#!/usr/bin/env python3
"""results/TEACH2/tools/teach2_run.py — kolejka lotu długiego TEACH-II (PRE_TEACH2 §5, PROMPT_TEACH2_S1 §1–§4; ≤ 3 booty)
= wzór results/TEACH/tools/teach_s3_run.py i results/NAD2/tools/nad2_s4_run.py (oba nietknięte).

Jedna pozycja L1: łata S, epizod 10 (c10_s01), manifest wahadła results/TEACH2/scenario_manifest_teach2L.json z sumą
(results/TEACH2/teach2_manifest.json; boot: NAD3_MANIFEST / NAD3_MANIFEST_SHA — strażnik boota sprawdza sumę), KONT_INJECT_T 200
(argument INJECT_T), NAD2_T_CONT_S 600.5, NAD2_WALL_MAX_CUT_S 1000, NAD2_ULG_LIMIT_MB 10 (w procesie kolejki przed importem nad2_ulg),
producent w pętli (BOOT_CIEN 0), TEACH_ETAP s3 (strażnik kopii boota), boot results/TEACH2/tools/teach2_boot.sh (kopia teach_boot.sh,
zmiana wyłącznie ścieżki wyników → results/TEACH2/s1). Strażniki stanowiska jak S3 (kont_s2_campaign_g READ-ONLY, ścieżki na
results/TEACH2/s1): lista procesów Windows (Chrome, ChatGPT), timesyncd nieaktywny, bramka zdrowia (A, NO-GO ⇒ 3 min ⇒ C; trzecie
NO-GO ⇒ STOP, nic nie zużyte), próbnik zegara, sieroty; telemetria hosta, rejestrator kadrów (wszystkie na stanowisku
~/teach_stanowisko/<nazwa>/, 12 do repo); próbnik pamięci procesu harness/nadir_obs.py (VmRSS / VmHWM co 1 s, CLOCK_MONOTONIC —
ta sama podstawa co „mono” wierszy nf) → <boot>/pamiec_producenta.jsonl.
Po locie: wyciąg ULG (nad2_ulg), sędzia teach2_lot (T_CONT 600 s). Reguły §4 (status_lotu, decyzja — sprawdzane na sucho):
  - naruszenie B1–B4 ⇒ L-C, STOP-TEACH2-1-LC natychmiast;
  - sprawdzian < 100 % albo meta niezgodna ⇒ STOP-TEACH2-1-PRZYRZAD; detekcja zgodna / mapa po fladze / drugie zamknięcie ⇒
    STOP-TEACH2-1-SWIAT-KOD;
  - powtórka z rezerwy wyłącznie: boot nieważny stanowiskowo w locie, cięcie bez wejścia, REFUSE(τ*) ≤ 3 s od flagi przy wolnej
    (> 0.5 s) klatce fazy mapy trwającej w chwili flagi (lot zostaje w raporcie);
  - każdy inny wynik pierwszego ważnego lotu jest werdyktem (L-A / L-B), następnego lotu nie ma;
  - budżet 3 booty; czwarta potrzeba ⇒ STOP-TEACH2-1-BUDZET; NO-GO bramki zdrowia nie jest bootem;
  - breach ⇒ STOP-TEACH2-1-BREACH; kody drivera 41–45 ⇒ STOP-TEACH2-1-OSLONA-<kod>; 8–9 ⇒ STOP-TEACH2-1-DRIVER-<kod>;
    strażnik 4–6 ⇒ STOP-TEACH2-1-GUARD.
Księga results/TEACH2/s1/kampania_ksiega.jsonl. timesyncd: kolejka go nie uruchamia — po sesji akcja Olgi.
Użycie: teach2_run.py [--sucho]. Wyjście: results/TEACH2/s1/kampania_teach2.log, kampania_teach2.json.
"""
import hashlib
import json
import os
import subprocess
import sys
import threading
import time

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [os.path.join(ROOT, "results/KONT/tools"), os.path.join(ROOT, "results/NADIR/tools"),
                os.path.join(ROOT, "results/NAD2/tools"), os.path.join(ROOT, "results/TEACH/tools"),
                os.path.join(ROOT, "results/TEACH2/tools"), ROOT]
os.environ["NAD2_ULG_LIMIT_MB"] = "10"                 # nad2_ulg czyta LIMIT przy imporcie (jak nad2_s4_run.py:42)
import kont_s2_campaign_g as G                         # READ-ONLY
import nadir_s4_tel as TL                              # READ-ONLY
import teach2_lot as LOT

S1 = os.path.join(ROOT, "results/TEACH2/s1")
G.S2 = S1
G.LOG = os.path.join(S1, "kampania_teach2.log")
G.SKRYPTY = G.SKRYPTY | {"kont_s4_flight", "nadir_s4_flight", "nad2_flight", "nad3_flight", "teach_flight", "intruder_motion",
                         "nadir_obs", "teach_rejestrator"}
log = G.log
BOOT = os.path.join(ROOT, "results/TEACH2/tools/teach2_boot.sh")
KSIEGA = os.path.join(S1, "kampania_ksiega.jsonl")
INFO_MAN = os.path.join(ROOT, "results/TEACH2/teach2_manifest.json")
STANOWISKO = os.path.expanduser("~/teach_stanowisko")
BUDZET = 3
TASKLIST = "/mnt/c/Windows/System32/tasklist.exe"
ZAKAZANE = ("chrome.exe", "chatgpt.exe")
NAZWA = "L1_S_c10"
EPIZOD, INJECT = "10", "200"


def info_man():
    return json.load(open(INFO_MAN))


def env_L():
    im = info_man()
    return {"BOOT_NADIR_MODE": "1", "BOOT_KONT_MODE": "1", "BOOT_PASSTHROUGH": "0", "TEACH_ETAP": "s3", "BOOT_LATA": "S", "BOOT_CIEN": "0",
            "NAD3_MANIFEST": im["manifest"], "NAD3_MANIFEST_SHA": im["sha256"], "NAD2_T_CONT_S": "600.5", "NAD2_WALL_MAX_CUT_S": "1000"}


def niezmiennik():
    im = info_man()
    p = os.path.join(ROOT, im["manifest"])
    eps = json.load(open(p))["episodes"]
    return (hashlib.sha256(open(p, "rb").read()).hexdigest() == im["sha256"] and im["sprawdziany_c10_s01"]["pierwsze_200s_rowne_v2"]
            and len(eps) == 120 and all(i == e["episode_id"] for i, e in enumerate(eps)) and eps[int(EPIZOD)]["scenario_id"] == "c10_s01"
            and eps[int(EPIZOD)]["ep_dur_s"] >= 830.0)


def procesy():
    try:
        out = subprocess.run([TASKLIST, "/FO", "CSV"], capture_output=True, timeout=30).stdout.decode("utf-8", errors="replace").lower()
    except (OSError, subprocess.TimeoutExpired) as ex:
        return False, repr(ex)
    zn = {z: out.count(f'"{z}"') for z in ZAKAZANE}
    return all(v == 0 for v in zn.values()), zn


def ksiega():
    return [json.loads(l) for l in open(KSIEGA) if l.strip()] if os.path.exists(KSIEGA) else []


def wolna(nm):
    n = 1
    while True:
        c = nm if n == 1 else f"{nm}_r{n}"
        if not os.path.exists(S1) or not any(f == c or f.startswith(c + "_") or f.startswith(c + ".") for f in os.listdir(S1)):
            return c
        n += 1


def status_lotu(rc, names, kt, sd):
    """Reguły §4 po locie ⇒ (status, stop | None). status ∈ werdykt (L-A, L-B, L-C), powtórka (niewazny_stanowisko, bez_wejscia,
    powtorka_tau_wolna) albo STOP."""
    if rc in (41, 42, 43, 44, 45):
        return "oslona", f"STOP-TEACH2-1-OSLONA-{rc}"
    if rc in (8, 9):
        return "driver", f"STOP-TEACH2-1-DRIVER-{rc}"
    if any(n in ("breach", "breach_gt") for n in names):
        return "breach", "STOP-TEACH2-1-BREACH"
    if "episode_start" not in names:
        return ("niewazny_stanowisko", None) if (kt is not None and not kt.get("ok")) else ("bez_epizodu", "STOP-TEACH2-1-BEZ-EPIZODU")
    if sd is None:
        return "bez_sedziego", "STOP-TEACH2-1-SEDZIA"
    if not sd["litera_ok"]:
        return "L-C", "STOP-TEACH2-1-LC"
    nw = sd.get("niewaznosc") or []
    if "przyrzad" in nw:
        return "niewazny_przyrzad", "STOP-TEACH2-1-PRZYRZAD"
    if "swiat_kod" in nw:
        return "niewazny_swiat_kod", "STOP-TEACH2-1-SWIAT-KOD"
    if "wejscie" in nw:
        return "bez_wejscia", None
    if not sd["wazny"]:
        return "niewazny_inny", "STOP-TEACH2-1-NIEWAZNY"
    if sd.get("powtorka_dopuszczona"):
        return "powtorka_tau_wolna", None
    return sd["werdykt"], None


POWTORKI = ("niewazny_stanowisko", "bez_wejscia", "powtorka_tau_wolna")


def decyzja(status, zuzyte):
    """Po boocie: ('koniec', None) — werdykt; ('dalej', None) — powtórka z rezerwy; ('stop', kod)."""
    if status in ("L-A", "L-B"):
        return "koniec", None
    if status in POWTORKI:
        return ("stop", "STOP-TEACH2-1-BUDZET") if zuzyte >= BUDZET else ("dalej", None)
    return "stop", None


class Pamiec:
    """Próbnik pamięci procesu harness/nadir_obs.py (VmRSS, VmHWM) co 1 s; mono = time.monotonic (CLOCK_MONOTONIC)."""

    def __init__(self, path):
        self.f, self.stop = open(path, "w"), False
        self.th = threading.Thread(target=self._run, daemon=True)
        self.th.start()

    def _pid(self):
        for p in os.listdir("/proc"):
            if p.isdigit():
                try:
                    c = open(f"/proc/{p}/cmdline", "rb").read().split(b"\0")
                except OSError:
                    continue
                if any(x.endswith(b"harness/nadir_obs.py") for x in c) and int(p) != os.getpid():
                    return int(p)
        return None

    def _run(self):
        pid = None
        while not self.stop:
            pid = pid if pid and os.path.exists(f"/proc/{pid}") else self._pid()
            if pid:
                try:
                    st = {l.split(":")[0]: l.split()[1] for l in open(f"/proc/{pid}/status") if l.startswith(("VmRSS", "VmHWM"))}
                    self.f.write(json.dumps({"mono": round(time.monotonic(), 3), "pid": pid, "rss_mb": round(int(st["VmRSS"]) / 1024, 1),
                                             "hwm_mb": round(int(st["VmHWM"]) / 1024, 1)}) + "\n")
                    self.f.flush()
                except (OSError, KeyError):
                    pid = None
            time.sleep(1.0)

    def close(self):
        self.stop = True
        self.th.join(timeout=5)
        self.f.close()


BRAMKA_PY = """
import json, os, sys
sys.path[:0] = {sciezki!r}
import nadir_s4_bramka as B
B.OUT = {out!r}
B.zegar_ok()
r = B.przyrzad_a({tag!r}, tel={tel!r})
print("WYNIK " + json.dumps({{k: r.get(k) for k in ("wariant", "tempo", "GO", "czolowka_operatora")}}, ensure_ascii=False, default=str))
"""


def bramka_zdrowia(name):
    proby = []
    for k in range(3):
        if k:
            time.sleep(180)
        tag = f"{name}_g{k + 1}"
        kod = BRAMKA_PY.format(sciezki=[os.path.join(ROOT, "results/NADIR/tools"), os.path.join(ROOT, "results/KONT/tools"), ROOT],
                               out=os.path.join(S1, "bramka"), tag=tag, tel=bool(k))
        w = subprocess.run([sys.executable, "-c", kod], cwd=ROOT, capture_output=True, text=True)
        line = next((l for l in w.stdout.splitlines() if l.startswith("WYNIK ")), None)
        if w.returncode != 0 or line is None:
            log(f"{name}: bramka zdrowia błąd rc={w.returncode}: {(w.stdout + w.stderr)[-600:]}")
            return None, proby
        r = json.loads(line[6:])
        p = {"tag": tag, "wariant": r["wariant"], "tempo": r["tempo"], "GO": r["GO"], "czolowka_operatora": r.get("czolowka_operatora"),
             "t": time.strftime("%F %T")}
        proby.append(p)
        with open(os.path.join(S1, "bramka_ksiega.jsonl"), "a") as f:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
        log(f"{name}: bramka zdrowia {tag} ({p['wariant']}) GO={p['GO']} tempo={p['tempo']}")
        if r["GO"]:
            return True, proby
    return False, proby


def boot(bn):
    """Zwraca (stop | None, wpis | None). wpis = zużyty boot (zapisany w księdze)."""
    if not niezmiennik():
        return "STOP-TEACH2-1-MANIFEST", None
    ok, zn = procesy()
    log(f"boot {bn}: procesy Windows {zn}")
    if not ok:
        return "STOP-TEACH2-1-PROCESY", None
    if subprocess.run(["systemctl", "is-active", "--quiet", "systemd-timesyncd"]).returncode == 0:
        return "STOP-TEACH2-1-TIMESYNCD", None
    name = wolna(NAZWA)
    go, proby = bramka_zdrowia(name)
    if go is None:
        return "STOP-TEACH2-1-BRAMKA", None
    if not go:
        return "STOP-TEACH2-1-STANOWISKO", None
    ok, z = G.zegar(name)
    log(f"{name}: próbnik zegara {z['skoki']} skoków ok={ok}")
    if not ok:
        return "STOP-TEACH2-1-ZEGAR", None
    znal, zywe = G.sprzataj_sieroty()
    if zywe:
        return "STOP-TEACH2-1-SIEROTY", None
    shm = G.shm_krok(name, False)
    env = {**os.environ, **env_L(), "PERC2_FASTDDS_PROFILE": G.PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
    tp = os.path.join(S1, f"{name}_host_telemetria.jsonl")
    tl = TL.Telemetria2(tp, 3600)
    pm_p = os.path.join(S1, f"{name}_pamiec_producenta.jsonl")
    pm = Pamiec(pm_p)
    kad = os.path.join(STANOWISKO, name)
    rej = subprocess.Popen([sys.executable, os.path.join(ROOT, "results/TEACH/tools/teach_rejestrator.py"), "--world", "world_teach_S",
                            "--model", "x500_teach_flow_0", "--out", kad],
                           stdout=open(os.path.join(S1, f"{name}_rejestrator.log"), "w"), stderr=subprocess.STDOUT,
                           env={**os.environ, "GZ_IP": "127.0.0.1"}, start_new_session=True)
    log(f"=== TEACH2 L1 {name} boot {bn}/{BUDZET} env={env_L()} epizod={EPIZOD} inject={INJECT}")
    t0 = time.time()
    try:
        for _ in range(4):
            r = subprocess.run(["bash", BOOT, str(bn), name, EPIZOD, INJECT], cwd=ROOT, env=env, capture_output=True, text=True)
            open(os.path.join(S1, f"{name}_driver.log"), "a").write(r.stdout + r.stderr)
            if r.returncode != 3:
                break
            log(f"{name}: env-block rc=3, nie boot, czekam 120 s"); time.sleep(120)
        else:
            return "STOP-TEACH2-1-ENV", None
    finally:
        tl.close()
        pm.close()
        rej.terminate()
        try:
            rej.wait(timeout=15)
        except subprocess.TimeoutExpired:
            rej.kill()
    if r.returncode in (4, 5, 6):
        log(f"{name}: guard rc={r.returncode}, stos nie ruszył, nie boot")
        return "STOP-TEACH2-1-GUARD", None
    d = os.path.join(S1, name)
    if os.path.isdir(d):
        for src, dst in ((tp, "host_telemetria.jsonl"), (pm_p, "pamiec_producenta.jsonl")):
            if os.path.exists(src):
                os.replace(src, os.path.join(d, dst))
    try:
        kt = json.load(open(os.path.join(d, "kont_tempo.json")))
    except (OSError, ValueError):
        kt = None
    trp = os.path.join(d, "trace.jsonl")
    ev = [json.loads(l) for l in open(trp) if '"event"' in l] if os.path.exists(trp) else []
    names = [e.get("ev") for e in ev]
    wpis = {"boot": bn, "nazwa": name, "rc": r.returncode, "czas_s": round(time.time() - t0, 1), "tempo": kt, "bramka_zdrowia": proby,
            "shm": shm, "procesy": zn, "epizod_wystartowal": "episode_start" in names, "breach": any(n in ("breach", "breach_gt") for n in names),
            "wejscie_denial": "denial" in names, "teach_producent": next((e for e in ev if e.get("ev") == "teach_producent"), None),
            "kadry_stanowisko": kad, "n_kadrow": len(os.listdir(kad)) if os.path.isdir(kad) else 0, "t": time.strftime("%F %T")}
    sd = None
    if "episode_start" in names and r.returncode not in (8, 9, 41, 42, 43, 44, 45):
        import nad2_ulg
        log(f"{name}: wyciąg ULG {nad2_ulg.wyciag(d)}")
        sd = LOT.sedzia(d, LOT.T_CONT_L, kad)
        wpis["sedzia"] = {k: sd.get(k) for k in ("wazny", "niewaznosc", "litera_ok", "wejscie", "DL_dostepne", "b1_nieocenione_w_misji",
                                                 "tempo", "werdykt", "powtorka_dopuszczona")}
        wpis["sedzia"]["sprawdzian"] = sd["sprawdzian"]["procent"]
        wpis["sedzia"]["meta_ok"] = sd["meta"]["ok"]
        ep = sd.get("epizod") or {}
        wpis["sedzia"]["B"] = ep.get("B")
        wpis["sedzia"]["D_L"] = ep.get("D_L")
        wpis["sedzia"]["odmowa"] = ep.get("odmowa_w_misji")
        wpis["sedzia"]["max_blad_poprawki"] = ((sd.get("misja") or {}).get("blad_poprawki") or {}).get("max")
    wpis["status"], stop = status_lotu(r.returncode, names, kt, sd)
    with open(KSIEGA, "a") as f:
        f.write(json.dumps(wpis, ensure_ascii=False, default=str) + "\n")
    log(f"{name} boot {bn} rc={r.returncode} tempo={(kt or {}).get('dsim_dwall_settle')} status={wpis['status']} sędzia={wpis.get('sedzia')}")
    return stop, wpis


def main():
    sucho = "--sucho" in sys.argv[1:]
    os.makedirs(S1, exist_ok=True)
    ks = ksiega()
    zuzyte = len(ks)
    werd = next((w for w in ks if w.get("status") in ("L-A", "L-B", "L-C")), None)
    log(f"=== TEACH2 {'(na sucho) ' if sucho else ''}start: zużyte {zuzyte}/{BUDZET}, werdykt {werd and werd['status']}")
    if sucho:
        print(json.dumps({"nazwa": wolna(NAZWA), "env": env_L(), "args": [EPIZOD, INJECT], "budzet": BUDZET, "zuzyte": zuzyte,
                          "niezmiennik": niezmiennik(), "NAD2_ULG_LIMIT_MB": os.environ["NAD2_ULG_LIMIT_MB"], "boot": BOOT}, ensure_ascii=False))
        return
    stop = None
    try:
        while werd is None:
            if zuzyte >= BUDZET:
                stop = "STOP-TEACH2-1-BUDZET"; break
            st, w = boot(zuzyte + 1)
            if w is not None:
                zuzyte += 1
            if st:
                stop = st; break
            dec, kod = decyzja(w["status"], zuzyte)
            if dec == "koniec":
                werd = w; break
            if dec == "stop":
                stop = kod or f"STOP-TEACH2-1-{w['status']}"; break
            log(f"boot {zuzyte}: {w['status']} — powtórka z rezerwy ({zuzyte}/{BUDZET})")
    except Exception as ex:
        stop = "STOP-TEACH2-1-WYJATEK"; log(f"ALARM {stop}: {ex!r}"); raise
    finally:
        log(f"KONIEC booty={zuzyte}/{BUDZET} werdykt={werd and werd['status']} stop={stop}")
        p = os.path.join(S1, "kampania_teach2.json")
        prev = json.load(open(p)) if os.path.exists(p) else {"przebiegi": []}
        prev["przebiegi"].append({"booty": zuzyte, "werdykt": werd and werd["status"], "stop": stop, "t": time.strftime("%F %T")})
        json.dump(prev, open(p, "w"), ensure_ascii=False, indent=1, default=str)
    print("KONIEC", zuzyte, werd and werd["status"], stop)


if __name__ == "__main__":
    main()
