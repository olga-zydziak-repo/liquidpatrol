# RAPORT_LIQ_S2 — smoke lotny GRU + kampania rundy 1–6 (NCP vs GRU) → STOP-LIQ2

LiquidPatrol · CC · 02.10.2026 · PROMPT_LIQ_S2 · ANEKS_LIQ-1 ratyfikowany (ARCH commit 5551219,
sha256 kopii `73481492cd6595e2…` — byte-identyczna z dostarczoną). Raport = liczby; werdykt drabiny
należy do aneksu zamykającego (ANEKS_LIQ-1 §6).

## §0. Bramka wejścia (wykonaniem, przed czymkolwiek)

origin/master = `de6e855` ✓ · `origin/master..HEAD` puste ✓ · porcelain pełny pusty (REPO-1) ✓.
Piny 5/5 (`check_shield_frozen=True`: shield.py, config.py, gate_run_r03.py, base.py,
safe_descend.py) · certy 9/9 (`certs_selfcheck` PASS) · sha 5/5: bench_judge `8ec0fcfb` ✓,
features `9adc1505` ✓, ncp.npz `0337d5ea` ✓, gru.npz `5ec02755` ✓, mlp20.npz `74b5ae7d` ✓
(mlp20 nie lata — tożsamość wyniku). Host przed kampanią: load1 0.04, 24 rdzenie, 29 GB wolne.

## §1. Ramiona i tor (ścieżki DOKŁADNE)

- **NCP:** `CONTROLLER=net NET_ARM=ncp`, wagi `0337d5ea` — ścieżka F2 bez jednej zmiany.
- **GRU:** `CONTROLLER=gru`, wagi `5ec02755` (guard FREEZE_SHA_LIQ aktywny; rozjazd sha ⇒
  RuntimeError ODMOWA LOTU, SR-2).
- MLP-k20 NIE lata (ANEKS_LIQ-1 §2).

Tor: `harness/run_boot.sh` FLIGHT=bench, WORLD=world_demo_A3, model stock (B1_MODEL
x500_mono_cam_0), feed emulowany (FeedB), INTRUDER=1, FILM=0, KIND=liq, pełne uzbrojenie
domyślne ławki (bez K2_LEGACY_UNARMED; `k2_arm_monitor=true` w meta trace, echo do manifestu).
Scenariusze: `results/BENCH/scenario_manifest.json` blok 1 (48 epizodów = 12 komórek × ziarna
s01–s04, porządek manifestu F2 = episode_id 0–47). Sędzia: bench_judge `8ec0fcfb` przez
`campaign_analyze` (D9=V2′: longest_stall≤1.5 s ∧ Δsim/Δwall≥0.90 ∧ timejump=0; liczba deep
niebramkująca). Kolejki per ramię: `results/LIQ/camp/queue_{ncp,gru}.json`
(campaign_queue init block 1). OUTDIR per boot pod `results/LIQ/camp/` (REPO-2: driver
odmawia bootu w katalog z istniejącym manifest.json). Cooldown ≥300 s (results/.last_boot_end),
sustained CLEAN 3×30 s (proc_gate) przed każdym bootem.

## §2. Mapa rund (deterministyczna, wypisana PRZED pierwszym lotem)

Blok rundy r = scenariusze 4(r−1)+1…4r w porządku manifestu F2 (episode_id 4(r−1)…4r−1).
Kolejność ramion: rundy nieparzyste NCP→GRU, parzyste GRU→NCP. S2 = rundy 1–6; rundy 7–12 w S3.

| runda | episode_id | scenariusze | kolejność ramion |
|---|---|---|---|
| 1 | 0–3 | c00_s01 c01_s01 c02_s01 c03_s01 | NCP→GRU |
| 2 | 4–7 | c04_s01 c05_s01 c06_s01 c07_s01 | GRU→NCP |
| 3 | 8–11 | c08_s01 c09_s01 c10_s01 c11_s01 | NCP→GRU |
| 4 | 12–15 | c00_s02 c01_s02 c02_s02 c03_s02 | GRU→NCP |
| 5 | 16–19 | c04_s02 c05_s02 c06_s02 c07_s02 | NCP→GRU |
| 6 | 20–23 | c08_s02 c09_s02 c10_s02 c11_s02 | GRU→NCP |
| (7–12, S3) | 24–47 | c00_s03…c11_s04 analogicznie | kontynuacja parzystości |

Nazwy bootów: `r<runda>_<ramię>` (powtórka: sufiks `r`), smoke: `smoke_gru`.

## §3. Smoke lotny GRU (1 boot, NIEKRYTERIALNY — wynik nie wchodzi do Δ)

