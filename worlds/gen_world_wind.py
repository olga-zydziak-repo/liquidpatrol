#!/usr/bin/env python3
"""worlds/gen_world_wind.py — generator świata SONDY WIATRU (noga W, RECON_W §R2).

Baza: worlds/world_demo_v1.sdf (znany-dobry teren+fizyka, hash pinowany w RECON_W).
DODAJE względem bazy DOKŁADNIE dwie rzeczy:
  1) <plugin filename="gz-sim-wind-effects-system" name="gz::sim::systems::WindEffects">
     (server.config PX4 NIE ładuje WindEffects — musi być w SDF świata; R1 §2/§3).
  2) <wind><linear_velocity>Vx Vy Vz</linear_velocity></wind>  (globalny wektor, world-frame ENU).
Nazwa <world> = basename pliku (PX4 buduje topiki /world/<name>/... z nazwy SDF, nie z pliku).
Ground-plane <enable_wind> pozostaje false (nie chcemy wiatru na gruncie). Dron dostaje wiatr przez
kopię modelu worlds/wind_models/x500_base (enable_wind=true) resolwowaną prepend-em GZ_SIM_RESOURCE_PATH.

Użycie:  python3 worlds/gen_world_wind.py <NAME> <Vx> <Vy> <Vz>
Wypisuje ścieżkę + sha256 wygenerowanego świata.
"""
import sys, os, re, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "worlds", "world_demo_v1.sdf")

# PEŁNY stack systemów = server.config verbatim (gz_bridge/server.config:3-17). MUSI być w świecie,
# bo gdy SDF świata deklaruje JAKIKOLWIEK <plugin>, gz IGNORUJE GZ_SIM_SERVER_CONFIG_PATH — więc
# bez tej listy zniknęłyby Physics/SceneBroadcaster/Sensors (→ brak scene/info → PX4 stall).
SERVER_SYSTEMS = [
    ('gz-sim-physics-system', 'gz::sim::systems::Physics', None),
    ('gz-sim-user-commands-system', 'gz::sim::systems::UserCommands', None),
    ('gz-sim-scene-broadcaster-system', 'gz::sim::systems::SceneBroadcaster', None),
    ('gz-sim-contact-system', 'gz::sim::systems::Contact', None),
    ('gz-sim-imu-system', 'gz::sim::systems::Imu', None),
    ('gz-sim-air-pressure-system', 'gz::sim::systems::AirPressure', None),
    ('gz-sim-air-speed-system', 'gz::sim::systems::AirSpeed', None),
    ('gz-sim-apply-link-wrench-system', 'gz::sim::systems::ApplyLinkWrench', None),
    ('gz-sim-navsat-system', 'gz::sim::systems::NavSat', None),
    ('gz-sim-magnetometer-system', 'gz::sim::systems::Magnetometer', None),
    ('gz-sim-sensors-system', 'gz::sim::systems::Sensors', '<render_engine>ogre2</render_engine>'),
    ('libOpticalFlowSystem.so', 'custom::OpticalFlowSystem', None),
    ('libGstCameraSystem.so', 'custom::GstCameraSystem', None),
]
WIND_SYS = ('gz-sim-wind-effects-system', 'gz::sim::systems::WindEffects')


def _plugins_block():
    lines = []
    for fn, nm, child in SERVER_SYSTEMS:
        if child:
            lines.append(f'    <plugin filename="{fn}" name="{nm}">{child}</plugin>')
        else:
            lines.append(f'    <plugin filename="{fn}" name="{nm}"/>')
    # WindEffects na końcu
    lines.append(f'    <plugin filename="{WIND_SYS[0]}" name="{WIND_SYS[1]}">')
    lines.append('      <force_approximation_scaling_factor>1.0</force_approximation_scaling_factor>')
    lines.append('    </plugin>')
    return "\n".join(lines)


def build(name, vx, vy, vz):
    src = open(BASE).read()
    base_sha = hashlib.sha256(src.encode()).hexdigest()
    m = re.search(r'<world name="([^"]+)">', src)
    if not m:
        raise SystemExit("nie znaleziono <world name=...> w bazie")
    inject = (
        f'<world name="{name}">\n'
        f'    <!-- SONDA WIATRU (noga W). Baza world_demo_v1 sha256={base_sha}. '
        f'Wygenerowane gen_world_wind.py. Pełny stack systemów (server.config) + WindEffects. -->\n'
        f'{_plugins_block()}\n'
        f'    <wind>\n'
        f'      <linear_velocity>{vx} {vy} {vz}</linear_velocity>\n'
        f'    </wind>'
    )
    out = src.replace(m.group(0), inject, 1)
    dst = os.path.join(ROOT, "worlds", f"{name}.sdf")
    open(dst, "w").write(out)
    sha = hashlib.sha256(out.encode()).hexdigest()
    return dst, sha, base_sha


if __name__ == "__main__":
    name, vx, vy, vz = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    dst, sha, base_sha = build(name, vx, vy, vz)
    print(f"WROTE {dst}\n  sha256={sha}\n  base(world_demo_v1) sha256={base_sha}\n  wind=({vx},{vy},{vz}) m/s (ENU)")
