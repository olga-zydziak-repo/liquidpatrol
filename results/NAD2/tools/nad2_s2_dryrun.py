#!/usr/bin/env python3
"""results/NAD2/tools/nad2_s2_dryrun.py — PROMPT_NAD2_S2 §0.1/§1.3: próba na sucho skryptów smoke (0 bootów); wzór
results/NADIR/tools/nadir_s4_dryrun.py (nietknięty).

(1) main() drivera results/NAD2/tools/nad2_flight.py przez atrapy results/KONT/tools/kont_s4_dryrun_c.py (READ-ONLY, podmieniona
    ścieżka DRIVER), scenariusz „zdrowy”, do uzbrojenia: NADIR_MODE=1 + NADIR_LITERA=NAD2 ⇒ arm_retry, selfcheck certów NAD2 PASS,
    meta nad2 (T_CONT_S 110.5, sha tabeli); NADIR_MODE=1 bez litery ⇒ odmowa kod 8; NADIR_MODE=0 bez passthrough ⇒ kod 8.
(2) blok zgodności litery DOSŁOWNYM tekstem z pliku drivera (od `if rama is not None and shield.nad2:` do `for ep in episodes:`)
    na stanie syntetycznym: datagram i meta NAD2 ⇒ start; datagram NADIR1 ⇒ kod 8; meta bez litery ⇒ kod 8; brak datagramów przez
    30 s ⇒ kod 8.
(3) shellcheck (-S warning) nad2_boot.sh / nad2_launch.sh wobec oryginałów S4: zero nowych ostrzeżeń; ROOT absolutny, pipefail,
    bash -n; strażnik trybów bootu pod `bash -uo pipefail`: kombinacje spoza (1/1/0/NAD2, 0/0/1/NADIR1) ⇒ kod 5 przed czymkolwiek
    ciężkim; kolejka `nad2_s2_run.py --sucho` pod `bash -uo pipefail -c` ⇒ plan [P, C], 0 bootów.
(4) łańcuch po locie C na syntetycznym boocie c11_s02 w formacie NAD2 (katalog tymczasowy; ULG, trace i klatki S4 przez dowiązania):
    producent = Rama(litera=NAD2) na zapisanych klatkach (nadir_obs.jsonl z fx NAD2), rama.jsonl z kroku drivera (nad2_krok) z obs
    przyjętych poprawek, R_k, nad2 ⇒ nad2_ulg.wyciag (≤ 3 MB), nad2_analyze (B1–B4, D1), nad2_s2_spr (s1)–(s3) — oczekiwane PASS;
    kontrola negatywna: rama z r_est = |p_EKF| (stara ścieżka) ⇒ (s3) FAIL.
Wyjście: results/NAD2/s2/dryrun/dryrun_s2.json.
"""
import asyncio
import bisect
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap

ROOT = "/home/olga/projects/liquidpatrol"
T = os.path.join(ROOT, "results/NAD2/tools")
OUT = os.path.join(ROOT, "results/NAD2/s2/dryrun")
DRV = os.path.join(T, "nad2_flight.py")
MAN = "results/NADIR/s4/scenario_manifest_s4.json"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/KONT/tools"), T, os.path.join(ROOT, "results/NAD2_RECON/tools")]


def czesc1(tag, env):
    sock = os.path.join(tempfile.mkdtemp(), "drv.sock")
    out = os.path.join(OUT, tag)
    r = subprocess.run([sys.executable, "-c", f"""
import os, sys, json
os.environ.update({{"NADIR_SOCK_DRIVER": {sock!r}, "BENCH_MANIFEST": {MAN!r}, **{env!r}}})
for k in ("NADIR_LITERA", "NAD2_PASSTHROUGH"):
    if k not in {env!r}: os.environ.pop(k, None)
sys.path[:0] = [{ROOT!r}, {os.path.join(ROOT, 'results/KONT/tools')!r}]
import kont_s4_dryrun_c as D
D.DRIVER = {DRV!r}
res = D.run({out!r}, "zdrowy")
print("WYNIK", json.dumps({{k: res[k] for k in ("wynik", "kroki")}}, ensure_ascii=False))
"""], capture_output=True, text=True, timeout=600, cwd=ROOT)
    line = next((l for l in r.stdout.splitlines() if l.startswith("WYNIK ")), None)
    w = json.loads(line[6:]) if line else None
    cs = open(os.path.join(out, "certs_selfcheck.log")).read() if os.path.exists(os.path.join(out, "certs_selfcheck.log")) else ""
    return {"rc": r.returncode, "wynik": w, "nad2_selfcheck_pass": "WERDYKT nad2_certs_selfcheck: PASS" in cs,
            "odmowa_litera": "NADIR_LITERA != NAD2 — ODMOWA" in (r.stdout + r.stderr),
            "odmowa_nadir0": "NADIR_MODE != 1 — ODMOWA" in (r.stdout + r.stderr), "ogon": (r.stdout + r.stderr)[-300:]}


