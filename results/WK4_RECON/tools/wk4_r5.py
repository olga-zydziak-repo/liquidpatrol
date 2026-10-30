#!/usr/bin/env python3
"""results/WK4_RECON/tools/wk4_r5.py — R5: rachunek sufitu PRZED lotami sieci (desk, 0 bootów).
Litery: k = 0.494 /s (habitat s = 0.63), g = 9.81; kamera mono_cam 3354ae1e: horizontal_fov 1.74 rad,
640×480 (model.sdf:53-56), montaż poziomy (x500_mono_cam/model.sdf:9 pose .12 .03 .242 0 0 0); pół-pole
pionowe atan(240/fy), fy = 320/tan(0.87); margines MTI 10 px (wk3_kadr). Orbita: executor_params.json —
z_orb 12 m, cel z 10 m (Δz 2 m), r 6–10 m, v_tan 1.8 m/s. PX4 (domyślne, airframe 4010→4001 bez
nadpisań): MPC_TILTMAX_AIR 45° (limits_params.c:96), MPC_THR_MAX 1.0 (:140), MPC_THR_HOVER 0.60
(4001_gz_x500:50), MPC_XY_VEL_MAX 12 (:47), MPC_ACC_HOR 3 (autonomous_params.c:88); sieć V_MAX 3.0
(net_controller.py:50). Intensywność: σ_u = 0.1889·Ū (wk4_dryden).
Wyjście: results/WK4_RECON/r5_sufit.json
"""
import json
import math
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "r5_sufit.json")
K, G = 0.494, 9.81
fy = 320 / math.tan(1.74 / 2)
half_v = math.degrees(math.atan(240 / fy)); half_v_m = math.degrees(math.atan(230 / fy))
half_h = math.degrees(1.74 / 2)
tilt = lambda v: math.degrees(math.atan(K * v / G))  # noqa: E731
res = {"fy_px": round(fy, 2), "pol_pole_pion_deg": round(half_v, 2), "pol_pole_pion_po_marginesie_deg": round(half_v_m, 2),
       "pol_pole_poziom_deg": round(half_h, 2), "przechyl_statyczny": {}, "kadr": {}, "px4": {}}
for U in (2, 3, 4, 5, 6, 8, 10):
    su = 0.1889 * U
    res["przechyl_statyczny"][f"U{U}"] = {"zawis": round(tilt(U), 1), "zawis_+3sigma_u": round(tilt(U + 3 * su), 1),
                                          "orbita_pod_wiatr_+3sigma": round(tilt(U + 3 * su + 1.8), 1)}
for r in (6, 8, 10):
    dep = math.degrees(math.atan(2.0 / r))
    res["kadr"][f"r{r}"] = {"cel_pod_osia_deg": round(dep, 1),
                            "wypadniecie_DOL_przy_pitch_nos_w_gore_deg": round(half_v_m - dep, 1),
                            "wypadniecie_GORA_przy_pitch_nos_w_dol_deg": round(half_v_m + dep, 1)}
    th = half_v_m - dep
    vrel = G * math.tan(math.radians(th)) / K
    res["kadr"][f"r{r}"]["U_statyczne_dla_progu_dol"] = round(vrel, 2)
    res["kadr"][f"r{r}"]["U_gdy_szczyt_+3sigma_osiaga_prog"] = round(vrel / (1 + 3 * 0.1889), 2)
res["px4"] = {"TILTMAX_45_przy_v_rel_m_s": round(G * math.tan(math.radians(45)) / K, 1),
              "U_srednie_gdy_szczyt_orbity_+3sigma_osiaga_45deg": round((G / K - 1.8) / (1 + 3 * 0.1889), 1),
              "THR_MAX_1_przy_HOVER_0.6_max_przechyl_utrzymania_wys_deg": round(math.degrees(math.acos(0.6)), 1),
              "XY_VEL_MAX_12_vs_V_MAX_sieci_3": "predkosc GRUNTOWA; wiatr nie zwieksza wymaganej predkosci gruntowej orbity",
              "uwaga": "MPC_ACC_HOR dotyczy trybów autonomicznych; offboard prędkościowy — nie weryfikowane"}
json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
