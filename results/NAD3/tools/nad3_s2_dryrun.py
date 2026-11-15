#!/usr/bin/env python3
"""results/NAD3/tools/nad3_s2_dryrun.py — PROMPT_NAD3_S2 §1.4: próba drivera i skryptów smoke na sucho przed pierwszym bootem (0 bootów);
wzór results/NAD2/tools/nad2_s2_dryrun.py (nietknięty).

(1) main() drivera results/NAD3/tools/nad3_flight.py przez atrapy results/KONT/tools/kont_s4_dryrun_c.py (READ-ONLY, podmieniona ścieżka
    DRIVER; MAVSDK, gz, EKF, rclpy, watchdog, rtf_stream), manifest NAD3, tabela P1:
      „start” — NADIR_MODE=1, NADIR_LITERA=NAD2, NADIR_OSLONA=nad3, tabela i suma P1 ⇒ dojście do uzbrojenia (arm_retry), selfcheck certów
      NAD3 PASS, meta nad3 (echo tabeli P1, sha);
      odmowy: bez NADIR_OSLONA ⇒ kod 8; litera NADIR1 ⇒ kod 8; brak tabeli ⇒ 41; zła suma ⇒ 42; NADIR_OSLONA=xx ⇒ 44; tabela
      z przeliczoną sumą i τ* 1.10 ⇒ 45. Kod 43 (nad2 + nad3) nieosiągalny z env drivera (driver woła NadirShield() bez argumentów;
      NADIR_OSLONA=nad2 wybiera reżim nad2 ⇒ kod 8) — sprawdzany testem jednostkowym test_nad3_s1.py.
(2) blok zgodności litery i degradacji DOSŁOWNYM tekstem z pliku drivera (od `if rama is not None and shield.nad3:` do
    `for ep in episodes:`) na stanie syntetycznym: litera NAD2 + meta nad3 P1 bias ⇒ start; bez degradacji + NAD3_BEZ_DEGRADACJI=1 ⇒
    start; bez degradacji bez zgody ⇒ 9; degradacja przy NAD3_BEZ_DEGRADACJI=1 ⇒ 9; E ≠ E tabeli ⇒ 9; model „bialy” ⇒ 9; f 2 ⇒ 9;
    K 1 ⇒ 9; datagram NADIR1 ⇒ 8; meta bez litery ⇒ 8.
(3) strażnik boota pod `bash -uo pipefail`: tryb spoza 1/1/0/NAD2, BOOT_PUNKT spoza P1–P3, BOOT_DEGRAD spoza {na_zewnatrz, do_srodka, 0},
    NAD3_ETAP spoza {s2, s3} ⇒ kod 5 przed czymkolwiek ciężkim; kombinacja poprawna przechodzi strażniki trybu do kontroli profilu
    FastDDS (kod 5 z komunikatem profilu); NAD3_DEGRAD budowany przez boot jest JSON-em = {bias_rad, kierunek, E_max = E tabeli, f 1, K 0,
    ziarno}; shellcheck (-S warning) nad3_boot.sh / nad3_launch.sh wobec NAD2: zero nowych ostrzeżeń; kolejka `nad3_s2_run.py --sucho`
    ⇒ plan [N1, N2, B3, B4]; mapowanie indeksów epizodów kolejki na scenariusze manifestu NAD3.
(4) epizod syntetyczny NAD3: lot NAD2 c05_s01_r2 (najbliższa geometria) przepisany na format bootu NAD3 — producent Rama(NAD2) na
    zapisanych klatkach → harness/nad3_degrad (P1, bias na zewnątrz, ziarno 1) → nadir_obs.jsonl z fx i fx_deg, meta nad3;
    rama.jsonl z kroku drivera (nad3_krok, osłona nad3 P1, stan ramy po degradacji, obs z polem nad3); trace z meta nad3 ⇒
    nad2_ulg.wyciag, nad3_analyze (B1–B4), nad3_s2_spr B4 ((r), (s1), (s3), b1 nieocenione) — oczekiwane PASS; kontrole negatywne:
    fx_deg z podmienionym E ⇒ (r) FAIL; meta producenta z kierunkiem do_srodka ⇒ (s3) FAIL. Ten sam lot bez degradacji ⇒ nad3_s2_spr B3
    ((k), (r)) PASS. nad3_s2_geom na nominale NAD2 nom_b2 (wyniki z nad2_analyze podstawione) — dymny bieg narzędzia.
(5) ANEKS_NAD3-1 §3.4 — próba procesu intruza: dla każdego epizodu planu (N2: 2, 3, 5, 10; B3/B4: 5; kontrolnie N1: 0, 1, 5, 10)
    wpis wybrany ścieżką drivera (funkcja _resolve_episodes wycięta DOSŁOWNIE z nad3_flight.py, BENCH_EPISODE_IDS z kolejki) i ścieżką
    procesu intruza (`manifest["episodes"][episode_id]` — wyrażenie sprawdzone w harness/intruder_motion.py, numer = episode_id wpisu
    drivera, jak w episode_control.json) ma ten sam scenario_id i te same odcinki; negatyw: manifest z S1 z planem N1 jak poleciał
    (indeksy 0, 1, 4, 5) ⇒ rozjazd dla numerów 5 (tor c10) i 10 (IndexError).
Wyjście: results/NAD3/s2/dryrun_v2/dryrun_s2.json (próba S2 na v2; pierwsza próba na S1 zostaje w results/NAD3/s2/dryrun).
"""
import asyncio
import copy
import gzip
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap

