#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s2_dryrun.py — PROMPT_NADIR_S2 §0.3: próba na sucho skryptów S2 (0 bootów).

(1) main() drivera results/NADIR/tools/nadir_s2_flight.py przez atrapy results/KONT/tools/kont_s4_dryrun_c.py (import
    READ-ONLY, podmieniona wyłącznie ścieżka DRIVER), scenariusz „zdrowy”, NADIR_MODE=1: import gałęzi S2N (harness.nadir_fix),
    ROOT absolutny (lekcja STOP-KONT4-DRIVER: kopię sprawdzać uruchomieniem main() z atrapą), preflight KONT do uzbrojenia.
(2) Bloki S2N pętli epizodu — DOSŁOWNY tekst z pliku drivera (wycięty między znacznikami, nie przepisany) wykonany na atrapach
    feedu/kontrolera i prawdziwym harness.nadir_fix.RamaKlient z datagramem producenta przez UDS: NADIR_MODE=1 ⇒ own_net = p_corr,
    tgt = sp_EKF, wiersz rama.jsonl kompletny (klucze §1.4) i parsowalny; NADIR_MODE=0 ⇒ own_net to ten sam obiekt co own,
    tgt to ten sam obiekt co cmd["tgt_ned"], brak wiersza.
(3) shellcheck (-S warning, w tym SC2154 zmienna nieprzypisana ≈ set -u) nowych skryptów bash vs ich oryginałów: wymóg — zero
    nowych ostrzeżeń; ROOT absolutny w nagłówku każdego skryptu.
Wyjście: results/NADIR/s2/dryrun/dryrun_s2.json.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import types

ROOT = "/home/olga/projects/liquidpatrol"
T = os.path.join(ROOT, "results/NADIR/tools")
OUT = os.path.join(ROOT, "results/NADIR/s2/dryrun")
DRV = os.path.join(T, "nadir_s2_flight.py")
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/KONT/tools")]


def czesc1():
    sock = os.path.join(tempfile.mkdtemp(), "drv.sock")
    r = subprocess.run([sys.executable, "-c", f"""
import os, sys, json
os.environ.update(NADIR_MODE="1", NADIR_SOCK_DRIVER={sock!r})
sys.path[:0] = [{ROOT!r}, {os.path.join(ROOT, 'results/KONT/tools')!r}]
import kont_s4_dryrun_c as D
D.DRIVER = {DRV!r}
res = D.run({os.path.join(OUT, 'zdrowy')!r}, "zdrowy")
print("WYNIK", json.dumps({{k: res[k] for k in ("wynik", "reinit_wywolan", "kroki")}}, ensure_ascii=False))
"""], capture_output=True, text=True, timeout=600, cwd=ROOT)
    line = next((l for l in r.stdout.splitlines() if l.startswith("WYNIK ")), None)
    w = json.loads(line[6:]) if line else None
    ok = r.returncode == 0 and w is not None and w["wynik"] == "zatrzymane: uzbrojenie" and "arm_retry" in w["kroki"]
    return {"rc": r.returncode, "wynik": w, "PASS": ok, "stderr_ogon": r.stderr[-800:]}


def wytnij(src, start, stop):
    i = src.index(start)
    i = src.rfind("\n", 0, i) + 1
    j = src.index(stop, i)
    j = src.rfind("\n", 0, j) + 1
    return textwrap.dedent(src[i:j])


