#!/usr/bin/env python3
"""results/TEACH/tools/teach_s2_dryrun.py — PROMPT_TEACH_S2 §2.6: próba drivera i producenta na sucho przed pierwszym bootem (0 bootów);
wzór results/NAD3/tools/nad3_s2_dryrun.py (nietknięty).

(1) main() drivera results/TEACH/tools/teach_flight.py przez atrapy results/KONT/tools/kont_s4_dryrun_c.py (READ-ONLY, podmieniona
    ścieżka DRIVER; MAVSDK, gz, EKF, rclpy, watchdog, rtf_stream), manifest NAD3 v2, tabela TEACH:
      „start” — NADIR_MODE=1, TEACH_MODE=1, NADIR_OSLONA=nad3, tabela i suma TEACH ⇒ dojście do uzbrojenia (arm_retry), selfcheck
      certów TEACH PASS, meta teach (echo tabeli TEACH);
      odmowy kodem 8: bez TEACH_MODE; tabela P1 NAD3 zamiast TEACH; bez NADIR_OSLONA. Kontrolnie 42 (zła suma).
(2) blok zgodności producenta DOSŁOWNYM tekstem z pliku drivera (od `if rama is not None and shield.nad3:` do `for ep in episodes:`):
    lot (datagram zrodlo teach, meta TEACH, tor = tor.json, cień fałsz, bez nad3) ⇒ start; cień (TEACH_CIEN=1, bez datagramów, meta
    cień prawda) ⇒ start; kod 9: datagram Rama (bez zrodlo), meta z blokiem nad3, inna suma toru, meta cień przy env lotu, meta lot
    przy env cienia, meta bez litery TEACH.
(3) producent: odmowy nadir_obs 47 (TEACH + NAD3_DEGRAD) i 48 (cień bez TEACH_T_CIEN); strażnik boota teach_boot.sh pod
    `bash -uo pipefail` (BOOT_LATA spoza S/M/J, BOOT_CIEN spoza 0/1, cień bez BOOT_T_CIEN, maska bez pliku, tryb spoza 1/1/0,
    TEACH_ETAP spoza s2/s3 ⇒ kod 5 przed czymkolwiek ciężkim; poprawna kombinacja dochodzi do kontroli profilu FastDDS); `bash -n`.
(4) epizody syntetyczne z flagą w sekwencji bootu: proces harness/nadir_obs.py (gałąź TEACH, moduł ładowany jak w testach, atrapa
    obrazu gz = render terenu łaty S przy pozie GT z trace, migawka EKF z wiersza nf) na KAŻDEJ klatce lotu NAD3 (od 13 s sim);
    flaga przez teach_flaga: przed logiem ULG sekwencja bootu (13 s: 0 — pierwsza wiadomość; 20 s: 1 — GPS po higienie; 107.1 s: 0 —
    restart EKF przedlotu, kont_ekf_preflight.json; 115 s: 1), od logu ULG zmiany cs_gnss_pos z estimator_status_flags.
      „lot” — p01_p1_c05_zew (cięcie 173.696): datagramy do gniazda; rama.jsonl odtworzona ścieżką drivera (nad3_krok, osłona nad3
      z tabelą TEACH, stan ramy z datagramów TEACH dostarczanych w miejscu seq lotu), trace z meta teach ⇒ teach_analyze: B1–B4,
      ważność; fazy wierszy sprzed startu ∈ {przed_mapa, mapa}; jedno zamknięcie, mapa niepusta, chwila flagi producenta = spadek ULG;
      zatrzask skasowany w chwili startu (armed);
      „cień” — p05_p1_nom_zew_NA (nominał), TEACH_T_CIEN 173.6: nic nie wysłane, jedno zamknięcie w chwili cienia, wiersz niesie flagę
      rzeczywistą i zatrzask, zatrzask w chwili startu skasowany.
ANEKS_TEACH-2 (TEACH-2A): ważność wg „zero detekcji zgodnych z manifestem” (teach_analyze), producent z NADIR_FLIP=0 jak w boocie.
Wyjście: results/TEACH/s2/dryrun/dryrun_s2.json (+ katalogi epizodów syntetycznych w katalogu tymczasowym — nie w repo).
"""
import asyncio
import importlib.util
import json
import math
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import types

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
T = os.path.join(ROOT, "results/TEACH/tools")
OUT = os.path.join(ROOT, "results/TEACH/s2/dryrun")
DRV = os.path.join(T, "teach_flight.py")
MAN = "results/NAD3/s1/scenario_manifest_nad3_v2.json"
TAB = os.path.join(ROOT, "results/TEACH/s1/freeze_U_TEACH.json")
TAB_P1 = os.path.join(ROOT, "results/NAD3/s1/freeze_U_P1.json")
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/KONT/tools"), T, os.path.join(ROOT, "results/NAD3/tools"),
                os.path.join(ROOT, "results/NAD3_RECON/tools"), os.path.join(ROOT, "results/ORTO_RECON/tools")]
