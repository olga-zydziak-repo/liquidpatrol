#!/usr/bin/env python3
"""results/NAD2/tools/nad2_krok.py — krok osłony drivera NAD2 (PRE_NAD2 §3.4, ANEKS_NAD2-1 §2.6; PROMPT_NAD2_S1 §1.3).

Jedyna ścieżka, którą driver results/NAD2/tools/nad2_flight.py woła osłonę — wydzielona, żeby obligacja wejścia C3 (P5_nad2)
sprawdzała DOKŁADNIE kod lotu na tickach S4 (replay), a nie jego opis.
  krok(shield, tick, own, own_net, vel, tgt_ekf, tgt_net, …) → (d_dec, pos_bramki)
osłona dostaje pozycję i cel w obu ramach (EKF: own, tgt_ekf; poprawiona: own_net = p_corr, tgt_net = setpoint sieci) i sama
wybiera ramę po aktualizacji monitora GNSS (r03/nadir_shield.NadirShield._step_nad2). pos_bramki = pozycja w ramie wybranej
— wejście projekcji promieniowej R-G-NOM w warstwie komend (r03/kont_gate.KontCommand.patrol). Przy rama is None (brak ramy B+)
obie ramy = EKF.
"""


def krok(shield, tick, own, own_net, vel, tgt_ekf, tgt_net, mode, pos_flag, cs_gnss_pos, now, dr, rama):
    d = shield.step(tick, own, vel, tgt_ekf, mode=mode, pos_flag=pos_flag, cs_gnss_pos=cs_gnss_pos, now=now, dr=dr,
                    t_fix=(rama.t_fix if rama is not None else None), kosz_j=(rama.kosz if rama is not None else None),
                    tryb=(rama.tryb if rama is not None else None),
                    pos_corr=own_net, target_corr=tgt_net)
    pos_bramki = own_net if (d.get("nad2") or {}).get("rama") == "corr" else own
    return d, pos_bramki
