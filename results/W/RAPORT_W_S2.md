RAPORT_W_S2 — sesja S2 nogi W: R-NC + kampania W-B 16/18 → STOP-W2 (S2-C: REFUSE R-G na L3/net_s02)
====================================================================================================
CC · 29.09.2026 · PROMPT_W_S2 · autoryzacje: ANEKS_W-1 + ANEKS_W-1b (errata route→orbit).
Hashe (§0.1, linia pierwsza): S1 [CB] `2529c5a0b9060653f311f79793d70bb71ed1111d` ·
S1 [CW-A] `d7663100879ea7283ad9bd645ce2d1ba2dd79438` · C-F `c1fb143deabe51344890536d8eb57a30c91df88d` ·
STOP-crash `39bf7b7c24acc907ece290a9cdef85bdd0981fa2` · ARCH-1b `2803aad8985e48ce83761d012d4ea2f16a370e57`.


§0. Przebieg sesji i podstawy formalne
--------------------------------------
1. 20–21.09 (sesja urwana): C-F FREEZE_W `c1fb143deabe51344890536d8eb57a30c91df88d`;
   boot-0 R-NC z literalnym `CONTROLLER=route` → crash przyrządu PRZED armem (TypeError
   fabryki). Raport crashu + ślad: commit `39bf7b7` (wersja tego pliku z 28.09, verbatim
   w historii git) — kategoria „crash przyrządu", POZA budżetem (ANEKS_W-1b §3).
2. 28.09: ANEKS_W-1b (errata: „route-executor"≡`CONTROLLER=orbit`; crash nie liczy się do
   budżetu ani do licznika R-NC). ARCH-1: `ANEKS_W-1b.md` commit `2803aad`. Push `39bf7b7`
   na origin potwierdzony PRZED kontynuacją. Sha egzekutora zweryfikowane:
   orbit_executor.py `840514361e4ae5e93ddbb0dd31a7dae81832805b90abccc334d84bbd043730d4`,
   executor_params.json (plik) `12c14adb83efc762e2b2c8f3119d747bdcac5ae865250e9be7ed4a7c40844d9c`
   (w manifestach pole exec_params_sha = sha kanonicznego JSON `5a724499…` — obie tożsamości
   spójne, jak w całej historii ławki).
3. FREEZE_W: 11/11 sha zgodnych z drzewem (weryfikacja 28.09). Zero zmian kodu w S2 (S2-A);
   jedyne commity = dokumenty + wyniki.
4. Wyłączność: każdy boot przez w_launcher (lock+pgrep+guard OUTDIR), zero kolizji,
   cooldowny ≥300 s trzymane (wbudowane przed każdym startem). Host po sesji czysty
   (pgrep gz/px4/agent pusty).


§1. R-NC boot-0 (diag @3.0, `camp/diag_boot0_r`) — GAŁĄŹ (a)
------------------------------------------------------------
c11_s01 (episode_id 11), CONTROLLER=orbit, W_ARM_ALWAYS=1, world_wind_s3, kind=diag.
- **Wznoszenie z ziemi: TAK** — z_max GT = 12.05 m (NO-CLIMB z W-A był artefaktem modułu
  infra1, nie wiatru; pętla ławki wznosi i lata @3.0 normalnie).
- **Wejście w pasmo wg bench_judge: TAK** — t_entry = 17.34 s; frac[6,10] = 0.684.
- **Habitat V2′: VALID** (dsim_dwall 0.9381 ≥ 0.90, longest_stall 0.0, timejump 0).
- REFUSE 0, breach false, dr_any False.
⇒ Siatka pełna: {0, 1.5, 3.0} × {orbit, net} × {s01,s02,s03} = 18 bootów. Kontynuacja
automatyczna (jedno podejście, licznik R-NC 1/2).


