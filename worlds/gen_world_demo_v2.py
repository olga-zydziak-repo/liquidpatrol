#!/usr/bin/env python3
"""gen_world_demo_v2.py — PROMPT_D_U2: uplift WIZUALNY świata dema (world_demo_v2).

REUŻYWA v1 (gen_world_demo_v1: HEADER, LCG, BOX_TMPL, FILM_CAM_TMPL, ACT_CAM, _cam_pose, build_boxes,
SEED) — plik v1 NIETKNIĘTY (hash world_demo_v1 a76a38c8 zamrożony). U2 §2d: fizyka/spec/sędzia/tracker
i logika generatora v1 bez zmian; JEDYNA zmiana wejścia = ŚWIAT (wzbogacenie wizualne).

U2 §2 zasady:
 a) STREFA OPERACJI (korytarz origin→ring 7.86→lądowisko ~13, wszystko wzdłuż +E): podłoże PŁASKIE z=0,
    ZERO nowych kolizji — całe wzbogacenie jest WIZUALNE (bez <collision>, jak pole tex_ w v1);
 b) wzbogacenie: (1) niebo (scene background) + trawiaste podłoże (ground_plane material),
    (2) obiekty POZA strefą (drzewa/skały/zabudowa) na r>CLEAR_ZONE — tło w kadrze kamery,
    (3) oświetlenie (fill-light) — bez zmiany słońca;
 c) assety = prymitywy standardowe (box/cylinder/sphere/ellipsoid — renderują się headless, ENGINE-RECON);
 d) nazwy wewn. world_demo_<AKT> (topiki spójne); kamera i pole brył z v1 (paralaksa) NIETKNIĘTE.

Determinizm: osobny LCG (SEED_ENR) — pole brył v1 bit-identyczne, wzbogacenie reprodukowalne.
Gęstość regulowana env U2_TREES/U2_BLDG/U2_ROCKS (fallback LOD dla bramki RTF §3b).

Uruchom:  python3 worlds/gen_world_demo_v2.py --act A1   (→ worlds/world_demo_A1.sdf, v2)
          python3 worlds/gen_world_demo_v2.py --act A3
          python3 worlds/gen_world_demo_v2.py            (→ worlds/world_demo_v2.sdf, baza)
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gen_world_demo_v1 as v1   # REUŻYCIE — v1 NIETKNIĘTY

CLEAR_ZONE = 18.0     # promień strefy operacji (akcja ≤15 m: ring 7.86, A3 13) — wzbogacenie tylko POZA
PERIM = 46.0          # zewnętrzny perymetr wzbogacenia
SEED_ENR = 20260821   # osobny seed (pole brył v1 nietknięte)

# skala gęstości (env — fallback LOD dla §3b). U2 §3b: control_1 @166 modeli → H2 FAIL na segm. roszczeń
# (dwell Δsim/Δwall=0.9328<0.95, frac<0.5=0.0037>0 — koszt renderu szczytuje w dwell gdy kamera kadruje
# pełną scenę). Redukcja: trees 44→12, bldg 16→10, rocks 22→6 (28 enrich, total 112 vs v1 84) — sky+grunt+
# skyline utrzymują uplift, koszt renderu ~v1. Fallback dalszy przez env gdyby 2. bieg też FAIL (→ STOP v1.0).
N_TREES = int(os.environ.get("U2_TREES", "12"))
N_BLDG = int(os.environ.get("U2_BLDG", "10"))
N_ROCKS = int(os.environ.get("U2_ROCKS", "6"))

# ---- materiały (ambient≈diffuse, specular niski jak v1) ----
GROUND_MAT = "<ambient>0.34 0.42 0.27 1</ambient><diffuse>0.36 0.45 0.28 1</diffuse><specular>0.05 0.06 0.04 1</specular>"
SKY_BG = "0.52 0.66 0.85 1"     # niebo (zamiast szarego 0.7)

TREE_TMPL = """    <model name="tree_{i}">
      <static>true</static>
      <pose>{x:.3f} {y:.3f} 0 0 0 0</pose>
      <link name="l">
        <visual name="trunk"><pose>0 0 {th2:.3f} 0 0 0</pose>
          <geometry><cylinder><radius>{tr:.3f}</radius><length>{th:.3f}</length></cylinder></geometry>
          <material><ambient>0.30 0.20 0.10 1</ambient><diffuse>0.33 0.22 0.11 1</diffuse><specular>0.02 0.02 0.02 1</specular></material>
        </visual>
        <visual name="canopy"><pose>0 0 {cz:.3f} 0 0 0</pose>
          <geometry><ellipsoid><radii>{cr:.3f} {cr:.3f} {ch:.3f}</radii></ellipsoid></geometry>
          <material><ambient>{cr0:.3f} {cg0:.3f} {cb0:.3f} 1</ambient><diffuse>{cr1:.3f} {cg1:.3f} {cb1:.3f} 1</diffuse><specular>0.03 0.05 0.03 1</specular></material>
        </visual>
      </link>
    </model>
