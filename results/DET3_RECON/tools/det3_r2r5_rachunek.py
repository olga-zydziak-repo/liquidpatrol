#!/usr/bin/env python3
"""results/DET3_RECON/tools/det3_r2r5_rachunek.py — R2 (piksele 15–30 m, ruch pozorny, MTI) + R5 (sufit).

Litera: f=270 px (r02/mti.py:17), W_REAL 2.5 / H_REAL 0.5 m (det_labels.py:33-34), MTI delta=3 klatki
(r02/mti.py MTITracker.__init__), open_k=3, min_area 8, diff_thr 22 (r02/mti.py:30-34).
Model MTI (dolna granica, obserwator nieruchomy, derotacja idealna): pasek różnicy na krawędzi celu ma
szerokość d = przesunięcie pozorne między klatkami pary; MORPH_OPEN 3×3 usuwa struktury węższe niż 3 px
⇒ warunek widoczności d ≥ 3 px ∧ h ≥ 3 px. Styczny: d = f·v·Δt/Z. Radialny: przyrost szerokości na
stronę d = f·W·v·Δt/(2·Z²). Δt = 3/kadencja.
R5: okno admisji radialnego celu v z R0: [max(0,(R0−D)/v), (R0−5)/v] (podłoga 5.01 m RECON_TRANSIT §R1);
gwarancja skanem o maks. przerwie rewizyty G i stare 1.2 s: długość okna ≥ G + 1.2 (G 12.0 CH87 / 13.9 CH0,
RECON_TRANSIT §R3 tabela). D_min = 5 + v·(G + 1.2).
"""
import json, sys
F, W, H = 270.0, 2.5, 0.5
out = {"box_px": {}, "ruch": {}, "mti_Zmax": {}, "r5": {}}
for Z in (15, 20, 25, 30):
    out["box_px"][Z] = [round(F * W / Z, 2), round(F * H / Z, 2)]
for hz in (14.7, 5.0):
    dt = 3 / hz
    for v in (0.5, 1.0):
        out["ruch"][f"{hz}Hz_v{v}"] = {Z: {"styczny_px_kl": round(F * v / hz / Z, 2),
                                         "styczny_px_para": round(F * v * dt / Z, 2),
                                         "radialny_px_strona_para": round(F * W * v * dt / (2 * Z * Z), 3)}
                                     for Z in (10, 15, 20, 25, 30)}
        out["mti_Zmax"][f"{hz}Hz_v{v}"] = {"styczny_m": round(F * v * dt / 3, 1),
                                          "radialny_m": round((F * W * v * dt / 6) ** 0.5, 1)}
out["mti_Zmax"]["h_ge_3px_m"] = round(F * H / 3, 1)
for G, nm in ((12.0, "CH87"), (13.9, "CH0")):
    for v in (0.5, 1.0):
        out["r5"][f"{nm}_v{v}_Dmin_m"] = round(5 + v * (G + 1.2), 1)
for R0 in (15, 25, 30):
    for D in (15, 20, 25, 30):
        t_open, t_close = max(0.0, (R0 - D) / 1.0), (R0 - 5.01) / 1.0
        out["r5"][f"R0_{R0}_D_{D}_v1"] = {"okno_s": [round(t_open, 2), round(t_close, 2)],
                                          "dlugosc_s": round(t_close - t_open, 2),
                                          "gwarancja_CH87": t_close - t_open >= 13.2,
                                          "pierwszy_przeglad_11.15_w_oknie": t_open <= t_close - 1.2 and 11.15 <= t_close}
json.dump(out, open(sys.argv[1], "w"), indent=1)
print(json.dumps(out, indent=1))
