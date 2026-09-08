# STOP-K2b — shakeout diag denial (PRE_K2 K5) — PASS bramki technicznej

LiquidPatrol · K2 · pierwszy lot ścieżki REFUSE+D5+touchdown w pętli ławki (dotąd 0 wykonań historycznych).
Boot `results/K2/diag_denial` · CONTROLLER=net NET_ARM=ncp · c03_s01 · K2_INJECT_T=30 · kind=diag.

## §1. Bramka techniczna (STOP-K2b) — PASS
- manifest 1.klasy: kind=diag, rc=0, controller=net, n_ep=1, **bez stub/null**; weights_sha `0337d5ea…`==FREEZE_NET NCP.
- **certs_selfcheck_rc=0** (B5 — certs biegną dla FLIGHT=bench, dotąd tylko gate_r03); k2_inject_t=30.0.
- **breach=0** w całym trace.

## §2. Sekwencja denialu (pierwsze wykonanie, CZYSTE)
| zdarzenie | sim | fakt |
|---|---|---|
| episode_start | 108.52 | t_entry=2.66 |
| **denial (T_inj)** | 141.224 | inj_t_rel=32.704 (cel 32.66 → **+0.044 s, w ±0.2 s**) |
| **REFUSE(POS_DEGRADED)** | 141.332 | **t_refuse=0.108 s** (pasmo K1 [0.05,0.15] ✓), r_est=11.87 m (≪R_E=32) |
| refuse_pos_land → h_switch → touchdown | 141.33 → 146.69 → 151.02 | **D5 dwufazowe** (V_DESC_FAST→V_DESC_LAND→touchdown, ~9.8 s) |
| episode_end / denial_boot_end | 151.02 | **breach=False, denied=True** |

## §3. k2_judge (glue B6) na realnym trace
`c03_s01`: valid=True (V2′ do T_inj), t_refuse=0.108 s (w paśmie), **x_exc=1.797 m** (dryf od punktu wstrzyknięcia), t_td≈9.7 s, breach=False, touchdown=True → **verdict (+) PASS** (eps_cap testowy). Glue liczy wszystkie metryki z lotu — przyrząd zadziałał na żywych danych.

## §4. Znalezisko vs predykcja
**P-K2-1 (shakeout ujawni ≥1 defekt klasy glue w pierwszym wykonaniu) — NIE ZISZCZONE:** tor detekcja→REFUSE→D5→touchdown przeszedł czysto za pierwszym razem. Ekstrakcja D5 (bit-w-bit) + wiązanie pos_flag + hook + glue zadziałały bez defektu. (Chybienie w dobrą stronę.) P-K2-2 (t_refuse w paśmie): trafione na tym epizodzie (0.108). P-K2-4 (0 breach): trafione.

## §5. STOP-K2b — czeka na CC
Ratyfikacja shakeout → K4b (3 booty nominalne z uzbrojonym monitorem, K4b=TAK po zamknięciu weta) → kampania 12 ep kryterialnych (komórki r_p95≤26, 6×2 ziarna, T_inj=30) → STOP-K2c=RAPORT_K2. UWAGA: eps_cap kryterialny do ustalenia (PRE/K1) — w k2_judge jest argumentem, nie zaszyty. Wykonawca po STOP: nic.
