#!/usr/bin/env python3
"""results/NADIR/tools/nadir_n1_build.py — ANEKS_NADIR-1: model v2 x500_nadir2_flow + pin_nadir_v2 + skrypty bootu v2.
Model v2 = results/NADIR/s1/zrodla/x500_nadir_flow/model.sdf (v1, nietknięty) z różnicami WYŁĄCZNIE w bloku nadir_link:
nazwa modelu, montaż (0, 0, −0.215) względem base_link (pod płozy, §2.3; maska v2 0.0% stożka — n1/maska_v2.json),
update_rate nadir 5 Hz (§2.2, n1/ab_kadencja.json wybór 5). Świat v2 = worlds/world_nadir2_A3.sdf (nadir_n1_manifest.py).
Skrypty: nadir_s1v2_boot.sh / nadir_s1v2_launch.sh = kopie v1 z zamianą nazw modelu, świata i źródła modelu (asercje)."""
import hashlib, json, os
ROOT = "/home/olga/projects/liquidpatrol"
Z = os.path.join(ROOT, "results/NADIR/s1/zrodla")
T = os.path.join(ROOT, "results/NADIR/tools")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
m = open(os.path.join(Z, "x500_nadir_flow/model.sdf"), encoding="utf8").read()
i = m.index('<link name="nadir_link">')
head, tail = m[:i], m[i:]
reps = [('<pose relative_to="base_link">0 0 0 0 0 0</pose>', '<pose relative_to="base_link">0 0 -0.215 0 0 0</pose>'),
        ("<update_rate>15</update_rate>", "<update_rate>5</update_rate>")]
for a, b in reps:
    assert tail.count(a) == 1, a
    tail = tail.replace(a, b)
assert head.count("<model name='x500_nadir_flow'>") == 1
head = head.replace("<model name='x500_nadir_flow'>", "<model name='x500_nadir2_flow'>")
head = head.replace("<!-- NADIR: druga kamera, oś −z_body (PRE_NADIR §2.2) -->", "<!-- NADIR v2: druga kamera, oś −z_body, montaż pod płozy −0.215 m, 5 Hz (ANEKS_NADIR-1 §2.2–2.3) -->")
os.makedirs(os.path.join(Z, "x500_nadir2_flow"), exist_ok=True)
mp = os.path.join(Z, "x500_nadir2_flow/model.sdf"); open(mp, "w", encoding="utf8").write(head + tail)
cp = os.path.join(Z, "x500_nadir2_flow/model.config")
open(cp, "w").write(open(os.path.join(Z, "x500_nadir_flow/model.config")).read().replace("x500_nadir_flow", "x500_nadir2_flow")
                    .replace("kamera nadir ", "kamera nadir v2 pod płozami 5 Hz "))
def kopia(src, dst, head_c, reps):
    t = open(os.path.join(T, src)).read()
    for a, b, n in reps:
        assert t.count(a) == n, (src, a, t.count(a)); t = t.replace(a, b)
    l = t.split("\n"); t = "\n".join([l[0], head_c] + l[1:])
    open(os.path.join(T, dst), "w").write(t); os.chmod(os.path.join(T, dst), 0o755)
kopia("nadir_s1_launch.sh", "nadir_s1v2_launch.sh",
      "# results/NADIR/tools/nadir_s1v2_launch.sh — KOPIA nadir_s1_launch.sh (nietknięty), ANEKS_NADIR-1: model x500_nadir2_flow, świat world_nadir2_A3.",
      [('WORLD="${1:-${WORLD:-world_nadir_A3}}"', 'WORLD="${1:-${WORLD:-world_nadir2_A3}}"', 1),
       ("MODEL=gz_x500_nadir_flow PX4_SYS_AUTOSTART=4010 PX4_SIM_MODEL=gz_x500_nadir_flow", "MODEL=gz_x500_nadir2_flow PX4_SYS_AUTOSTART=4010 PX4_SIM_MODEL=gz_x500_nadir2_flow", 1), ("B1_MODEL=x500_nadir_flow_0", "B1_MODEL=x500_nadir2_flow_0", 6),
       ("zrodla/x500_nadir_flow\"", "zrodla/x500_nadir2_flow\"", 1), ("models/x500_nadir_flow\"", "models/x500_nadir2_flow\"", 1),
       ("x500_nadir_flow/$f różny", "x500_nadir2_flow/$f różny", 1)])
kopia("nadir_s1_boot.sh", "nadir_s1v2_boot.sh",
      "# results/NADIR/tools/nadir_s1v2_boot.sh — KOPIA nadir_s1_boot.sh (nietknięty), ANEKS_NADIR-1: świat world_nadir2_A3, model x500_nadir2_flow, launcher v2.",
      [("WORLD=world_nadir_A3", "WORLD=world_nadir2_A3", 1), ("model/x500_nadir_flow_0/", "model/x500_nadir2_flow_0/", 1),
       ('bash "$ROOT/results/NADIR/tools/nadir_s1_launch.sh"', 'bash "$ROOT/results/NADIR/tools/nadir_s1v2_launch.sh"', 1), ("--model x500_nadir_flow_0", "--model x500_nadir2_flow_0", 1)])
w = os.path.join(ROOT, "worlds/world_nadir2_A3.sdf")
pin = {"wersja": 2, "aneks": "ANEKS_NADIR-1 §2.2–§2.4",
       "model_sdf": {"plik": os.path.relpath(mp, ROOT), "sha256": sha(mp)}, "model_config": {"plik": os.path.relpath(cp, ROOT), "sha256": sha(cp)},
       "swiat": {"plik": os.path.relpath(w, ROOT), "sha256": sha(w)},
       "manifest": {"plik": "results/NADIR/s1/n1/manifest_znaczniki_v2.json", "sha256": sha(os.path.join(ROOT, "results/NADIR/s1/n1/manifest_znaczniki_v2.json"))},
       "nadir": {"montaz": "base_link (0, 0, -0.215) m, rpy czujnika (0, +90°, 0)", "os_optyczna": "-z_body", "w_h": [640, 480], "horizontal_fov": 1.74,
                 "f_px": 269.47, "update_hz": 5, "topic": "/world/<W>/model/x500_nadir2_flow_0/link/nadir_link/sensor/nadir/image",
                 "maska_stozek": 0.0, "opencv": "4.6.0 systemowe (bez .b0deps)"},
       "mono_cam_pin": "3354ae1e8bcb99cec143317fce607e460b13a451bc59f1da98e50e5ddd0ee64c"}
json.dump(pin, open(os.path.join(ROOT, "results/NADIR/s1/n1/pin_nadir_v2.json"), "w"), ensure_ascii=False, indent=1)
print(pin["model_sdf"]["sha256"][:16], pin["swiat"]["sha256"][:16])
