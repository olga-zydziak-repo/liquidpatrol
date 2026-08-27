#!/usr/bin/env python3
"""acts/ensure_mag_baseline.py — MAG-2 N1: higiena kalibracji magnetometru przed bootem K1.

ZNALEZISKO MAG-1 (results/K1/MAG/RAPORT_MAG1.md): EKF2 uczy się biasu magnetometru w locie
(EKF2::UpdateMagCalibration) i zapisuje do CAL_MAG0_{X,Y,Z}OFF w persystowanym parameters.bson,
którego harness NIGDY nie czyścił. Offset PEŁZA monotonicznie przez sesję (YOFF -0.1026 -> -0.1506)
i przy ~-0.1506 skorygowana |siła pola - WMM| przekracza trwale EKF2_MAG_CHK_STR=0.20 Gs ->
mag_field_disturbed -> "Strong magnetic interference" -> arm DENY. F4 separacja perfekcyjna:
9/9 bootów YOFF<=-0.1417 arm-OK; 5/5 YOFF=-0.1506 mag-fail. Ten sam gatunek co zatrzask biasu gyro.

MITYGACJA STANU (nie naprawa mechanizmu uczenia): przed KAŻDYM bootem przywróć CAL_MAG0_{X,Y,Z}OFF
do wartości ze znanego-czystego bootu S@0.2 boot7 (arm-OK, mag-fail=0). EKF dalej pełznie w locie;
my zerujemy pełzanie MIĘDZY bootami — dokładnie zmierzony wektor trybu. Mechanizm 1:1 jak
ensure_gps_enabled.py: edycja parameters.bson in-place PRZED startem PX4 (ładowane przy starcie
stacku, aktywne w preflighcie przed arm). Symetryczne S/N/E, wyłącznie przed-lotowe.
Sędzia/osłona/piny NIETKNIĘTE — E5 (EKF2_MAG_CHK_STR) nietykalne (N3).

Snapshot baseline (S@0.2 boot7, verbatim float32; MAG-2 ANEKS_SHA):
  CAL_MAG0_XOFF = -0.00601893151178956
  CAL_MAG0_YOFF = -0.1369396150112152
  CAL_MAG0_ZOFF =  0.1544266939163208

Uruchom: python3 acts/ensure_mag_baseline.py  (edytuje parameters.bson in-place; backup .magbak)
"""
import os
import struct
import sys

BSON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "PX4-Autopilot/build/px4_sitl_default/rootfs/parameters.bson")

# baseline S@0.2 boot7 (float32 wartości; zapisywane jako BSON double, PX4 rzutuje na float)
BASELINE = {
    b"CAL_MAG0_XOFF\x00": -0.00601893151178956,
    b"CAL_MAG0_YOFF\x00": -0.1369396150112152,
    b"CAL_MAG0_ZOFF\x00":  0.1544266939163208,
}
BSON_DOUBLE = 0x01
TOL = 1e-9


def ensure(path=BSON, baseline=BASELINE):
    if not os.path.exists(path):
        print(f"[mag-hygiene] brak {path} (PX4 wygeneruje świeży default) — OK")
        return True
    data = bytearray(open(path, "rb").read())
    changed = False
    report = []
    for name, target in baseline.items():
        i = data.find(name)
        if i < 0:
            report.append(f"{name.decode().strip(chr(0))}=NIEOBECNY(default)")
            continue
        typ = data[i - 1]                       # typ BSON poprzedza null-terminowaną nazwę
        if typ != BSON_DOUBLE:
            print(f"[mag-hygiene] BŁĄD: {name.decode().strip(chr(0))} typ=0x{typ:02x} != double — ABORT")
            return False
        vs = i + len(name)                      # 8-bajtowy double tuż po null-terminowanej nazwie
        old = struct.unpack("<d", data[vs:vs + 8])[0]
        # zapisz float32(target) jako double, żeby stored == baseline float32 po rzutowaniu PX4
        tgt = struct.unpack("<f", struct.pack("<f", target))[0]
        if abs(old - tgt) <= TOL:
            report.append(f"{name.decode().strip(chr(0))}={tgt:.9g}(już-baseline)")
            continue
        data[vs:vs + 8] = struct.pack("<d", tgt)
        changed = True
        report.append(f"{name.decode().strip(chr(0))} {old:.9g}->{tgt:.9g}")
    if changed:
        open(path + ".magbak", "wb").write(open(path, "rb").read())
        open(path, "wb").write(data)
        print(f"[mag-hygiene] RESET CAL_MAG0 do baseline S@0.2 b7 — {'; '.join(report)}")
    else:
        print(f"[mag-hygiene] CAL_MAG0 już = baseline — OK ({'; '.join(report)})")
    return True


if __name__ == "__main__":
    ok = ensure()
    sys.exit(0 if ok else 1)
