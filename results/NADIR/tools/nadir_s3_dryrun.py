#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s3_dryrun.py — PROMPT_NADIR_S3 §0.2: próba na sucho skryptów S3 (0 bootów), wzór nadir_s2_dryrun.py.

(1) main() drivera results/NADIR/tools/nadir_s3_flight.py przez atrapy results/KONT/tools/kont_s4_dryrun_c.py (import
    READ-ONLY, podmieniona ścieżka DRIVER), scenariusz „zdrowy”, do uzbrojenia — konfiguracja B1 (NADIR_MODE=0,
    KONT_MODE=0, NADIR_S3_PASSTHROUGH=1; atrapa nadpisuje KONT_MODE=1, więc env.update owinięty tak, by KONT_MODE został 0)
    i konfiguracja S4 (NADIR_MODE=1, KONT_MODE=1). Sprawdza: dojście do arm_retry, selfcheck certów NADIR PASS
    w certs_selfcheck.log, plik passthrough.jsonl tylko w B1 (cień kanoniczny wyłącznie przy NADIR_MODE=0).
(2) Blok S3N wywołania osłony — DOSŁOWNY tekst z pliku drivera (od `d_dec = shield.step` do `is_pos =`) na prawdziwych
    osłonach: B1 ⇒ cień PatrolShield, równość dictów, wiersz passthrough; S4 ⇒ t_fix/koszyk z RamaKlient trafiają do
    NadirShield (τ, j w decyzji), brak cienia.
(3) shellcheck (-S warning) nowych skryptów bash vs oryginałów S2: zero nowych ostrzeżeń; ROOT absolutny, pipefail.
Wyjście: results/NADIR/s3/dryrun/dryrun_s3.json.
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import types

ROOT = "/home/olga/projects/liquidpatrol"
T = os.path.join(ROOT, "results/NADIR/tools")
OUT = os.path.join(ROOT, "results/NADIR/s3/dryrun")
DRV = os.path.join(T, "nadir_s3_flight.py")
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/KONT/tools")]


def czesc1(tag, nm, km, pt):
    sock = os.path.join(tempfile.mkdtemp(), "drv.sock")
    out = os.path.join(OUT, tag)
    r = subprocess.run([sys.executable, "-c", f"""
import os, sys, json
os.environ.update(NADIR_MODE={nm!r}, NADIR_S3_PASSTHROUGH={pt!r}, NADIR_SOCK_DRIVER={sock!r})
_u = os.environ.update
os.environ.update = lambda d=(), **kw: _u({{**dict(d, **kw), "KONT_MODE": {km!r}}})
sys.path[:0] = [{ROOT!r}, {os.path.join(ROOT, 'results/KONT/tools')!r}]
import kont_s4_dryrun_c as D
D.DRIVER = {DRV!r}
res = D.run({out!r}, "zdrowy")
print("WYNIK", json.dumps({{k: res[k] for k in ("wynik", "kroki")}}, ensure_ascii=False))
"""], capture_output=True, text=True, timeout=600, cwd=ROOT)
    line = next((l for l in r.stdout.splitlines() if l.startswith("WYNIK ")), None)
    w = json.loads(line[6:]) if line else None
    # trace.jsonl atrapy zostaje pusty (bufor pliku nieopróżniony przed wyjątkiem zatrzymania atrapy — cecha przyrządu,
    # S2 tak samo); tryb osłony potwierdzają: plik passthrough.jsonl (tylko cień przy NADIR_MODE=0) i selfcheck certów
    pt_file = os.path.exists(os.path.join(out, "passthrough.jsonl"))
    cs = open(os.path.join(out, "certs_selfcheck.log")).read() if os.path.exists(os.path.join(out, "certs_selfcheck.log")) else ""
    nadir_sc = "WERDYKT nadir_certs_selfcheck: PASS" in cs
    ok = (r.returncode == 0 and w is not None and w["wynik"] == "zatrzymane: uzbrojenie" and nadir_sc
          and pt_file == (nm == "0"))
    return {"rc": r.returncode, "wynik": w, "nadir_selfcheck_pass": nadir_sc, "certs_selfcheck_rc_linia": cs.strip().splitlines()[-1:],
            "passthrough_plik": pt_file, "PASS": ok, "stderr_ogon": r.stderr[-600:]}


def wytnij(src, start, stop):
    i = src.rfind("\n", 0, src.index(start)) + 1
    j = src.index(stop, i)
    j = src.rfind("\n", 0, j) + 1
    return textwrap.dedent(src[i:j])