def czesc2():
    src = open(DRV, encoding="utf8").read()
    i = src.rfind("\n", 0, src.index("if rama is not None and shield.nad2:")) + 1
    j = src.rfind("\n", 0, src.index("    for ep in episodes:")) + 1
    blk = textwrap.dedent(src[i:j])
    assert "nad2_litera" in blk and "os._exit(8)" in blk
    fn = "async def _blok():\n" + textwrap.indent(blk, "    ")

    class Exit8(Exception):
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

    def run(dgs, meta_lit):
        tmp = tempfile.mkdtemp()
        with open(os.path.join(tmp, "nadir_obs.jsonl"), "w") as f:
            f.write(json.dumps({"t": "meta", **({"litera": meta_lit} if meta_lit else {})}) + "\n")
        evs = []

        class OS:
            path = os.path

            @staticmethod
            def _exit(c):
                raise Exit8(c)

        class Sh:
            nad2 = True

        class FF:
            def flush(self):
                pass

        async def sl(_):
            return None
        ns = {"rama": Rama(dgs), "shield": Sh(), "time": Clock(), "asyncio": type("A", (), {"sleep": staticmethod(sl)}),
              "os": OS, "OUTDIR": tmp, "json": json, "open": open, "ev": lambda s, **kw: evs.append((s, kw)), "print": lambda *a, **k: None,
              "_f": FF()}
        exec(compile(fn, DRV + ":NAD2-litera", "exec"), ns)
        try:
            asyncio.run(ns["_blok"]())
            return "start", evs
        except Exit8 as e:
            return f"kod{e.args[0]}", evs
    w = {}
    w["NAD2_NAD2"] = run([{"powod": "brak_ekf"}, {"seq": 2, "litera": "NAD2", "ok": False}], "NAD2")[0] == "start"
    w["datagram_NADIR1"] = run([{"seq": 2, "ok": True}], "NAD2")[0] == "kod8"
    w["meta_bez_litery"] = run([{"seq": 2, "litera": "NAD2"}], None)[0] == "kod8"
    w["brak_datagramow"] = run([], "NAD2")[0] == "kod8"
    w["PASS"] = all(w.values())
    return w


def sc(path):
    r = subprocess.run(["shellcheck", "-S", "warning", "-f", "json", path], capture_output=True, text=True)
    return {(x["code"], x["message"]) for x in json.loads(r.stdout or "[]")}