ROOT = "/home/olga/projects/liquidpatrol"
T = os.path.join(ROOT, "results/NAD3/tools")
OUT = os.path.join(ROOT, "results/NAD3/s2/dryrun_v2")
DRV = os.path.join(T, "nad3_flight.py")
MAN = "results/NAD3/s1/scenario_manifest_nad3_v2.json"            # ANEKS_NAD3-1 §3.4: próba powtórzona na v2
MAN_V1 = "results/NAD3/s1/scenario_manifest_nad3.json"
TAB = os.path.join(ROOT, "results/NAD3/s1/freeze_U_P1.json")
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/KONT/tools"), T, os.path.join(ROOT, "results/NAD2/tools"),
                os.path.join(ROOT, "results/NAD3_RECON/tools")]
from r03 import nadir_shield as NS

SHA_P1 = json.load(open(TAB))["sha256_tabeli"]
ENV_START = {"NADIR_MODE": "1", "NADIR_LITERA": "NAD2", "NADIR_OSLONA": "nad3", "NAD3_TABELA": TAB, "NAD3_TABELA_SHA": SHA_P1,
             "NAD3_BEZ_DEGRADACJI": "1"}


def tabela_45():
    doc = json.load(open(TAB))
    doc["tabela"]["tau_star_s"] = 1.10
    doc["sha256_tabeli"] = NS.tabela_sha(doc["tabela"])
    p = os.path.join(tempfile.mkdtemp(), "tabela_45.json")
    json.dump(doc, open(p, "w"))
    return p, doc["sha256_tabeli"]


