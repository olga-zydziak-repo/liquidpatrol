#!/usr/bin/env python3
"""results/WK_RECON/tools/wk_gen_world.py — R1(c) minimalne złożenie: świat kamerowy + wiatr (0 bootów).

Baza: worlds/world_demo_A3.sdf (habitat percepcyjny FROZEN, sha adc91803 — świat lotów kamerowych
w reżimie OPS: perc2_s2_boot.sh:26, democ_v3_boot.sh:20). Dokłada DOKŁADNIE to, co generator nogi W
(worlds/gen_world_wind.py, import READ-ONLY): blok 13 systemów server.config verbatim + WindEffects
(gdy SDF świata deklaruje jakikolwiek <plugin>, gz ignoruje server.config — gen_world_wind.py:20-22)
oraz <wind><linear_velocity/></wind>. Nazwa <world> = nazwa pliku (topiki /world/<name>/...).
Zapis WYŁĄCZNIE do results/WK_RECON/worlds/ (recon nie tworzy plików w worlds/).

Użycie: wk_gen_world.py <NAME> <Vx> <Vy> <Vz>    (ENU, m/s)
"""
import hashlib
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "worlds"))
from gen_world_wind import _plugins_block  # noqa: E402

BASE = os.path.join(ROOT, "worlds", "world_demo_A3.sdf")
BASE_SHA_EXPECTED = "adc918032bc00b08d382b814717d9c77fe0e632362326ff2d5e81cbe715157e0"
OUTD = os.path.join(ROOT, "results", "WK_RECON", "worlds")


def build(name, vx, vy, vz):
    src = open(BASE).read()
    base_sha = hashlib.sha256(src.encode()).hexdigest()
    if base_sha != BASE_SHA_EXPECTED:
        raise SystemExit(f"baza A3 sha {base_sha[:8]} != {BASE_SHA_EXPECTED[:8]} — STOP")
    m = re.search(r'<world name="([^"]+)">', src)
    inject = (
        f'<world name="{name}">\n'
        f'    <!-- WK (recon WIATR-KAMERA). Baza world_demo_A3 sha256={base_sha}. '
        f'Wygenerowane wk_gen_world.py. Pełny stack systemów (server.config) + WindEffects. -->\n'
        f'{_plugins_block()}\n'
        f'    <wind>\n'
        f'      <linear_velocity>{vx} {vy} {vz}</linear_velocity>\n'
        f'    </wind>'
    )
    out = src.replace(m.group(0), inject, 1)
    os.makedirs(OUTD, exist_ok=True)
    dst = os.path.join(OUTD, f"{name}.sdf")
    open(dst, "w").write(out)
    return dst, hashlib.sha256(out.encode()).hexdigest(), base_sha


if __name__ == "__main__":
    name, vx, vy, vz = sys.argv[1:5]
    dst, sha, base_sha = build(name, vx, vy, vz)
    print(f"WROTE {os.path.relpath(dst, ROOT)} sha256={sha} base(A3)={base_sha[:16]} wind=({vx},{vy},{vz}) ENU")