from r03 import nadir_shield as NS                                  # noqa: E402

SHA = json.load(open(TAB))["sha256_tabeli"]
SHA_P1 = json.load(open(TAB_P1))["sha256_tabeli"]
TOR = json.load(open(os.path.join(ROOT, "results/TEACH/s1/tor.json")))["sha256_toru"]
ENV_START = {"NADIR_MODE": "1", "TEACH_MODE": "1", "NADIR_OSLONA": "nad3", "NAD3_TABELA": TAB, "NAD3_TABELA_SHA": SHA}
FLAGA_BOOTU = [(13.0, False), (20.0, True), (107.092, False), (115.0, True)]
LOT, NOM = "results/NAD3/s3/p01_p1_c05_zew", "results/NAD3/s3/p05_p1_nom_zew_NA"
T_CIEN = 173.6


# ---------------------------------------------------------------- (1)
def czesc1(tag, env):
    sock = os.path.join(tempfile.mkdtemp(), "drv.sock")
    out = os.path.join(tempfile.mkdtemp(prefix="teach_dry1_"), tag)
    r = subprocess.run([sys.executable, "-c", f"""
import os, sys, json
for k in list(os.environ):
    if k.startswith(("NADIR_", "NAD3_", "TEACH_", "NAD2_")):
        os.environ.pop(k)
os.environ.update({{"NADIR_SOCK_DRIVER": {sock!r}, "BENCH_MANIFEST": {MAN!r}, **{env!r}}})
sys.path[:0] = [{ROOT!r}, {os.path.join(ROOT, 'results/KONT/tools')!r}]
import kont_s4_dryrun_c as D
D.DRIVER = {DRV!r}
res = D.run({out!r}, "zdrowy")
import gc, io
for _f in gc.get_objects():
    if isinstance(_f, io.TextIOWrapper) and not _f.closed:
        try:
            _f.flush()
        except Exception:
            pass
print("WYNIK", json.dumps({{k: res[k] for k in ("wynik", "kroki")}}, ensure_ascii=False))
"""], capture_output=True, text=True, timeout=600, cwd=ROOT)
    line = next((l for l in r.stdout.splitlines() if l.startswith("WYNIK ")), None)
    w = json.loads(line[6:]) if line else None
    cs = open(os.path.join(out, "certs_selfcheck.log")).read() if os.path.exists(os.path.join(out, "certs_selfcheck.log")) else ""
    tp = os.path.join(out, "trace.jsonl")
    meta = next((json.loads(l) for l in open(tp) if '"meta"' in l), None) if os.path.exists(tp) else None
    txt = r.stdout + r.stderr
    return {"rc": r.returncode, "wynik": w, "teach_selfcheck_pass": "WERDYKT teach_certs_selfcheck: PASS" in cs,
            "odmowa": next((l.strip() for l in txt.splitlines() if "ODMOWA" in l), None),
            "meta_teach": (meta or {}).get("teach"), "ogon": txt[-300:] if r.returncode else ""}


def czesc1_all():
    przyp = {"start": (ENV_START, 0),
             "bez_TEACH_MODE": ({k: v for k, v in ENV_START.items() if k != "TEACH_MODE"}, 8),
             "tabela_P1_NAD3": ({**ENV_START, "NAD3_TABELA": TAB_P1, "NAD3_TABELA_SHA": SHA_P1}, 8),
             "bez_NADIR_OSLONA": ({k: v for k, v in ENV_START.items() if k != "NADIR_OSLONA"}, 8),
             "zla_suma_42": ({**ENV_START, "NAD3_TABELA_SHA": "0" * 64}, 42)}
    w = {}
    for tag, (env, rc) in przyp.items():
        x = czesc1(tag, env)
        x["oczekiwany_rc"] = rc
        if rc == 0:
            x["ok"] = (x["rc"] == 0 and (x["wynik"] or {}).get("wynik") == "zatrzymane: uzbrojenie" and x["teach_selfcheck_pass"]
                       and ((x["meta_teach"] or {}).get("oslona") or {}).get("sha256_tabeli") == SHA)
        else:
            x["ok"] = x["rc"] == rc
        w[tag] = x
        print("  (1)", tag, x["rc"], x["ok"], x["odmowa"], flush=True)
    w["PASS"] = all(v["ok"] for v in w.values() if isinstance(v, dict))
    return w