Boot `smoke_gru` (BOOT_N=0, c11_s01, BENCH_EPISODE_IDS=11, KIND=liq), rc=0, finalize=0.
Kryterium smoke — **3/3 spełnione**:
1. **V2′ VALID**: longest_stall 0.0 s (≤1.5) ∧ Δsim/Δwall 0.9904 (≥0.90) ∧ timejump 0 (pre 0/post 0).
2. **Faza orbit osiągnięta**: fazy approach 106 / hold 13 / orbit 1306 ticków; t_entry 2.096 s.
3. **Zero wyjątków kontrolera/guardu**: act.log grep traceback/exception/RuntimeError/ODMOWA = 0.

Liczby lotu (sędzia 8ec0fcfb przez V2′): D6=True, frac[6,10]=0.9209, d_min=6.926 m,
dorb=6.926 m, n_deep=2 (niebramkujące), REFUSE=0, breach=False, z_max=14.56 m.
Prowieniencja: weights_sha `5ec02755…` (guard SR-2 przeszedł = zgodność z FREEZE_LIQ),
controller_sha `6d72437f…`, world_hash A3 `adc91803…`, arm_monitor=True, model_in_state=True.

**Zestawienie offline (S1 replay feedu D6 c11_s01) ↔ lot (ten boot):** offline 1378 ticków,
wyjścia skończone 1378/1378, |v|max=3.000, fazy approach→orbit; lot 1425 ticków epizodu,
|cmd_v|max=3.000, fazy approach→hold→orbit, D6 PASS. Zero wyjątków w obu torach.
(c11_s01 poleci normalnie w swojej rundzie — runda 3; smoke poza Δ.)

## §4. Rundy 1–6 — wpisy płaskie (per boot, per epizod)

Format: per epizod werdykt sędziego (D6) PASS/FAIL · ważność V2′ · z_max [m] · t_entry [s] ·
REFUSE (licznik; gałąź przy niezerowym) · V2′-składowe (dsw = Δsim/Δwall, longest stall, timejump)
+ d_min. Wszystkie booty: rc=0, finalize=0, breach_ev w trace = 0, chyba że zaznaczono.

### Runda 1 (c00–c03_s01) — NCP→GRU

**Boot r1_ncp (BOOT_N=1, ramię NCP):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c00_s01 | PASS | VALID | 13.13 | 2.884 | 0 | dsw 0.9957 · longest 0.0 s · tj 0 · d_min 7.726 |
| c01_s01 | PASS | VALID | 12.74 | 3.02 | 0 | dsw 1.0 · longest 0.0 s · tj 0 · d_min 7.584 |
| c02_s01 | PASS | VALID | 12.63 | 2.932 | 0 | dsw 0.9999 · longest 0.0 s · tj 0 · d_min 7.834 |
| c03_s01 | PASS | VALID | 12.59 | 3.052 | 0 | dsw 0.9999 · longest 0.0 s · tj 0 · d_min 7.683 |

**Boot r1_gru (BOOT_N=2, ramię GRU):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c00_s01 | PASS | VALID | 13.31 | 2.936 | 0 | dsw 0.9905 · longest 0.0 s · tj 0 · d_min 7.543 |
| c01_s01 | PASS | VALID | 13.33 | 3.368 | 0 | dsw 0.9999 · longest 0.0 s · tj 0 · d_min 7.711 |
| c02_s01 | PASS | VALID | 14.05 | 2.956 | 0 | dsw 0.9998 · longest 0.0 s · tj 0 · d_min 6.998 |
| c03_s01 | FAIL(c_sweep) | VALID | 14.44 | 3.292 | 0 | dsw 0.9999 · longest 0.0 s · tj 0 · d_min 7.364 |

### Runda 2 (c04–c07_s01) — GRU→NCP

**Boot r2_gru (BOOT_N=3, ramię GRU):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c04_s01 | FAIL(c_sweep) | VALID | 16.21 | 2.468 | 0 | dsw 0.9968 · longest 0.0 s · tj 0 · d_min 7.284 |
| c05_s01 | PASS | VALID | 14.13 | 2.932 | 0 | dsw 0.9998 · longest 0.0 s · tj 0 · d_min 6.881 |
| c06_s01 | PASS | VALID | 14.99 | 2.264 | 0 | dsw 0.9997 · longest 0.0 s · tj 0 · d_min 5.828 |
| c07_s01 | PASS | VALID | 14.18 | 0.06 | 0 | dsw 0.9997 · longest 0.0 s · tj 0 · d_min 7.071 |

**Boot r2_ncp (BOOT_N=4, ramię NCP):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c04_s01 | PASS | VALID | 12.76 | 2.388 | 0 | dsw 0.9959 · longest 0.0 s · tj 0 · d_min 6.78 |
| c05_s01 | PASS | VALID | 13.06 | 2.74 | 0 | dsw 0.9999 · longest 0.0 s · tj 0 · d_min 6.265 |
| c06_s01 | PASS | VALID | 12.97 | 0.0 | 0 | dsw 0.9999 · longest 0.0 s · tj 0 · d_min 6.062 |
| c07_s01 | PASS | VALID | 12.89 | 2.376 | 0 | dsw 0.9999 · longest 0.0 s · tj 0 · d_min 7.221 |

