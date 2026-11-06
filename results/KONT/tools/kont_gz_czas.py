#!/usr/bin/env python3
"""results/KONT/tools/kont_gz_czas.py — bramka fazy dołączenia PX4 (ANEKS_KONT-1c §3): czeka na serwer gz (scene/info, dopiero potem subskrypcja /clock, por. px4-rc.gzsim:33), potem aż czas symulacji ≥ --min. Zapisuje odczyt do --out. Kod 2 po --timeout.
Użycie: kont_gz_czas.py --world W --min 0.5 --out plik.json [--timeout 90]"""
import argparse
import json
import re
import subprocess
import time


def czas(world):
    try:
        r = subprocess.run(["gz", "topic", "-e", "-n", "1", "-t", f"/world/{world}/clock"], capture_output=True, text=True, timeout=5).stdout
    except subprocess.TimeoutExpired:
        return None
    m = re.search(r"sim\s*\{(.*?)\}", r, re.S)
    if not m:
        return None
    s = re.search(r"sec:\s*(\d+)", m.group(1).replace("nsec", "n"))
    n = re.search(r"nsec:\s*(\d+)", m.group(1))
    return (int(s.group(1)) if s else 0) + (int(n.group(1)) / 1e9 if n else 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--min", type=float, default=0.5)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=float, default=90.0)
    a = ap.parse_args()
    t0 = time.monotonic()
    t = None
    serwer = False
    while time.monotonic() - t0 < a.timeout:
        if not serwer:
            i = subprocess.run(["gz", "service", "-i", "--service", f"/world/{a.world}/scene/info"], capture_output=True, text=True)
            serwer = "Service providers" in i.stdout + i.stderr
        if serwer:
            t = czas(a.world)
            if t is not None and t >= a.min:
                break
        time.sleep(0.2)
    ok = t is not None and t >= a.min
    json.dump({"prog_s": a.min, "sim_s_przy_starcie_px4": t, "czekanie_wall_s": round(time.monotonic() - t0, 2), "ok": ok}, open(a.out, "w"))
    print("gz sim", t, "ok", ok)
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