# ---------------------------------------------------------------- (2)
def czesc2():
    src = open(DRV, encoding="utf8").read()
    i = src.rfind("\n", 0, src.index("if rama is not None and shield.nad3:")) + 1
    j = src.rfind("\n", 0, src.index("    for ep in episodes:")) + 1
    blk = textwrap.dedent(src[i:j])
    assert "teach_producent" in blk and "os._exit(9)" in blk
    fn = "async def _blok():\n" + textwrap.indent(blk, "    ")

    class Wyjscie(Exception):
        pass

    class Rama:
        def __init__(self, dgs):
            self.nowe, self._d = [], list(dgs)

        def drain(self):
            self.nowe += self._d; self._d = []

    class Clock:
        t = 0.0

        def monotonic(self):
            Clock.t += 1.0; return Clock.t

    def run(dgs, meta, env):
        tmp = tempfile.mkdtemp()
        with open(os.path.join(tmp, "nadir_obs.jsonl"), "w") as f:
            f.write(json.dumps({"t": "meta", **meta}) + "\n")
        evs = []

        class OS:
            path = os.path
            environ = env

            @staticmethod
            def _exit(c):
                raise Wyjscie(c)

        class FF:
            def flush(self):
                pass

        async def sl(_):
            return None
        ns = {"rama": Rama(dgs), "shield": type("Sh", (), {"nad3": True})(), "time": Clock(), "os": OS, "OUTDIR": tmp, "ROOT": ROOT,
              "asyncio": type("A", (), {"sleep": staticmethod(sl)}), "json": json, "open": open, "_f": FF(),
              "ev": lambda s, **kw: evs.append((s, kw)), "print": lambda *a, **k: None}
        exec(compile(fn, DRV + ":TEACH-blok", "exec"), ns)
        try:
            asyncio.run(ns["_blok"]())
            return "start"
        except Wyjscie as e:
            return f"kod{e.args[0]}"
    DG = [{"seq": 1, "zrodlo": "teach", "ok": False, "powod": "przed_mapa"}]
    M_LOT = {"litera": "TEACH", "teach": {"sha256_toru": TOR, "cien": False}}
    M_CIEN = {"litera": "TEACH", "teach": {"sha256_toru": TOR, "cien": True}}
    przyp = {"lot": (DG, M_LOT, {}, "start"),
             "cien": ([], M_CIEN, {"TEACH_CIEN": "1"}, "start"),
             "datagram_Rama": ([{"seq": 1, "litera": "NAD2", "ok": False}], M_LOT, {}, "kod9"),
             "meta_z_nad3": (DG, {**M_LOT, "nad3": {"model": "bias_rad"}}, {}, "kod9"),
             "inna_suma_toru": (DG, {"litera": "TEACH", "teach": {"sha256_toru": "0" * 64, "cien": False}}, {}, "kod9"),
             "meta_cien_przy_locie": (DG, M_CIEN, {}, "kod9"),
             "meta_lot_przy_cieniu": ([], M_LOT, {"TEACH_CIEN": "1"}, "kod9"),
             "meta_bez_litery_TEACH": (DG, {"litera": "NAD2", "teach": M_LOT["teach"]}, {}, "kod9"),
             "lot_bez_datagramow": ([], M_LOT, {}, "kod9")}
    w = {}
    for k, (dg, meta, env, exp) in przyp.items():
        got = run(dg, meta, env)
        w[k] = {"wynik": got, "oczekiwany": exp, "ok": got == exp}
    w["PASS"] = all(v["ok"] for v in w.values())
    return w


