# RAPORT_KONT_S1 — sonda nogi 2d, STOP-KONT1

LiquidPatrol · 6.11.2026 · PRE_KONT sha 57d899f2 (`c3d12087`), budowa `56a2695e`. Booty **2/3** (A, B; rezerwa C nieużyta). Breach 0, REFUSE(POS) 0.

## Werdykt S1 (PRE §4): **PASS**

| Warunek | Próg | Wynik | |
|---|---|---|---|
| (i) identyczność klatek mono_cam | T ≤ K w każdej pozie | T = K = 0 w 8/8 póz | PASS |
| (ii) xy_valid, brak nav 14→12 | ≥ 70 s orbity po odcięciu, z ulogu | 72.01 s sim; xy_valid min 1; nav 14 do 233.656 (po przyziemieniu GT) | PASS |
| (iii) cs_gnss_pos | ≤ 0.5 s; 0 przeskoków w nominale | 0.02 s; 0 przeskoków | PASS |
| (iv) kadencja OPS | ≥ 10 Hz | preflight 14.71 Hz, lot 14.71 Hz, próg FROZEN 8df528bb też PASS | PASS |

**Dwa znaleziska poza literą bramki, do decyzji CC przed S2:**

1. **Bias wysokości 1.8 m, już w nominale.** GT z p50 13.77 m przy EKF 11.99 m przed odcięciem (w oknie 13.80 / 12.00); dalmierz 13.94, czyli zgodny z GT. W K2, bez dalmierza, p90 GT/EKF to 12.35/12.50 i 12.03/12.24 (b1, b6). Dron lata więc ok. 1.8 m wyżej, niż sądzi, na tym modelu i tych parametrach. `cs_rng_hgt` gaśnie przy 100.596 s. [MECHANIZM NIEZMIERZONY]. Dotyczy to O8 i geometrii kamery w S4 (kąt do intruza na z = 10 m).
2. **Bramka instrumentu gt_judge nie przeszła:** `healthy_valid=false`, p95 ε w oknie zdrowym 0.119 m przy progu 0.10 (K2, ten sam kod: 0.055–0.100). T_home policzone, ε(t) poniżej niesie tę niepewność.

## (i) Boot A: tabela identyczności

`bootA/frames_identity.json`, PNG bezstratne w `frames/`; przeliczenie bez bootu: `kont_frames.py --compare`.
R1, R2 = x500_mono_cam (pin) na A3; T = x500_mono_cam_flow (maska) na world_kont_A3; N = kontrola negatywna, x500_mono_cam bez maski na world_kont_A3. Klatka wewnątrz przebiegu: 5 kolejnych, różnica 0 we wszystkich.

| Poza | K max | K n≠0 | T max | T n≠0 | N max | N n≠0 | std flow |
|---|---|---|---|---|---|---|---|
| p1 środek z10 | 0 | 0 | 0 | 0 | 99 | 85206 | 37.6 |
| p2 r20 na zewnątrz | 0 | 0 | 0 | 0 | 94 | 26305 | 31.3 |
| p3 r20 do środka | 0 | 0 | 0 | 0 | 95 | 90977 | 31.5 |
| p4 r30 na zewnątrz | 0 | 0 | 0 | 0 | 93 | 10682 | 42.3 |
| p5 r30 do środka | 0 | 0 | 0 | 0 | 95 | 94897 | 42.4 |
| p6 r10 pochylenie 15° | 0 | 0 | 0 | 0 | 95 | 104455 | 37.6 |
| p7 z5 | 0 | 0 | 0 | 0 | 95 | 109790 | 42.7 |
| p8 r30 pochylenie 15° | 0 | 0 | 0 | 0 | 95 | 30256 | 38.6 |

Kontrola N dowodzi czułości testu: bez maski dekal zmienia kadr. Kamera przepływu widzi szachownicę (`frames/flow_*.png`). Granica: statyczny model na pozie, bez intruza; pozy nie obejmują śmigieł w ruchu.

## Boot B: lot

Scenariusz `c08_s02` (najmniejszy margines R4, m = 2.99), nauczyciel orbit_executor, FeedB. t_entry 2.02 s, odcięcie sim 147.712 (t_entry + 30, r_GT 22.14 m, poza R_route′ 19.90), koniec okna 219.724 (`koniec_okna`), przyziemienie GT 233.632 (z 0.107 m, r_GT 17.30). r_GT max 23.86 m; bezpiecznik 29 m nie zadziałał. V2′ dsim/dwall **0.9105** (próg 0.90, blisko). Zegar: próbniki 0 skoków, `bootB/zegar2.jsonl` 0 skoków, timesyncd zatrzymany na sesję i przywrócony. Certs_selfcheck 9/9 po sesji, piny bez zmian.

Czas ulogu = czas gz (arming 91.456 vs 91.46). **Stempel `t_px4` w zdarzeniu `cut` jest w bazie DDS, nie ulogu (1793924297), wbrew nagłówkowi `kont_probe.py`.** Nieużywany: odniesienie to sim z `t_rel` sprzed `set_param`.

