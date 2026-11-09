#!/usr/bin/env python3
"""results/NADIR/tools/nadir_n1_manifest.py — ANEKS_NADIR-1 §CO (3): manifest v2 + świat v2 + asercja wolności vs SDF.

Parser PEŁNY (poprawka wobec nadir_gen.bryly, który brał tylko pierwszy box modelu — korony drzew umykały): każdy
<visual> z <box> w każdym statycznym modelu świata world_kont_A3, poza ground_plane / kont_decal / film_cam; prostokąt
w rzucie z góry = pose modelu ∘ pose visuala (yaw), półboki + MARGIN. Węzeł jest „pod bryłą” ⇔ środek znacznika leży
w tym prostokącie (margines 1.0 m = pół płyty 0.667 + 0.33 zapasu na widok skośny).
Przesunięcie (ANEKS §2.4): wyłącznie id z listy aneksu {1, 4, 7, 14, 24, 27, 31}; kandydaci na siatce 0.25 m w kole ≤ s/2
(5 m) od węzła idealnego, wolni od wszystkich brył (MARGIN) i ≥ 2.0 m od innych znaczników, |p| ≤ R_E; wybór = najmniejsze
przesunięcie (remis: mniejszy |p|). Węzły spoza listy, które pełny parser uzna za zasłonięte, NIE są ruszane — raport.
Wynik: results/NADIR/s1/n1/manifest_znaczniki_v2.json, worlds/world_nadir2_A3.sdf (= world_kont_A3 + 37 znaczników v2,
assert bajtowy jak v1), raport kolizji v1/v2.
"""
import hashlib
import json
import math
import os
import re
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/NADIR/tools"))
import nadir_gen as G                                      # READ-ONLY: model_xml, stałe

V1 = json.load(open(os.path.join(ROOT, "results/NADIR/s1/manifest_znaczniki.json")))
OUT = os.path.join(ROOT, "results/NADIR/s1/n1")
KONT_W = os.path.join(ROOT, "worlds/world_kont_A3.sdf")
OUT_W = os.path.join(ROOT, "worlds/world_nadir2_A3.sdf")
MARGIN, MIN_SEP, KROK = 1.0, 2.0, 0.25
DO_PRZESUNIECIA = (1, 4, 7, 14, 24, 27, 31)
POMIN = ("ground_plane", "kont_decal", "film_cam")


def prostokaty(src):
    out = []
    for m in re.finditer(r'<model name="([^"]+)">(.*?)</model>', src, re.S):
        n, body = m.groups()
        if n in POMIN:
            continue
        pm = re.search(r"<static>true</static>\s*<pose>([^<]+)</pose>", body)
        if not pm:
            continue
        mx, my, mz, _, _, myaw = map(float, pm.group(1).split())
        for v in re.finditer(r"<visual name=\"([^\"]+)\">(.*?)</visual>", body, re.S):
            vn, vb = v.groups()
            sz = re.search(r"<box><size>([^<]+)</size></box>", vb)
            if not sz:
                continue
            vp = re.search(r"<pose>([^<]+)</pose>", vb)
            vx, vy, vz, _, _, vyaw = map(float, vp.group(1).split()) if vp else (0, 0, 0, 0, 0, 0)
            c, s = math.cos(myaw), math.sin(myaw)
            cx, cy = mx + c * vx - s * vy, my + s * vx + c * vy
            sx, sy, szz = map(float, sz.group(1).split())
            out.append({"model": n, "visual": vn, "cx": cx, "cy": cy, "yaw": myaw + vyaw, "sx": sx, "sy": sy,
                        "z_gora": round(mz + vz + szz / 2, 2)})
    return out


def zaslania(e, n, p, margin=MARGIN):
    dx, dy = e - p["cx"], n - p["cy"]
    c, s = math.cos(-p["yaw"]), math.sin(-p["yaw"])
    lx, ly = c * dx - s * dy, s * dx + c * dy
    return abs(lx) <= p["sx"] / 2 + margin and abs(ly) <= p["sy"] / 2 + margin


