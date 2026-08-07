#!/usr/bin/env python3
"""r02/intruder_driver.py — deterministyczny sterownik pozy intruza (R1, PRE §2.1).

Poza intruza = f(SIM-TIME) przez gz set_pose: czyta /world/<w>/clock (sim-time), liczy pozę ze
skryptu trajektorii i ustawia ją. DETERMINIZM: poza jest czystą funkcją sim-time (bez fizyki/losu)
⇒ ta sama sim-time ⇒ ta sama poza między biegami (powtarzalność scenariuszy). Model (nie gz <actor>):
gz <actor> bez <skin> segfaultuje serwer (results/R02/RAPORT_R1.md §błąd).

Trajektoria (seed=ID scenariusza podmienia parametry): przelot boczny przed kamerą +x,
y ∈ [YMIN,YMAX] na wysokości Z, prędkość V (m/s), w pętli. Domyślnie x=12, z=10.

Uruchom: python3 -m r02.intruder_driver --world default --seconds 20 [--log out.jsonl]
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time


def scripted_pose(sim_t, x=12.0, z=10.0, ymin=-15.0, ymax=15.0, v=3.0):
    """Poza = f(sim_t): trójkątna fala po y (tam-i-z-powrotem), okres = 2*(ymax-ymin)/v."""
    span = ymax - ymin
    period = 2.0 * span / v
    tau = sim_t % period
    y = ymin + v * tau if tau <= span / v else ymax - v * (tau - span / v)
    return (x, y, z)


def gz_clock(world, timeout=4.0):
    """Zwraca bieżący sim-time [s] z /world/<w>/clock (sec+nsec)."""
    r = subprocess.run(["gz", "topic", "-e", "-t", f"/world/{world}/clock", "-n", "1"],
                       capture_output=True, text=True, timeout=timeout)
    import re
    m = re.search(r"sec:\s*(-?\d+).*?nsec:\s*(\d+)", r.stdout, re.S)
    return int(m.group(1)) + int(m.group(2)) * 1e-9 if m else None


def set_pose(world, x, y, z, timeout=4.0):
    req = f'name: "intruder", position: {{x: {x}, y: {y}, z: {z}}}, orientation: {{w: 1.0}}'
    subprocess.run(["gz", "service", "-s", f"/world/{world}/set_pose",
                    "--reqtype", "gz.msgs.Pose", "--reptype", "gz.msgs.Boolean",
                    "--timeout", "3000", "--req", req],
                   capture_output=True, text=True, timeout=timeout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="default")
    ap.add_argument("--seconds", type=float, default=20.0)   # sim-sekundy działania
    ap.add_argument("--rate", type=float, default=15.0)       # wall-Hz aktualizacji
    ap.add_argument("--x", type=float, default=12.0)
    ap.add_argument("--z", type=float, default=10.0)
    ap.add_argument("--log", default=None)
    args = ap.parse_args()

    t0 = gz_clock(args.world)
    if t0 is None:
        print("[driver] BRAK zegara symu — świat żywy?", file=sys.stderr); sys.exit(2)
    logf = open(args.log, "w") if args.log else None
    dt = 1.0 / args.rate
    while True:
        st = gz_clock(args.world)
        if st is None:
            break
        if st - t0 >= args.seconds:
            break
        x, y, z = scripted_pose(st, x=args.x, z=args.z)
        set_pose(args.world, x, y, z)
        if logf:
            logf.write(json.dumps({"sim_t": round(st, 3), "cmd": [round(x, 3), round(y, 3), round(z, 3)]}) + "\n")
        time.sleep(dt)
    if logf:
        logf.close()
    print(f"[driver] koniec po ~{args.seconds}s sim (poza=f(sim_t), deterministycznie).")


if __name__ == "__main__":
    main()
