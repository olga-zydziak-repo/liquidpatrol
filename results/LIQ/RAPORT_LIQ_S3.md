# RAPORT_LIQ_S3 — rundy 7–12 + sonda STOCK (koniec lotów nogi) → STOP-LIQ3

LiquidPatrol · CC · 03.10.2026 · PROMPT_LIQ_S3 · po STOP-LIQ2 (push wykonany). Raport =
liczby; werdykt drabiny i rozstrzygnięcia kanoniczne = ANEKS_LIQ-2 (po tym raporcie).

## §0. Bramka wejścia (wykonaniem, przed czymkolwiek)

origin/master = `bd93a63`; `5551219` i `bd93a63` w origin/master ✓ · `origin/master..HEAD`
puste ✓ · porcelain pełny pusty (REPO-1) ✓. Piny 5/5 (`check_shield_frozen=True`) · certy
9/9 (`certs_selfcheck` PASS) · sha 5/5: bench_judge `8ec0fcfb` ✓, features `9adc1505` ✓,
ncp.npz `0337d5ea` ✓, gru.npz `5ec02755` ✓, mlp20.npz `74b5ae7d` ✓. Driver kampanii BEZ
ZMIAN od S2: `results/LIQ/camp/run_liq_boot.sh` sha256 `43b8d2dd…` (byte-identyczny z commitem
bd93a63 — porcelain pusty to poświadcza). Launcher sondy `tools/liq_launcher_stock.sh` sha256
`7324f850…` (byte-check diffu w §2). Pliki dotykane: wyłącznie `results/LIQ/**`; kod zero.
Host przed kampanią: load1 0.32. Reżim bootów identyczny S2 (run_boot.sh, KIND=liq, FILM=0,
pełne uzbrojenie bez LEGACY, cooldown ≥300 s, sustained CLEAN 3×30 s, manifesty 1. klasy).

## §1. Mapa rund 7–12 (deterministyczna, wypisana PRZED pierwszym lotem)

Blok rundy r = episode_id 4(r−1)…4r−1 porządku manifestu F2 (`results/BENCH/
scenario_manifest.json`, blok 1). Kolejność ramion = kontynuacja wzoru S2.
Stany kolejek na wejściu: done 24 / pending 24 / in_flight 0 per ramię (zgodne z S2).

| runda | episode_id | scenariusze | kolejność ramion |
|---|---|---|---|
| 7 | 24–27 | c00_s03 c01_s03 c02_s03 c03_s03 | NCP→GRU |
| 8 | 28–31 | c04_s03 c05_s03 c06_s03 c07_s03 | GRU→NCP |
| 9 | 32–35 | c08_s03 c09_s03 c10_s03 c11_s03 | NCP→GRU |
| 10 | 36–39 | c00_s04 c01_s04 c02_s04 c03_s04 | GRU→NCP |
| 11 | 40–43 | c04_s04 c05_s04 c06_s04 c07_s04 | NCP→GRU |
| 12 | 44–47 | c08_s04 c09_s04 c10_s04 c11_s04 | GRU→NCP |

Nazwy bootów: `r<runda>_<ramię>` (powtórka: sufiks `r`), BOOT_N 13–24. Sonda: `probe_s01`,
`probe_s02` (BOOT_N 25–26). Kampania leci DO KOŃCA; przerwanie wyłącznie REFUSE(POS)/breach
R_E (rundy) albo nie-GEOFENCE REFUSE/anomalia (sonda).

## §2. Rundy 7–12 — wpisy płaskie (per boot, per epizod)

Format jak S2: werdykt sędziego (D6) PASS/FAIL(gałąź) · V2′ · z_max [m] · t_entry [s] ·
REFUSE · V2′-składowe + d_min. Wszystkie booty rc=0, finalize=0, breach_ev=0, 0 wyjątków
kontrolera/guardu w act.log, chyba że zaznaczono.

### Runda 7 (c00–c03_s03) — NCP→GRU

**Boot r7_ncp (BOOT_N=13, ramię NCP):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c00_s03 | PASS | VALID | 12.49 | 2.9 | 0 | dsw 0.965 · longest 0.0 s · tj 0 · d_min 7.798 |
| c01_s03 | PASS | VALID | 13.6 | 2.8 | 0 | dsw 0.9788 · longest 0.0 s · tj 0 · d_min 7.724 |
| c02_s03 | PASS | VALID | 12.6 | 2.7 | 0 | dsw 0.9685 · longest 0.0 s · tj 0 · d_min 7.79 |
| c03_s03 | PASS | VALID | 12.57 | 2.796 | 0 | dsw 0.9775 · longest 0.0 s · tj 0 · d_min 7.783 |