def main():
    os.makedirs(OUT, exist_ok=True)
    src = open(KONT_W, encoding="utf8").read()
    P = prostokaty(src)
    kol_v1 = {z["id"]: sorted({f"{p['model']}/{p['visual']}" for p in P if zaslania(z["E"], z["N"], p)}) for z in V1["znaczniki"]}
    kol_v1 = {k: v for k, v in kol_v1.items() if v}
    poz = {z["id"]: (z["E"], z["N"]) for z in V1["znaczniki"]}
    przes = {}
    for i in DO_PRZESUNIECIA:
        e0, n0 = poz[i]
        best = None
        k = int(5.0 / KROK)
        for a in range(-k, k + 1):
            for b in range(-k, k + 1):
                e, n = e0 + a * KROK, n0 + b * KROK
                d = math.hypot(e - e0, n - n0)
                if d > 5.0 or math.hypot(e, n) > V1["R_E_m"]:
                    continue
                if any(zaslania(e, n, p) for p in P):
                    continue
                if any(math.hypot(e - x, n - y) < MIN_SEP for j, (x, y) in poz.items() if j != i):
                    continue
                c = (round(d, 3), round(math.hypot(e, n), 3), e, n)
                if best is None or c < best:
                    best = c
        assert best is not None, f"id {i}: brak wolnego miejsca ≤ 5 m"
        przes[i] = {"z": [e0, n0], "na": [best[2], best[3]], "przesuniecie_m": best[0]}
        poz[i] = (best[2], best[3])
    zn2 = []
    xml = ""
    for z in V1["znaczniki"]:
        e, n = poz[z["id"]]
        kol = sorted({f"{p['model']}/{p['visual']}" for p in P if zaslania(e, n, p)})
        if z["id"] in DO_PRZESUNIECIA:
            assert not kol, (z["id"], kol)                    # asercja vs SDF
        png = os.path.join(ROOT, z["png"])
        zn2.append(dict(z, E=e, N=n, E_idealny=z["E"], N_idealny=z["N"], kolizje_z_brylami=kol,
                        przesuniety=z["id"] in DO_PRZESUNIECIA))
        xml += G.model_xml(z["id"], e, n, png)
    name_k, name_n = '<world name="world_kont_A3">', '<world name="world_nadir2_A3">'
    out = src.replace(name_k, name_n).replace("  </world>", xml + "  </world>")
    assert out.replace(xml, "").replace(name_n, name_k) == src
    open(OUT_W, "w", encoding="utf8").write(out)
    man = dict(V1, opis="manifest v2 (ANEKS_NADIR-1 §2.4): 7 węzłów przesuniętych ≤ s/2 od brył; pozycje = prawda poprawki",
               wersja=2, parser_bryl="pełny (każdy visual box), margines 1.0 m", znaczniki=zn2,
               n_kolizje=sum(1 for z in zn2 if z["kolizje_z_brylami"]),
               swiat={"plik": os.path.relpath(OUT_W, ROOT), "sha256": hashlib.sha256(out.encode()).hexdigest()})
    man.pop("swiat_bazowy", None)
    man["swiat_bazowy"] = {"plik": "worlds/world_kont_A3.sdf", "sha256": hashlib.sha256(src.encode()).hexdigest()}
    json.dump(man, open(os.path.join(OUT, "manifest_znaczniki_v2.json"), "w"), ensure_ascii=False, indent=1)
    rap = {"kolizje_v1_pelny_parser": kol_v1, "przesuniecia": przes,
           "kolizje_v2": {z["id"]: z["kolizje_z_brylami"] for z in zn2 if z["kolizje_z_brylami"]},
           "swiat_v2_sha256": man["swiat"]["sha256"], "n_prostokatow": len(P)}
    json.dump(rap, open(os.path.join(OUT, "manifest_v2_raport.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rap, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
