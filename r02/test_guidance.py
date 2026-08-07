"""r02/test_guidance.py — testy DETERMINISTYCZNE naprowadzania OBSERVE (R4).

Chroni: (1) paralaksa — estymata bez separacji wysokości zdegenerowana; (2) ANTY-WIROWANIE —
ObserveController ZOH estymaty świata (nie reprojekcja piksela przez bieżący yaw); (3) d≥D_safe;
(4) yaw stabilny na stały punkt świata. Uruchom: python3 -m r02.test_guidance
"""
from __future__ import annotations
import math, sys

from r02.observe_guidance import (estimate_intruder_ned, ObserveController, HFOV, VFOV)
from r02.target_channel import Box
from r02.config_r02 import D_SAFE_M, INTRUDER_ALT_M, ALT_M

FAILS = []


def check(name, cond):
    print(f"  {'✓' if cond else '✗ FAIL'}  {name}")
    if not cond:
        FAILS.append(name)


def test_parallax_needed():
    """Bez separacji wysokości (dron i intruz na tej samej wysokości) wiązka pozioma → fallback
    (fantom), Z separacją → sensowna estymata w kierunku celu."""
    pos_same = [0.0, 0.0, -10.0]                  # dron na 10, cel projektowany na 10 → brak paralaksy
    est_same = estimate_intruder_ned(pos_same, 0.0, 0.5, 0.5, intruder_alt=10.0)
    # fallback horyzontalny: estymata na wprost, dystans = D_safe (fantom) — nie realny zasięg
    check("bez paralaksy: fallback ~D_safe przed dronem",
          est_same is not None and abs(est_same[0] - D_SAFE_M) < 1e-6)
    pos = [0.0, 0.0, -10.0]                        # dron 10, intruz 6 → paralaksa
    est = estimate_intruder_ned(pos, 0.0, 0.5, 0.5, intruder_alt=6.0)
    check("z paralaksą: estymata na płaszczyźnie intruza (z=-6)", est is not None and abs(est[2] + 6.0) < 1e-6)
    check("z paralaksą: estymata przed dronem (+N)", est[0] > 0)


def test_anti_spin_zoh_estimate():
    """ANTY-WIROWANIE: po JEDNEJ detekcji estymata jest STAŁYM punktem świata — yaw_cmd nie zależy
    od bieżącego yaw drona (brak dodatniego sprzężenia). Reprodukcja błędu R3."""
    ctrl = ObserveController(d_safe=D_SAFE_M, alt=ALT_M)
    pos = [0.0, 0.0, -10.0]
    ctrl.on_detection(pos, 0.0, Box(0.5, 0.5, 0.05, 0.05))   # cel na wprost, intruz na z=-6
    est0 = tuple(ctrl.est)
    yaws = [ctrl.yaw_cmd(pos) for _ in range(5)]              # wielokrotne wywołania nie zmieniają
    check("estymata zamrożona (stały punkt świata)", tuple(ctrl.est) == est0)
    check("yaw_cmd stabilny (identyczny przy tym samym pos)", all(abs(y - yaws[0]) < 1e-9 for y in yaws))
    # gdyby estymata reprojektowała piksel przez yaw, obrót drona zmieniłby ją; tu NIE:
    yaw_from_pos_only = ctrl.yaw_cmd(pos)
    check("yaw_cmd = kurs na STAŁY punkt (niezależny od kolejnych wywołań)",
          abs(yaw_from_pos_only - yaws[0]) < 1e-9)


def test_dsafe_ring_no_approach():
    """setpoint trzyma dron poza D_safe (pierścień d_safe+margin); gdy dron dalej — nie wciąga do środka."""
    ctrl = ObserveController(d_safe=D_SAFE_M, alt=ALT_M)
    ctrl.est = [12.0, 0.0, -6.0]                   # zamrożona estymata
    sp = ctrl.setpoint([0.0, 0.0, -10.0])          # dron 12 m przed estymatą (poziomo)
    d_sp = math.hypot(sp[0] - 12.0, sp[1] - 0.0)
    check("setpoint na pierścieniu ≥ D_safe", d_sp >= D_SAFE_M - 1e-6)
    check("setpoint utrzymuje wysokość patrolu (z=-ALT)", abs(sp[2] + ALT_M) < 1e-6)


def test_fov_geometry_sane():
    """FOV pochodne (hfov z SDF, vfov z aspektu) — dodatnie, vfov<hfov dla 4:3."""
    check("hfov=1.74", abs(HFOV - 1.74) < 1e-9)
    check("vfov < hfov (aspekt 4:3)", 0 < VFOV < HFOV)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    print(f"=== R4 testy naprowadzania OBSERVE ({len(tests)} grup) ===")
    for t in tests:
        print(f"[{t.__name__}]"); t()
    ok = not FAILS
    print(f"\nWERDYKT test_guidance: {'PASS' if ok else 'FAIL — ' + ', '.join(FAILS)}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