# ---------------------------------------------------------------- (3)
def czesc3():
    out = {}

    def kod(env):
        e = {**{k: v for k, v in os.environ.items() if not k.startswith(("NADIR_", "NAD3_", "TEACH_"))}, **env}
        return subprocess.run([sys.executable, os.path.join(ROOT, "harness/nadir_obs.py"), "--world", "w", "--model", "m", "--out",
                               os.path.join(tempfile.mkdtemp(), "x.jsonl")], env=e, capture_output=True, text=True, timeout=120,
                              cwd=ROOT).returncode
    k47 = kod({"NADIR_MODE": "1", "TEACH_MODE": "1", "NAD3_DEGRAD": json.dumps({"model": "bias_rad"})})
    k48 = kod({"NADIR_MODE": "1", "TEACH_MODE": "1", "TEACH_CIEN": "1"})
    out["nadir_obs_kody"] = {"47": k47, "48": k48, "PASS": (k47, k48) == (47, 48)}
    baza = {"BOOT_NADIR_MODE": "1", "BOOT_KONT_MODE": "1", "BOOT_PASSTHROUGH": "0", "BOOT_LATA": "S", "BOOT_CIEN": "0", "TEACH_ETAP": "s2"}
    zle = {"lata_X": {"BOOT_LATA": "X"}, "lata_pusta": {"BOOT_LATA": ""}, "cien_2": {"BOOT_CIEN": "2"},
           "cien_bez_T": {"BOOT_CIEN": "1"}, "maska_bez_pliku": {"BOOT_MASKA": "/nie/ma/maski.png"}, "tryb_NM0": {"BOOT_NADIR_MODE": "0"},
           "tryb_PT1": {"BOOT_PASSTHROUGH": "1"}, "etap_s9": {"TEACH_ETAP": "s9"}}
    guard = {}
    for nm, zm in {**zle, "poprawna_kombinacja": {}, "poprawny_cien": {"BOOT_CIEN": "1", "BOOT_T_CIEN": "173.6"}}.items():
        env = {k: v for k, v in os.environ.items() if k != "PERC2_FASTDDS_PROFILE"}
        env.update({**baza, **zm})
        r = subprocess.run(["bash", "-uo", "pipefail", os.path.join(T, "teach_boot.sh"), "99", "dryrun_guard", "4", "-"], env=env,
                           capture_output=True, text=True, timeout=120, cwd=ROOT)
        guard[nm] = {"rc": r.returncode, "komunikat": (r.stdout.strip().splitlines() or [""])[-1][-160:]}
        guard[nm]["ok"] = (r.returncode == 5 and "brak PERC2_FASTDDS_PROFILE" in r.stdout) if nm.startswith("poprawn") else \
            (r.returncode == 5 and "GUARD" in r.stdout and "PERC2" not in r.stdout)
    for e in ("s2", "s9"):
        shutil.rmtree(os.path.join(ROOT, f"results/TEACH/{e}/dryrun_guard"), ignore_errors=True)
        p = os.path.join(ROOT, f"results/TEACH/{e}")
        ml = os.path.join(p, f"teach_{e}_monitor.log")
        if e == "s9" and os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
        elif os.path.exists(ml):
            os.remove(ml)
    out["straznik"] = {**guard, "PASS": all(v["ok"] for v in guard.values())}
    out["bash_n"] = {f: subprocess.run(["bash", "-n", os.path.join(T, f)]).returncode == 0 for f in ("teach_boot.sh", "teach_launch.sh")}
    out["bash_n"]["PASS"] = all(out["bash_n"].values())
    out["PASS"] = all(v["PASS"] for v in out.values())
    return out


