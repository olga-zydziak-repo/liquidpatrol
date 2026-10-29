#!/usr/bin/env python3
"""results/WK2_RECON/tools/wk2_gen_world.py — świat WK2: habitat kamerowy A3 + stos systemów + WindEffects
z ZADANĄ skalą oporu (force_approximation_scaling_factor) + wektor wiatru (PROMPT_WK2_S0 §R3).

Wzór: results/WK_RECON/tools/wk_gen_world.py (WK, skala 1.0). Lista 13 systemów importowana READ-ONLY
z worlds/gen_world_wind.py (SERVER_SYSTEMS = server.config verbatim); jedyna różnica bloku wobec WK
to wartość skali. Zapis do worlds/ (wymóg harness/world_hash.sh:11-16), odmowa nadpisania.

Użycie: wk2_gen_world.py <NAME> <SCALE> <Vx> <Vy> <Vz> [--out-dir DIR]
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "worlds"))
from gen_world_wind import SERVER_SYSTEMS, WIND_SYS  # noqa: E402

BASE = os.path.join(ROOT, "worlds", "world_demo_A3.sdf")
BASE_SHA_EXPECTED = "adc918032bc00b08d382b814717d9c77fe0e632362326ff2d5e81cbe715157e0"


def plugins_block(scale):
    lines = []
    for fn, nm, child in SERVER_SYSTEMS:
        lines.append(f'    <plugin filename="{fn}" name="{nm}">{child}</plugin>' if child
                     else f'    <plugin filename="{fn}" name="{nm}"/>')
    lines.append(f'    <plugin filename="{WIND_SYS[0]}" name="{WIND_SYS[1]}">')
    lines.append(f'      <force_approximation_scaling_factor>{scale}</force_approximation_scaling_factor>')
    lines.append('    </plugin>')
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name"); ap.add_argument("scale"); ap.add_argument("vx"); ap.add_argument("vy"); ap.add_argument("vz")
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "worlds"))
    a = ap.parse_args()
    src = open(BASE).read()
    base_sha = hashlib.sha256(src.encode()).hexdigest()
    if base_sha != BASE_SHA_EXPECTED:
        raise SystemExit(f"baza A3 sha {base_sha[:8]} != {BASE_SHA_EXPECTED[:8]} — STOP")
    m = re.search(r'<world name="([^"]+)">', src)
    inject = (f'<world name="{a.name}">\n'
              f'    <!-- WK2 (recon OPÓR REALNY). Baza world_demo_A3 sha256={base_sha}. '
              f'Wygenerowane wk2_gen_world.py. Pełny stack systemów (server.config) + WindEffects skala {a.scale}. -->\n'
              f'{plugins_block(a.scale)}\n'
              f'    <wind>\n      <linear_velocity>{a.vx} {a.vy} {a.vz}</linear_velocity>\n    </wind>')
    out = src.replace(m.group(0), inject, 1)
    dst = os.path.join(a.out_dir, f"{a.name}.sdf")
    if os.path.exists(dst):
        raise SystemExit(f"{dst} istnieje — ODMOWA nadpisania")
    open(dst, "w").write(out)
    print(f"WROTE {os.path.relpath(dst, ROOT)} sha256={hashlib.sha256(out.encode()).hexdigest()} skala={a.scale} wind=({a.vx},{a.vy},{a.vz})")


if __name__ == "__main__":
    main()
