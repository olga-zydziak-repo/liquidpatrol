#!/usr/bin/env python3
"""Atrapa PX4 do próby na sucho (ANEKS_KONT-1d §2.3): zapisuje argumenty i środowisko, odczytuje stan gz tak jak px4-rc.gzsim, drukuje wiersz rcS, na który czeka stos, i udaje proces. Nazwa pliku px4, żeby inwentarz kont_inw.py ją widział."""
import json
import os
import re
import subprocess
import sys
import time

t = time.time()
lst = subprocess.run(["gz", "topic", "-l"], capture_output=True, text=True).stdout
m = re.search(r"^/world/(.*)/clock", lst, re.M)
world = m.group(1) if m else None
c = subprocess.run(["gz", "topic", "-e", "-n", "1", "-t", f"/world/{world}/clock"], capture_output=True, text=True, timeout=10).stdout
sc = subprocess.run(["gz", "service", "-i", "--service", f"/world/{world}/scene/info"], capture_output=True, text=True)
json.dump({"wall_start": t, "argv": sys.argv, "cwd": os.getcwd(), "gz_world_jak_rcS": world, "clock_przy_starcie": c, "scene_info_ok": "Service providers" in sc.stdout + sc.stderr,
           "env": {k: os.environ.get(k) for k in ("PX4_SIM_MODEL", "PX4_GZ_WORLD", "PX4_SYS_AUTOSTART", "HEADLESS", "GZ_IP", "GZ_SIM_RESOURCE_PATH", "GZ_SIM_SYSTEM_PLUGIN_PATH", "GZ_SIM_SERVER_CONFIG_PATH", "PX4_GZ_WORLDS")}},
          open(os.environ["DRY_OUT"] + "/px4_stub.json", "w"), indent=1)
print("INFO  [init] Gazebo world is ready", flush=True)
time.sleep(600)
