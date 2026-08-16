#!/usr/bin/env python3
"""gen_world_demo_v1.py — generator TERENU DEMA (R-M1 PROMPT_MTI_BUILD).

Buduje `worlds/world_demo_v1.sdf`: nagłówek świata IDENTYCZNY z `default.sdf` (physics ode 250 Hz,
gravity, magnetic_field, atmosphere, scene ambient/background/shadows, ground_plane collision+szary,
sun `sunUTC` — ŚWIATŁO JAK W DEFAULT), PLUS teksturowany grunt: deterministyczne pole statycznych
brył WIZUALNYCH (bez kolizji → zero kosztu fizyki, ZERO naruszenia koperty R_E/geofence; dron lata
na alt 9-10 m, bryły ≤1 m przy gruncie). Struktura przestrzenna → REALNA PARALAKSA pod ego-motion
(dominujące źródło FP MTI z inwentarza R2). Prymitywy `<box>` (znane że renderują się headless —
ENGINE-RECON: powietrzny sensor renderuje headless, kontencja GUI była konfundem).

Determinizm: seeded LCG (bez random/np — reprodukowalny SDF; habitat hashowalny w ANEKS-H).
Nazwa świata WEWNĘTRZNA = `world_demo_v1` (spójna z nazwą pliku → wszystkie topiki /world/world_demo_v1/*).
NIE zmienia geometrii koperty (R_E/geofence żyją w config osłony, nie w świecie).

DEMO-B blok B2 (PROMPT_D_BUILD_2 §2): rozszerzenie PARAMETRYCZNE — warianty aktów `--act A1|A2|A3`
dokładają KAMERĘ filmową (par. z sondy R2: 1280×720@30, always_on, statyczna) skadrowaną na centroid
akcji aktu, i zmieniają nazwę świata na `world_demo_<AKT>` (spójność topików — lekcja bugu sondy R2).
INTRUZ NIE jest pieczony w świat (frozen finding RAPORT_R1 §1: skinless <actor> segfaultuje serwer gz)
— pozostaje modelem `r02/intruder_model.sdf` spawnowanym w runtime i sterowanym przez runner per-akt (B4)
wg trajektorii f(sim_t) w spec `acts/<AKT>_spec.yaml`. Domyślne wywołanie (bez --act) generuje
world_demo_v1.sdf BAJT-w-BAJT identycznie (hash a76a38c8 ZAMROŻONY) — terrain/seed/kolejność nietknięte.
Kadr kamery per akt: FREEZE (sha256) w ANEKS_D2.md; zmiana po freeze = nowy hash + adnotacja.
"""
import math
import os
import sys

# v1.1 (2026-08-15): ZMNIEJSZONA gęstość — 359 brył (v1.0) dawało kontencję renderu gz → EKF High Gyro Bias
# → arm denied (ANEKS-H/E2). Mniej, WIĘKSZYCH brył = ta sama struktura przestrzenna/paralaksa, ~4× mniejszy
# koszt renderu → EKF stabilny. Hash re-zamrożony w ANEKS-H H.4.
SEED = 20260815
EXTENT = 44.0          # pole ±44 m
SPACING = 7.0          # siatka co 7 m (rzadziej)
JITTER = 2.0           # rozrzut pozycji ±2.0 m
FILL_P = 0.55          # prawdopodobieństwo wypełnienia komórki
CLEAR_R = 3.0          # czysty pad wokół origin (start/ląd)


class LCG:
    """Deterministyczny generator (glibc constants). Zamiast random — reprodukowalność SDF."""
    def __init__(self, seed): self.s = seed & 0x7fffffff
    def next(self):
        self.s = (1103515245 * self.s + 12345) & 0x7fffffff
        return self.s
    def uniform(self, a, b): return a + (b - a) * (self.next() / 0x7fffffff)


HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<!-- world_demo_v1 — teren DEMA (R-M1). Nagłówek == default.sdf; DODANE: teksturowany grunt (par? R2).
     Wygenerowane przez worlds/gen_world_demo_v1.py (seed={seed}). Habitat percepcyjny ZAMROŻONY (hash w ANEKS-H).
     Liczby percepcyjne MIĘDZY ŚWIATAMI SIĘ NIE PRZENOSZĄ — pomiary MTI/conf wyłącznie w tym świecie. -->
