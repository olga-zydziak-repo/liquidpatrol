#!/usr/bin/env python3
"""gen_world.py — generator świata do ENGINE-RECON (diagnostyka renderu, NIE budowa percepcji).

Jedna KAMERA na świat (izolacja „jedna zmienna"). Scena/sun/ground_plane skopiowane z PX4 default.sdf
(habitat renderujący). Intruz DEAD-AHEAD kamery (ten sam z/wysokość co kamera, +X o INTR_RANGE) → projekcja
w CENTRUM obrazu, odporna na znaki konwencji. Kopia as-run zapisywana przez runner (prowieniencja §6).

Env:
  CAM_KIND = drone_high | standalone   (drone_high: attached-high = x500_mono_cam statycznie na CAM_Z;
                                        standalone: unattached camera-sensor na CAM_Z — ground-low lub tower-high)
  CAM_Z    = wysokość kamery [m] (gz world, z-up)
  INTR_KIND= mesh | box                (mesh = x500_base NXP-HGD-CF.dae jak §3f/C1; box = prymityw 0.6 m)
  INTR_RANGE = odległość dead-ahead [m] (domyślnie 7)
  OUT      = ścieżka world.sdf
Kamera: imager, h_fov 1.74, 640×480, near0.1/far3000 (identyczna z mono_cam PX4).
"""
import os

CAM_KIND = os.environ.get("CAM_KIND", "standalone")
CAM_Z = float(os.environ.get("CAM_Z", "9.0"))
INTR_KIND = os.environ.get("INTR_KIND", "mesh")
INTR_RANGE = float(os.environ.get("INTR_RANGE", "7.0"))
OUT = os.environ.get("OUT", "world.sdf")

# intruz dead-ahead: kamera patrzy +X (yaw=0), ten sam z → cel w centrum kadru
INTR_X = round(INTR_RANGE, 4)
INTR_Y = 0.0
INTR_Z = round(CAM_Z, 4)

SCENE = """
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors"><render_engine>ogre2</render_engine></plugin>
    <physics type="ode"><max_step_size>0.004</max_step_size><real_time_factor>1.0</real_time_factor><real_time_update_rate>250</real_time_update_rate></physics>
    <gravity>0 0 -9.8</gravity>
    <scene><grid>false</grid><ambient>0.4 0.4 0.4 1</ambient><background>0.7 0.7 0.7 1</background><shadows>true</shadows></scene>
    <model name="ground_plane"><static>true</static><link name="link">
      <collision name="collision"><geometry><plane><normal>0 0 1</normal><size>1 1</size></plane></geometry></collision>
      <visual name="visual"><geometry><plane><normal>0 0 1</normal><size>500 500</size></plane></geometry>
        <material><ambient>0.8 0.8 0.8 1</ambient><diffuse>0.8 0.8 0.8 1</diffuse><specular>0.8 0.8 0.8 1</specular></material></visual>
      <pose>0 0 0 0 0 0</pose></link><pose>0 0 0 0 0 0</pose></model>
    <light name="sunUTC" type="directional"><pose>0 0 500 0 0 0</pose><cast_shadows>true</cast_shadows><intensity>1</intensity>
      <direction>0.001 0.625 -0.78</direction><diffuse>0.904 0.904 0.904 1</diffuse><specular>0.271 0.271 0.271 1</specular>
      <attenuation><range>2000</range><linear>0</linear><constant>1</constant><quadratic>0</quadratic></attenuation>
      <spot><inner_angle>0</inner_angle><outer_angle>0</outer_angle><falloff>0</falloff></spot></light>
"""

IMAGER = """
        <sensor name="imager" type="camera"><pose>0 0 0 0 0 0</pose>
          <camera><horizontal_fov>1.74</horizontal_fov><image><width>640</width><height>480</height></image>
            <clip><near>0.1</near><far>3000</far></clip></camera>
          <always_on>1</always_on><update_rate>15</update_rate><visualize>false</visualize></sensor>
"""

if INTR_KIND == "mesh":
    # x500_base mesh (jak §3f/C1) — wymaga GZ_SIM_RESOURCE_PATH → PX4 .../gz/models
    intr_vis = (
        '<visual name="body"><pose>0 0 .025 0 0 3.141592654</pose>'
        '<geometry><mesh><scale>1 1 1</scale><uri>model://x500_base/meshes/NXP-HGD-CF.dae</uri></mesh></geometry></visual>'
    )
else:
    intr_vis = (
        '<visual name="body"><geometry><box><size>0.6 0.6 0.2</size></box></geometry>'
        '<material><ambient>0.05 0.05 0.05 1</ambient><diffuse>0.05 0.05 0.05 1</diffuse></material></visual>'
    )

INTRUDER = f"""
    <model name="intruder"><static>true</static><pose>{INTR_X} {INTR_Y} {INTR_Z} 0 0 0</pose>
      <link name="link">{intr_vis}</link></model>
"""

if CAM_KIND == "drone_high":
    # attached-high: x500_mono_cam (kamera dziecko base_link) statycznie na CAM_Z. Kamera forward +X.
    CAM = f"""
    <model name="aerial_probe"><static>true</static><pose>0 0 {CAM_Z} 0 0 0</pose>
      <include merge="true"><uri>model://x500_mono_cam</uri></include></model>
"""
else:
    # standalone (unattached): sensor-kamera bez nosiciela, na CAM_Z, patrzy +X.
    CAM = f"""
    <model name="probe_cam"><static>true</static><pose>0 0 {CAM_Z} 0 0 0</pose>
      <link name="camera_link"><pose>0 0 0 0 0 0</pose>
        <visual name="housing"><geometry><box><size>0.05 0.05 0.05</size></box></geometry></visual>
        {IMAGER}</link></model>
"""

WORLD = f"""<?xml version="1.0" encoding="UTF-8"?>
<sdf version="1.9">
  <world name="recon">
{SCENE}{INTRUDER}{CAM}
  </world>
</sdf>
"""

with open(OUT, "w") as f:
    f.write(WORLD)
print(f"[gen_world] {OUT} CAM_KIND={CAM_KIND} CAM_Z={CAM_Z} INTR={INTR_KIND}@({INTR_X},{INTR_Y},{INTR_Z}) range={INTR_RANGE}")