# ---------------------------------------------------------------- (4)
def zaladuj(env, outp):
    old_env, old_argv = dict(os.environ), sys.argv
    for k in list(os.environ):
        if k.startswith(("NADIR_", "NAD3_", "TEACH_")):
            os.environ.pop(k)
    os.environ.update(env)
    sys.argv = ["nadir_obs.py", "--world", "w", "--model", "m", "--out", outp]
    try:
        spec = importlib.util.spec_from_file_location(f"nobs_dry_{time.monotonic_ns()}", os.path.join(ROOT, "harness/nadir_obs.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.argv = old_argv
        os.environ.clear(); os.environ.update(old_env)
    return mod


def zdarzenia_flagi(d):
    import nad3_dane as N
    u = N.czytaj_ulg(d)["estimator_status_flags"]
    ev, prev = list(FLAGA_BOOTU), None
    for t, v in zip(u["timestamp"], u["cs_gnss_pos"]):
        if v != prev:
            ev.append((float(t), bool(v))); prev = v
    return sorted(ev)


def epizod(d, env, t_konca=None):
    """Proces nadir_obs (gałąź TEACH) na każdej klatce lotu; zwraca (moduł, wiersze nf, meta, datagramy odebrane, zdarzenia flagi)."""
    import cv2
    import nad3_dane as N
    import orto_r2 as R2
    from harness import teach_map as TM
    tmp = tempfile.mkdtemp(prefix="teach_dry4_")
    sk = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sp = os.path.join(tmp, "drv.sock"); sk.bind(sp); sk.setblocking(False)
    outp = os.path.join(tmp, "nadir_obs.jsonl")
    mod = zaladuj({**env, "NADIR_FIX_SOCKS": sp, "NADIR_FLIP": "0"}, outp)          # TEACH-2A: lustro jak w boocie
    meta = {"t": "meta", "litera": "TEACH", "teach": {**mod._prod.echo(), "sha256_toru": mod._tor["sha256_toru"],
                                                      "cien": mod.TEACH_CIEN, "t_cien": mod.T_CIEN}}
    with open(outp, "w") as f0:
        pass
    mod.fout = open(outp, "w", buffering=1)
    mod.fout.write(json.dumps(meta) + "\n")
    th = threading.Thread(target=mod.worker, daemon=True); th.start()
    kam = R2.Kam(R2.kamera())
    teren = cv2.imread(os.path.join(ROOT, "results/TEACH_RECON/dane/S_2024-04-27.png"))
    g = R2.GT(d)
    ev = zdarzenia_flagi(d)
    ie, got = 0, []
    rows = [r for r in N.jl(d, "nadir_obs.jsonl", "nf")]
    if t_konca is not None:
        rows = [r for r in rows if r["sim"] <= t_konca]
    for r in rows:
        while ie < len(ev) and ev[ie][0] <= r["sim"]:
            mod.teach_flaga(ev[ie][1], ev[ie][0]); ie += 1
        p, q, _ = g(r["sim"])
        C, Rk = kam.poza(p, R2.rotm(q))
        img = kam.renderuj(teren, TM.T.PIKSEL_T, C, Rk)[0]
        mod._ekf.update({"q": r.get("ekf_q"), "q_mono": time.monotonic(), "pos": r.get("ekf_pos"), "hdg": r.get("ekf_hdg"),
                         "pos_mono": time.monotonic()})
        n0 = mod.st["n_proc"]
        sec = int(r["sim"]); nsec = int(round((r["sim"] - sec) * 1e9))
        mod.on_img(types.SimpleNamespace(header=types.SimpleNamespace(stamp=types.SimpleNamespace(sec=sec, nsec=nsec)), width=640,
                                         height=480, data=img[:, :, ::-1].tobytes()))
        t0 = time.monotonic()
        while mod.st["n_proc"] == n0 and time.monotonic() - t0 < 30:
            time.sleep(0.001)
        while True:
            try:
                got.append(json.loads(sk.recv(65536).decode()))
            except (BlockingIOError, InterruptedError):
                break
    mod._stop[0] = True; th.join(timeout=2); mod.fout.close()
    time.sleep(0.2)                                                  # worker podbija n_proc przed wysyłką — ostatni datagram
    while True:
        try:
            got.append(json.loads(sk.recv(65536).decode()))
        except (BlockingIOError, InterruptedError):
            break
    nf = [x for x in map(json.loads, open(outp)) if x.get("t") == "nf"]
    return mod, nf, outp, got, ev


def syntetyczny_lot():
    import nad3_dane as N
    import nad3_krok
    from r03 import config as C
    mod, nf, outp, got, ev = epizod(LOT, {"NADIR_MODE": "1", "TEACH_MODE": "1"})
    d = tempfile.mkdtemp(prefix="teach_syn_lot_")
    for f in ("boot.ulg", "kont_tempo.json", "demo.jsonl", "gt_intruder.jsonl", "percep_feed.jsonl.summary.json"):
        os.symlink(os.path.join(ROOT, LOT, f), os.path.join(d, f))
    shutil.copy(outp, os.path.join(d, "nadir_obs.jsonl"))
    oslona = NS.nad3_echo(type("X", (), {"nad3_T": NS.nad3_tabela(TAB, SHA)})())
    with open(os.path.join(ROOT, LOT, "trace.jsonl")) as fi, open(os.path.join(d, "trace.jsonl"), "w") as fo:
        for l in fi:
            if '"t": "meta"' in l:
                m = json.loads(l); m["teach"] = {"oslona": oslona}; l = json.dumps(m) + "\n"
            fo.write(l)
    L = N.Lot("p01", os.path.join(ROOT, LOT), None)
    seq_lotu = [r["fx"]["seq"] for r in L.nf]
    assert seq_lotu == list(range(1, len(seq_lotu) + 1)) and len(nf) == len(seq_lotu), "seq lotu ≠ kolejność klatek"
    st = {r["fx"]["seq"]: r["fx"] for r in nf}
    tk = {r["tick"]: r for r in N.jl(L.d, "trace.jsonl", "tk")}
    demo = {r["tick"]: r for r in N.jl(L.d, "demo.jsonl")}
    sh = NS.NadirShield(nadir_mode=True, kont_mode=True, nad3=True, tabela=TAB, tabela_sha=SHA); sh.reset()
    sh.pos_debounce_ticks = C.DEBOUNCE_TICKS
    sh.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))

    class Kl:
        d_ne, t_fix, kosz, tryb = [0.0, 0.0], None, None, None
    kl, seqs, ip = Kl(), sorted(st), 0
    t_ut = None
    with open(os.path.join(d, "rama.jsonl"), "w") as fr:
        for r in L.rama:
            obs = []
            while ip < len(seqs) and seqs[ip] <= r["seq"]:
                m = st[seqs[ip]]
                kl.d_ne, kl.t_fix = list(m["d_ne"]), m["t_fix"]
                if m.get("ok"):
                    kl.kosz, kl.tryb = m.get("kosz"), m.get("tryb")
                obs.append({k: m.get(k) for k in ("seq", "t_frame", "ok", "tryb", "powod", "p_fix_ne", "p_ekf_fix", "kosz", "zrodlo")})
                ip += 1
            t, dm = tk[r["tick"]], demo[r["tick"]]
            pe, se = r["p_ekf"], r["sp_ekf"]
            pc = [pe[0] + kl.d_ne[0], pe[1] + kl.d_ne[1], pe[2]]
            dd, _ = nad3_krok.krok(sh, r["tick"], pe, pc, dm["own_vel_ned"], se, [se[0] + kl.d_ne[0], se[1] + kl.d_ne[1], se[2]], "PATROL",
                                   t["pf"], t["cs"], r["sim"], t.get("dr"), kl)
            if t_ut is None and sh.kont_phase() != "NOMINAL":
                t_ut = r["sim"]
            k = dd["kont"]
            fr.write(json.dumps({**r, "d_ne": kl.d_ne, "p_corr": pc, "t_fix": kl.t_fix, "kosz": kl.kosz, "tryb": kl.tryb,
                                 "nadir": dd.get("nadir"), "ph": k["phase"], "R_k": k["R_k"], "nad2": dd.get("nad2"), "dec": dd["decision"],
                                 "obs": obs}) + "\n")
    import teach_analyze as A
    A.TABELA_SUCHO = None
    res = A.analyze(d, os.path.join(d, "wyniki_teach.json"))
    armed = next(e["sim"] for e in N.jl(L.d, "trace.jsonl", "event") if e.get("ev") == "armed")
    przed_start = [r for r in nf if r["sim"] < armed]
    fazy_przed = sorted({r["teach"]["faza"] for r in przed_start})
    zamk = [r for r in nf if r["teach"].get("georef")]
    t_spadku = max(t for t, v in ev if not v and t < 300)
    w = {"klatki": len(nf), "datagramy_odebrane": len(got), "fazy_przed_startem": fazy_przed,
         "t_flagi_w_chwili_startu": next((r["t_flagi"] for r in nf if r["sim"] >= armed), "brak"),
         "zamkniecia": len(zamk), "zamkniecie_sim": zamk[0]["sim"] if zamk else None,
         "t_flagi_producenta": mod._prod.t_flagi, "spadek_ulg": t_spadku, "wejscie_oslony_w_utrate": t_ut,
         "mapa_kadry": len(mod._prod.kadry), "mapa_kf": len(mod._prod.kf), "n_wiazan_w_rejestrze": len(zamk[0]["teach"]["georef"]["wiazania"]) if zamk else 0,
         "poprawki_przyjete": sum(1 for r in nf if r["fx"]["ok"]),
         "analizator": {"wazny": res.get("wazny"), "powod": res.get("powod_niewazny"),
                        "epizody": [{"scen": o["scenario_id"], **{b: o[b]["ok"] for b in ("B1", "B2", "B3", "B4") if b in o},
                                     "max_e_do_U": o["B1"]["max_e_do_U"], "D1": (o.get("D1") or {}).get("dostepne")} for o in res["epizody"]],
                        "zrodlo": {k: res["teach"].get(k) for k in ("warunki_waznosci", "blad_poprawki", "opoznienie_pierwszej_poprawki_s",
                                                                   "skok_delta_pierwsza_m", "przerwy", "georef", "n_det_znacznikow",
                                                                   "detekcje")}}}                     # TEACH-2A
    w["PASS"] = (w["datagramy_odebrane"] == w["klatki"] and set(fazy_przed) <= {"przed_mapa", "mapa"} and w["t_flagi_w_chwili_startu"] is None
                 and w["zamkniecia"] == 1 and w["mapa_kadry"] > 0 and abs(w["t_flagi_producenta"] - t_spadku) < 1e-6
                 and res.get("wazny") is True and all(e.get(b, True) for e in w["analizator"]["epizody"] for b in ("B1", "B2", "B3", "B4"))
                 and w["n_wiazan_w_rejestrze"] > 0)
    return w


