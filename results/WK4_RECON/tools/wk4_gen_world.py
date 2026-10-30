#!/usr/bin/env python3
"""results/WK4_RECON/tools/wk4_gen_world.py — świat WK4: habitat oporu WK2 bez zmian (A3 + stos systemów +
WindEffects s = 0.63; wk2_gen_world.plugins_block importowany READ-ONLY, wzór wk3_gen_world 1b5895c3)
+ blok <horizontal>/<vertical> WYŁĄCZNIE z <time_for_rise>0.01 (R1: domyślny filtr ~1 s działa także na
zmiany z topiku /world/<W>/wind; 0.01 ⇒ odpowiedź skokowa ≤ 0.03 s w trzech osiach), BEZ bloków <sin>
(R1c: <sin> modulowałby wokół wartości z topiku) i BEZ <noise>; wiatr bazowy <wind> 0 0 0 —
cały przebieg podaje publikator serii (wk4_publisher.py) po topiku.

Użycie: wk4_gen_world.py <NAME>     (np. world_wk4)
"""
import hashlib
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "results", "WK2_RECON", "tools"))
from wk2_gen_world import BASE, BASE_SHA_EXPECTED, plugins_block  # noqa: E402

SCALE = "0.63"   # habitat oporu WK2 (k zmierzone 0.49 /s) — NIEZMIENNY

RISE_BLOCK = "\n".join([
    '      <horizontal>',
    '        <magnitude><time_for_rise>0.01</time_for_rise></magnitude>',
    '        <direction><time_for_rise>0.01</time_for_rise></direction>',
    '      </horizontal>',
    '      <vertical><time_for_rise>0.01</time_for_rise></vertical>'])


def main():
    name = sys.argv[1]
    src = open(BASE).read()
    base_sha = hashlib.sha256(src.encode()).hexdigest()
    if base_sha != BASE_SHA_EXPECTED:
        raise SystemExit("baza A3 sha rozjazd — STOP")
    blk = plugins_block(SCALE)
    tail = '    </plugin>'
    assert blk.endswith(tail)
    blk = blk[: -len(tail)] + RISE_BLOCK + "\n" + tail
    m = re.search(r'<world name="([^"]+)">', src)
    inject = (f'<world name="{name}">\n'
              f'    <!-- WK4 (recon TURBULENCJA). Baza world_demo_A3 sha256={base_sha}. Wygenerowane wk4_gen_world.py. '
              f'Stos systemów + WindEffects skala {SCALE} + time_for_rise 0.01 (bez sin/noise); wiatr z topiku. -->\n'
              f'{blk}\n'
              f'    <wind>\n      <linear_velocity>0 0 0</linear_velocity>\n    </wind>')
    out = src.replace(m.group(0), inject, 1)
    dst = os.path.join(ROOT, "worlds", f"{name}.sdf")
    if os.path.exists(dst):
        raise SystemExit(f"{dst} istnieje — ODMOWA nadpisania")
    open(dst, "w").write(out)
    print(f"WROTE {os.path.relpath(dst, ROOT)} sha256={hashlib.sha256(out.encode()).hexdigest()}")


if __name__ == "__main__":
    main()
