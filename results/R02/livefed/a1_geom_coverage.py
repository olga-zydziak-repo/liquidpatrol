#!/usr/bin/env python3
"""a1_geom_coverage.py — A1 (dyskryminator 0b), tor GEOMETRYCZNY z artefaktów B1.

Pytanie A1: czy jitter attitude pod OBSERVE-motion wyrzuca NOMINALNIE-DEAD-AHEAD cel operacyjny z FOV?
Instrument: rozkład attitude POD RUCHEM już zmierzony w B1 (attitude_samples.json, N=336 motion @ mav 20 Hz).
Dla KAŻDEJ próbki attitude umieszczam cel dead-ahead w geometrii OPERACYJNEJ (config_r02: R_h=6.84 m poziomo,
Δalt=1.5 m nad dronem → 3D=7.0 m, el_nom=12.4°), przy azymucie=yaw próbki (⇒ az_nominal=0, izoluję sam
pitch/roll). Rzutuję przez gate_run_r02.project_full_attitude (pełne attitude, V-FOV 1.453 rad / H-FOV 1.74).

To NIE zależy od detektora ani od placement-lagu — czysty test mechanizmu, który 0b (gimbal) miałby naprawić.
coverage_seen(geom) = frakcja próbek z celem IN-FOV. frames_out_of_fov = 1 - coverage. Reguła A1 (zamrożona):
≥0.95 ⇒ 0b ODRZUCONE. Etykieta przyrządu: mav (attitude_euler ~20 Hz), sim-time B1.
"""
import json, math, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import r02.config_r02 as C


def project_full_attitude(pos, yaw, pitch, roll, intr):
    """KOPIA VERBATIM z r02/gate_run_r02.py:50-69 (pure; unikam importu rclpy w tym module).
    NED→body: Rx(roll)·Ry(pitch)·Rz(yaw); kamera forward = body +X (montaż x500_mono_cam)."""
    import math as _m
    HFOV = 1.74; VFOV = 1.453
    wx, wy, wz = intr[0]-pos[0], intr[1]-pos[1], intr[2]-pos[2]
    cy_, sy = _m.cos(yaw), _m.sin(yaw); cp, sp = _m.cos(pitch), _m.sin(pitch); cr, sr = _m.cos(roll), _m.sin(roll)
    x1 =  cy_*wx + sy*wy;  y1 = -sy*wx + cy_*wy;  z1 = wz
    x2 =  cp*x1 - sp*z1;   y2 = y1;               z2 = sp*x1 + cp*z1
    bx = x2;               by = cr*y2 + sr*z2;    bz = -sr*y2 + cr*z2
    if bx <= 0.1:
        return {"in_fov": False, "reason": "za_kamera", "cx": None, "cy": None, "az_deg": None, "el_deg": None}
    az = _m.atan2(by, bx); el = _m.atan2(-bz, _m.hypot(bx, by))
    in_fov = (abs(az) <= HFOV/2.0 and abs(el) <= VFOV/2.0)
    cx = 0.5 + _m.tan(az)/(2.0*_m.tan(HFOV/2.0))
    cyp = 0.5 - _m.tan(el)/(2.0*_m.tan(VFOV/2.0))
    return {"in_fov": in_fov, "cx": round(cx,3), "cy": round(cyp,3),
            "az_deg": round(_m.degrees(az),2), "el_deg": round(_m.degrees(el),2)}

# geometria operacyjna (config_r02 §D_SAFE derywacja): R_h poziomo, Δalt nad dronem, 3D=7.0 m
DALT = C.INTRUDER_ALT_M - C.ALT_M            # 11.5 - 10 = 1.5 m separacja pionowa
R_H = math.sqrt(7.0**2 - DALT**2)            # 6.84 m poziomo (środek koperty A7)
EL_NOM = math.degrees(math.atan2(DALT, R_H)) # ~12.4° elewacja nominalna
SAMPLES = os.path.join(os.path.dirname(__file__), "B1", "run1", "attitude_samples.json")