§2. Kampania kryterialna — tabela per epizod (16 bootów wykonanych, STOP po 16.)
--------------------------------------------------------------------------------
Kolejność literalna: poziomy rosnąco, przeplot ramion per ziarno. Wiatr ENU +x.
Kolumny: valid V2′ (dsw) · t_entry · frac[6,10] · d_min approach [m] · r_max [m] (margines
do R_E=32) · eps_cap_used [m z 9.25] · vmax GT [m/s] (V_ENV=6.0, flaga przekr.) · z_max GT
[m] · dr_any · REFUSE.

| boot | V2′(dsw) | t_e | frac | d_min | r_max(marg) | eps | vGT | z_max | dr | REF |
|------|----------|------|-------|-------|--------------|------|------|-------|----|-----|
| L0/orbit_s01   | VALID(.960) | 16.69 | 0.698 | 6.07 | 23.43 (8.57) | 0.68 | 3.43 | 11.77 | F | 0 |
| L0/net_s01     | VALID(.951) | 14.56 | 0.844 | 6.98 | 25.21 (6.79) | 2.46 | 2.37 | 18.45 | F | 0 |
| L0/orbit_s02   | VALID(.948) | 13.94 | 0.769 | 3.55 | 19.39 (12.61)| 0.00 | 2.46 | 12.40 | F | 0 |
| L0/net_s02     | VALID(.944) | 13.99 | 0.899 | 5.64 | 20.52 (11.48)| 0.00 | 2.24 | 13.88 | F | 0 |
| L0/orbit_s03   | VALID(.937) | 14.27 | 0.815 | 4.17 | 24.89 (7.11) | 2.14 | 2.46 | 12.16 | F | 0 |
| L0/net_s03     | VALID(.938) |  9.17 | 0.831 | 6.41 | 17.38 (14.62)| 0.00 | 3.73 | 14.91 | F | 0 |
| L1p5/orbit_s01 | VALID(.911) | 14.46 | 0.797 | 1.27 | 25.40 (6.60) | 2.65 | 2.59 | 11.78 | F | 0 |
| L1p5/net_s01   | VALID(.938) | 14.40 | 0.886 | 1.70 | 25.12 (6.88) | 2.37 | 2.58 | 13.48 | F | 0 |
| L1p5/orbit_s02 | VALID(.939) | 14.38 | 0.756 | 4.78 | 18.90 (13.10)| 0.00 | 2.47 | 11.93 | F | 0 |
| L1p5/net_s02   | VALID(.938) | 14.34 | 0.877 | 6.65 | 20.89 (11.11)| 0.00 | 2.45 | 16.44 | F | 0 |
| L1p5/orbit_s03 | VALID(.938) | 14.38 | 0.835 | 3.84 | 25.23 (6.77) | 2.48 | 2.55 | 12.18 | F | 0 |
| L1p5/net_s03   | VALID(.936) | 14.31 | 0.833 | 3.42 | 25.12 (6.88) | 2.37 | 2.56 | 12.40 | F | 0 |
| L3/orbit_s01   | VALID(.939) | 14.86 | 0.786 | 1.18 | 25.35 (6.65) | 2.60 | 2.59 | 12.08 | F | 0 |
| L3/net_s01     | VALID(.908) | 14.64 | 0.845 | 1.86 | 25.51 (6.49) | 2.76 | 2.53 | 12.96 | F | 0 |
| L3/orbit_s02   | VALID(.939) | 14.68 | 0.771 | 4.68 | 18.39 (13.61)| 0.00 | 2.48 | 11.89 | F | 0 |
| **L3/net_s02** | VALID(.930) | 14.58 | 0.856 | 6.03 | 20.53 (11.47)| 0.00 | 2.70 | **19.77** | F | **1 GEOFENCE** |

NIEWYKONANE (STOP §3): L3/orbit_s03, L3/net_s03. Flaga vmax>V_ENV: 0/16. Breach R_E: 0/16.
Kadencja t_entry/frac/d_min z bench_judge (sędzia bazowy niezmieniony); w_judge tylko dokłada w_*.