def czesc2():
    from harness import nadir_fix as NF
    from r03.nadir_shield import NadirShield
    from r03.kont_shield import KontShield
    from r01.shield import PatrolShield
    src = open(DRV, encoding="utf8").read()
    blk = wytnij(src, "d_dec = shield.step(tick, own, vel, tgt", "is_pos = (d_dec")
    assert "kosz_j=(rama.kosz" in blk and "shadow.step" in blk
    wyn = {}
    for tag, nm, km in (("B1", False, False), ("S4", True, True)):
        sh = NadirShield(kont_mode=km, nadir_mode=nm); sh.reset()
        shadow = None if nm else (KontShield(kont_mode=True) if km else PatrolShield())
        if shadow is not None:
            shadow.reset()
        rama = None
        if nm:
            sp = os.path.join(tempfile.mkdtemp(), "d.sock")
            rama = NF.RamaKlient(sp)
            NF.nadawca([sp])({"t": "fx", "seq": 1, "t_frame": 99.9, "ok": True, "p_fix_ne": [1.0, 2.0], "kosz": 2,
                              "d_ne": [0.1, 0.1], "t_fix": 99.9})
            rama.drain()
        plog, n_pt = io.StringIO(), [0, 0]
        ns = {"shield": sh, "shadow": shadow, "rama": rama, "plog": plog, "n_pt": n_pt, "json": json, "tick": 3,
              "own": [5.0, 1.0, -10.0], "vel": [0.5, 0.0, 0.0], "tgt": [6.0, 1.0, -10.0], "M_PATROL": "PATROL",
              "pf": None, "cs": False, "now_sim": 100.0, "dr": False, "ep": {"episode_id": 0}}
        for i in range(3):                                  # 3 ticki: przy cs=False wejście w utratę po debounce
            ns["tick"], ns["now_sim"] = 3 + i, 100.0 + 0.05 * i
            exec(compile(blk, DRV + ":S3N", "exec"), ns)
        d = ns["d_dec"]
        if nm:
            r = {"tau": d["nadir"]["tau"], "j": d["nadir"]["j"], "faza": d["kont"]["phase"], "passthrough_wiersze": n_pt[0]}
            r["PASS"] = r["j"] == 2 and abs(r["tau"] - 0.2) < 1e-9 and r["faza"] == "KONT" and n_pt[0] == 0
        else:
            rows = [json.loads(x) for x in plog.getvalue().splitlines()]
            r = {"passthrough_wiersze": n_pt[0], "roznice": n_pt[1], "wszystkie_eq": all(x["eq"] for x in rows),
                 "klucz_kont_w_decyzji": "kont" in d}
            r["PASS"] = n_pt[0] == 3 and n_pt[1] == 0 and r["wszystkie_eq"] and not r["klucz_kont_w_decyzji"]
        wyn[tag] = r
        if rama is not None:
            rama.close()
    return {**wyn, "PASS": all(v["PASS"] for v in wyn.values())}


def sc(path):
    r = subprocess.run(["shellcheck", "-S", "warning", "-f", "json", path], capture_output=True, text=True)
    return {(x["code"], x["message"]) for x in json.loads(r.stdout or "[]")}


def czesc3():
    out = {}
    for new, old in (("nadir_s3_boot.sh", "nadir_s2_boot.sh"), ("nadir_s3_launch.sh", "nadir_s2_launch.sh")):
        n, o = sc(os.path.join(T, new)), sc(os.path.join(T, old))
        head = open(os.path.join(T, new)).read()
        out[new] = {"ostrzezenia": len(n), "w_oryginale": len(o), "nowe": [f"SC{c}: {m}" for c, m in sorted(n - o)],
                    "root_absolutny": f'ROOT="{ROOT}"' in head, "pipefail": "set -o pipefail" in head}
        out[new]["PASS"] = not out[new]["nowe"] and out[new]["root_absolutny"] and out[new]["pipefail"]
    out["PASS"] = all(v["PASS"] for v in out.values() if isinstance(v, dict))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    res = {"opis": __doc__.split("\n\n")[0], "1_B1": czesc1("B1", "0", "0", "1"), "1_S4": czesc1("S4", "1", "1", "0"),
           "2_blok_S3N": czesc2(), "3_shellcheck": czesc3()}
    res["PASS"] = all(res[k]["PASS"] for k in ("1_B1", "1_S4", "2_blok_S3N", "3_shellcheck"))
    json.dump(res, open(os.path.join(OUT, "dryrun_s3.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str)[:4000])
    sys.exit(0 if res["PASS"] else 1)


if __name__ == "__main__":
    main()
