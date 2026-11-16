#!/usr/bin/env python3
"""results/TEACH_RECON/tools/teach_r1_podglad.py — PROMPT_TEACH_S0 R1: podgląd kandydatów łat (WMS HighResolution GUGiK = edycja 2024,
okno 400 × 400 m, czerwona ramka ≈ 100 m) przed wyborem; arkusz r1_podglad_kandydatow.jpg. Uruchamiany w katalogu roboczym podglądów."""
import sys, cv2
sys.path.insert(0, "/home/olga/projects/liquidpatrol/results/ORTO_RECON/tools")
import orto_r1 as R, orto_uklad as UK
K = {"S1_stadion_parking": (51.1405, 16.9445), "S2_magnolia": (51.1185, 16.9905), "S3_bielany_retail": (51.0505, 17.0005),
     "S4_kozanow_osiedle": (51.1395, 16.9690), "S5_swojczyce_przem": (51.1150, 17.1270),
     "J1_pola_marsowe": (51.1065, 17.0975), "J2_pole_jerzmanowo": (51.0960, 16.8350), "J3_pole_oltaszyn": (51.0570, 17.0400),
     "J4_blonia_wroc": (51.1060, 17.0810)}
for n, (la, lo) in K.items():
    xN, yE = UK.wgs84_do_2180(la, lo)
    P = 200
    im, q = R.wms_getmap(R.WMS_HR, "Raster", yE - P, xN - P, yE + P, xN + P, 1000, 1000)
    cv2.imwrite(f"teach_pod/{n}.jpg", im); print(n, round(xN), round(yE), im.shape)