<sdf version="1.9">
  <world name="world_demo_v1">
    <physics type="ode">
      <max_step_size>0.004</max_step_size>
      <real_time_factor>1.0</real_time_factor>
      <real_time_update_rate>250</real_time_update_rate>
    </physics>
    <gravity>0 0 -9.8</gravity>
    <magnetic_field>6e-06 2.3e-05 -4.2e-05</magnetic_field>
    <atmosphere type="adiabatic"/>
    <scene>
      <grid>false</grid>
      <ambient>0.4 0.4 0.4 1</ambient>
      <background>0.7 0.7 0.7 1</background>
      <shadows>true</shadows>
    </scene>
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><plane><normal>0 0 1</normal><size>1 1</size></plane></geometry>
          <surface><friction><ode/></friction><bounce/><contact/></surface>
        </collision>
        <visual name="visual">
          <geometry><plane><normal>0 0 1</normal><size>500 500</size></plane></geometry>
          <material>
            <ambient>0.8 0.8 0.8 1</ambient>
            <diffuse>0.8 0.8 0.8 1</diffuse>
            <specular>0.8 0.8 0.8 1</specular>
          </material>
        </visual>
        <pose>0 0 0 0 -0 0</pose>
        <inertial><pose>0 0 0 0 -0 0</pose><mass>1</mass>
          <inertia><ixx>1</ixx><ixy>0</ixy><ixz>0</ixz><iyy>1</iyy><iyz>0</iyz><izz>1</izz></inertia>
        </inertial>
        <enable_wind>false</enable_wind>
      </link>
      <pose>0 0 0 0 -0 0</pose>
      <self_collide>false</self_collide>
    </model>
    <light name="sunUTC" type="directional">
      <pose>0 0 500 0 -0 0</pose>
      <cast_shadows>true</cast_shadows>
      <intensity>1</intensity>
      <direction>0.001 0.625 -0.78</direction>
      <diffuse>0.904 0.904 0.904 1</diffuse>
      <specular>0.271 0.271 0.271 1</specular>
      <attenuation><range>2000</range><linear>0</linear><constant>1</constant><quadratic>0</quadratic></attenuation>
      <spot><inner_angle>0</inner_angle><outer_angle>0</outer_angle><falloff>0</falloff></spot>
    </light>
    <spherical_coordinates>
      <surface_model>EARTH_WGS84</surface_model>
      <world_frame_orientation>ENU</world_frame_orientation>
      <latitude_deg>47.397971057728974</latitude_deg>
      <longitude_deg> 8.546163739800146</longitude_deg>
      <elevation>0</elevation>
    </spherical_coordinates>
"""

BOX_TMPL = """    <model name="tex_{i}">
      <static>true</static>
      <pose>{x:.3f} {y:.3f} {z:.3f} 0 0 {yaw:.3f}</pose>
      <link name="l">
        <visual name="v">
          <geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry>
          <material>
            <ambient>{r:.3f} {g:.3f} {b:.3f} 1</ambient>
            <diffuse>{r:.3f} {g:.3f} {b:.3f} 1</diffuse>
            <specular>0.1 0.1 0.1 1</specular>
          </material>
        </visual>
      </link>
    </model>
"""


# --- DEMO-B: kamera filmowa (par. z sondy R2 — results/demo/recon/world_demo_probe.sdf) ------------
FILM_CAM_TMPL = """    <!-- DEMO-B kamera filmowa (par. sonda R2; kadr na centroid aktu {act}, FREEZE w ANEKS_D2). -->
    <model name="film_cam">
      <static>true</static>
      <pose>{px:.3f} {py:.3f} {pz:.3f} 0 {pitch:.4f} {yaw:.4f}</pose>
      <link name="l">
        <sensor name="film" type="camera">
          <pose>0 0 0 0 0 0</pose>
          <camera>
            <horizontal_fov>1.20</horizontal_fov>
            <image><width>1280</width><height>720</height></image>
            <clip><near>0.1</near><far>3000</far></clip>
          </camera>
          <always_on>1</always_on>
          <update_rate>30</update_rate>
          <visualize>false</visualize>
        </sensor>
      </link>
    </model>
