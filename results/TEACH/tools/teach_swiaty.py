#!/usr/bin/env python3
"""results/TEACH/tools/teach_swiaty.py — generator światów i modelu drona nogi TEACH (PRE_TEACH §4 „Świat”, §5.5; PROMPT_TEACH_S1 §1.5;
0 bootów — poprawność sprawdza S2).

Światy worlds/world_teach_{S,M,J}.sdf = kopia worlds/world_nadir2_A3.sdf (nietknięty, sha 7f2bbe13…) ze zmianami wyłącznie:
  - nazwa świata world_teach_<łata> (tematy gz /world/<nazwa>/…) i komentarz nagłówka;
  - przed </world> model „teren_teach”: statyczny, tylko wizual (bez kolizji — kontakt z gruntem bez zmian), płaszczyzna 100 × 100 m,
    środek (0, 0), wysokość 0.005 m (nad ground_plane, pod znacznikami z 0.03), visibility_flags 8 (bit 3), bez cienia własnego,
    tekstura łaty results/TEACH_RECON/dane/<łata>_2024-04-27.png (2000 × 2000 px, 0.05 m/px, N do góry — jak okno reconu), materiał
    jak dekal KONT (pbr metal, albedo_map ścieżką bezwzględną jak w świecie źródłowym).
Model results/TEACH/s1/zrodla/x500_teach_flow/ (launcher kopiuje do PX4-Autopilot/Tools/simulation/gz/models/, wzór
x500_nadir2_flow) = kopia przypiętego results/NADIR/s1/zrodla/x500_nadir2_flow (nietknięty, sha 1fa0c57d…) z czterema maskami:
  - kamera w dół „nadir”: <visibility_mask>8</visibility_mask> (widzi teren i obiekty z flagami domyślnymi; nie widzi znaczników
    — flagi 4 — ani dekalu KONT — flagi 2);
  - kamera misji „imager”: 4294967293 → 4294967285 (~(bit 1 | bit 3));
  - kamera przepływu „flow_camera”: 4294967291 → 4294967283 (~(bit 2 | bit 3));
  - lidar gpu_lidar: <visibility_mask>4294967287</visibility_mask> w <ray> (~bit 3; warstwa 5 mm nie zmienia odległości);
  oraz nazwa modelu x500_teach_flow. Modele innych dronów i intruza bez zmian („TEREN-I-OBIEKTY”, PRE_TEACH §3.5).
Asercje: każda zamiana trafia dokładnie raz; pliki źródłowe bez zmiany bajtu (sumy przed i po). Wyjście: sumy w
results/TEACH/s1/swiaty.json.
"""
import hashlib
import json
import os

ROOT = "/home/olga/projects/liquidpatrol"
SWIAT_SRC = os.path.join(ROOT, "worlds/world_nadir2_A3.sdf")
SWIAT_SHA = "7f2bbe1360819a8b64ee462ad9c1852e6525b02fa197460953725ca44aeb81d8"
MODEL_SRC = os.path.join(ROOT, "results/NADIR/s1/zrodla/x500_nadir2_flow")
MODEL_SHA = "1fa0c57d3863081b51a43f9cb54e6e6a3987be1fe7ab113f51b2fa992cd6a093"
MODEL_DST = os.path.join(ROOT, "results/TEACH/s1/zrodla/x500_teach_flow")
DANE = os.path.join(ROOT, "results/TEACH_RECON/dane")
LATY = ("S", "M", "J")
FLAGA_TERENU, Z_TERENU, BOK = 8, 0.005, 100.0
MASKI = {"nadir": 8, "imager": 4294967285, "flow_camera": 4294967283, "lidar": 4294967287}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def zamien(s, a, b):
    assert s.count(a) == 1, (s.count(a), a[:80])
    return s.replace(a, b)