### Runda 3 (c08–c11_s01) — NCP→GRU

**Boot r3_ncp (BOOT_N=5, ramię NCP):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c08_s01 | PASS | VALID | 13.17 | 2.02 | 0 | dsw 0.9957 · longest 0.0 s · tj 0 · d_min 6.725 |
| c09_s01 | PASS | VALID | 13.39 | 1.876 | 0 | dsw 0.9998 · longest 0.0 s · tj 0 · d_min 6.498 |
| c10_s01 | PASS | VALID | 13.37 | 0.0 | 0 | dsw 1.0 · longest 0.0 s · tj 0 · d_min 6.408 |
| c11_s01 | PASS | VALID | 13.26 | 0.0 | 0 | dsw 0.9997 · longest 0.0 s · tj 0 · d_min 5.702 |

**Boot r3_gru (BOOT_N=6, ramię GRU):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c08_s01 | FAIL(c_sweep) | VALID | 16.79 | 1.968 | 0 | dsw 0.996 · longest 0.0 s · tj 0 · d_min 6.692 |
| c09_s01 | PASS | VALID | 15.37 | 1.936 | 0 | dsw 0.9998 · longest 0.0 s · tj 0 · d_min 5.984 |
| c10_s01 | FAIL(c_sweep) | VALID | 15.22 | 0.0 | 0 | dsw 0.9999 · longest 0.0 s · tj 0 · d_min 6.036 |
| c11_s01 | PASS | VALID | 16.3 | 2.2 | 0 | dsw 0.9999 · longest 0.0 s · tj 0 · d_min 6.992 |

### Runda 4 (c00–c03_s02) — GRU→NCP

**Boot r4_gru (BOOT_N=7, ramię GRU):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c00_s02 | PASS | VALID | 15.13 | 3.064 | 0 | dsw 0.9958 · longest 0.0 s · tj 0 · d_min 7.292 |
| c01_s02 | PASS | VALID | 14.09 | 2.676 | 0 | dsw 1.0 · longest 0.0 s · tj 0 · d_min 7.332 |
| c02_s02 | PASS | VALID | 13.43 | 2.956 | 0 | dsw 0.9998 · longest 0.0 s · tj 0 · d_min 7.231 |
| c03_s02 | FAIL(c_sweep) | VALID | 13.91 | 3.096 | 0 | dsw 0.9998 · longest 0.0 s · tj 0 · d_min 7.279 |

**Boot r4_ncp (BOOT_N=8, ramię NCP):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c00_s02 | PASS | VALID | 12.69 | 2.944 | 0 | dsw 0.9971 · longest 0.0 s · tj 0 · d_min 7.536 |
| c01_s02 | PASS | VALID | 13.28 | 2.924 | 0 | dsw 1.0 · longest 0.0 s · tj 0 · d_min 7.658 |
| c02_s02 | PASS | VALID | 12.91 | 2.792 | 0 | dsw 0.9999 · longest 0.0 s · tj 0 · d_min 7.84 |
| c03_s02 | PASS | VALID | 12.45 | 2.852 | 0 | dsw 1.0 · longest 0.0 s · tj 0 · d_min 7.938 |

### Runda 5 (c04–c07_s02) — NCP→GRU

**Boot r5_ncp (BOOT_N=9, ramię NCP):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c04_s02 | PASS | VALID | 13.4 | 2.376 | 0 | dsw 0.9959 · longest 0.0 s · tj 0 · d_min 7.177 |
| c05_s02 | PASS | VALID | 12.89 | 2.652 | 0 | dsw 0.9998 · longest 0.0 s · tj 0 · d_min 4.56 |
| c06_s02 | PASS | VALID | 12.52 | 2.132 | 0 | dsw 1.0 · longest 0.0 s · tj 0 · d_min 7.183 |
| c07_s02 | FAIL(d_dmin) | VALID | 12.78 | 2.316 | 0 | dsw 0.9998 · longest 0.0 s · tj 0 · d_min 3.907 |

**Boot r5_gru (BOOT_N=10, ramię GRU):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c04_s02 | PASS | VALID | 14.74 | 2.472 | 0 | dsw 0.9901 · longest 0.41 s · tj 0 · d_min 7.5 |
| c05_s02 | FAIL(c_sweep) | VALID | 14.13 | 0.06 | 0 | dsw 1.0 · longest 0.0 s · tj 0 · d_min 4.978 |
| c06_s02 | PASS | VALID | 13.65 | 2.276 | 0 | dsw 0.9999 · longest 0.0 s · tj 0 · d_min 7.001 |
| c07_s02 | FAIL(d_dmin) | VALID | 14.09 | 2.38 | 0 | dsw 0.9999 · longest 0.0 s · tj 0 · d_min 3.978 |