def syntetyczny_cien():
    import nad3_dane as N
    mod, nf, outp, got, ev = epizod(NOM, {"NADIR_MODE": "1", "TEACH_MODE": "1", "TEACH_CIEN": "1", "TEACH_T_CIEN": str(T_CIEN)}, t_konca=260.0)
    armed = next(e["sim"] for e in N.jl(os.path.join(ROOT, NOM), "trace.jsonl", "event") if e.get("ev") == "armed")
    zamk = [r for r in nf if r["teach"].get("georef")]
    przy_starcie = next(r for r in nf if r["sim"] >= armed)
    zmiany, prev = [], None
    for r in nf:
        if r["gnss_rz"] != prev:
            zmiany.append((r["sim"], r["gnss_rz"], r["t_flagi_rz"])); prev = r["gnss_rz"]
    w = {"klatki": len(nf), "datagramy_odebrane": len(got), "zamkniecia": len(zamk), "zamkniecie_sim": zamk[0]["sim"] if zamk else None,
         "t_flagi_producenta": mod._prod.t_flagi, "mapa_kadry": len(mod._prod.kadry), "mapa_kf": len(mod._prod.kf),
         "flaga_rzeczywista_zmiany": zmiany, "zatrzask_rz_w_chwili_startu": przy_starcie["t_flagi_rz"],
         "poprawki_przyjete_w_rejestrze": sum(1 for r in nf if r["fx"]["ok"]),
         "fazy": sorted({r["teach"]["faza"] for r in nf})}
    w["PASS"] = (w["datagramy_odebrane"] == 0 and w["zamkniecia"] == 1 and w["t_flagi_producenta"] == T_CIEN and w["mapa_kadry"] > 0
                 and w["zatrzask_rz_w_chwili_startu"] is None and w["poprawki_przyjete_w_rejestrze"] > 0 and all("gnss_rz" in r for r in nf))
    return w