**Boot r7_gru (BOOT_N=14, ramię GRU):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c00_s03 | PASS | VALID | 14.44 | 2.844 | 0 | dsw 0.9741 · longest 0.0 s · tj 0 · d_min 7.448 |
| c01_s03 | FAIL(c_sweep) | VALID | 14.86 | 2.776 | 0 | dsw 0.969 · longest 0.0 s · tj 0 · d_min 7.04 |
| c02_s03 | PASS | VALID | 13.48 | 3.008 | 0 | dsw 0.9791 · longest 0.0 s · tj 0 · d_min 7.597 |
| c03_s03 | FAIL(c_sweep) | VALID | 15.23 | 2.776 | 0 | dsw 0.9791 · longest 0.0 s · tj 0 · d_min 7.158 |

### Runda 8 (c04–c07_s03) — GRU→NCP

**Boot r8_gru (BOOT_N=15, ramię GRU):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c04_s03 | FAIL(c_sweep) | VALID | 15.63 | 2.336 | 0 | dsw 0.9751 · longest 0.0 s · tj 0 · d_min 6.766 |
| c05_s03 | PASS | VALID | 14.57 | 2.592 | 0 | dsw 0.9792 · longest 0.0 s · tj 0 · d_min 7.158 |
| c06_s03 | FAIL(c_sweep) | VALID | 14.93 | 0.0 | 0 | dsw 0.978 · longest 0.0 s · tj 0 · d_min 6.487 |
| c07_s03 | PASS | VALID | 14.96 | 0.02 | 0 | dsw 0.9682 · longest 0.0 s · tj 0 · d_min 7.659 |

**Boot r8_ncp (BOOT_N=16, ramię NCP):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c04_s03 | PASS | VALID | 12.83 | 2.376 | 0 | dsw 0.9688 · longest 0.529 s · tj 0 · d_min 7.57 |
| c05_s03 | PASS | VALID | 13.54 | 2.524 | 0 | dsw 0.9791 · longest 0.0 s · tj 0 · d_min 7.083 |
| c06_s03 | PASS | VALID | 12.72 | 2.136 | 0 | dsw 0.9785 · longest 0.0 s · tj 0 · d_min 6.99 |
| c07_s03 | PASS | VALID | 12.55 | 2.508 | 0 | dsw 0.9783 · longest 0.0 s · tj 0 · d_min 7.361 |

### Runda 9 (c08–c11_s03) — NCP→GRU

**Boot r9_ncp (BOOT_N=17, ramię NCP):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c08_s03 | PASS | VALID | 13.4 | 2.036 | 0 | dsw 0.9633 · longest 0.0 s · tj 0 · d_min 5.107 |
| c09_s03 | FAIL(d_dmin) | VALID | 13.37 | 2.02 | 0 | dsw 0.9781 · longest 0.0 s · tj 0 · d_min 0.352 |
| c10_s03 | PASS | VALID | 13.12 | 2.012 | 0 | dsw 0.9762 · longest 0.0 s · tj 0 · d_min 5.569 |
| c11_s03 | PASS | VALID | 13.24 | 1.9 | 0 | dsw 0.978 · longest 0.0 s · tj 0 · d_min 6.939 |

**Boot r9_gru (BOOT_N=18, ramię GRU):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c08_s03 | FAIL(c_sweep) | VALID | 15.88 | 1.98 | 0 | dsw 0.9724 · longest 0.0 s · tj 0 · d_min 6.619 |
| c09_s03 | FAIL(c_sweep,d_dmin) | VALID | 14.73 | 0.12 | 0 | dsw 0.9771 · longest 0.0 s · tj 0 · d_min 0.341 |
| c10_s03 | FAIL(c_sweep) | VALID | 15.5 | 1.98 | 0 | dsw 0.9646 · longest 0.0 s · tj 0 · d_min 5.515 |
| c11_s03 | PASS | VALID | 14.6 | 2.008 | 0 | dsw 0.9766 · longest 0.0 s · tj 0 · d_min 6.339 |

### Runda 10 (c00–c03_s04) — GRU→NCP

