#!/usr/bin/env python3
"""gen_world_demo_v3.py — PROMPT_D_U2R: świat v3 (uplift v2 + naprawa kosztu renderu).

REUŻYWA v1 (HEADER/LCG/kamera/pole-brył; plik v1 i v2 NIETKNIĘTE). U2R §2:
 - ZOSTAJE z v2: niebo (background), trawiaste podłoże, odległy backdrop (skyline);
 - cast_shadows=FALSE na WSZYSTKICH dekoracjach (drzewa/zabudowa/skały + pole brył) — to była
   dominująca przyczyna render-hitch w U2 (H2 FAIL 2/2, deep-stalle). Słońce/scene shadows zostają
   (dynamiczny dron/intruz nadal rzucają cień → cień intruza użyteczny w HUD);
 - korony LOW-POLY: box zamiast ellipsoid (mniej tessellacji); mniej drzew;
 - strefa operacji płaska z=0, ZERO nowych kolizji (tylko wizual, bez <collision>).
Determinizm: SEED_ENR (pole brył v1 bit-identyczne). Gęstość: env U2_TREES/U2_BLDG/U2_ROCKS.

Uruchom:  python3 worlds/gen_world_demo_v3.py --act A1|A3   (→ worlds/world_demo_A1|A3.sdf, v3)
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gen_world_demo_v1 as v1   # v1 NIETKNIĘTY

CLEAR_ZONE = 18.0
PERIM = 46.0
SEED_ENR = 20260822
N_TREES = int(os.environ.get("U2_TREES", "14"))
N_BLDG = int(os.environ.get("U2_BLDG", "11"))
N_ROCKS = int(os.environ.get("U2_ROCKS", "7"))

GROUND_MAT = "<ambient>0.34 0.42 0.27 1</ambient><diffuse>0.36 0.45 0.28 1</diffuse><specular>0.05 0.06 0.04 1</specular>"
SKY_BG = "0.52 0.66 0.85 1"

# pole brył v1 z cast_shadows=false (dekoracja, U2R §2) — reszta jak v1 BOX_TMPL
BOX_TMPL_NS = """    <model name="tex_{i}">
      <static>true</static>
      <pose>{x:.3f} {y:.3f} {z:.3f} 0 0 {yaw:.3f}</pose>
      <link name="l">
        <visual name="v"><cast_shadows>false</cast_shadows>
          <geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry>
          <material><ambient>{r:.3f} {g:.3f} {b:.3f} 1</ambient><diffuse>{r:.3f} {g:.3f} {b:.3f} 1</diffuse><specular>0.1 0.1 0.1 1</specular></material>
        </visual>
      </link>
    </model>
"""

# drzewo LOW-POLY: pień box + korona BOX (mniej tessellacji niż ellipsoid), cast_shadows=false
TREE_TMPL = """    <model name="tree_{i}">
      <static>true</static>
      <pose>{x:.3f} {y:.3f} 0 0 0 {yaw:.3f}</pose>
      <link name="l">
        <visual name="trunk"><cast_shadows>false</cast_shadows><pose>0 0 {th2:.3f} 0 0 0</pose>
          <geometry><box><size>{tw:.3f} {tw:.3f} {th:.3f}</size></box></geometry>
          <material><ambient>0.30 0.20 0.10 1</ambient><diffuse>0.33 0.22 0.11 1</diffuse><specular>0.02 0.02 0.02 1</specular></material>
        </visual>
        <visual name="canopy"><cast_shadows>false</cast_shadows><pose>0 0 {cz:.3f} 0 0 0.5</pose>
          <geometry><box><size>{cw:.3f} {cw:.3f} {chh:.3f}</size></box></geometry>
          <material><ambient>{cg0:.3f} {cg1:.3f} {cg2:.3f} 1</ambient><diffuse>{cg0:.3f} {cg1:.3f} {cg2:.3f} 1</diffuse><specular>0.03 0.05 0.03 1</specular></material>
        </visual>
      </link>
    </model>
"""

BLDG_TMPL = """    <model name="bldg_{i}">
      <static>true</static>
      <pose>{x:.3f} {y:.3f} {z:.3f} 0 0 {yaw:.3f}</pose>
      <link name="l">
        <visual name="v"><cast_shadows>false</cast_shadows>
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
        <visual name="v"><cast_shadows>false</cast_shadows>
          <geometry><box><size>{rx:.3f} {ry:.3f} {rz:.3f}</size></box></geometry>
          <material><ambient>{s:.3f} {s:.3f} {s2:.3f} 1</ambient><diffuse>{s:.3f} {s:.3f} {s2:.3f} 1</diffuse><specular>0.08 0.08 0.08 1</specular></material>
        </visual>
      </link>
    </model>
