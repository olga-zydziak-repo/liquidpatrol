#!/usr/bin/env python3
"""results/NADIR/tools/nadir_gen.py — budowa S1 nogi NADIR (PROMPT_NADIR_S1 §1.1–§1.3, PRE_NADIR §2.1–§2.2). Tylko nowe pliki.

1. Manifest znaczników results/NADIR/s1/manifest_znaczniki.json: siatka s = 10 m, węzeł (0,0) pod home, |węzeł| ≤ 32 m
   (37 węzłów), DICT_4X4_50, ID = indeks węzła (kolejność: E rosnąco, potem N rosnąco), W = 1.00 m (bok czarnej ramki).
   Dodatkowo kolizje węzłów z bryłami świata (rzut prostokąta bryły z marginesem 0.7 m) — znacznik leży na gruncie
   i pod bryłą jest zasłonięty; siatki się NIE przesuwa (FROZEN w PRE), kolizja = fakt do R6.
2. Tekstury worlds/nadir_markers/aruco4x4_id{NN}.png: cv2.aruco.drawMarker (OpenCV 4.6.0 — systemowe; w 4.7+ nazywa się
   generateImageMarker) 384 px = 6 komórek × 64 px + biała strefa ciszy 1 komórka z każdej strony ⇒ 512 px = 8/6 · W.
3. Świat worlds/world_nadir_A3.sdf = worlds/world_kont_A3.sdf bajt-w-bajt + 37 modeli nadir_m{NN} przed </world>;
   różnice WYŁĄCZNIE: nazwa świata (PX4 czeka na /world/<PX4_GZ_WORLD>) i dodane modele (assert jak kont_gen_world.py).
   Znacznik: statyczny, sam visual (bez kolizji), płaszczyzna 1.3333 × 1.3333 m na z = 0.03 (nad dekalem KONT 0.01),
   cast_shadows false, visibility_flags = 4 (bit 2).
4. Model-wariant results/NADIR/s1/zrodla/x500_nadir_flow/ (instalowany do PX4 models/ przy boocie — nowy katalog):
   = x500_mono_cam_flow/model.sdf (pin KONT, nietknięty) z różnicami WYŁĄCZNIE:
   (a) nazwa modelu; (b) kamera przepływu: replace czujnika flow_camera z identycznymi parametrami + visibility_mask
   4294967291 (= ~bit 2) — przepływ NIE widzi znaczników, więc wejście EKF jest jak w 2d (warunek PRE §2.4 „ε_b bez zmian”;
   decyzja wykonawcy, nazwana w raporcie); (c) nowy link nadir_link (masa 0.001 kg, jak lidar_sensor_link) na złączu
   stałym w początku base_link, czujnik „nadir”: oś optyczna −z_body (pitch +90°: góra kadru = przód, prawo = −y_body),
   640×480, horizontal_fov 1.74 (f = 269.5 px, jak mono_cam), 15 Hz, clip 0.1–100, maska domyślna (widzi wszystko).
   Kamera misji (imager, maska ~bit 1) widzi znaczniki — tak każe R1/R4.
5. rig_nadir.sdf (statyczny wrapper do bootu b1, wzór results/KONT/s1/zrodla/rig_flow.sdf) i pin_nadir.json (sha256 plików).
"""
import hashlib
import json
import math
import os
import re

import cv2
import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
S1 = os.path.join(ROOT, "results/NADIR/s1")
ZR = os.path.join(S1, "zrodla")
KONT_W = os.path.join(ROOT, "worlds/world_kont_A3.sdf")
OUT_W = os.path.join(ROOT, "worlds/world_nadir_A3.sdf")
TEX = os.path.join(ROOT, "worlds/nadir_markers")
SRC_MODEL = os.path.join(ROOT, "PX4-Autopilot/Tools/simulation/gz/models/x500_mono_cam_flow/model.sdf")
S, R_E, W = 10.0, 32.0, 1.0
PLATE = W * 8 / 6
Z_M = 0.03
FLAG = 4
FLOW_MASK = 4294967295 & ~FLAG
MARGIN = 0.7