**Boot r10_gru (BOOT_N=19, ramię GRU):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c00_s04 | PASS | VALID | 13.79 | 2.944 | 0 | dsw 0.9728 · longest 0.0 s · tj 0 · d_min 7.356 |
| c01_s04 | FAIL(c_sweep) | VALID | 15.21 | 2.776 | 0 | dsw 0.9762 · longest 0.0 s · tj 0 · d_min 7.704 |
| c02_s04 | PASS | VALID | 13.29 | 2.856 | 0 | dsw 0.976 · longest 0.0 s · tj 0 · d_min 6.722 |
| c03_s04 | FAIL(c_sweep) | VALID | 14.92 | 2.948 | 0 | dsw 0.9766 · longest 0.0 s · tj 0 · d_min 7.129 |

**Boot r10_ncp (BOOT_N=20, ramię NCP):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c00_s04 | PASS | VALID | 12.96 | 2.86 | 0 | dsw 0.9716 · longest 0.0 s · tj 0 · d_min 7.813 |
| c01_s04 | PASS | VALID | 13.31 | 2.932 | 0 | dsw 0.9756 · longest 0.0 s · tj 0 · d_min 7.718 |
| c02_s04 | PASS | VALID | 12.49 | 2.696 | 0 | dsw 0.9758 · longest 0.0 s · tj 0 · d_min 7.978 |
| c03_s04 | PASS | VALID | 12.52 | 2.632 | 0 | dsw 0.976 · longest 0.0 s · tj 0 · d_min 7.888 |

### Runda 11 (c04–c07_s04) — NCP→GRU

**Boot r11_ncp (BOOT_N=21, ramię NCP):** V2′ bootu: 4/4 VALID, timejump 0. Nota act.log:
1 linia `terminate called without an active exception` PO ostatnim episode_end+reset_done,
przed czystym `[bench] done` — szum teardownu warstwy C++/MAVSDK, wzorzec precedensowany
w F2 (f2_mlp_b5, f2_mlp_b6); zero wyjątków kontrolera/guardu (Python), finalize 4/4.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c04_s04 | PASS | VALID | 12.8 | 2.392 | 0 | dsw 0.9544 · longest 0.0 s · tj 0 · d_min 7.451 |
| c05_s04 | PASS | VALID | 13.49 | 0.0 | 0 | dsw 0.9745 · longest 0.0 s · tj 0 · d_min 6.693 |
| c06_s04 | PASS | VALID | 12.71 | 2.172 | 0 | dsw 0.9625 · longest 0.0 s · tj 0 · d_min 7.281 |
| c07_s04 | PASS | VALID | 12.82 | 0.1 | 0 | dsw 0.9751 · longest 0.0 s · tj 0 · d_min 7.112 |

**Boot r11_gru (BOOT_N=22, ramię GRU):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c04_s04 | PASS | VALID | 15.54 | 2.428 | 0 | dsw 0.9722 · longest 0.155 s · tj 0 · d_min 7.154 |
| c05_s04 | PASS | VALID | 14.96 | 2.276 | 0 | dsw 0.9756 · longest 0.0 s · tj 0 · d_min 7.018 |
| c06_s04 | FAIL(c_sweep,d_dmin) | VALID | 13.74 | 2.912 | 0 | dsw 0.9638 · longest 0.0 s · tj 0 · d_min 2.02 |
| c07_s04 | PASS | VALID | 14.0 | 2.672 | 0 | dsw 0.9746 · longest 0.0 s · tj 0 · d_min 7.344 |

### Runda 12 (c08–c11_s04) — GRU→NCP

**Boot r12_gru (BOOT_N=23, ramię GRU):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c08_s04 | FAIL(c_sweep) | VALID | 15.95 | 1.984 | 0 | dsw 0.9584 · longest 0.0 s · tj 0 · d_min 6.367 |
| c09_s04 | PASS | VALID | 14.01 | 1.88 | 0 | dsw 0.9757 · longest 0.0 s · tj 0 · d_min 6.403 |
| c10_s04 | FAIL(c_sweep) | VALID | 15.2 | 1.992 | 0 | dsw 0.9755 · longest 0.0 s · tj 0 · d_min 7.087 |
| c11_s04 | PASS | VALID | 14.42 | 2.18 | 0 | dsw 0.9643 · longest 0.0 s · tj 0 · d_min 6.957 |

