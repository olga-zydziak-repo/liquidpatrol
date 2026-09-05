# RAPORT diag F0 — booty smoke kontrolera sieci → STOP-F0 (PROMPT_NET_FLY F1)

LiquidPatrol · pozycja 4 · CC 5.09.2026 · świat world_demo_A3 · commity N-F0 `7593c48`·`891f4c1` · N-F1 `0f984dc` · driver `7a05df5` · boot0n `4034811` · boot0m `035a87a` (niepushowane, push=Olga)

## §1. Bramka techniczna (F1 — jedyna bramka bootów diag; sukces D6 NIE jest bramką)

| boot | arm | kind | rc | controller | n_ep | stub/null | weights_sha == FREEZE_NET | zero crash |
|---|---|---|---|---|---|---|---|---|
| boot-0n | ncp | diag | 0 | net | 4 | brak/brak | `0337d5ea…` ✓ | tak |
| boot-0m | mlp | diag | 0 | net | 4 | brak/brak | `1d190023…` ✓ | tak |

**Obie bramki techniczne PASS.** Manifest 1. klasy (bench_finalize, bez stubu/null), weights_sha wstrzyknięty przez driver (net_controller ODMÓWIŁBY lotu przy rozjeździe wag — przelot 4 ep dowodzi zgodności z FREEZE_NET), 4 epizody przelecane, sekwencje faz + reset stanu per epizod (4× episode_start), zero crashy. controller_sha `e8c1b658` (net_controller.py).

## §2. Smoke (obserwacja, NIE bramka — 4 ep ziaren shakeout c00/c05/c10/c11 s01)

### boot-0n (NCP) — 4/4 D6, czysto
| ep | D6 | frac[6,10] | d_min | REFUSE | breach |
|---|---|---|---|---|---|
| c00_s01 | ✓ | 1.000 | 7.818 | 0 | False |
| c05_s01 | ✓ | 1.000 | 6.442 | 0 | False |
| c10_s01 | ✓ | 0.944 | 5.950 | 0 | False |
| c11_s01 | ✓ | 0.899 | 5.605 | 0 | False |

### boot-0m (MLP) — 1/4 D6
| ep | D6 | frac[6,10] | d_min | REFUSE | breach |
|---|---|---|---|---|---|
| c00_s01 | ✗ | 0.925 | 5.459 | 0 | False |
| c05_s01 | ✗ | 0.871 | 4.988 | 0 | False |
| c10_s01 | ✓ | 0.931 | 6.463 | 0 | False |
| c11_s01 | ✗ | 0.735 | 3.613 | 0 | False |

**Zero REFUSE, zero breach w obu bootach.** (c11_s01 MLP d_min=3.613<4 = porażka D6(d) separacji od intruza; osłona chroni R_E=32, NIE separację — słusznie brak REFUSE/breach.)

## §3. ZNALEZISKO do CC: luka model-punktowy ↔ SITL (MLP)

MLP w rollout offline (N3(i), model punktowy FEED-B) = **21/24 PASS**; MLP live SITL smoke = **1/4** na ziarnach shakeout (frac niżej, d_min ciaśniej). NCP offline 24/24 → live smoke 4/4 (spójny). **Model punktowy zawyżał MLP** — nie oddaje dynamiki SITL (EKF/offboard/opóźnienia/RTF), na którą MLP (okno k=5, bez pamięci ciągłej) jest wrażliwszy niż NCP (stan ciągły). To smoke (4 ep, nie pomiar), ale **prognozuje, że MLP może nie osiągnąć progu ≥40/48 w locie** mimo PASS offline. NCP wygląda solidniej live.

**To NIE zmienia niczego w tej sesji** (bramka diag = techniczna, obie PASS). Nota dla CC: kampania kryterialna F2 zmierzy to wprost; próg ≥40/48 pozostaje; jeśli MLP padnie w locie mimo offline-PASS, to wynik tezy (offline-gate nie gwarantuje lotu — analog D6 na modelu punktowym jest optymistyczny), raportowalny.

## §4. Fakt D0(b) — mechanizm ograniczenia r w osłonie (dla CC)

Aktywna bramka r = **R-G GEOFENCE** (`r01/shield.py:101-110`): REFUSE(GEOFENCE) gdy `radial(target)>R_E` (l.105-106) LUB `radial(pos)+v²/2·a_brake>R_E` (l.108-109, bariera P2) LUB pion>V_E. R_E=32 m, a_brake=2.0, v_max=3.0. NIE „tylko zasięg+clip_v" — aktywna bramka celu i hamowania. Pełny D0: `results/NET/FLY/D0.md`.

## §5. STOP-F0 — czeka na ratyfikację CC (ANEKS_NET-3)

Build lotu domknięty (N-F0/N-F1, 64 pytest PASS, frozen+FREEZE_NET bajt-identyczne), oba booty diag przeszły bramkę techniczną, zero SITL poza 2 diagami, drivery wersjonowane w repo. **Nie wchodzę na kampanię kryterialną (F2) bez ratyfikacji CC** (PROMPT F1: STOP-F0 przed lotami kryterialnymi).

Do decyzji CC: (1) ratyfikacja STOP-F0 → GO na F2 (48+48 kryterialne, przeplot, próg ≥40/48); (2) czy znalezisko §3 (luka offline↔SITL, MLP prawdopodobnie słabszy) zmienia cokolwiek w protokole F2 — czy oba ramiona lecą pełne 48 mimo prognozy (rekomendacja: TAK, to jest właśnie pomiar tezy). Wykonawca po STOP: nic. Olga: push {N-F0/fix/D0, N-F1, driver, boot0n, boot0m}.