def czesc3():
    out = {}
    O = os.path.join(ROOT, "results/NADIR/tools")
    for new, old in (("nad2_boot.sh", "nadir_s4_boot.sh"), ("nad2_launch.sh", "nadir_s4_launch.sh")):
        n, o = sc(os.path.join(T, new)), sc(os.path.join(O, old))
        head = open(os.path.join(T, new)).read()
        out[new] = {"ostrzezenia": len(n), "w_oryginale": len(o), "nowe": [f"SC{c}: {m}" for c, m in sorted(n - o)],
                    "root_absolutny": f'ROOT="{ROOT}"' in head, "pipefail": "set -o pipefail" in head,
                    "bash_n": subprocess.run(["bash", "-n", os.path.join(T, new)]).returncode == 0}
        out[new]["PASS"] = not out[new]["nowe"] and out[new]["root_absolutny"] and out[new]["pipefail"] and out[new]["bash_n"]
    guard = {}
    for kom in (("1", "1", "0", "NADIR1"), ("1", "1", "1", "NAD2"), ("0", "0", "1", "NAD2"), ("1", "0", "0", "NAD2"), ("", "", "", "")):
        env = {**os.environ, "BOOT_NADIR_MODE": kom[0], "BOOT_KONT_MODE": kom[1], "BOOT_PASSTHROUGH": kom[2], "BOOT_LITERA": kom[3]}
        r = subprocess.run(["bash", "-uo", "pipefail", os.path.join(T, "nad2_boot.sh"), "99", "dryrun_guard", "0", "-"], env=env,
                           capture_output=True, text=True, timeout=60)
        guard["/".join(kom) or "puste"] = {"rc": r.returncode, "odmowa": "poza dopuszczonymi" in r.stdout}
    out["straznik_trybow"] = {**guard, "PASS": all(v["rc"] == 5 and v["odmowa"] for v in guard.values())}
    st = os.path.join(ROOT, "results/NAD2/s2/dryrun_guard")
    if os.path.isdir(st):
        shutil.rmtree(st)
    r = subprocess.run(["bash", "-uo", "pipefail", "-c", f"python3 {os.path.join(T, 'nad2_s2_run.py')} --sucho"], capture_output=True,
                       text=True, cwd=ROOT, timeout=120)
    line = next((l for l in r.stdout.splitlines() if l.startswith("{")), None)
    plan = json.loads(line)["plan"] if line else None
    out["kolejka_sucho"] = {"rc": r.returncode, "plan": plan, "PASS": r.returncode == 0 and plan == ["P", "C"]}
    out["PASS"] = all(v["PASS"] for v in out.values() if isinstance(v, dict))
    return out


def syntetyczny(tmp, stara_sciezka=False):
    """Boot c11_s02 S4 w formacie NAD2: klatki → producent Rama(NAD2) (nadir_obs.jsonl), ticki → nad2_krok (rama.jsonl)."""
    import nad2_dane as D
    import nad2_krok
    from harness import nadir_fix as NF
    from r03 import nadir_shield as NS
    src = os.path.join(ROOT, "results/NADIR/s4/c11_s02")
    d = os.path.join(tmp, "c11_s02")
    os.makedirs(d)
    for f in ("trace.jsonl", "boot.ulg", "kont_tempo.json", "demo.jsonl"):
        os.symlink(os.path.join(src, f), os.path.join(d, f))
    b = D.Boot("c11_s02")
    rv = NF.Rama(litera="NAD2")
    fixy = []
    with open(os.path.join(d, "nadir_obs.jsonl"), "w") as fo:
        fo.write(json.dumps({"t": "meta", "litera": "NAD2"}) + "\n")
        for r in b.nf:
            fx = rv.obserwacja(r["sim"], r["det"], r.get("ekf_q"), r.get("ekf_pos"))
            fo.write(json.dumps({**{k: r[k] for k in r if k != "fx"}, "fx": fx}) + "\n")
            if fx["ok"]:
                fixy.append((r["mono"] + r.get("ms", 0.0) / 1000.0 + 0.005, fx, list(rv.d_ne)))
    av = [f[0] for f in fixy]
    tk = {r["tick"]: r for r in D.jl(os.path.join(src, "trace.jsonl"), "tk")}
    demo = {r["tick"]: r for r in D.jl(os.path.join(src, "demo.jsonl"))}
    sh = NS.NadirShield(kont_mode=True, nadir_mode=True, nad2=True); sh.reset()

    class Rm:
        t_fix = kosz = tryb = None
    rm, last = Rm(), -1
    with open(os.path.join(d, "rama.jsonl"), "w") as fr:
        for r in sorted(b.rama, key=lambda x: x["tick"]):
            t, dm = tk.get(r["tick"]), demo.get(r["tick"])
            if t is None or dm is None:
                continue
            i = bisect.bisect_right(av, r["mono"]) - 1
            obs, dne = [], [0.0, 0.0]
            if i >= 0:
                _, fx, dne = fixy[i]
                rm.t_fix, rm.kosz, rm.tryb = fx["t_frame"], fx["kosz"], fx["tryb"]
                obs = [{k: f[1].get(k) for k in ("seq", "t_frame", "ok", "tryb", "kosz", "litera", "p_fix_ne", "p_ekf_fix", "jeden", "para")}
                       for f in fixy[last + 1:i + 1]]
                last = i
            pe, se = r["p_ekf"], r["sp_ekf"]
            pc = [pe[0] + dne[0], pe[1] + dne[1], pe[2]]
            sc_ = [se[0] + dne[0], se[1] + dne[1], se[2]]
            dd, _ = nad2_krok.krok(sh, r["tick"], pe, pc, dm["own_vel_ned"], se, sc_, "PATROL", t["pf"], t["cs"], r["sim"], None, rm)
            n2 = dict(dd["nad2"])
            if stara_sciezka:
                n2["r_est"] = math.hypot(pe[0], pe[1])
            fr.write(json.dumps({"sim": r["sim"], "mono": r["mono"], "tick": r["tick"], "ep": r["ep"], "p_ekf": pe, "p_corr": pc,
                                 "ph": sh.kont_phase(), "R_k": dd["kont"]["R_k"], "nadir": dd["nadir"], "nad2": n2, "tryb": rm.tryb,
                                 "desc": r["desc"], "phase": r.get("phase"), "obs": obs}) + "\n")
    return d


