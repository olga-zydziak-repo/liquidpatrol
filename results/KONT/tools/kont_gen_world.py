#!/usr/bin/env python3
"""results/KONT/tools/kont_gen_world.py — świat nogi KONT (PROMPT_KONT_S1 §1.2): world_demo_A3 bajt-w-bajt + dekal.
Różnice wobec A3 WYŁĄCZNIE: nazwa świata (PX4 czeka na /world/<PX4_GZ_WORLD>/scene/info, więc musi być równa nazwie
pliku) oraz jeden model kont_decal przed </world>. Tekstura: szachownica o boku 1 m, 72×72 pola (płyta 72×72 m pokrywa
koło R≤36), odcienie pól losowane z ziarna w dwóch klasach (ciemna/jasna), żeby KLT nie widział obrazu okresowego.
Wynik: worlds/world_kont_A3.sdf, worlds/kont_checker.png; assert: po usunięciu dodatków plik == A3."""
import hashlib
import os
import random
import struct
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
A3 = os.path.join(ROOT, "worlds", "world_demo_A3.sdf")
OUT = os.path.join(ROOT, "worlds", "world_kont_A3.sdf")
PNG = os.path.join(ROOT, "worlds", "kont_checker.png")
A3_SHA8 = "adc91803"
SEED = 20261106
N_CELLS, CELL_PX = 72, 16
FLAGS = 2                       # bit 1; maska imagera 4294967293 = ~bit 1
DECAL = f"""    <!-- KONT dekal pod przepływ (PRE_KONT §2.3): widzi go kamera przepływu, imager nie (maska ~bit1). -->
    <model name="kont_decal">
      <static>true</static>
      <pose>0 0 0 0 0 0</pose>
      <link name="l">
        <visual name="v"><cast_shadows>false</cast_shadows>
          <visibility_flags>{FLAGS}</visibility_flags>
          <geometry><box><size>72 72 0.02</size></box></geometry>
          <material><ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse><specular>0 0 0 1</specular>
            <pbr><metal><albedo_map>{PNG}</albedo_map><metalness>0</metalness><roughness>1</roughness></metal></pbr>
          </material>
        </visual>
      </link>
    </model>
"""


def checker_png():
    rng = random.Random(SEED)
    vals = [[(rng.randint(20, 90) if (i + j) % 2 == 0 else rng.randint(165, 245)) for j in range(N_CELLS)]
            for i in range(N_CELLS)]
    w = N_CELLS * CELL_PX
    raw = bytearray()
    for i in range(N_CELLS):
        row = b"\x00" + b"".join(bytes([vals[i][j]]) * CELL_PX for j in range(N_CELLS))
        raw += row * CELL_PX

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, w, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def main():
    src = open(A3, encoding="utf8").read()
    assert hashlib.sha256(src.encode()).hexdigest()[:8] == A3_SHA8
    name_a, name_k = '<world name="world_demo_A3">', '<world name="world_kont_A3">'
    assert src.count(name_a) == 1 and src.count("  </world>") == 1
    out = src.replace(name_a, name_k).replace("  </world>", DECAL + "  </world>")
    assert out.replace(DECAL, "").replace(name_k, name_a) == src
    open(OUT, "w", encoding="utf8").write(out)
    open(PNG, "wb").write(checker_png())
    for p in (OUT, PNG):
        print(hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.relpath(p, ROOT))


main()