def swiat(lata):
    s = open(SWIAT_SRC, encoding="utf-8").read()
    s = zamien(s, '<world name="world_nadir2_A3">', f'<world name="world_teach_{lata}">')
    s = zamien(s, "<sdf version=\"1.9\">", f"<!-- TEACH (PRE_TEACH §4, §5.5): kopia world_nadir2_A3.sdf (sha {SWIAT_SHA[:8]}…) + warstwa terenu "
                                            f"łaty {lata} (flagi {FLAGA_TERENU}, z {Z_TERENU} m); results/TEACH/tools/teach_swiaty.py -->\n"
                                            "<sdf version=\"1.9\">")
    tex = os.path.join(DANE, f"{lata}_2024-04-27.png")
    assert os.path.exists(tex), tex
    model = f"""    <!-- TEACH: warstwa terenu łaty {lata} (ortofotomapa 2024-04-27, 0.05 m/px), widoczna tylko dla masek z bitem 3 (kamera w dół). -->
    <model name="teren_teach">
      <static>true</static>
      <pose>0 0 {Z_TERENU} 0 0 0</pose>
      <link name="l">
        <visual name="v"><cast_shadows>false</cast_shadows>
          <visibility_flags>{FLAGA_TERENU}</visibility_flags>
          <geometry><plane><normal>0 0 1</normal><size>{BOK:g} {BOK:g}</size></plane></geometry>
          <material><ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse><specular>0 0 0 1</specular>
            <pbr><metal><albedo_map>{tex}</albedo_map><metalness>0</metalness><roughness>1</roughness></metal></pbr>
          </material>
        </visual>
      </link>
    </model>
  </world>"""
    s = zamien(s, "  </world>", model)
    p = os.path.join(ROOT, f"worlds/world_teach_{lata}.sdf")
    open(p, "w", encoding="utf-8").write(s)
    return p, tex


def model():
    s = open(os.path.join(MODEL_SRC, "model.sdf"), encoding="utf-8").read()
    s = zamien(s, "<model name='x500_nadir2_flow'>", "<model name='x500_teach_flow'>")
    s = zamien(s, "<visibility_mask>4294967293</visibility_mask>", f"<visibility_mask>{MASKI['imager']}</visibility_mask>")
    s = zamien(s, "<visibility_mask>4294967291</visibility_mask>", f"<visibility_mask>{MASKI['flow_camera']}</visibility_mask>")
    s = zamien(s, """            <resolution>0.01</resolution>
          </range>
        </ray>""", f"""            <resolution>0.01</resolution>
          </range>
          <visibility_mask>{MASKI['lidar']}</visibility_mask>
        </ray>""")
    s = zamien(s, """            <far>100</far>
          </clip>
        </camera>""", f"""            <far>100</far>
          </clip>
          <visibility_mask>{MASKI['nadir']}</visibility_mask>
        </camera>""")
    s = zamien(s, "    <!-- NADIR v2: druga kamera", "    <!-- TEACH: maski kamer i lidaru z bitem 3 (warstwa terenu) — results/TEACH/tools/teach_swiaty.py -->\n"
                                                    "    <!-- NADIR v2: druga kamera")
    c = open(os.path.join(MODEL_SRC, "model.config"), encoding="utf-8").read()
    c = zamien(c, "<name>x500_nadir2_flow</name>", "<name>x500_teach_flow</name>")
    c = zamien(c, "<description>", "<description>TEACH: kopia x500_nadir2_flow z maskami bitu 3 (kamera w dół 8, misja 4294967285, "
                                   "przepływ 4294967283, lidar 4294967287). ")
    os.makedirs(MODEL_DST, exist_ok=True)
    open(os.path.join(MODEL_DST, "model.sdf"), "w", encoding="utf-8").write(s)
    open(os.path.join(MODEL_DST, "model.config"), "w", encoding="utf-8").write(c)
    return os.path.join(MODEL_DST, "model.sdf"), os.path.join(MODEL_DST, "model.config")


def main():
    przed = {p: sha(p) for p in (SWIAT_SRC, os.path.join(MODEL_SRC, "model.sdf"), os.path.join(MODEL_SRC, "model.config"))}
    assert przed[SWIAT_SRC] == SWIAT_SHA and przed[os.path.join(MODEL_SRC, "model.sdf")] == MODEL_SHA, przed
    out = {"swiaty": {}, "model": {}, "zrodla": {os.path.relpath(p, ROOT): h for p, h in przed.items()}, "maski": MASKI,
           "teren": {"flagi": FLAGA_TERENU, "z_m": Z_TERENU, "bok_m": BOK}}
    for lata in LATY:
        p, tex = swiat(lata)
        out["swiaty"][os.path.relpath(p, ROOT)] = {"sha256": sha(p), "tekstura": os.path.relpath(tex, ROOT), "tekstura_sha256": sha(tex)}
    for p in model():
        out["model"][os.path.relpath(p, ROOT)] = sha(p)
    po = {p: sha(p) for p in przed}
    out["zrodla_bez_zmian"] = po == przed
    assert out["zrodla_bez_zmian"]
    json.dump(out, open(os.path.join(ROOT, "results/TEACH/s1/swiaty.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