"""


def _ring_pos(rng, r_lo, r_hi):
    ang = rng.uniform(0, 2 * math.pi)
    r = math.sqrt(rng.uniform(r_lo * r_lo, r_hi * r_hi))
    return r * math.cos(ang), r * math.sin(ang)


def build_boxes_noshadow():
    """Pole brył v1 (IDENTYCZNA geometria/seed) ale cast_shadows=false (dekoracja §2)."""
    rng = v1.LCG(v1.SEED)
    out = []; i = 0
    n = int(v1.EXTENT / v1.SPACING)
    for gx in range(-n, n + 1):
        for gy in range(-n, n + 1):
            if rng.uniform(0, 1) > v1.FILL_P:
                continue
            x = gx * v1.SPACING + rng.uniform(-v1.JITTER, v1.JITTER)
            y = gy * v1.SPACING + rng.uniform(-v1.JITTER, v1.JITTER)
            if (x * x + y * y) ** 0.5 < v1.CLEAR_R:
                continue
            sx = rng.uniform(1.5, 3.8); sy = rng.uniform(1.5, 3.8); sz = rng.uniform(0.1, 1.2)
            z = sz / 2.0; yaw = rng.uniform(0, 3.14159)
            shade = rng.uniform(0.20, 0.78); tint = rng.uniform(0, 1)
            r, g, b = shade, shade, shade
            if tint > 0.85: r, g, b = shade * 1.15, shade * 0.85, shade * 0.7
            elif tint < 0.15: r, g, b = shade * 0.7, shade * 0.9, shade * 1.15
            out.append(BOX_TMPL_NS.format(i=i, x=x, y=y, z=z, yaw=yaw, sx=sx, sy=sy, sz=sz,
                                          r=min(r, 1), g=min(g, 1), b=min(b, 1)))
            i += 1
    return out


def build_enrichment():
    rng = v1.LCG(SEED_ENR)
    parts = []
    for i in range(N_TREES):
        x, y = _ring_pos(rng, CLEAR_ZONE + 2, PERIM)
        th = rng.uniform(2.4, 5.0); tw = rng.uniform(0.3, 0.5)
        cw = rng.uniform(2.6, 4.4); chh = rng.uniform(2.4, 3.8); cz = th + chh * 0.45
        g = rng.uniform(0.30, 0.46)
        parts.append(TREE_TMPL.format(i=i, x=x, y=y, th=th, th2=th / 2, tw=tw, cw=cw, chh=chh, cz=cz,
                                      cg0=0.15 + rng.uniform(0, 0.05), cg1=g, cg2=0.13 + rng.uniform(0, 0.04),
                                      yaw=rng.uniform(0, 1.57)))
    palette = [(0.60, 0.60, 0.63), (0.68, 0.64, 0.55), (0.46, 0.54, 0.66), (0.55, 0.52, 0.50), (0.50, 0.58, 0.62)]
    for i in range(N_BLDG):
        x, y = _ring_pos(rng, 26.0, PERIM)
        sx = rng.uniform(3.0, 8.0); sy = rng.uniform(3.0, 8.0); sz = rng.uniform(5.0, 20.0); z = sz / 2.0
        col = palette[rng.next() % len(palette)]; j = rng.uniform(-0.05, 0.05)
        parts.append(BLDG_TMPL.format(i=i, x=x, y=y, z=z, yaw=rng.uniform(0, 1.57), sx=sx, sy=sy, sz=sz,
                                      r=min(max(col[0] + j, 0), 1), g=min(max(col[1] + j, 0), 1), b=min(max(col[2] + j, 0), 1)))
    for i in range(N_ROCKS):
        x, y = _ring_pos(rng, CLEAR_ZONE, PERIM)
        rx = rng.uniform(1.0, 2.6); ry = rng.uniform(1.0, 2.6); rz = rng.uniform(0.6, 1.4); z = rz / 2.0
        s = rng.uniform(0.34, 0.52)
        parts.append(ROCK_TMPL.format(i=i, x=x, y=y, z=z, yaw=rng.uniform(0, 3.14), rx=rx, ry=ry, rz=rz, s=s, s2=s + 0.03))
    return parts, (N_TREES, N_BLDG, N_ROCKS)


def build_world_v3(act=None):
    world_name = "world_demo_v3" if act is None else f"world_demo_{act}"
    header = v1.HEADER.format(seed=v1.SEED).replace("world_demo_v1", world_name)
    header = header.replace("<background>0.7 0.7 0.7 1</background>", f"<background>{SKY_BG}</background>")
    header = header.replace(
        "<ambient>0.8 0.8 0.8 1</ambient>\n            <diffuse>0.8 0.8 0.8 1</diffuse>\n            <specular>0.8 0.8 0.8 1</specular>",
        GROUND_MAT)
    parts = [header]
    boxes = build_boxes_noshadow()
    parts.append(f"    <!-- v1 pole brył ({len(boxes)}) cast_shadows=false (§2) -->\n"); parts.extend(boxes)
    enr, counts = build_enrichment()
    parts.append(f"    <!-- U2R wzbogacenie low-poly, cast_shadows=false (drzewa={counts[0]} zabudowa={counts[1]} skały={counts[2]}) -->\n")
    parts.extend(enr)
    if act is not None:
        pitch, yaw = v1._cam_pose(v1.ACT_CAM[act]["cam_pos"], v1.ACT_CAM[act]["centroid"])
        px, py, pz = v1.ACT_CAM[act]["cam_pos"]
        parts.append(v1.FILM_CAM_TMPL.format(act=act, px=px, py=py, pz=pz, pitch=pitch, yaw=yaw))
    parts.append("  </world>\n</sdf>\n")
    return "".join(parts), world_name, len(boxes), counts


def main():
    act = None
    if len(sys.argv) > 2 and sys.argv[1] == "--act":
        act = sys.argv[2]; assert act in v1.ACT_CAM
    body, wn, nb, counts = build_world_v3(act)
    fname = "world_demo_v3.sdf" if act is None else f"world_demo_{act}.sdf"
    open(os.path.join(_HERE, fname), "w").write(body)
    print(f"[gen-v3] {fname} (world={wn}, boxes={nb}, enrich={counts}, total={nb + sum(counts)}, shadows_decor=OFF)")


if __name__ == "__main__":
    main()