### Runda 6 (c08–c11_s02) — GRU→NCP

**Boot r6_gru (BOOT_N=11, ramię GRU):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c08_s02 | FAIL(c_sweep) | VALID | 15.58 | 2.048 | 0 | dsw 0.9958 · longest 0.0 s · tj 0 · d_min 6.729 |
| c09_s02 | FAIL(d_dmin) | VALID | 14.48 | 2.136 | 0 | dsw 0.9997 · longest 0.0 s · tj 0 · d_min 1.4 |
| c10_s02 | PASS | VALID | 14.01 | 1.896 | 0 | dsw 0.9998 · longest 0.0 s · tj 0 · d_min 7.208 |
| c11_s02 | PASS | VALID | 16.35 | 0.0 | 0 | dsw 0.9999 · longest 0.0 s · tj 0 · d_min 6.402 |

**Boot r6_ncp (BOOT_N=12, ramię NCP):** V2′ bootu: 4/4 VALID, timejump 0.
| scenariusz | sędzia | V2′ | z_max | t_entry | REFUSE | V2′-składowe |
|---|---|---|---|---|---|---|
| c08_s02 | PASS | VALID | 13.38 | 2.024 | 0 | dsw 0.9959 · longest 0.0 s · tj 0 · d_min 7.231 |
| c09_s02 | FAIL(d_dmin) | VALID | 13.66 | 2.08 | 0 | dsw 1.0 · longest 0.0 s · tj 0 · d_min 1.221 |
| c10_s02 | PASS | VALID | 13.77 | 1.856 | 0 | dsw 1.0 · longest 0.0 s · tj 0 · d_min 6.902 |
| c11_s02 | FAIL(b_frac,d_dmin) | VALID | 13.1 | 0.0 | 0 | dsw 0.9998 · longest 0.0 s · tj 0 · d_min 1.257 |

## §5. Liczniki, budżet, higiena

**Ważność:** 12/12 bootów kryterialnych VALID za pierwszym podejściem (48/48 epizodów V2′
VALID; wszystkie timejump=0, longest_stall max 0.41 s, dsw min 0.9901). **Powtórki: 0/2**
(pula nietknięta). **Budżet sesji:** 1 smoke + 12 kryterialnych = 13 bootów (limit 1+12+≤2;
budżet nogi po S2: 13 z ≤31). Żaden blok nie wypadł parowo.

**REFUSE:** 0 we wszystkich 48 epizodach + smoke (ledger pusty; w szczególności zero
REFUSE(POS)). **Breach R_E:** 0 zdarzeń breach w trace wszystkich 13 bootów. Warunki STOP
twardego nie wystąpiły. Wyjątki kontrolera/guardu w act.log: 0 we wszystkich bootach.

**Zliczenia płaskie sędziego D6 (pierwsza ważna próba; werdykt drabiny = aneks zamykający po
rundach 7–12):** NCP 21/24 PASS (FAIL: c07_s02 d_dmin · c09_s02 d_dmin · c11_s02 b_frac,d_dmin);
GRU 15/24 PASS (FAIL: c03_s01 · c04_s01 · c08_s01 · c10_s01 · c03_s02 · c05_s02 · c08_s02 —
wszystkie c_sweep; c07_s02 d_dmin · c09_s02 d_dmin). Wspólne ważne: 24/24 par (komplet).
Kolejki po S2: done 24 / pending 24 per ramię (rundy 7–12 = S3).

**Prowieniencja (każdy manifest):** controller_sha (net `e8c1b658…` / gru `6d72437f…`),
weights_sha (ncp `0337d5ea…` / gru `5ec02755…`), world_hash A3 `adc91803…` (kind=repo),
trace+ulog_sha obecne, arm_monitor=True (bez LEGACY), model_in_state=True, KIND=liq.
Driver: `results/LIQ/camp/run_liq_boot.sh` (wzór run_fly_boot.sh; REPO-2 odmowa przy
istniejącym manifest.json; zero edycji kodu nogi — lista zamknięta §0.4 dotrzymana).

**Commity sesji:** (1) `5551219` ANEKS_LIQ-1 verbatim; (2) booty `results/LIQ/camp/**`
+ ten raport (boot.ulg poza repo: gitignore `results/**/*.ulg` z porządku REPO, 13 szt. na
dysku, sha każdego w manifeście jako ulog_sha). Porcelain po commicie 2: PUSTY (zweryfikowane
wykonaniem przy STOP); żadnych obcych M. Push = Olga. Czeka: **PROMPT_LIQ_S3** (rundy 7–12 + sonda STOCK na progach
ANEKS_LIQ-1 §3). STOP-LIQ2.