§3. STOP S2-C — REFUSE na L3/net_s02: pełna klasyfikacja (główny pomiar nogi)
------------------------------------------------------------------------------
**Zdarzenie:** `ev=refuse, reason=GEOFENCE, r_est=19.98, sim=179.556` (t_rel=68.5 s epizodu,
tuż przed końcem T_orb=70); następnie protokołowy hover + episode_end + reset_done. Breach
R_E: NIE (r_max=20.53, margines 11.47 m). Trace/ulog/manifest komplet w
`results/W/camp/L3/net_s02/` (ulog_sha w manifeście; boot.ulg poza gitem per gitignore).

**Tor tripu (rekonstrukcja z osłony r01/shield.py:101-112 + stanu):** bariera R-G, gałąź
PIONOWA: EKF |z|=19.787 < V_E=20.0 w ticku tripu ⇒ zadziałała gałąź celu
`|target_z| > V_E` — NCP podał cel poniżej pułapu obwiedni (cmd_vz NED mediana −0.118 m/s
przez ostatnie 30 s = uporczywa komenda wznoszenia przy z≈19.8). Bariera zadziałała
PREWENCYJNIE, zanim pozycja przekroczyła obwiednię.

**Klasyfikacja (PRE_W §5 + liczby okna):** REFUSE **NIE jest z toru POS** —
dead_reckoning=False cały lot, w_judge n_refuse(POS)=0. Okno 1 s przed tripem (20 ticków,
metoda w_judge): |EKF−GT| poziom mediana **0.099 m** (max 0.108), pion mediana **0.024 m**
(max 0.026), eph 0.151. Estymator ZDROWY, stan realny ⇒ w nomenklaturze nogi to REFUSE
**PRAWDZIWY** (osłona zatrzymała RZECZYWISTE wyjście poza obwiednię pionową; mediana błędu
0.099 ≪ ε_false=2.0 — nawet gdyby liczyć regułą POS, nie byłby to fałszywy alarm toru
estymacji, tylko poprawna reakcja na stan).

**Mechanizm (z profilu GT):** z(t_rel) epizodu = 8.2 → 11.4 → 11.8 → 14.6 → 17.1 → 15.7 →
18.8 → trip 19.78 m — systematyczny CREEP WYSOKOŚCI ramienia net. Wzorzec z_max całej
kampanii: **orbit 11.77–12.40 m na wszystkich poziomach** (pion trzymany), **net 12.40–19.77 m
Z L0 WŁĄCZNIE** (18.45 m przy wietrze ZERO, L0/net_s01) ⇒ skłonność do luźnego pionu jest
WŁASNOŚCIĄ ramienia NCP (obecna bez wiatru), amplituda moduluje się per ziarno/poziom;
do obwiedni dobił dopiero L3/net_s02. To pomiar degradacji pod przesunięciem domeny
z zadziałaniem osłony — nie awaria przyrządu.