def czesc1(tag, env):
    sock = os.path.join(tempfile.mkdtemp(), "drv.sock")
    out = os.path.join(OUT, tag)
    shutil.rmtree(out, ignore_errors=True)
    r = subprocess.run([sys.executable, "-c", f"""
import os, sys, json
for k in ("NADIR_LITERA", "NADIR_OSLONA", "NAD3_TABELA", "NAD3_TABELA_SHA", "NAD3_BEZ_DEGRADACJI", "NAD2_PASSTHROUGH", "NAD3_DEGRAD"):
    os.environ.pop(k, None)
os.environ.update({{"NADIR_SOCK_DRIVER": {sock!r}, "BENCH_MANIFEST": {MAN!r}, **{env!r}}})
sys.path[:0] = [{ROOT!r}, {os.path.join(ROOT, 'results/KONT/tools')!r}]
import kont_s4_dryrun_c as D
D.DRIVER = {DRV!r}
res = D.run({out!r}, "zdrowy")
import gc, io                                          # driver zatrzymany wyjątkiem atrapy przy uzbrojeniu — bufor trace niezrzucony
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
    meta = None
    tp = os.path.join(out, "trace.jsonl")
    if os.path.exists(tp):
        meta = next((json.loads(l) for l in open(tp) if '"meta"' in l), None)
    txt = r.stdout + r.stderr
    return {"rc": r.returncode, "wynik": w, "nad3_selfcheck_pass": "WERDYKT nad3_certs_selfcheck: PASS" in cs,
            "odmowa": next((l.strip() for l in txt.splitlines() if "ODMOWA" in l), None),
            "meta_nad3": (meta or {}).get("nad3"), "ogon": txt[-300:] if r.returncode not in (0,) else ""}


def czesc1_all():
    p45, s45 = tabela_45()
    przypadki = {
        "start": (ENV_START, 0),
        "bez_oslony_nad3": ({k: v for k, v in ENV_START.items() if k != "NADIR_OSLONA"}, 8),
        "litera_NADIR1": ({**ENV_START, "NADIR_LITERA": "NADIR1"}, 8),
        "brak_tabeli_41": ({**ENV_START, "NAD3_TABELA": "/nie/ma/tabeli.json"}, 41),
        "zla_suma_42": ({**ENV_START, "NAD3_TABELA_SHA": "0" * 64}, 42),
        "nieznany_rezim_44": ({**ENV_START, "NADIR_OSLONA": "xx"}, 44),
        "stala_tabeli_45": ({**ENV_START, "NAD3_TABELA": p45, "NAD3_TABELA_SHA": s45}, 45),
    }
    w = {}
    for tag, (env, rc) in przypadki.items():
        w[tag] = czesc1(tag, env)
        w[tag]["oczekiwany_rc"] = rc
        if rc == 0:
            w[tag]["ok"] = (w[tag]["rc"] == 0 and (w[tag]["wynik"] or {}).get("wynik") == "zatrzymane: uzbrojenie"
                            and w[tag]["nad3_selfcheck_pass"] and ((w[tag]["meta_nad3"] or {}).get("oslona") or {}).get("sha256_tabeli") == SHA_P1)
        else:
            w[tag]["ok"] = w[tag]["rc"] == rc
        print("  czesc1", tag, w[tag]["rc"], w[tag]["ok"], w[tag]["odmowa"], flush=True)
    w["kod_43"] = "nieosiągalny z env drivera — test_nad3_s1.py::test_odmowa_startu_kody"
    w["PASS"] = all(v["ok"] for v in w.values() if isinstance(v, dict))
    return w


def czesc2():
    src = open(DRV, encoding="utf8").read()
    i = src.rfind("\n", 0, src.index("if rama is not None and shield.nad3:")) + 1
    j = src.rfind("\n", 0, src.index("    for ep in episodes:")) + 1
    blk = textwrap.dedent(src[i:j])
    assert "nad3_degradacja" in blk and "os._exit(9)" in blk and "os._exit(8)" in blk
    fn = "async def _blok():\n" + textwrap.indent(blk, "    ")

    class Wyjscie(Exception):
        pass

    class Rama:
        def __init__(self, dgs):
            self.nowe = []; self._d = list(dgs)

        def drain(self):
            self.nowe += self._d; self._d = []

    class Clock:
        t = 0.0

        def monotonic(self):
            Clock.t += 1.0; return Clock.t

    def run(dgs, meta_lit, meta_n3, bez):
        tmp = tempfile.mkdtemp()
        with open(os.path.join(tmp, "nadir_obs.jsonl"), "w") as f:
            m = {"t": "meta"}
            if meta_lit:
                m["litera"] = meta_lit
            if meta_n3 is not None:
                m["nad3"] = meta_n3
            f.write(json.dumps(m) + "\n")
        evs = []

        class OS:
            path = os.path
            environ = {"NAD3_BEZ_DEGRADACJI": "1"} if bez else {}

            @staticmethod
            def _exit(c):
                raise Wyjscie(c)

        class Sh:
            nad3 = True
            nad3_T = {"E": 1.0}

        class FF:
            def flush(self):
                pass

        async def sl(_):
            return None
        ns = {"rama": Rama(dgs), "shield": Sh(), "time": Clock(), "asyncio": type("A", (), {"sleep": staticmethod(sl)}),
              "os": OS, "OUTDIR": tmp, "json": json, "open": open, "ev": lambda s, **kw: evs.append((s, kw)), "print": lambda *a, **k: None,
              "_f": FF(), "float": float, "int": int, "abs": abs}
        exec(compile(fn, DRV + ":NAD3-blok", "exec"), ns)
        try:
            asyncio.run(ns["_blok"]())
            return "start"
        except Wyjscie as e:
            return f"kod{e.args[0]}"
    D = [{"powod": "brak_ekf"}, {"seq": 2, "litera": "NAD2", "ok": False}]
    BIAS = {"model": "bias_rad", "kierunek": "na_zewnatrz", "E_max": 1.0, "f": 1, "K": 0, "ziarno": 1}
    przyp = {
        "bias_P1": (D, "NAD2", BIAS, False, "start"),
        "bez_degradacji_ze_zgoda": (D, "NAD2", None, True, "start"),
        "bez_degradacji_bez_zgody": (D, "NAD2", None, False, "kod9"),
        "degradacja_przy_zgodzie_bez": (D, "NAD2", BIAS, True, "kod9"),
        "E_niezgodne": (D, "NAD2", {**BIAS, "E_max": 1.75}, False, "kod9"),
        "model_bialy": (D, "NAD2", {**BIAS, "model": "bialy"}, False, "kod9"),
        "f_2": (D, "NAD2", {**BIAS, "f": 2}, False, "kod9"),
        "K_1": (D, "NAD2", {**BIAS, "K": 1}, False, "kod9"),
        "datagram_NADIR1": ([{"seq": 2, "ok": True}], "NAD2", BIAS, False, "kod8"),
        "meta_bez_litery": (D, None, BIAS, False, "kod8"),
    }
    w = {}
    for k, (dg, lit, n3, bez, exp) in przyp.items():
        got = run(dg, lit, n3, bez)
        w[k] = {"wynik": got, "oczekiwany": exp, "ok": got == exp}
    w["PASS"] = all(v["ok"] for v in w.values())
    return w


def sc(path):
    r = subprocess.run(["shellcheck", "-S", "warning", "-f", "json", path], capture_output=True, text=True)
    return {(x["code"], x["message"]) for x in json.loads(r.stdout or "[]")}


def czesc3():
    out = {}
    O = os.path.join(ROOT, "results/NAD2/tools")
    for new, old in (("nad3_boot.sh", "nad2_boot.sh"), ("nad3_launch.sh", "nad2_launch.sh")):
        n, o = sc(os.path.join(T, new)), sc(os.path.join(O, old))
        head = open(os.path.join(T, new)).read()
        out[new] = {"ostrzezenia": len(n), "w_oryginale": len(o), "nowe": [f"SC{c}: {m}" for c, m in sorted(n - o)],
                    "root_absolutny": f'ROOT="{ROOT}"' in head, "pipefail": "set -o pipefail" in head,
                    "bash_n": subprocess.run(["bash", "-n", os.path.join(T, new)]).returncode == 0}
        out[new]["PASS"] = not out[new]["nowe"] and out[new]["root_absolutny"] and out[new]["pipefail"] and out[new]["bash_n"]
    baza = {"BOOT_NADIR_MODE": "1", "BOOT_KONT_MODE": "1", "BOOT_PASSTHROUGH": "0", "BOOT_LITERA": "NAD2", "BOOT_PUNKT": "P1",
            "BOOT_DEGRAD": "na_zewnatrz", "NAD3_ETAP": "s2"}
    zle = {"tryb_NADIR1": {"BOOT_LITERA": "NADIR1"}, "tryb_PT1": {"BOOT_PASSTHROUGH": "1"}, "tryb_NM0": {"BOOT_NADIR_MODE": "0"},
           "punkt_P4": {"BOOT_PUNKT": "P4"}, "punkt_pusty": {"BOOT_PUNKT": ""}, "degrad_bialy": {"BOOT_DEGRAD": "bialy"},
           "degrad_pusty": {"BOOT_DEGRAD": ""}, "etap_s9": {"NAD3_ETAP": "s9"}}
    guard = {}
    for nm, zm in {**zle, "poprawna_kombinacja": {}}.items():
        env = {k: v for k, v in os.environ.items() if k != "PERC2_FASTDDS_PROFILE"}
        env.update({**baza, **zm})
        r = subprocess.run(["bash", "-uo", "pipefail", os.path.join(T, "nad3_boot.sh"), "99", "dryrun_guard", "4", "-"], env=env,
                           capture_output=True, text=True, timeout=60)
        guard[nm] = {"rc": r.returncode, "komunikat": (r.stdout.strip().splitlines() or [""])[-1][-160:]}
        guard[nm]["ok"] = (r.returncode == 5 and "brak PERC2_FASTDDS_PROFILE" in r.stdout) if nm == "poprawna_kombinacja" else \
            (r.returncode == 5 and "GUARD" in r.stdout and "PERC2" not in r.stdout)
    for e in ("s2", "s9"):
        p = os.path.join(ROOT, f"results/NAD3/{e}/dryrun_guard")
        shutil.rmtree(p, ignore_errors=True)
    out["straznik"] = {**guard, "PASS": all(v["ok"] for v in guard.values())}
    # NAD3_DEGRAD z boota: blok case wycięty dosłownie
    src = open(os.path.join(T, "nad3_boot.sh")).read()
    a = src.index('E3=$(python3'); b = src.index('N3ENV=();')
    blok = src[a:b]
    js = {}
    for deg in ("na_zewnatrz", "do_srodka", "0"):
        r = subprocess.run(["bash", "-uo", "pipefail", "-c", f'ROOT={ROOT}; TAB=results/NAD3/s1/freeze_U_P2.json; DEG={deg}; ZIA=7; '
                            f'MONLOG=/dev/null; NAME=x\n{blok}\nN3ENV=(); [ -n "$N3DEG" ] && N3ENV=(NAD3_DEGRAD="$N3DEG")\n'
                            'printf "%s\\n" "${N3ENV[@]}"; echo "BEZ=$N3BEZ"'], capture_output=True, text=True, cwd=ROOT)
        lines = r.stdout.strip().splitlines()
        cfg = json.loads(lines[0].split("=", 1)[1]) if lines and lines[0].startswith("NAD3_DEGRAD=") else None
        js[deg] = {"rc": r.returncode, "NAD3_DEGRAD": cfg, "bez": lines[-1] if lines else None}
    js_ok = (js["na_zewnatrz"]["NAD3_DEGRAD"] == {"model": "bias_rad", "kierunek": "na_zewnatrz", "E_max": 1.75, "f": 1, "K": 0, "ziarno": 7}
             and js["do_srodka"]["NAD3_DEGRAD"]["kierunek"] == "do_srodka" and js["0"]["NAD3_DEGRAD"] is None and js["0"]["bez"] == "BEZ=1"
             and js["na_zewnatrz"]["bez"] == "BEZ=0")
    out["nad3_degrad_z_boota"] = {**js, "PASS": js_ok}
    r = subprocess.run(["bash", "-uo", "pipefail", "-c", f"python3 {os.path.join(T, 'nad3_s2_run.py')} --sucho"], capture_output=True,
                       text=True, cwd=ROOT, timeout=120)
    line = next((l for l in r.stdout.splitlines() if l.startswith("{")), None)
    plan = json.loads(line) if line else {}
    man = json.load(open(os.path.join(ROOT, MAN)))["episodes"]
    mapa = {lot: [man[int(i)]["scenario_id"] for i in v["epizody"].split(",")] for lot, v in (plan.get("loty") or {}).items()}
    mapa_ok = mapa == {"N1": ["c00_s01", "c01_s01", "c05_s01", "c10_s01"], "N2": ["c02_s01", "c03_s01", "c05_s01", "c10_s01"],
                       "B3": ["c05_s01"], "B4": ["c05_s01"]} and all(i == e["episode_id"] for i, e in enumerate(man))
    out["kolejka_sucho"] = {"rc": r.returncode, "plan": plan.get("plan"), "mapa_epizodow": mapa,
                            "PASS": r.returncode == 0 and plan.get("plan") == ["N2", "B3", "B4"] and mapa_ok}   # N1 zużyty (ANEKS_NAD3-1 §3.6)
    # sprzątanie logu kolejki na sucho (kolejka pisze kampania_s2.log)
    out["PASS"] = all(v["PASS"] for v in out.values() if isinstance(v, dict))
    return out


def syntetyczny(tmp, cfg, nazwa):
    """Lot NAD2 c05_s01_r2 w formacie bootu NAD3 z degradacją cfg (None ⇒ bez)."""
    import nad3_dane as N
    import nad3_krok
    from harness import nad3_degrad as DG
    from harness.nadir_fix import Rama
    from r03 import config as C
    src = os.path.join(ROOT, "results/NAD2/s3/c05_s01_r2")
    d = os.path.join(tmp, nazwa)
    os.makedirs(d)
    for f in ("boot.ulg", "kont_tempo.json", "demo.jsonl", "gt_intruder.jsonl", "percep_feed.jsonl.summary.json"):
        os.symlink(os.path.join(src, f), os.path.join(d, f))
    oslona = NS.nad3_echo(type("X", (), {"nad3_T": NS.nad3_tabela(TAB, SHA_P1)})())
    with open(os.path.join(src, "trace.jsonl")) as fi, open(os.path.join(d, "trace.jsonl"), "w") as fo:
        for l in fi:
            if '"t": "meta"' in l:
                m = json.loads(l); m["nad3"] = {"oslona": oslona}; l = json.dumps(m) + "\n"
            fo.write(l)
    L = N.wczytaj("c05_s01_r2", src, "c05_s01")
    R, dg = Rama(litera="NAD2"), DG.Degradacja(cfg)
    st = {}
    meta0 = json.loads(open(os.path.join(src, "nadir_obs.jsonl")).readline())
    with open(os.path.join(d, "nadir_obs.jsonl"), "w") as fo:
        m = dict(meta0)
        if cfg is not None:
            m["nad3"] = dict(cfg)
        fo.write(json.dumps(m) + "\n")
        for row in L.nf:
            fx = R.obserwacja(row["sim"], row["det"], row["ekf_q"], row["ekf_pos"])
            o = dg.przetworz(fx)
            r = {k: row[k] for k in row if k not in ("fx",)}
            r["fx"] = fx
            if o is not fx:
                r["fx_deg"] = json.loads(json.dumps(o))
            fo.write(json.dumps(r) + "\n")
            st[o["seq"]] = json.loads(json.dumps(o))
    tk = {r["tick"]: r for r in N.jl(src, "trace.jsonl", "tk")}
    demo = {r["tick"]: r for r in N.jl(src, "demo.jsonl")}
    sh = NS.NadirShield(nadir_mode=True, kont_mode=True, nad3=True, tabela=TAB, tabela_sha=SHA_P1); sh.reset()
    sh.pos_debounce_ticks = C.DEBOUNCE_TICKS
    sh.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))

    class Kl:
        d_ne, t_fix, kosz, tryb = [0.0, 0.0], None, None, None
    kl, seqs, ip = Kl(), sorted(st), 0
    with open(os.path.join(d, "rama.jsonl"), "w") as fr:
        for r in L.rama:
            obs = []
            while ip < len(seqs) and seqs[ip] <= r["seq"]:
                m = st[seqs[ip]]
                kl.d_ne, kl.t_fix = list(m["d_ne"]), m["t_fix"]
                if m.get("ok"):
                    kl.kosz, kl.tryb = m.get("kosz"), m.get("tryb")
                obs.append({k: m.get(k) for k in ("seq", "t_frame", "ok", "tryb", "ids", "odrz", "powod", "p_fix_ne", "p_ekf_fix", "jeden",
                                                  "para", "kosz", "litera", "t1", "nad3")})
                ip += 1
            t, dm = tk[r["tick"]], demo[r["tick"]]
            pe, se = r["p_ekf"], r["sp_ekf"]
            pc = [pe[0] + kl.d_ne[0], pe[1] + kl.d_ne[1], pe[2]]
            dd, _ = nad3_krok.krok(sh, r["tick"], pe, pc, dm["own_vel_ned"], se, r["sp_net"], "PATROL", t["pf"], t["cs"], r["sim"],
                                   t.get("dr"), kl)
            fr.write(json.dumps({**{k: r[k] for k in ("sim", "mono", "tick", "ep", "sp_net", "sp_ekf", "gt", "desc", "phase")},
                                 "seq": seqs[ip - 1] if ip else r["seq"], "t_fix": kl.t_fix, "d_ne": [round(x, 6) for x in kl.d_ne],
                                 "p_ekf": pe, "p_corr": [round(x, 4) for x in pc], "ph": sh.kont_phase(), "R_k": dd["kont"]["R_k"],
                                 "nadir": dd["nadir"], "nad2": dd["nad2"], "dec": dd["decision"], "rule": dd["rule"], "tryb": kl.tryb,
                                 "kosz": kl.kosz, "obs": obs}) + "\n")
    return d


def czesc4():
    import nad2_ulg
    import nad3_analyze as A
    import nad3_s2_spr as S
    import nad3_s2_geom as GG
    tmp = tempfile.mkdtemp()
    cfg = {"model": "bias_rad", "kierunek": "na_zewnatrz", "E_max": 1.0, "f": 1, "K": 0, "ziarno": 1}
    d = syntetyczny(tmp, cfg, "b4_synt")
    w = nad2_ulg.wyciag(d)
    a = A.analyze(d)
    e = a["epizody"][0]
    s = S.sprawdz(d, "B4", "na_zewnatrz")
    # negatywy
    neg = {}
    p = os.path.join(d, "nadir_obs.jsonl")
    rows = open(p).read().splitlines()
    d_neg = os.path.join(tmp, "b4_neg"); shutil.copytree(d, d_neg, symlinks=True)
    with open(os.path.join(d_neg, "nadir_obs.jsonl"), "w") as f:
        zrobione = False
        for l in rows:
            r = json.loads(l)
            if not zrobione and (r.get("fx_deg") or {}).get("ok"):
                r["fx_deg"]["nad3"]["E"][0] += 0.01; zrobione = True
            f.write(json.dumps(r) + "\n")
    neg["E_podmienione_replay"] = S.replay(d_neg)["ok"]
    d_neg2 = os.path.join(tmp, "b4_neg2"); shutil.copytree(d, d_neg2, symlinks=True)
    with open(os.path.join(d_neg2, "nadir_obs.jsonl"), "w") as f:
        for k, l in enumerate(rows):
            r = json.loads(l)
            if k == 0:
                r["nad3"]["kierunek"] = "do_srodka"
            f.write(json.dumps(r) + "\n")
    neg["kierunek_meta_s3"] = S.meta_spr(d_neg2, "na_zewnatrz")["ok"]
    d3 = syntetyczny(tmp, None, "b3_synt")
    nad2_ulg.wyciag(d3)
    A.analyze(d3)
    s3 = S.sprawdz(d3, "B3")
    # geometria — dymny bieg narzędzia na nominale NAD2
    srcn = os.path.join(ROOT, "results/NAD2/s3/nom_b2")
    gd = None
    if os.path.isdir(srcn):
        gd = os.path.join(tmp, "nom_geom"); os.makedirs(gd)
        for f in ("trace.jsonl", "gt_intruder.jsonl"):
            os.symlink(os.path.join(srcn, f), os.path.join(gd, f))
        wn = json.load(open(os.path.join(srcn, "wyniki_nad2.json")))
        json.dump(wn, open(os.path.join(gd, "wyniki_nad3.json"), "w"))
        g = GG.geometria(gd)
        geom = {"epizody": len(g["epizody"]), "r_max": [(x["scenario_id"], x.get("r_max_gt"), x.get("frac_track"), x.get("frac_pasmo"),
                                                         x.get("kryterium_nominalu")) for x in g["epizody"]]}
    else:
        geom = {"pominiety": "brak results/NAD2/s3/nom_b2"}
    out = {"b4": {"ulg_MB": w["MB"], "analizator": {k: e[k]["ok"] for k in ("B1", "B2", "B3", "B4")} | {"max_e_do_U": e["B1"]["max_e_do_U"]},
                  "obserwable": e.get("nad3_obserwable"),
                  "sprawdziany": {k: v.get("ok") for k, v in s.items() if isinstance(v, dict) and "ok" in v},
                  "b1_nieocenione": s["b1_nieocenione"], "decymacja": s["s1_decymacja"]},
           "negatywy": neg, "b3": {k: v.get("ok") for k, v in s3.items() if isinstance(v, dict) and "ok" in v}, "geometria_dym": geom}
    out["PASS"] = (all(out["b4"]["analizator"][k] for k in ("B1", "B2", "B3", "B4")) and all(out["b4"]["sprawdziany"].values())
                   and neg["E_podmienione_replay"] is False and neg["kierunek_meta_s3"] is False and all(out["b3"].values())
                   and w["MB"] <= 3.0)
    shutil.rmtree(tmp)
    return out


def czesc5():
    src = open(DRV, encoding="utf8").read()
    i = src.index("def _resolve_episodes(manifest):")
    j = src.index("\n\n\n", i)
    fn = src[i:j]
    im = open(os.path.join(ROOT, "harness/intruder_motion.py"), encoding="utf8").read()
    assert 'ep = manifest["episodes"][this_id]' in im and 'this_id = ctl["episode_id"]' in im

    def sprawdz(man_path, ids):
        man = json.load(open(os.path.join(ROOT, man_path)))
        ns = {"os": type("O", (), {"environ": {"BENCH_QUEUE": ""}})(), "EP_IDS": ",".join(map(str, ids)), "N_EP": 99}
        exec(compile(fn, DRV + ":_resolve_episodes", "exec"), ns)
        drv = ns["_resolve_episodes"](man)
        wyn = []
        for e in drv:
            eid = e["episode_id"]
            try:
                ie = man["episodes"][eid]
                zg = ie["scenario_id"] == e["scenario_id"] and ie["segments"] == e["segments"]
                wyn.append({"episode_id": eid, "driver": e["scenario_id"], "intruz": ie["scenario_id"], "zgodne": zg})
            except IndexError:
                wyn.append({"episode_id": eid, "driver": e["scenario_id"], "intruz": "IndexError", "zgodne": False})
        return wyn
    plan = {"N2": [2, 3, 5, 10], "B3": [5], "B4": [5], "N1_kontrolnie": [0, 1, 5, 10]}
    w = {k: sprawdz(MAN, v) for k, v in plan.items()}
    neg = sprawdz(MAN_V1, [0, 1, 4, 5])
    rozjazd = sorted(x["episode_id"] for x in neg if not x["zgodne"])
    out = {"v2": w, "negatyw_S1_plan_N1": neg, "rozjazd_S1": rozjazd}
    out["PASS"] = all(x["zgodne"] for v in w.values() for x in v) and rozjazd == [5, 10]
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    w = {"czesc1": czesc1_all()}
    w["czesc2"] = czesc2()
    print("czesc2", w["czesc2"]["PASS"], flush=True)
    w["czesc3"] = czesc3()
    print("czesc3", w["czesc3"]["PASS"], flush=True)
    w["czesc4"] = czesc4()
    print("czesc4", w["czesc4"]["PASS"], flush=True)
    w["czesc5"] = czesc5()
    print("czesc5", w["czesc5"]["PASS"], w["czesc5"]["rozjazd_S1"], flush=True)
    w["PASS"] = all(w[k]["PASS"] for k in ("czesc1", "czesc2", "czesc3", "czesc4", "czesc5"))
    json.dump(w, open(os.path.join(OUT, "dryrun_s2.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: (v["PASS"] if isinstance(v, dict) else v) for k, v in w.items()}))


if __name__ == "__main__":
    main()