def wezly():
    k = int(R_E // S)
    return [(i * S, j * S) for i in range(-k, k + 1) for j in range(-k, k + 1) if math.hypot(i * S, j * S) <= R_E]


def bryly(src):
    out = []
    for m in re.finditer(r'<model name="([^"]+)">\s*<static>true</static>\s*<pose>([^<]+)</pose>.*?<size>([^<]+)</size>', src, re.S):
        n, p, sz = m.groups()
        x, y, z, _, _, yaw = map(float, p.split())
        sx, sy, sz_ = map(float, sz.split())
        if n in ("kont_decal", "film_cam"):
            continue
        out.append((n, x, y, yaw, sx, sy, sz_))
    return out


def koliduje(e, n, b):
    name, x, y, yaw, sx, sy, sz = b
    dx, dy = e - x, n - y
    c, s_ = math.cos(-yaw), math.sin(-yaw)
    lx, ly = c * dx - s_ * dy, s_ * dx + c * dy
    return abs(lx) <= sx / 2 + MARGIN and abs(ly) <= sy / 2 + MARGIN


def marker_png(i):
    d = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
    m = cv2.aruco.drawMarker(d, i, 384)
    return cv2.copyMakeBorder(m, 64, 64, 64, 64, cv2.BORDER_CONSTANT, value=255)


def model_xml(i, e, n, png):
    return f"""    <model name="nadir_m{i:02d}">
      <static>true</static>
      <pose>{e:g} {n:g} {Z_M} 0 0 0</pose>
      <link name="l">
        <visual name="v"><cast_shadows>false</cast_shadows>
          <visibility_flags>{FLAG}</visibility_flags>
          <geometry><plane><normal>0 0 1</normal><size>{PLATE:.4f} {PLATE:.4f}</size></plane></geometry>
          <material><ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse><specular>0 0 0 1</specular>
            <pbr><metal><albedo_map>{png}</albedo_map><metalness>0</metalness><roughness>1</roughness></metal></pbr>
          </material>
        </visual>
      </link>
    </model>
"""


FLOW_INC_OLD = """    <include merge='true'>
      <uri>model://optical_flow</uri>
      <pose relative_to="base_link">0.03 0 -0.1 0 0 0</pose>
    </include>"""
FLOW_INC_NEW = f"""    <include merge='true'>
      <uri>model://optical_flow</uri>
      <pose relative_to="base_link">0.03 0 -0.1 0 0 0</pose>
      <experimental:params>
        <!-- NADIR: kopia czujnika flow_camera z optical_flow/model.sdf + maska ~bit 2 (znaczniki niewidoczne dla przepływu) -->
        <sensor element_id="flow_link::flow_camera" action="replace" name="flow_camera" type="camera">
        <pose>0 0 0 0 1.5707 0</pose>
        <camera>
          <horizontal_fov>0.733038</horizontal_fov>
          <image>
            <width>100</width>
            <height>100</height>
          </image>
          <clip>
            <near>0.1</near>
            <far>30</far>
          </clip>
          <visibility_mask>{FLOW_MASK}</visibility_mask>
        </camera>
        <always_on>1</always_on>
        <update_rate>50</update_rate>
        <visualize>true</visualize>
      </sensor>
      </experimental:params>
    </include>"""
NADIR_LINK = """    <!-- NADIR: druga kamera, oś −z_body (PRE_NADIR §2.2) -->
    <link name="nadir_link">
      <pose relative_to="base_link">0 0 0 0 0 0</pose>
      <inertial>
        <mass>0.001</mass>
        <inertia>
          <ixx>0.00001</ixx>
          <iyy>0.00001</iyy>
          <izz>0.00001</izz>
          <ixy>0.0</ixy>
          <ixz>0.0</ixz>
          <iyz>0.0</iyz>
        </inertia>
      </inertial>
      <sensor name="nadir" type="camera">
        <pose>0 0 0 0 1.5707963 0</pose>
        <camera>
          <horizontal_fov>1.74</horizontal_fov>
          <image>
            <width>640</width>
            <height>480</height>
          </image>
          <clip>
            <near>0.1</near>
            <far>100</far>
          </clip>
        </camera>
        <always_on>1</always_on>
        <update_rate>15</update_rate>
        <visualize>false</visualize>
      </sensor>
    </link>
    <joint name="nadir_joint" type="fixed">
      <parent>base_link</parent>
      <child>nadir_link</child>
    </joint>
  </model>"""


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    os.makedirs(TEX, exist_ok=True)
    os.makedirs(os.path.join(ZR, "x500_nadir_flow"), exist_ok=True)
    src = open(KONT_W, encoding="utf8").read()
    sw = hashlib.sha256(src.encode()).hexdigest()
    br = bryly(src)
    wz = sorted(wezly())
    assert len(wz) == 37, len(wz)
    znaczniki, xml = [], ""
    for i, (e, n) in enumerate(wz):
        png = os.path.join(TEX, f"aruco4x4_id{i:02d}.png")
        cv2.imwrite(png, marker_png(i))
        kol = [b[0] for b in br if koliduje(e, n, b)]
        znaczniki.append({"id": i, "E": e, "N": n, "z": Z_M, "kolizje_z_brylami": kol, "png": os.path.relpath(png, ROOT),
                          "png_sha256": sha(png)})
        xml += model_xml(i, e, n, png)
    name_k, name_n = '<world name="world_kont_A3">', '<world name="world_nadir_A3">'
    assert src.count(name_k) == 1 and src.count("  </world>") == 1
    out = src.replace(name_k, name_n).replace("  </world>", xml + "  </world>")
    assert out.replace(xml, "").replace(name_n, name_k) == src
    open(OUT_W, "w", encoding="utf8").write(out)
    # model
    m = open(SRC_MODEL, encoding="utf8").read()
    assert m.count("<model name='x500_mono_cam_flow'>") == 1 and m.count(FLOW_INC_OLD) == 1 and m.count("  </model>") == 1
    mn = (m.replace("<model name='x500_mono_cam_flow'>", "<model name='x500_nadir_flow'>").replace(FLOW_INC_OLD, FLOW_INC_NEW)
          .replace("  </model>", NADIR_LINK))
    mp = os.path.join(ZR, "x500_nadir_flow/model.sdf")
    open(mp, "w", encoding="utf8").write(mn)
    cp = os.path.join(ZR, "x500_nadir_flow/model.config")
    open(cp, "w").write('<?xml version="1.0"?>\n<model>\n  <name>x500_nadir_flow</name>\n  <version>1.0</version>\n'
                        '  <sdf version="1.9">model.sdf</sdf>\n  <description>LiquidPatrol NADIR: x500_mono_cam_flow + kamera nadir '
                        '(oś -z_body); przepływ z maską ~bit2 (bez znaczników).</description>\n</model>\n')
    rig = os.path.join(ZR, "rig_nadir.sdf")
    open(rig, "w").write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!-- Rig bootu b1 NADIR S1: statyczne opakowanie x500_nadir_flow, "
                         "nie lata (wzór results/KONT/s1/zrodla/rig_flow.sdf). -->\n<sdf version='1.9'>\n  <model name='probe'>\n"
                         "    <static>true</static>\n    <include merge='true'>\n      <uri>x500_nadir_flow</uri>\n    </include>\n"
                         "  </model>\n</sdf>\n")
    man = {"opis": __doc__.split("\n\n")[0], "s_m": S, "R_E_m": R_E, "W_m": W, "plyta_m": round(PLATE, 4), "z_m": Z_M,
           "slownik": "DICT_4X4_50", "visibility_flags": FLAG, "flow_visibility_mask": FLOW_MASK,
           "swiat_bazowy": {"plik": "worlds/world_kont_A3.sdf", "sha256": sw},
           "n": len(znaczniki), "n_kolizje": sum(1 for z in znaczniki if z["kolizje_z_brylami"]), "znaczniki": znaczniki}
    json.dump(man, open(os.path.join(S1, "manifest_znaczniki.json"), "w"), ensure_ascii=False, indent=1)
    pin = {"model_sdf": {"plik": os.path.relpath(mp, ROOT), "sha256": sha(mp)},
           "model_config": {"plik": os.path.relpath(cp, ROOT), "sha256": sha(cp)},
           "rig": {"plik": os.path.relpath(rig, ROOT), "sha256": sha(rig)},
           "zrodlo_modelu": {"plik": os.path.relpath(SRC_MODEL, ROOT), "sha256": sha(SRC_MODEL)},
           "swiat": {"plik": os.path.relpath(OUT_W, ROOT), "sha256": sha(OUT_W)},
           "nadir": {"montaz": "base_link origin, rpy czujnika (0, +90°, 0)", "os_optyczna": "-z_body", "w_h": [640, 480],
                     "horizontal_fov": 1.74, "f_px": round(320 / math.tan(0.87), 2), "update_hz": 15,
                     "topic": "/world/<W>/model/x500_nadir_flow_0/link/nadir_link/sensor/nadir/image",
                     "obraz": "u w prawo = -y_body, v w dół = -x_body (góra kadru = przód)"},
           "mono_cam_pin": {"plik": "PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf",
                            "sha256": sha(os.path.join(ROOT, "PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf"))}}
    json.dump(pin, open(os.path.join(S1, "pin_nadir.json"), "w"), ensure_ascii=False, indent=1)
    print("świat", sha(OUT_W)[:16], "model", sha(mp)[:16], "węzły", len(znaczniki), "kolizje",
          [(z["id"], z["E"], z["N"], z["kolizje_z_brylami"]) for z in znaczniki if z["kolizje_z_brylami"]])


if __name__ == "__main__":
    main()