"""

BLDG_TMPL = """    <model name="bldg_{i}">
      <static>true</static>
      <pose>{x:.3f} {y:.3f} {z:.3f} 0 0 {yaw:.3f}</pose>
      <link name="l">
        <visual name="v">
          <geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry>
          <material><ambient>{r:.3f} {g:.3f} {b:.3f} 1</ambient><diffuse>{r:.3f} {g:.3f} {b:.3f} 1</diffuse><specular>0.14 0.14 0.16 1</specular></material>
        </visual>
      </link>
    </model>
"""

ROCK_TMPL = """    <model name="rock_{i}">
      <static>true</static>
      <pose>{x:.3f} {y:.3f} {z:.3f} 0 0 {yaw:.3f}</pose>
      <link name="l">
        <visual name="v">
          <geometry><ellipsoid><radii>{rx:.3f} {ry:.3f} {rz:.3f}</radii></ellipsoid></geometry>
          <material><ambient>{s:.3f} {s:.3f} {s2:.3f} 1</ambient><diffuse>{s:.3f} {s:.3f} {s2:.3f} 1</diffuse><specular>0.08 0.08 0.08 1</specular></material>
        </visual>
      </link>
    </model>
"""

FILL_LIGHT = """    <!-- U2: fill-light miękki (niebieskawy sky-fill) — głębia cieni; słońce sunUTC nietknięte. -->
    <light name="u2_fill" type="directional">
      <pose>0 0 400 0 -0 0</pose>
      <cast_shadows>false</cast_shadows>
      <intensity>0.35</intensity>
      <direction>-0.3 -0.4 -0.86</direction>
      <diffuse>0.55 0.60 0.70 1</diffuse>
      <specular>0.05 0.05 0.06 1</specular>
      <attenuation><range>2000</range><linear>0</linear><constant>1</constant><quadratic>0</quadratic></attenuation>
      <spot><inner_angle>0</inner_angle><outer_angle>0</outer_angle><falloff>0</falloff></spot>
    </light>
