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
"""
import os

SEED = 20260815
EXTENT = 44.0          # pole ±44 m
SPACING = 4.0          # siatka co 4 m
JITTER = 1.5           # rozrzut pozycji ±1.5 m
FILL_P = 0.70          # prawdopodobieństwo wypełnienia komórki
CLEAR_R = 2.5          # czysty pad wokół origin (start/ląd)


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


def main():
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
            sx = rng.uniform(0.8, 2.4); sy = rng.uniform(0.8, 2.4); sz = rng.uniform(0.05, 1.0)
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
    out = os.path.join(os.path.dirname(__file__), "world_demo_v1.sdf")
    with open(out, "w") as f:
        f.write(HEADER.format(seed=SEED))
        f.write(f"    <!-- {len(boxes)} statycznych brył wizualnych (tekstura przestrzenna, par? R2) -->\n")
        f.writelines(boxes)
        f.write("  </world>\n</sdf>\n")
    print(f"[gen] {len(boxes)} brył → {out} (seed={SEED}, extent=±{EXTENT}, spacing={SPACING})")


if __name__ == "__main__":
    main()