"""

# Geometria akcji per akt (ENU; źródła w acts/<AKT>_spec.yaml i RAPORT_D_B2). Centroid = punkt celowania
# kamery; cam_pos = stanowisko (standoff boczny + lekko powyżej). Pitch/yaw LICZONE (aim-at-centroid).
#   DRONE_DWELL=(0,0,10) [ALT_M=10, r01.config] · INTRUDER_RING=(7.86,0,11.5) [3D 8.0 m: √(7.86²+1.5²);
#   INTRUDER_ALT_M=11.5, koperta 5–9 m środek — config_r02] · A3 zejście ~ (13,0,4) [pkt trasy < R_route'=20.5 m].
ACT_CAM = {
    "A1": {"centroid": (3.93, 0.0, 10.75), "cam_pos": (10.0, -14.0, 8.0)},   # midpoint dron↔intruz
    "A2": {"centroid": (3.93, 0.0, 10.75), "cam_pos": (12.0, -16.0, 8.0)},   # jw. + zapas na wyjście/powrót
    "A3": {"centroid": (13.0, 0.0, 4.0),   "cam_pos": (14.0, -18.0, 7.0)},   # zejście velocity-descent
}


def _cam_pose(cam_pos, centroid):
    """Aim-at-centroid → (pitch, yaw) w konwencji SDF ENU. roll=0."""
    dx = centroid[0] - cam_pos[0]; dy = centroid[1] - cam_pos[1]; dz = centroid[2] - cam_pos[2]
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(dz, math.hypot(dx, dy))
    return pitch, yaw


def build_boxes():
    """Deterministyczne pole brył (identyczne dla wszystkich światów — terrain frozen)."""
    rng = LCG(SEED)
    boxes = []
    i = 0
    n = int(EXTENT / SPACING)
    for gx in range(-n, n + 1):
        for gy in range(-n, n + 1):
            if rng.uniform(0, 1) > FILL_P:
                continue
            x = gx * SPACING + rng.uniform(-JITTER, JITTER)
            y = gy * SPACING + rng.uniform(-JITTER, JITTER)
            if (x * x + y * y) ** 0.5 < CLEAR_R:      # czysty pad start/ląd
                continue
            sx = rng.uniform(1.5, 3.8); sy = rng.uniform(1.5, 3.8); sz = rng.uniform(0.1, 1.2)
            z = sz / 2.0                              # spoczywa na gruncie
            yaw = rng.uniform(0, 3.14159)
            shade = rng.uniform(0.20, 0.78)
            # kilka „tinted" dla wyższej częstotliwości przestrzennej kontrastu
            tint = rng.uniform(0, 1)
            r, g, b = shade, shade, shade
            if tint > 0.85: r, g, b = shade * 1.15, shade * 0.85, shade * 0.7   # ciepły
            elif tint < 0.15: r, g, b = shade * 0.7, shade * 0.9, shade * 1.15  # zimny
            boxes.append(BOX_TMPL.format(i=i, x=x, y=y, z=z, yaw=yaw, sx=sx, sy=sy, sz=sz,
                                         r=min(r, 1), g=min(g, 1), b=min(b, 1)))
            i += 1
    return boxes


def build_world(act=None):
    """act=None → world_demo_v1 (BAJT-identyczny, terrain-only). act∈{A1,A2,A3} → +kamera, nazwa world_demo_<act>."""
    boxes = build_boxes()
    parts = []
    if act is None:
        world_name = "world_demo_v1"
        parts.append(HEADER.format(seed=SEED))
    else:
        world_name = f"world_demo_{act}"
        parts.append(HEADER.format(seed=SEED).replace("world_demo_v1", world_name))
    parts.append(f"    <!-- {len(boxes)} statycznych brył wizualnych (tekstura przestrzenna, par? R2) -->\n")
    parts.extend(boxes)
    if act is not None:                               # kamera PRZED </world> (intruz spawnowany w runtime, B4)
        pitch, yaw = _cam_pose(ACT_CAM[act]["cam_pos"], ACT_CAM[act]["centroid"])
        px, py, pz = ACT_CAM[act]["cam_pos"]
        parts.append(FILM_CAM_TMPL.format(act=act, px=px, py=py, pz=pz, pitch=pitch, yaw=yaw))
    parts.append("  </world>\n</sdf>\n")
    return "".join(parts), world_name, len(boxes)


def main():
    act = None
    if len(sys.argv) > 2 and sys.argv[1] == "--act":
        act = sys.argv[2]
        assert act in ACT_CAM, f"nieznany akt {act} (dozwolone: {list(ACT_CAM)})"
    body, world_name, nboxes = build_world(act)
    fname = "world_demo_v1.sdf" if act is None else f"world_demo_{act}.sdf"
    out = os.path.join(os.path.dirname(__file__), fname)
    with open(out, "w") as f:
        f.write(body)
    print(f"[gen] {nboxes} brył → {out} (world={world_name}, seed={SEED}, act={act})")


if __name__ == "__main__":
    main()