"""


def _ring_pos(rng, r_lo, r_hi, ang_lo=0.0, ang_hi=2 * math.pi):
    ang = rng.uniform(ang_lo, ang_hi)
    r = math.sqrt(rng.uniform(r_lo * r_lo, r_hi * r_hi))   # jednorodnie po powierzchni
    return r * math.cos(ang), r * math.sin(ang)


def build_enrichment():
    """Wizualne obiekty POZA strefą operacji (r>CLEAR_ZONE). Deterministyczne (SEED_ENR). Zero kolizji."""
    rng = v1.LCG(SEED_ENR)
    parts = []
    # DRZEWA — pierścień wokół perymetru, gęściej w tle akcji (skłon ku +E/±N widoczny w kadrze)
    for i in range(N_TREES):
        x, y = _ring_pos(rng, CLEAR_ZONE + 2, PERIM)
        th = rng.uniform(2.4, 5.2)                 # wysokość pnia
        tr = rng.uniform(0.18, 0.34)               # promień pnia
        cr = rng.uniform(1.4, 2.8)                 # promień korony
        ch = rng.uniform(1.6, 3.0)                 # półwysokość korony
        cz = th + ch * 0.7                         # środek korony nad pniem
        g = rng.uniform(0.30, 0.46)                # zieleń
        parts.append(TREE_TMPL.format(i=i, x=x, y=y, th=th, th2=th / 2, tr=tr,
                                      cr=cr, ch=ch, cz=cz,
                                      cr0=0.14 + rng.uniform(0, 0.06), cg0=g, cb0=0.12 + rng.uniform(0, 0.05),
                                      cr1=0.16 + rng.uniform(0, 0.06), cg1=g + 0.04, cb1=0.14 + rng.uniform(0, 0.05)))
    # ZABUDOWA — skyline w tle (dalej: r>26), zróżnicowana wysokość/kolor; kilka odcieni „miejskich"
    palette = [(0.60, 0.60, 0.63), (0.68, 0.64, 0.55), (0.46, 0.54, 0.66), (0.55, 0.52, 0.50), (0.50, 0.58, 0.62)]
    for i in range(N_BLDG):
        x, y = _ring_pos(rng, 26.0, PERIM)
        sx = rng.uniform(3.0, 8.0); sy = rng.uniform(3.0, 8.0); sz = rng.uniform(5.0, 20.0)
        z = sz / 2.0
        yaw = rng.uniform(0, 1.57)
        col = palette[v1.LCG(int(rng.next())).next() % len(palette)]
        jitter = rng.uniform(-0.05, 0.05)
        parts.append(BLDG_TMPL.format(i=i, x=x, y=y, z=z, yaw=yaw, sx=sx, sy=sy, sz=sz,
                                      r=min(max(col[0] + jitter, 0), 1), g=min(max(col[1] + jitter, 0), 1),
                                      b=min(max(col[2] + jitter, 0), 1)))
    # SKAŁY — niskie, przy gruncie, rozproszone
    for i in range(N_ROCKS):
        x, y = _ring_pos(rng, CLEAR_ZONE, PERIM)
        rx = rng.uniform(0.6, 1.8); ry = rng.uniform(0.6, 1.8); rz = rng.uniform(0.4, 1.1)
        z = rz * 0.6
        yaw = rng.uniform(0, 3.14)
        s = rng.uniform(0.34, 0.52)
        parts.append(ROCK_TMPL.format(i=i, x=x, y=y, z=z, yaw=yaw, rx=rx, ry=ry, rz=rz, s=s, s2=s + 0.03))
    return parts, (N_TREES, N_BLDG, N_ROCKS)


def build_world_v2(act=None):
    world_name = "world_demo_v2" if act is None else f"world_demo_{act}"
    header = v1.HEADER.format(seed=v1.SEED)
    if act is not None:
        header = header.replace("world_demo_v1", world_name)
    else:
        header = header.replace("world_demo_v1", "world_demo_v2")
    # U2 §2b: niebo + trawiaste podłoże (materiał ground_plane) — string-replace na HEADER v1 (v1 plik nietknięty)
    header = header.replace("<background>0.7 0.7 0.7 1</background>", f"<background>{SKY_BG}</background>")
    header = header.replace(
        "<ambient>0.8 0.8 0.8 1</ambient>\n            <diffuse>0.8 0.8 0.8 1</diffuse>\n            <specular>0.8 0.8 0.8 1</specular>",
        GROUND_MAT)

    parts = [header]
    boxes = v1.build_boxes()                         # pole brył v1 — NIETKNIĘTE (paralaksa, §2d)
    parts.append(f"    <!-- v1 pole brył ({len(boxes)}) — NIETKNIĘTE (paralaksa frozen §2d) -->\n")
    parts.extend(boxes)
    enr, counts = build_enrichment()
    parts.append(f"    <!-- U2 wzbogacenie WIZUALNE (drzewa={counts[0]} zabudowa={counts[1]} skały={counts[2]}, r>{CLEAR_ZONE} m, ZERO kolizji) -->\n")
    parts.extend(enr)
    parts.append(FILL_LIGHT)
    if act is not None:                              # kamera filmowa v1 (aim-at-centroid) — NIETKNIĘTA
        pitch, yaw = v1._cam_pose(v1.ACT_CAM[act]["cam_pos"], v1.ACT_CAM[act]["centroid"])
        px, py, pz = v1.ACT_CAM[act]["cam_pos"]
        parts.append(v1.FILM_CAM_TMPL.format(act=act, px=px, py=py, pz=pz, pitch=pitch, yaw=yaw))
    parts.append("  </world>\n</sdf>\n")
    return "".join(parts), world_name, len(boxes), counts


def main():
    act = None
    if len(sys.argv) > 2 and sys.argv[1] == "--act":
        act = sys.argv[2]
        assert act in v1.ACT_CAM, f"nieznany akt {act}"
    body, world_name, nboxes, counts = build_world_v2(act)
    fname = "world_demo_v2.sdf" if act is None else f"world_demo_{act}.sdf"
    out = os.path.join(_HERE, fname)
    with open(out, "w") as f:
        f.write(body)
    print(f"[gen-v2] {out} (world={world_name}, boxes={nboxes}, +enrich trees/bldg/rocks={counts}, "
          f"total_models={nboxes + sum(counts)})")


if __name__ == "__main__":
    main()