**Boot r12_ncp (BOOT_N=24, ramię NCP):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c08_s04 | PASS | VALID | 13.29 | 1.992 | 0 | dsw 0.9589 · longest 0.0 s · tj 0 · d_min 7.154 |
| c09_s04 | PASS | VALID | 12.94 | 0.136 | 0 | dsw 0.9756 · longest 0.0 s · tj 0 · d_min 4.376 |
| c10_s04 | FAIL(d_dmin) | VALID | 13.25 | 1.936 | 0 | dsw 0.9745 · longest 0.0 s · tj 0 · d_min 2.292 |
| c11_s04 | PASS | VALID | 13.34 | 0.12 | 0 | dsw 0.9745 · longest 0.0 s · tj 0 · d_min 5.433 |

Kolejki po rundzie 12: **done 48 / pending 0 per ramię** (komplet 48 par).

## §3. Sonda STOCK (2 booty, po komplecie rund)

**Launcher:** `tools/liq_launcher_stock.sh` sha256 `7324f850…`; byte-check diffu vs
`tools/w_launcher.sh` (frozen, `28df8928…`) wykonany przed bootami: **dokładnie 2 hunki**
(nagłówek komentarza + prepend wind_models → mkdir+echo dowodu), verbatim zgodne z
RAPORT_LIQ_S1 §4-diff — launcher niezmieniony od S1. Wywołanie BEZ ZMIAN; OUTDIR przez
argument względny `../LIQ/probe/<boot>` (wynikowo `results/LIQ/probe/**` — lista zamknięta
dotrzymana; lock `results/W/.executor_lock` transientny, zdejmowany trapem EXIT).
Orkiestracja cooldownu ≥300 s + sustained CLEAN 3×30 s przed launcherem (poza repo,
scratchpad; launcher i run_boot nietknięte).

**Konfiguracja (PRE_LIQ §5 + ANEKS_LIQ-1 §3):** FLIGHT=bench, KIND=liq, świat
`world_wind_s0` — sha w manifeście OBU bootów `921bdda7…` = **FREEZE_W byte-identyczny** ✓,
komórka c11 (epizody 11/23 manifestu BENCH), CONTROLLER=net NET_ARM=ncp (weights_sha
`0337d5ea…` w manifestach), W_ARM_ALWAYS=1, INTRUDER=1, FILM=0, pełne uzbrojenie
(arm_monitor=True w obu manifestach).

**Dowody STOCK per boot:** `.gz_resource_path_proof` verbatim (oba booty):
`GZ_SIM_RESOURCE_PATH=<puste>` — zero prependu `worlds/wind_models` ⇒ model x500_base
rozwiązany z drzewa stock PX4 (dowód R1.7 w konwencji nogi W; gz_env dopisuje wyłącznie
ścieżki stock). Treść proof + nota modelu wstrzyknięte do manifestów
(`gz_resource_path_proof`, `model_stock`).

| boot | BOOT_N | scenariusz | V2′ | z_max [m] | t_entry | REFUSE | sędzia (opisowo) | V2′-składowe |
|---|---|---|---|---|---|---|---|---|
| probe_s01 | 25 | c11_s01 | VALID | **13.10** | 2.06 | 0 | PASS | dsw 0.9558 · longest 0.0 s · tj 0 |
| probe_s02 | 26 | c11_s02 | VALID | **14.26** | 2.24 | 0 | FAIL(b_frac) | dsw 0.9676 · longest 0.0 s · tj 0 |

Zero REFUSE jakiejkolwiek gałęzi (w tym zero GEOFENCE-datum), zero breach, zero wyjątków,
rc=0/finalize=0 ×2; obie próby ważne za 1. podejściem (powtórki sondy: 0).

**Klasyfikacja progowa (ANEKS_LIQ-1 §3, progi zamrożone przed pomiarem):**
NIEOBECNE wymaga z_max ≤ 14.0 w 2/2 → s01 13.10 ≤ 14.0 ✓, s02 14.26 > 14.0 ✗ — NIE spełnione.
POTWIERDZONE wymaga z_max ≥ 15.0 w ≥1/2 → max(13.10, 14.26) = 14.26 < 15.0 — NIE spełnione.
**⇒ NIEROZSTRZYGAJĄCE** (s02 w przerwie 14.0–15.0; kwalifikator habitatowy zostaje per
ANEKS_LIQ-1 §3). Wnioski kanoniczne → ANEKS_LIQ-2.