def cov_for_phase(samples, el_shift_up=True):
    n = 0; in_fov = 0; cxs = []; cys = []; els = []; edge = []; out = []
    for s in samples:
        yaw = math.radians(s["yaw"]); pitch = math.radians(s["pitch"]); roll = math.radians(s["roll"])
        # cel dead-ahead wg yaw TEJ próbki (az_nominal=0), poziomo R_H, w górę Δalt.
        # NED: pos=(0,0,0); intr = (R_H*cos yaw, R_H*sin yaw, -Δalt)  [down ujemny = w górę]
        dz = -DALT if el_shift_up else DALT
        intr = (R_H * math.cos(yaw), R_H * math.sin(yaw), dz)
        pf = project_full_attitude((0.0, 0.0, 0.0), yaw, pitch, roll, intr)
        n += 1
        if pf["in_fov"]:
            in_fov += 1
            cxs.append(pf["cx"]); cys.append(pf["cy"]); els.append(pf["el_deg"])
            edge.append(min(pf["cx"], 1 - pf["cx"], pf["cy"], 1 - pf["cy"]))
        else:
            out.append({"t": s["t"], "pitch": round(s["pitch"], 1), "roll": round(s["roll"], 1),
                        "az": pf["az_deg"], "el": pf["el_deg"], "reason": pf.get("reason", "kat")})

    def st(a):
        if not a: return None
        a = sorted(a)
        return {"n": len(a), "min": round(a[0], 3), "p05": round(a[max(0, int(0.05 * len(a)))], 3),
                "p50": round(a[len(a) // 2], 3), "p95": round(a[min(len(a) - 1, int(0.95 * len(a)))], 3),
                "max": round(a[-1], 3)}
    return {"n": n, "in_fov": in_fov, "coverage_seen_geom": round(in_fov / n, 3) if n else None,
            "frames_out_of_fov": len(out), "cx": st(cxs), "cy": st(cys), "el_deg": st(els),
            "edge_dist": st(edge), "out_examples": out[:8]}


def main():
    samples = json.load(open(SAMPLES))
    mot = [s for s in samples if s["phase"] == "motion"]
    hov = [s for s in samples if s["phase"] == "hover"]
    res = {
        "instrument": "mav (attitude_euler ~20Hz) — z B1 attitude_samples.json (POD OBSERVE-motion)",
        "geometry": {"R_h_m": round(R_H, 3), "delta_alt_m": DALT, "range_3d_m": 7.0,
                     "el_nominal_deg": round(EL_NOM, 2), "HFOV_rad": 1.74, "VFOV_rad": 1.453,
                     "half_VFOV_deg": round(math.degrees(1.453 / 2), 2), "az_nominal_deg": 0.0,
                     "note": "cel operacyjny dead-ahead (az=0 wg yaw próbki); izoluje pitch/roll jitter; "
                             "el_nom liczony jako el=atan(Δalt/R_h); rzut = project_full_attitude"},
        "MOTION": cov_for_phase(mot),
        "HOVER_baseline": cov_for_phase(hov),
        "routing_rule": "coverage_seen_geom >= 0.95 => 0b ODRZUCONE definitywnie (PRE_R02C/A1, zamrożona)",
    }
    # wariant kontrolny: cel PONIŻEJ (el ujemna) — czy znak Δalt zmienia werdykt (kierunkowość)
    res["MOTION_target_below"] = cov_for_phase(mot, el_shift_up=False)
    out = os.path.join(os.path.dirname(__file__), "a1_geom_coverage.json")
    json.dump(res, open(out, "w"), indent=2, ensure_ascii=False)
    m = res["MOTION"]
    print(f"[a1-geom] MOTION n={m['n']} coverage_seen_geom={m['coverage_seen_geom']} "
          f"out_of_fov={m['frames_out_of_fov']} cy={m['cy']} el={m['el_deg']} edge={m['edge_dist']}")
    print(f"[a1-geom] HOVER coverage={res['HOVER_baseline']['coverage_seen_geom']} "
          f"| below-variant coverage={res['MOTION_target_below']['coverage_seen_geom']} "
          f"out={res['MOTION_target_below']['frames_out_of_fov']}")
    verdict = "0b ODRZUCONE" if m["coverage_seen_geom"] >= 0.95 else "0b WRACA do ratyfikacji"
    print(f"[a1-geom] VERDICT (motion, target-above): coverage={m['coverage_seen_geom']} → {verdict}")
    print(f"→ {out}")


if __name__ == "__main__":
    main()
