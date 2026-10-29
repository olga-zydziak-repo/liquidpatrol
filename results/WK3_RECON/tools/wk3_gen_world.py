#!/usr/bin/env python3
"""results/WK3_RECON/tools/wk3_gen_world.py — świat WK3: habitat oporu WK2 (A3 + stos systemów + WindEffects
s = 0.63, generator wk2_gen_world.plugins_block importowany READ-ONLY) + blok porywu <horizontal> wewnątrz
pluginu WindEffects + wektor średni <wind><linear_velocity>.

Litera bloku zmierzona w RECON_WK3 §R1: |w| = średnia·(1 + amplitude_percent·sin(2π t_sim/period))
(amplitude_percent = UŁAMEK), kierunek = kierunek średniej + amplitude[deg]·sin(2π t_sim/period),
faza od t_sim = 0; time_for_rise [s] = wyłącznie rozruch po starcie świata; <noise> NIE używany
(niedeterministyczny bez --seed, którego launcher PX4 nie podaje).

Użycie: wk3_gen_world.py <NAME> <mean_vx> <amp_frac> <period_mag_s> <amp_dir_deg|0> <period_dir_s|0>
"""
import hashlib
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "results", "WK2_RECON", "tools"))
from wk2_gen_world import BASE, BASE_SHA_EXPECTED, plugins_block  # noqa: E402

SCALE = "0.63"   # habitat oporu WK2 (k zmierzone 0.49 /s) — NIEZMIENNY


def horizontal_block(amp, pm, ad, pd):
    s = ['      <horizontal>',
         '        <magnitude>',
         '          <time_for_rise>1.0</time_for_rise>',
         f'          <sin><amplitude_percent>{amp}</amplitude_percent><period>{pm}</period></sin>',
         '        </magnitude>']
    if float(ad) != 0.0:
        s += ['        <direction>',
              '          <time_for_rise>1.0</time_for_rise>',
              f'          <sin><amplitude>{ad}</amplitude><period>{pd}</period></sin>',
              '        </direction>']
    s += ['      </horizontal>']
    return "\n".join(s)


def main():
    name, vx, amp, pm, ad, pd = sys.argv[1:7]
    src = open(BASE).read()
    base_sha = hashlib.sha256(src.encode()).hexdigest()
    if base_sha != BASE_SHA_EXPECTED:
        raise SystemExit("baza A3 sha rozjazd — STOP")
    blk = plugins_block(SCALE)
    tail = '    </plugin>'
    assert blk.endswith(tail)
    blk = blk[: -len(tail)] + horizontal_block(amp, pm, ad, pd) + "\n" + tail
    m = re.search(r'<world name="([^"]+)">', src)
    inject = (f'<world name="{name}">\n'
              f'    <!-- WK3 (recon PORYWY). Baza world_demo_A3 sha256={base_sha}. Wygenerowane wk3_gen_world.py. '
              f'Stos systemów + WindEffects skala {SCALE} + poryw sinusowy (bez noise). -->\n'
              f'{blk}\n'
              f'    <wind>\n      <linear_velocity>{vx} 0 0</linear_velocity>\n    </wind>')
    out = src.replace(m.group(0), inject, 1)
    dst = os.path.join(ROOT, "worlds", f"{name}.sdf")
    if os.path.exists(dst):
        raise SystemExit(f"{dst} istnieje — ODMOWA nadpisania")
    open(dst, "w").write(out)
    print(f"WROTE {os.path.relpath(dst, ROOT)} sha256={hashlib.sha256(out.encode()).hexdigest()}")


if __name__ == "__main__":
    main()
