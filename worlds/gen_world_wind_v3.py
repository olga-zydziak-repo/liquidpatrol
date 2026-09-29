#!/usr/bin/env python3
"""worlds/gen_world_wind_v3.py — światy DEMO_V3 (PROMPT_DEMO_V3 §2): estetyka v3.1 + wiatr + kamera filmowa.

Baza: worlds/world_demo_v3_1.sdf (uplift U2R/U2R-2: skybox/trawa/skyline, cast_shadows=false na
dekoracjach — bramka świata U2R PASS z zapasem). Baza NIE deklaruje żadnego <plugin> (jedzie na
server.config), więc obowiązuje pułapka R1.8: dodanie WindEffects WYMUSZA pełną listę 13 systemów
server.config verbatim (identyczna z gen_world_wind.py — inaczej brak SceneBroadcaster → PX4 stall).

DODAJE względem bazy DOKŁADNIE trzy rzeczy:
  1) pełny stack 13 systemów + WindEffects (blok z gen_world_wind.py, źródło prawdy tamże);
  2) <wind><linear_velocity>Vx Vy Vz</linear_velocity></wind> (ENU, world-frame);
  3) model film_cam (szablon FILM_CAM_TMPL z gen_world_demo_v1, sensor "film" 1280x720@30,
     hfov 1.20) w pozie SZEROKIEJ na strefę orbit ławki W (home (0,0), intruz start r=15,
     dron r_max<=26, z do ~20 — akt 3 pełznie pod V_E=20; kadr musi mieścić pion).
Nazwa <world> = basename pliku (topiki gz z nazwy SDF). Dron dostaje wiatr przez kopię
wind_models/x500_base (enable_wind) prepend-em GZ_SIM_RESOURCE_PATH — jak w nodze W.
Światy world_wind_s* i generatory v1/v2/v3/v3_1/wind NIETKNIĘTE (nowy plik, nowe wyjścia).

Użycie:  python3 worlds/gen_world_wind_v3.py <NAME> <Vx> <Vy> <Vz>
         (np. world_wind_v3_s0 0 0 0 · world_wind_v3_s1p5 1.5 0 0 · world_wind_v3_s3 3 0 0)
Wypisuje ścieżkę + sha256.
"""
import sys, os, re, math, hashlib

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
import gen_world_wind as GW          # źródło prawdy: SERVER_SYSTEMS + WindEffects (R1.8)
import gen_world_demo_v1 as V1       # źródło prawdy: FILM_CAM_TMPL + _cam_pose (aim-at-centroid)

BASE = os.path.join(_HERE, "world_demo_v3_1.sdf")

# Kadr DEMO_V3: kamera statyczna PER ŚWIAT, pod kopertę xy epizodu aktu (zmierzona z trace:
# c10_s02 x[-20,23.5] y[-16.4,7] · c11_s01(L1p5) x[-15.8,23.3] y[-20.4,9.3] ·
# c11_s02(L3) x[-16.8,8.1] y[-1.7,17] z<=19.8). s3 najciaśniej (akt sejwu — dron największy
# w kadrze, pion do V_E w kadrze); s0/s1p5 szeroko z podwyższonego stanowiska (LOS ponad dekorem).
CAMS = {
    "world_wind_v3_s0":   {"pos": (2.0, -36.0, 20.0), "aim": (2.0, -3.0, 9.0)},
    "world_wind_v3_s1p5": {"pos": (4.0, -34.0, 20.0), "aim": (4.0, -2.0, 9.0)},
    "world_wind_v3_s3":   {"pos": (-4.0, -24.0, 14.0), "aim": (-5.0, 7.0, 10.0)},
}


def build(name, vx, vy, vz):
    src = open(BASE).read()
    base_sha = hashlib.sha256(src.encode()).hexdigest()
    m = re.search(r'<world name="([^"]+)">', src)
    if not m:
        raise SystemExit("nie znaleziono <world name=...> w bazie v3_1")
    inject = (
        f'<world name="{name}">\n'
        f'    <!-- DEMO_V3 (PROMPT_DEMO_V3 §2). Baza world_demo_v3_1 sha256={base_sha}. '
        f'Wygenerowane gen_world_wind_v3.py: pełny stack systemów (server.config, R1.8) + WindEffects '
        f'+ wind=({vx},{vy},{vz}) ENU + film_cam. -->\n'
        f'{GW._plugins_block()}\n'
        f'    <wind>\n'
        f'      <linear_velocity>{vx} {vy} {vz}</linear_velocity>\n'
        f'    </wind>'
    )
    out = src.replace(m.group(0), inject, 1)
    # _cam_pose (V1) zwraca pitch=atan2(dz,dh); w konwencji SDF (Ry, +pitch = nos w dół) kamera
    # POWYŻEJ celu (dz<0) wymaga pitch>0 — stąd negacja (suchy preview: kadr zadarty przy znaku V1;
    # tam dz było małe/dodatnie i szeroki fov maskował znak).
    cam_cfg = CAMS[name]
    pitch, yaw = V1._cam_pose(cam_cfg["pos"], cam_cfg["aim"])
    pitch = -pitch
    cam = V1.FILM_CAM_TMPL.format(act="DEMO_V3", px=cam_cfg["pos"][0], py=cam_cfg["pos"][1], pz=cam_cfg["pos"][2],
                                  pitch=pitch, yaw=yaw)
    # wstrzyknięcie modelu kamery przed zamknięciem świata
    out = out.replace("  </world>", cam + "  </world>", 1)
    if out.count('<sensor name="film"') != 1:
        raise SystemExit("film_cam nie wstrzyknięty dokładnie raz")
    dst = os.path.join(_HERE, f"{name}.sdf")
    open(dst, "w").write(out)
    sha = hashlib.sha256(out.encode()).hexdigest()
    return dst, sha, base_sha


if __name__ == "__main__":
    name, vx, vy, vz = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    dst, sha, base_sha = build(name, vx, vy, vz)
    print(f"WROTE {dst}\n  sha256={sha}\n  base(world_demo_v3_1) sha256={base_sha}\n  wind=({vx},{vy},{vz}) ENU")