**Nota rc:** proces bench_flight zakończył się rc=134 („terminate called without an active
exception") PO linii `[bench] done` — artefakt teardownu C++ (gz/rclpy destruktor) po
domknięciu lotu i zapisów; finalize przebiegł, manifest 1. klasy istnieje. Nie wpływa na dane.


§4. Pary orbit↔net per (poziom, ziarno) — opisowo (zakaz języka istotności)
---------------------------------------------------------------------------
- frac[6,10]: net wyższy w 7/8 par (mediana net 0.850 vs orbit 0.786); wyjątek (1.5,s03)
  parytet 0.833 vs 0.835.
- r_max: pary zbieżne (Δ typ. <2 m); oba ramiona zawsze ≤25.51, margines ≥6.49 do R_E.
- d_min approach: wspólny wzorzec per ziarno (s01@1.5/3.0 blisko 1.2–1.9 m w OBU ramionach —
  własność geometrii ziarna, nie ramienia).
- pion: patrz §3 — jedyna wyraźna asymetria ramion (orbit trzyma ALT, net pełza w górę).
- t_entry: stabilne ~14–17 s wszędzie (wiatr nie opóźnia wejścia w pasmo).

Przechył (w_tilt, okno=cały ulog — trace ławki nie emituje eventów hoveru; porównawczo OK):
mediana per poziom: L0 2.14–3.85° · L1p5 8.08–9.90° · L3 9.69–12.79° — monotoniczny podpis
wiatru, parytet ramion. (boot-0 diag: 1.40 — dłuższy segment naziemny w ulogu rozcieńcza
medianę; nieporównywalny wprost.) p95: L0 12.6–17.3° · L1p5 18.7–21.9° · L3 25.7–29.0°.


§5. Statystyka habitatów (V2′)
------------------------------
17/17 bootów lotnych VALID: dsim_dwall min 0.908 / mediana 0.938 / max 0.960 (wszystkie
≥0.90), longest_stall 0.0 s wszędzie (n_deep_stall 0–3, niebramkujące per D9=V2′),
timejump 0. eph nominał ~0.151 wszędzie. ZERO env-fail, ZERO ponowień, ZERO kolizji.


§6. Uzupełnienie danych W-A (§0.5 — bez zmian od wersji 28.09, zweryfikowane źródłowo)
--------------------------------------------------------------------------------------
| boot | poziom | eph_max | Δsim/Δwall | min_rtf |
|------|--------|---------|------------|---------|
| 1 s0 | 0.0 | 0.1536 | 0.9437 | 0.0146 |
| 2 s1p5 | 1.5 | 0.1535 | 0.9353 | 0.0057 |
| 3 s3 | 3.0 | 0.1524 | 0.9364 | 0.0018 |
| 3b s3 | 3.0 retry | 0.1524 | 0.9581 | 0.0316 |
| 4 s4p5 | 4.5 | 0.1524 | 0.9875 | 0.0091 |
(ANEKS_W-1b §5: przyjęte; INVALID W-A dotyczyło progu 0.95 przyrządu W-A, niebramkujące.)


§7. Budżet i stan siatki
------------------------
Booty lotne S2: **17/27** (boot-0 + 16 kryterialnych; crash 20.09 poza budżetem per
ANEKS_W-1b §3, drugi crash nie wystąpił). Siatka: **16/18** — komplety L0 (6/6 VALID)
i L1p5 (6/6 VALID); L3: orbit 2/2 wykonanych VALID, net 2/2 wykonanych VALID (w tym s02
z REFUSE), s03 obu ramion NIEWYKONANE (STOP S2-C literalny: zero dalszych bootów po REFUSE).
Reguła ≥2/3 ważnych ziaren per komórka: L0×2 i L1p5×2 spełnione 3/3; L3×orbit i L3×net mają
po 2 ważne z 2 wykonanych — czy 2/3 przy nieodlecianym trzecim ziarnie wystarcza do werdyktu
komórki, rozstrzyga ANEKS_W-2 (nie przesądzam). Kanon REFUSE: ledger = 1 (GEOFENCE,
prawdziwy, L3/net/s02); tor POS przez całą kampanię CZYSTY (dr=False 17/17, 0 REFUSE(POS)).


§8. Higiena repo (REPO-1/S2-F) + hashe z git
--------------------------------------------
Hashe pełne w nagłówku (z `git log`). Porcelain przed commitem wyników: untracked
`results/W/camp/{L0,L1p5,L3, diag_boot0_r}` + launch logi + zmodyfikowany RAPORT_W_S2.md;
po commicie drzewo czyste (porcelain pusty — stan finalny w komunikacie sesji). Pliki
dotknięte: wyłącznie ANEKS_W-1b.md (ARCH-1) + results/W/** (lista zamknięta §0.4). ulogi
poza gitem (gitignore), tożsamość przez ulog_sha w manifestach. Push = Olga.

Ratyfikacja wróci jako **ANEKS_W-2** (werdykt nogi + kanon per PRE §14); sygnały bez
numeru odrzucam.
