#!/usr/bin/env python3
"""acts/ensure_gps_enabled.py — DEMO-B B5R3 D3 fix: higiena parametru EKF2_GPS_CTRL przed bootem LIVE.

ZNALEZISKO 5R3: testy A3 (gate_run_r03, GPS-denied) ustawiają `EKF2_GPS_CTRL=0` (wyłącz GPS). Wartość
PERSYSTUJE w PX4 SITL `parameters.bson` między bootami. Zostawiona na 0 ⇒ EKF bez GPS ⇒
`is_global_position_ok` nigdy True ⇒ health timeout ⇒ arm-fail (6 env-fail + topologia + łącze —
wszystko było POCHODNĄ tego jednego parametru; GT-fed też padał). Fix (harness, poza frozen): przed
KAŻDYM bootem LIVE resetuj EKF2_GPS_CTRL do 7 (default, GPS ON) w persystowanym bson.

Uruchom: python3 acts/ensure_gps_enabled.py  (edytuje parameters.bson in-place; backup .bak)
"""
import os
import sys

BSON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "PX4-Autopilot/build/px4_sitl_default/rootfs/parameters.bson")
DEFAULT = 7   # EKF2_GPS_CTRL default (GPS+baro; GPS-enabled)


def ensure(path=BSON, name=b"EKF2_GPS_CTRL\x00", target=DEFAULT):
    if not os.path.exists(path):
        print(f"[gps-hygiene] brak {path} (PX4 wygeneruje default {target}=GPS ON) — OK")
        return True
    data = bytearray(open(path, "rb").read())
    i = data.find(name)
    if i < 0:
        print(f"[gps-hygiene] EKF2_GPS_CTRL nieobecny w bson ⇒ default {target} (GPS ON) — OK")
        return True
    vs = i + len(name)                       # int32 (typ \x10) tuż po null-terminowanej nazwie
    old = int.from_bytes(data[vs:vs + 4], "little")
    if old == target:
        print(f"[gps-hygiene] EKF2_GPS_CTRL już = {target} (GPS ON) — OK")
        return True
    open(path + ".bak", "wb").write(data)
    data[vs:vs + 4] = int(target).to_bytes(4, "little")
    open(path, "wb").write(data)
    print(f"[gps-hygiene] EKF2_GPS_CTRL {old} -> {target} (GPS ON) — RESET (leftover po A3 GPS-denied)")
    return True


if __name__ == "__main__":
    ok = ensure()
    sys.exit(0 if ok else 1)