def main():
    os.makedirs(OUT, exist_ok=True)
    os.environ.setdefault("NAD3_CACHE", tempfile.mkdtemp(prefix="nad3_cache_"))
    wyn = {}
    print("(1) main() drivera", flush=True); wyn["1_main_drivera"] = czesc1_all()
    print("(2) blok zgodności producenta", flush=True); wyn["2_blok_producenta"] = czesc2(); print("  ", wyn["2_blok_producenta"]["PASS"])
    print("(3) producent i strażnik", flush=True); wyn["3_producent_straznik"] = czesc3(); print("  ", wyn["3_producent_straznik"]["PASS"])
    print("(4) epizod syntetyczny — lot", flush=True); wyn["4_lot"] = syntetyczny_lot(); print("  ", {k: v for k, v in wyn["4_lot"].items() if k != "analizator"})
    print("(4) epizod syntetyczny — cień", flush=True); wyn["4_cien"] = syntetyczny_cien(); print("  ", wyn["4_cien"])
    wyn["PASS"] = all(v["PASS"] for v in wyn.values())
    json.dump(wyn, open(os.path.join(OUT, "dryrun_s2.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print("PASS", wyn["PASS"])
    sys.exit(0 if wyn["PASS"] else 1)


if __name__ == "__main__":
    main()
