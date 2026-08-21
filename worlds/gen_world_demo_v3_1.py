#!/usr/bin/env python3
"""gen_world_demo_v3_1.py — PROMPT_D_U2R-2 §3: świat v3.1 = v3 + zmiana WYŁĄCZNIE kamery filmowej (A1),
by tłem ringu był teren/skyline zamiast jasnego nieba (dźwignia §1b). v3/v2/v1 generatory NIETKNIĘTE.
Materiał intruza (dźwignia §1a) = r02/intruder_model.sdf (osobno). Fizyka/spec/strefa/enrichment bez zmian.

Kamera A1: podniesiona do ~wysokości ringu (z 8→11.5) → ring rzutowany blisko horyzontu (tło = skyline/
trawa), sylwetka ciemnego intruza kontrastuje. A3 (brak intruza) — kamera jak v3.

Uruchom: python3 worlds/gen_world_demo_v3_1.py --act A1|A3   (→ worlds/world_demo_A1|A3.sdf, v3.1)
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gen_world_demo_v1 as v1
import gen_world_demo_v3 as v3

# §3: nowa poza kamery A1 (podniesiona; A3 bez zmian). centroid lekko wyżej (na ring), by intruz był w kadrze.
CAM_V31 = {
    "A1": {"centroid": (5.0, 0.0, 11.2), "cam_pos": (11.0, -13.0, 11.5)},
    "A3": dict(v1.ACT_CAM["A3"]),
}


def build(act):
    saved = {k: dict(v) for k, v in v1.ACT_CAM.items()}
    try:
        for a in ("A1", "A3"):
            v1.ACT_CAM[a] = CAM_V31[a]
        world_name = "world_demo_v3_1" if act is None else f"world_demo_{act}"
        body, wn, nb, counts = v3.build_world_v3(act)
        if act is None:
            body = body.replace("world_demo_v3", "world_demo_v3_1")
        return body, wn, nb, counts
    finally:
        v1.ACT_CAM = saved


def main():
    act = None
    if len(sys.argv) > 2 and sys.argv[1] == "--act":
        act = sys.argv[2]; assert act in v1.ACT_CAM
    body, wn, nb, counts = build(act)
    fname = "world_demo_v3_1.sdf" if act is None else f"world_demo_{act}.sdf"
    open(os.path.join(_HERE, fname), "w").write(body)
    print(f"[gen-v3.1] {fname} (boxes={nb}, enrich={counts}, total={nb+sum(counts)}, cam_A1={CAM_V31['A1']['cam_pos']})")


if __name__ == "__main__":
    main()