def czesc4():
    import nad2_ulg
    import nad2_analyze as A
    import nad2_s2_spr as S
    tmp = tempfile.mkdtemp()
    d = syntetyczny(tmp)
    w = nad2_ulg.wyciag(d)
    a = A.analyze(d)
    e = a["epizody"][0]
    s = S.sprawdz(d)
    tmp2 = tempfile.mkdtemp()
    d2 = syntetyczny(tmp2, stara_sciezka=True)
    s_neg = S.sprawdz(d2)
    out = {"ulg": {"MB": w["MB"], "okno": w["okno"]},
           "analizator": {k: e[k]["ok"] for k in ("B1", "B2", "B3", "B4")} | {"D1": e["D1"]["dostepne"], "max_e_do_U": e["B1"]["max_e_do_U"],
                                                                              "zapas_bariery_min": e["zapas_bariery_min"]},
           "sprawdziany": {k: v["ok"] for k, v in s.items()}, "sprawdziany_liczby": {k: {kk: vv for kk, vv in v.items() if kk != "przyklady"}
                                                                                       for k, v in s.items()},
           "negatyw_stara_sciezka_s3": s_neg["s3"]["ok"]}
    out["PASS"] = (all(out["analizator"][k] for k in ("B1", "B2", "B3", "B4", "D1")) and all(out["sprawdziany"].values())
                   and out["negatyw_stara_sciezka_s3"] is False and w["MB"] <= 3.0)
    shutil.rmtree(tmp); shutil.rmtree(tmp2)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    w = {"czesc1": {"NAD2": czesc1("nad2", {"NADIR_MODE": "1", "NADIR_LITERA": "NAD2"}),
                    "bez_litery": czesc1("bez_litery", {"NADIR_MODE": "1"}),
                    "nadir0_bez_passthrough": czesc1("nadir0", {"NADIR_MODE": "0"})}}
    c1 = w["czesc1"]
    c1["PASS"] = (c1["NAD2"]["rc"] == 0 and (c1["NAD2"]["wynik"] or {}).get("wynik") == "zatrzymane: uzbrojenie" and c1["NAD2"]["nad2_selfcheck_pass"]
                  and c1["bez_litery"]["rc"] == 8 and c1["bez_litery"]["odmowa_litera"]
                  and c1["nadir0_bez_passthrough"]["rc"] == 8 and c1["nadir0_bez_passthrough"]["odmowa_nadir0"])
    meta = None
    tp = os.path.join(OUT, "nad2", "trace.jsonl")
    if os.path.exists(tp):
        meta = next((json.loads(l) for l in open(tp) if '"meta"' in l), None)
    c1["meta_nad2"] = (meta or {}).get("nad2")
    w["czesc2"] = czesc2()
    w["czesc3"] = czesc3()
    w["czesc4"] = czesc4()
    w["PASS"] = all(w[k]["PASS"] for k in ("czesc1", "czesc2", "czesc3", "czesc4"))
    json.dump(w, open(os.path.join(OUT, "dryrun_s2.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: (v["PASS"] if isinstance(v, dict) else v) for k, v in w.items()}))


if __name__ == "__main__":
    main()