### (ii) Pozycja lokalna
Wyciąg: `ulog_wyciag_bootB.jsonl`, przejścia nav :1,:35,:67,:739,:740,:747; podsumowanie w ostatnim wierszu; liczby w `s1_wyniki.json` → `ii`.
- xy_valid, v_xy_valid: bez spadku od 1.66 s do końca (:7,:19). dead_reckoning 0 w całym oknie. failsafe 0 przez cały boot. `t_offboard_lost` +86.93 s i nav→4 +85.94 s to już po przyziemieniu GT i `offboard.stop`.
- Aiding: `cs_opt_flow` bez przerwy od 1.93 s. Fuzja 48.4 Hz, frakcja 0.9672 w oknie i 0.9673 w nominale; odrzucone 3.3 %; **najdłuższa luka 0.152 s, 0 luk > 0.2 s**.
- Jakość flow: p50 251.5, min 128, 0 próbek zerowych (EKF2_OF_QMIN = 1). Dalmierz 13.07–14.62 m.
- Osłona bierna: ALLOW przez cały lot (`bootB/trace.jsonl:3191`), jedyne zdarzenie. **Pod przepływem dzisiejsza flaga POS nie odpala**, potwierdzone (blocker O0).

### (iii) Flaga utraty
`cs_gnss_pos` (`ulog_wyciag_bootB.jsonl`:11,:32,:292): 1 od 2.988 s, 0 przy 147.732 s, opóźnienie 0.02 s od chwili przed `set_param`. Przeskoki w nominale: 0 przez 144.7 s. **Prompt wymaga ≥ 60 s nominału: spełnione z ziemią, w powietrzu było 54.4 s** (planowałem ≥ 60, za krótki zawis).

### (iv) Kadencja
Sonda 8df528bb preflight: 14.71 Hz, frac>0.10 = 0, PASS FROZEN. Lot arm→przyziemienie: dt_p50 0.068, max 0.068, frac 0, n = 2153. Po odcięciu 15.15 Hz. Domyślne 50 Hz flow wystarczyło, Boot C niepotrzebny.

### (v) Opisowo: ε(t) z jednego lotu, bez wniosków o ε_b

ε [m] od odcięcia, sekundy sim (`s1_wyniki.json` → `v.eps.krzywa_1s_sim`, gt_judge 447efaa2):

| t | 1 | 2 | 4 | 5 | 10 | 15 | 20 | 30 | 40 | 50 | 60 | 70 | 72 | 75 | 80 | 85 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ε | 0.10 | 0.07 | 0.20 | 0.43 | 1.59 | 1.69 | 2.19 | 0.53 | 1.94 | 3.43 | 4.70 | 6.50 | 7.09 | 8.74 | 8.72 | 8.93 |

Krzywa niemonotoniczna (spadek 2.19→0.53 przy 20–30 s). Przyrost ε w zejściu od 7.09: **Δ = 1.86 m** w 14 s sim. Maks. |r_GT − r_est| po odcięciu 6.71 m. Droga pozioma w oknie: EKF 169.8 m, GT 149.5 m (ratio 1.136; 20 s nominału przed odcięciem 0.993), opisowo, bez mechanizmu.

- **Nominał względem GT:** p95 poziomo 0.119 m (K2 0.055–0.100), inne loty i scenariusze, więc porównanie tylko orientacyjne. Pion: znalezisko 1.
- **Cień drona w klatkach flow: NIEZMIERZONY w locie.** Klatek flow w locie nie nagrywałem, są tylko statyczne z Bootu A. Pośrednio: jakość i odrzucenia bez zmian po odcięciu.
- **Artefakt przyrządu:** FeedB podaje intruza z GT, więc pod dryfem rel = GT − EKF nie znosi dryfu, inaczej niż det_v2. Orbita nauczyciela goni pozycję absolutną, a ε wpływa na tor. Do uwzględnienia przy S2.

## Odstępstwa od litery promptu

1. **Maska:** `action="modify"` odrzucone przez sdformat14 (Error Code 8, element nieobecny w pinie), użyte `action="replace"` z kopią czujnika. `gz sdf -p`: jedyna różnica czujnika wobec x500_mono_cam to `<visibility_mask>`.
2. **Świat:** poza dekalem zmieniona nazwa świata na world_kont_A3 (PX4 czeka na `/world/<PX4_GZ_WORLD>`). Płyta 72×72 m (superset koła R ≤ 36). Szachownica bok 1 m z odcieniami z ziarna w dwóch klasach.
3. **`kont_boot.sh`:** ponad wymienione zmiany także B1_MODEL, gałąź `kont_probe`, pkill, finalize. `kont_boot_vs_run_boot.diff`.
4. **Sonda:** bramka uzbrojenia = podłoga PRE 10 Hz, werdykt FROZEN obok. Oba PASS, rozstrzygnięcie niepotrzebne.
5. **Dodatkowo:** kontrola negatywna N w Boot A; bierna osłona i zawis 15 s w `kont_probe.py`; narzędzia `kont_gen_world.py`, `kont_s1_boot.sh`, `kont_s1_analyze.py`.
6. **Masa** +0.071 kg wobec x500_mono_cam (kopia z x500_flow).
7. **Boot A** to cztery serwery gz w jednym biegu, liczone jako jeden boot.

## Predykcje

- **P-KONT-1 (0.50): TAK.** Maska działa, klatki identyczne.
- **P-KONT-2 (0.65): TAK.** Aiding ≥ 70 s, brak nav 14→12. Jeden lot.

## Manifesty i odtworzenie

`manifest_budowa.json` (sha źródeł z submodułu, bramka FROZEN, kopie w `zrodla/`), `bootB/manifest.json` (echo parametrów, sonda, zegar, ulog_sha 5ec9ee0b), `bootB/kont_echo.json`. `.ulg` poza gitem, stąd wyciąg.
`export PYTHONDONTWRITEBYTECODE=1; python3 results/KONT/tools/kont_frames.py --compare; python3 results/KONT/tools/kont_s1_analyze.py; python3 results/KONT/tools/tests_kont_tools.py` (druga i trzecia komenda wymagają ulogów na dysku).

Push = Olga. STOP.