def czesc2():
    from harness import nadir_fix as NF
    src = open(DRV, encoding="utf8").read()
    b1 = wytnij(src, "own_net = own  ", "dr = bool(getattr(m, \"dead_reckoning\"")
    b2 = wytnij(src, "if rlog is not None:                                              # S2N: log ramy", "if r_est > shield.cfg.r_e:")
    assert "ctrl.step(tick, own_net" in b1 and "sp_ekf(cmd[\"tgt_ned\"], own, own_net)" in b1 and "rlog.write" in b2
    b1 = b1.replace("phase = cmd[\"extra\"].get(\"phase\")\n", "").replace("dband = cmd[\"extra\"].get(\"d\")\n", "")
    b1 = re.sub(r"if t_entry is None and dband.*\n.*\n", "", b1)
    wyn = {}
    for mode in ("1", "0"):
        cmd = {"tgt_ned": [5.0, -3.0, -12.0], "v_ned": [0.5, 0.2, 0.0], "yaw": 0.3, "extra": {"phase": "orbit", "d": 8.0}}

        class Ctrl:
            def set_feed(self, fs):
                self.fs = fs

            def step(self, tick, own, vel, now, x):
                self.own = own
                return cmd
        rama = rlog = None
        if mode == "1":
            sp = os.path.join(tempfile.mkdtemp(), "drv.sock")
            rama = NF.RamaKlient(sp)
            prod = NF.Rama()
            NF.nadawca([sp])(prod._stan({"t": "fx", "seq": 1, "t_frame": 99.8, "n_det": 2, "ok": True, "tryb": "para", "ids": [18, 19],
                                         "odrz": [], "p_fix_ne": [1.5, 2.5], "p_ekf_fix": [1.2, 2.1, -12.0]}) |
                                {"d_ne": [0.3, 0.4], "t_fix": 99.8})
            rlog = io.StringIO()
        own = [1.0, 2.0, -12.0]
        ns = {"rama": rama, "rlog": rlog, "own": own, "feed": types.SimpleNamespace(sample=lambda t: {"track_valid": True}),
              "ctrl": Ctrl(), "tick": 7, "vel": [0, 0, 0], "now_sim": 100.0, "sp_ekf": NF.sp_ekf, "json": json,
              "time": __import__("time"), "ep": {"episode_id": 20}, "_gt": {"x": 2.1, "y": 1.1, "z": 12.0, "mono": 5.0},
              "out": (0.5, 0.2, 0.0, 17.2), "d_dec": {"decision": "ALLOW", "rule": None}, "descending": False,
              "phase": "orbit", "dband": 8.0}
        exec(compile(b1, DRV + ":S2N-1", "exec"), ns)
        exec(compile(b2, DRV + ":S2N-2", "exec"), ns)
        r = {"own_net": ns["own_net"], "own_net_is_own": ns["own_net"] is own, "tgt": ns["tgt"],
             "tgt_is_cmd": ns["tgt"] is cmd["tgt_ned"], "ctrl_widzi": ns["ctrl"].own}
        if mode == "1":
            row = json.loads(rlog.getvalue().strip())
            klucze = {"tau", "t_fix", "d_ne", "p_ekf", "p_corr", "p_fix", "gt", "sp_net", "sp_ekf", "cmd", "obs"}
            r.update(wiersz_klucze_ok=klucze <= set(row), tau=row["tau"], obs_n=len(row["obs"]), p_fix=row["p_fix"])
            r["PASS"] = (abs(ns["own_net"][0] - 1.3) < 1e-12 and abs(ns["own_net"][1] - 2.4) < 1e-12 and ns["ctrl"].own is ns["own_net"]
                         and all(abs((ns["tgt"][k] - cmd["tgt_ned"][k]) - (own[k] - ns["own_net"][k])) <= 1e-9 for k in range(3))
                         and r["wiersz_klucze_ok"] and abs(row["tau"] - 0.2) < 1e-6 and r["obs_n"] == 1 and row["p_fix"] == [1.5, 2.5])
            rama.close()
        else:
            r["PASS"] = r["own_net_is_own"] and r["tgt_is_cmd"] and ns["ctrl"].own is own
        wyn[f"NADIR_MODE={mode}"] = r
    return {"bloki": {"S2N-1_linie": b1.count("\n"), "S2N-2_linie": b2.count("\n")}, **wyn,
            "PASS": all(v["PASS"] for k, v in wyn.items())}


def sc(path):
    r = subprocess.run(["shellcheck", "-S", "warning", "-f", "json", path], capture_output=True, text=True)
    return {(x["code"], x["message"]) for x in json.loads(r.stdout or "[]")}


def czesc3():
    out = {}
    for new, old in (("nadir_s2_boot.sh", "nadir_s1v2_boot.sh"), ("nadir_s2_launch.sh", "nadir_s1v2_launch.sh")):
        n, o = sc(os.path.join(T, new)), sc(os.path.join(T, old))
        nowe = sorted(n - o)
        head = open(os.path.join(T, new)).read()
        out[new] = {"ostrzezenia": len(n), "w_oryginale": len(o), "nowe": [f"SC{c}: {m}" for c, m in nowe],
                    "root_absolutny": f'ROOT="{ROOT}"' in head, "pipefail": "set -o pipefail" in head}
        out[new]["PASS"] = not nowe and out[new]["root_absolutny"] and out[new]["pipefail"]
    out["PASS"] = all(v["PASS"] for v in out.values() if isinstance(v, dict))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    res = {"opis": __doc__.split("\n\n")[0], "1_driver_main": czesc1(), "2_bloki_S2N": czesc2(), "3_shellcheck": czesc3()}
    res["PASS"] = all(res[k]["PASS"] for k in ("1_driver_main", "2_bloki_S2N", "3_shellcheck"))
    json.dump(res, open(os.path.join(OUT, "dryrun_s2.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str)[:4000])
    sys.exit(0 if res["PASS"] else 1)


if __name__ == "__main__":
    main()