**Zestawienie parami per ziarno (opisowe):**
| ziarno | sonda STOCK (world_wind_s0) | W L0 enable_wind (world_wind_s0) | Δ | stock-F2 (A3, poglądowe) |
|---|---|---|---|---|
| s01 | 13.10 | 18.45 | −5.35 | 13.27 (c11_s01) |
| s02 | 14.26 | 14.43 | −0.17 | 13.03 (c11_s02) |
(Pasmo stock-F2 całości: 12.86–13.27; s01 sondy siedzi w paśmie, s02 powyżej pasma.)

## §4. Liczniki, budżet, higiena

**Ważność S3:** 12/12 bootów rund VALID za pierwszym podejściem (48/48 epizodów V2′ VALID;
timejump=0 wszędzie, longest_stall max 0.529 s, dsw min 0.9544) + sonda 2/2 VALID.
**Powtórki: 0/4.** Żaden blok nie wypadł parowo. **Budżet S3:** 12 + 2 = 14 bootów (limit
12+2+≤4=18); noga łącznie 27 z ≤31. **REFUSE: 0** we wszystkich 50 epizodach S3 (kampania
48 + sonda 2); zero REFUSE(POS), zero GEOFENCE. **Breach R_E: 0** (breach_ev=0 ×14 bootów).
Wyjątki kontrolera/guardu: 0 (nota r11_ncp §2: 1 linia szumu teardownu C++/MAVSDK po
zakończeniu epizodów, precedens F2 f2_mlp_b5/b6 — nie wyjątek kontrolera).

**Zliczenia płaskie sędziego D6 — S3 (pierwsza ważna):** NCP 22/24 PASS (FAIL: c09_s03
d_dmin · c10_s04 d_dmin) · GRU 12/24 PASS (FAIL ×12: c_sweep — c01_s03,
c03_s03, c04_s03, c06_s03, c08_s03, c10_s03, c01_s04, c03_s04, c08_s04, c10_s04;
c_sweep+d_dmin — c09_s03, c06_s04).

**Agregat KOMPLETU 48 par (S2+S3, `aggregate_campaign` po pierwszej ważnej, unresolved=0):**
| ramię | success/resolved | p_exec | Wilson 95% | FAIL-e (pierwsza ważna) |
|---|---|---|---|---|
| NCP | 43/48 | 0.8958 | [0.7783, 0.9547] | c07_s02, c09_s02, c11_s02, c09_s03, c10_s04 |
| GRU | 27/48 | 0.5625 | [0.4227, 0.6930] | c03_s01, c04_s01, c08_s01, c10_s01, c03_s02, c05_s02, c07_s02, c08_s02, c09_s02, c01_s03, c03_s03, c04_s03, c06_s03, c08_s03, c09_s03, c10_s03, c01_s04, c03_s04, c06_s04, c08_s04, c10_s04 |
Wspólne ważne pary: 48/48. Liczby do drabiny (W0/W2/W1′/W4) liczy ANEKS_LIQ-2 — ten raport
ich nie interpretuje.

**Prowieniencja:** każdy manifest 1. klasy (controller_sha net `e8c1b658…`/gru `6d72437f…`,
weights_sha ncp `0337d5ea…`/gru `5ec02755…`, world_hash A3 `adc91803…` [kampania] /
wind_s0 `921bdda7…`=FREEZE_W [sonda], trace, ulog_sha, arm_monitor=True, KIND=liq).
Driver kampanii sha `43b8d2dd…` BEZ ZMIAN od S2; launcher sondy `7324f850…` BEZ ZMIAN od S1;
kod repo nietknięty (dotykane wyłącznie `results/LIQ/**` + transientny lock nogi W).

**Commit sesji:** booty rund 7–12 + sonda + ten raport (ulogi poza repo per gitignore
`results/**/*.ulg`, 14 szt. na dysku, sha w manifestach). Porcelain po commicie: PUSTY
(zweryfikowane wykonaniem przy STOP). Push = Olga. **Po STOP-LIQ3 lotów w tej nodze NIE MA.**
Dalej: ANEKS_LIQ-2 (werdykt drabiny na komplecie 48 par, rozstrzygnięcie sondy, kanon
roszczeń, KSIĘGA, zlecenie CO-LIQ). STOP-LIQ3.
