# RECON_KONT — kontynuacja zadania po utracie GNSS (pozycja 2d), STOP-KONTR

LiquidPatrol · 4.11.2026 · sesja deskowa: **0 bootów, 0 SITL, 0 make, 0 edycji istniejących plików**.
Bramka §0: HEAD = origin/master = `8de41054`, `origin/master..HEAD` puste, porcelain bez zmian poza 26 nazwanymi `??`.

**Wynik płaski**

| | |
|---|---|
| **T_cont B** | literalnie p50 >12 s (f5, cenzura 48/48, po 4 s to już DESCEND); **efektywnie 4.0 s = ściana natywna PX4**; najgorszy 2.0 s (f4, m=2.99) |
| **Status A** | dostępna bez przebudowy i bez edycji źródeł/pinu; działanie niezweryfikowane (0 bootów); grunt A3 jednolity, wymaga nowego wariantu świata albo maski widoczności |
| **Werdykt** | warunek śmierci (A niedostępna ∧ p50 B <10 s) **niespełniony ⇒ PRE**; rekomendacja: PRE tylko na ścieżkę A, B sama się nie opłaca (§R7) |

Dwa znaleziska, których prompt nie przewidywał:

1. **Hipoteza „sekundy, nie minuty" potwierdzona, ale z innego powodu.** Budżet B obcina nie dryf, tylko PX4: 4.02–4.12 s po utracie `xy_valid=False` kasuje offboard velocity, nav 14→12 (DESCEND), failsafe=1, **12/12 K2**.
2. **Liczby długiego okna B1-bis nie opisują lotu.** „Prosta 125 s, 25.7 m" to 4 s lotu poleceniem, potem DESCEND i ok. 9.3 s do ziemi, a następnie 143 s na ziemi z zamrożoną estymatą.

---

## R1. Źródła pozycji bez GNSS

**Wersje:** PX4 `v1.16.2-dirty` (HEAD `54f0455f`; dirty = submoduły i untracked, bez zmian w źródłach EKF/commandera), submoduł `Tools/simulation/gz` `e05f4312` (dirty: pin mono_cam + światy). Gazebo Harmonic, gz-sim 8.14.0. OpenCV 4.6.0.

Sha8 cytowanych plików PX4: `offboardCheck.cpp` 36890c99, `ekf2/module.yaml` 500db22a, `ekf_helper.cpp` 6825076f, `GZBridge.cpp` b1b79452, `server.config` 60871c73, `params_optical_flow.yaml` d1333293, `params_range_finder.yaml` f9520395, `params_external_vision.yaml` e8546603, `x500_flow/model.sdf` 23dca391, `optical_flow/model.sdf` 2ddd3d57, `4021_gz_x500_flow` dd4b19ac, `4010_gz_x500_mono_cam` 25c62080.

| Element | Stan | Dowód |
|---|---|---|
| Model flow + dalmierz | jest: `x500_flow` | `Tools/simulation/gz/models/x500_flow/model.sdf`, `optical_flow/model.sdf`, `LW20` |
| Airframe | jest: `4021_gz_x500_flow` (wyłącza GPS, więc do denialu w locie nieprzydatny wprost) | `init.d-posix/airframes/4021_gz_x500_flow` |
| Plugin zbudowany | **tak**, linkuje OpenCV i libOpticalFlow | `build/px4_sitl_default/src/modules/simulation/gz_plugins/libOpticalFlowSystem.so` (sha8 43df8c4f, 5.08), `ldd` bez „not found" |
| Plugin ładowany | tak | `server.config:16`, `gz_env.sh:17,21` |
| Most gz→PX4 | tak, stale subskrybuje flow i lidar po nazwie modelu | `GZBridge.cpp:113-117` (lidar), `:147-148` (flow) |
| Parametry EKF2 | `EKF2_OF_CTRL` (dom. 1), `EKF2_RNG_CTRL` (dom. 1), `EKF2_HGT_REF` (0 baro, dom. 1), `EKF2_EV_CTRL` (dom. 0) | `params_optical_flow.yaml:5,10`, `params_range_finder.yaml:5,26`, `module.yaml:87`, `params_external_vision.yaml:5,16` |
| Odometria wizyjna | **hydraulika jest, VIO nie ma.** `x500_vision` to odometria GT z gz (`gz-sim-odometry-publisher-system`), czyli wyrocznia, nie VIO. W `ros2_ws/src` tylko `px4_msgs`; brak VINS/ORB-SLAM/rtabmap | `x500_vision/model.sdf`, `GZBridge.cpp:97-101,495` |

**Werdykt A: dostępna bez przebudowy i bez edycji źródeł PX4 ani pinu** (potwierdzenie działania = sonda, 0 bootów tutaj).

Lista addytywna A:
1. Nowy katalog `Tools/simulation/gz/models/x500_mono_cam_flow/model.sdf`: `include` `x500_mono_cam` (pin mono_cam nietknięty) + kopia `optical_flow` i sekcji lidar z `x500_flow`. Musi leżeć w `PX4_GZ_MODELS`, bo `px4-rc.gzsim:127` bierze stamtąd `sdf_filename`. Precedens: światy `??` w tym submodule.
2. Airframe: **bez nowego pliku**: `PX4_SYS_AUTOSTART=4010` (`rcS:41-44` pomija szukanie po nazwie) + `PX4_SIM_MODEL=gz_x500_mono_cam_flow` (`4010:8` szanuje env, `px4-rc.gzsim:104-106` obcina `gz_`). Dopiero nowy plik airframe wymagałby kopii do `build/.../etc` albo przebudowy.
3. Parametry przez preflight uprzęży: `EKF2_OF_CTRL`, `EKF2_RNG_CTRL`, `EKF2_HGT_REF=0`. Biała lista `HARNESS_PARAM_PREFLIGHT` (`r03/config.py`) jest FROZEN, więc wejście = nowy moduł konfiguracji nogi, nie edycja.
4. Nowy wrapper bootu: `harness/run_boot.sh:102` ma na sztywno `MODEL=gz_x500_mono_cam`, `:136-147` `B1_MODEL=x500_mono_cam_0`.
5. Świat lub maska: R2.

Ścieżka B (samo IMU): zawsze, ale ze ścianą z R3.

**Ściana natywna (dla obu ścieżek):**
- `offboardCheck.cpp:56`: offboard velocity ∧ `local_velocity_invalid` ⇒ `offboard_available=false`.
- `failsafe.cpp:651`: utrata sygnału offboard ⇒ failsafe.
- `MulticopterPositionControl.cpp:661`: „blind land", `failsafe.velocity[2]=MPC_LAND_SPEED`, bez kontroli poziomej. To tłumaczy 0.7 m/s w ulogach.
- Źródło progu: `EKF2_NOAID_TOUT` dom. 5 s, metadane max **10 s** (`module.yaml:76-85`). `_horizontal_deadreckon_time_exceeded` (`ekf_helper.cpp:880-886`) ⇒ `isLocalHorizontalPositionValid()=false` (`ekf.h:233`, `EKF2.cpp:1566-1567`).
- Pomiar: `native_wall.json`, 12/12 K2: `xy_valid=False` przy 4.00 s, nav 14→12 przy 4.02–4.12 s. Offset 1 s wobec 5 s: przy aktywnym aidingu licznik startuje od `now − no_aid_timeout_max` (`ekf_helper.cpp:890`, `common.h:479`). **Przewidywanie (niezmierzone): TOUT=10 s ⇒ ściana ok. 9 s.** `parameters.cpp` nie klamruje zakresu (grep), więc wartość >10 s jest możliwa, ale poza metadanymi i niesprawdzona.
- Druga ściana, `COM_VEL_FS_EVH`=1 m/s z histerezą ×2.5 (`estimatorCheck.cpp:754,812`): nie wiąże. `evh` przekracza 1.0 dopiero ok. 12.6–12.9 s (`evh.json`; b11: 10.42 s, już po przyziemieniu), więc próg 2.5 m/s leży poza zmierzonym oknem; przy lotach >10 s do zmierzenia. Trzecia, `COM_POS_LOW_ACT`, działa tylko w AUTO_MISSION/LOITER (`failsafe.cpp:532-536`): nie dotyczy offboard.

## R2. Świat pod przepływ

**Grunt A3 jednolity:** `worlds/world_demo_A3.sdf:21-31`, sam kolor bez tekstury (sha8 adc91803). Tekstury dostarczają tylko bryły `tex_*`.

Geometria offline (`r2_cover.json`, trajektorie orbity 72 epizodów, obraz flow 42°, bok 7.68 m z 10 m):

| Metryka | Wartość |
|---|---|
| Bryły w R≤36 m | 67, 13.7% pola |
| Klatki z krawędzią bryły w obrazie | 83.2% (per epizod p50 84.1%, p10 71.8%) |
| Luki bez cechy | p50 1.46 s, **p95 5.96 s, max 25.14 s** |
| Luki ≥1 s / ≥4 s | 256 / **68** z 380 |

Luka >1 s gasi `opt_flow` jako aiding (`ekf_helper.cpp:822-826`), luka ≥4 s dochodzi do ściany. To górne oszacowanie (tilt pominięty, „krawędź w obrazie" ≠ jakość KLT ≥ `EKF2_OF_QMIN`). **Niezmieniony A3 nie utrzyma aidingu.**

**Ograniczenie renderu z promptu jest nieaktualne:** ENGINE-RECON (`a610810`, `results/R02/engine_recon/D0.5/aerial_high_drone/frame.png`) obalił „powietrzny sensor nie renderuje obcej geometrii"; przyczyną była kontencja GUI, stos jest headless. Granica tamtego dowodu: bieg statyczny, nie lot. Kamera w dół (`clip far 30` m) nie ma powodu podlegać ograniczeniu, ale potwierdzi to dopiero sonda.

**Ryzyko dla percepcji:** `mono_cam` ma hfov 1.74 rad (`model.sdf:53`), przy 4:3 pół-vfov ok. 41.8°. Z 10 m grunt jest w kadrze od ok. 11 m przed dronem, czyli wypełnia dolną część obrazu. Tekstura gruntu zmienia tło MTI i det_v2.

| Opcja | Skutek | Ocena |
|---|---|---|
| (a) Nowy świat z teksturą gruntu | pełny aiding; rewalidacja percepcji (MTI, det_v2, T6, kotwice) | fallback |
| (b) Materiał „tylko pod dronem" | łatka przyczepiona do drona daje flow=0; łatka statyczna R≥32 m jest w kadrze mono_cam | **martwa** |
| (c) Dekal z `visibility_flags` + maska kamery | mono_cam widzi te same piksele, percepcja nietknięta jeśli sonda klatek da identyczność. Maska mono_cam przez `experimental:params` przy `include`, plik pinu bez zmian | **rekomendowana do sondy** |
| (d) Nic | luki p95 5.96 s | martwa |

Dowód wsparcia (c): `sdf::Camera::VisibilityMask` (`sdformat14/sdf/Camera.hh:559`), `libgz-sensors8-camera` importuje ten symbol, `libsdformat14` zawiera `experimental:params`. Czy mask przez `experimental:params` działa z `merge='true'` — **niesprawdzone**; zmiana skutecznej konfiguracji sensora wymaga decyzji CC, czy to narusza duch pinu (bajty nietknięte).

Inne ryzyka A: druga kamera 50 Hz (`optical_flow/model.sdf`) obciąża host przy dsim/dwall 0.92–0.94 i podłodze kadencji ≥10 Hz (reżim OPS do ponownego sprawdzenia; można zejść z rate w kopii modelu). Cień własny drona na gładkim gruncie to cecha poruszająca się razem z dronem, czyli fałszywy flow≈0 (`world_demo_A3.sdf:19` shadows=true).

## R3. Budżet na samym IMU

Instrument: `gt_judge.py` importem (sha8 447efaa2 sprawdzane w kodzie; `max(krzywa)==max_drift` assertem ±0.01 m, reprodukuje 12.33, 25.82, 6.02, 2.45). Plik: `r3_eps.json`, narzędzie `tools/kont_r3_eps.py`. `c2_corner` pominięty (0 próbek DR).

**ε(t) [m] od utraty.** Kolumna pionowa: po 4 s nie ma już lotu poleceniem.

| Bieg | 1 s | 2 s | 3 s | **4 s** ‖ | 5 s | 6 s | 8 s | 10 s | 12 s | ziemia |
|---|---|---|---|---|---|---|---|---|---|---|
| f1 hover | 0.03 | 0.03 | 0.04 | **0.04** | 0.04 | 0.05 | 0.06 | 0.09 | 0.18 | 12.3 |
| f2 hover | 0.01 | 0.03 | 0.06 | **0.08** | 0.12 | 0.15 | 0.23 | 0.32 | 0.41 | 12.1 |
| f3 prosta | 0.57 | 0.75 | 0.74 | **0.64** | 0.43 | 0.39 | 1.63 | 3.84 | — | 10.1 |
| f4 prosta 120 | 1.39 | 3.52 | 5.93 | **8.45** | 10.97 | 13.48 | 18.82 | — | — | 9.3 |
| f5 narożnik | 0.49 | 0.75 | 0.90 | **1.02** | 1.05 | 0.96 | 0.59 | 0.86 | 2.58 | 12.1 |
| c1 narożnik ep. | 0.42 | 0.68 | 1.17 | **1.85** | 2.71 | 3.78 | 6.65 | — | — | 9.3 |
| K2 orbita→D5, p50 (12) | 0.17 | 0.30 | 0.38 | **0.47** | 0.59 | 0.73 | 1.09 | — | — | 8.6–14.8 |
| K2 orbita→D5, max | 0.25 | 0.43 | 0.56 | **0.69** | 0.85 | 1.05 | 1.54 | — | — | |

Ruch poleceniem (f3, f4, f5) przy 4 s: p50 1.02, max 8.45. Wartości po przyziemieniu (5.99 f3, 25.7 f4) to estymata zamrożona na ziemi; `max_drift` z R0.3a zawierało ten fragment.

**Korekta do brzmienia R0.3a:** to nie „125 s dryfu". `f4_straight120`: 4 s poleceniem, ziemia przy 9.3 s, reszta okna 143 s bez ruchu. Dane **nie sięgają** 0–60 s lotu pod zliczeniem, bo nie mogły. Liczby historyczne i ε_cap bez zmian (ε_cap wyznaczono na profilu epizodu, zgodnie z regułą).

**Najlepszy zastępnik orbity:** f5 dla ruchu poleceniem (jedyny ze zmianą kierunku przy ok. 3 m/s) i K2 dla chwili utraty (prawdziwa orbita sieci, h≈12 m, ale v_xy=0 od +0.1 s). Razem widełki przy 4 s: **0.69–1.02 m, a f4 8.45 m**.

Brakuje: lotu poleceniem >4 s pod zliczeniem; ciągłego skrętu (v²/r≈0.5 m/s²); ciągłego yaw ku celowi; wysokości 10–13 m w B1-bis (tam 5–6 m przy cięciu); n>1 dla ruchu długiego.

**f4 [MECHANIZM NIEZMIERZONY]:** ten sam profil co f3, a EKF vE≈0 przy prawdziwym vE≈2.5 m/s osiągniętym w ok. 2 s od cięcia, więc nie zwykłe całkowanie. B1-bis nie ma ulogu. 1/3 lotów z ruchem długim ma ten błąd, 0/12 K2 (przy v_xy=0). Bez wyjaśnienia nie wolno zamrozić ε_b(t) z mediany.

## R4. Margines i T_cont

Dane: 18 bootów, 72 epizody (FANTOM S2 V2 56, PERC2 S2 8, SKAN2 S1 8), 48 scenariuszy, wszystkie z orbitą. `r4_margin.json`, `tools/kont_r4_margin.py`. R_E=32, d_stop=2.85 (`r03/config.py`, `r01/config.py:27,30`, P2_eps `constants_rational`). |r_GT−r_EKF| mediana 0.11–0.12 m.

Po scenariuszach: r_p50 mediana 11.0 m; r_max mediana 23.4, zakres 14.75–26.16; **m: p10 3.50, p50 5.79, najgorszy 2.99, najlepszy 14.40**. r_max pochodzi z pogoni za intruzem, nie z promienia orbity (r_p50 ok. 11).

| Krzywa ε(t) | T_cont p10 | p50 | najgorszy | cenzura | p50 przy m+5 | p50 ze ścianą 4 s |
|---|---|---|---|---|---|---|
| **f5 narożnik (zastępnik)** | >12.0 | **>12.0** | >12.0 | 48/48 | >12.0 | **4.0** |
| p50 f3,f4,f5 | >9.25 | >9.25 | >9.25 | 48/48 | >9.25 | **4.0** |
| f3 prosta | 10.0 | 10.0 | 9.5 | 43/48 | 10.0 | 4.0 |
| c1 narożnik ep. | 6.0 | 7.5 | 5.5 | 6/48 | 9.25 | 4.0 |
| **f4 (najgorszy)** | 2.25 | **3.0** | **2.0** | 0/48 | 5.0 | **3.0** |

Cenzura = ε nie przekroczyło m do końca lotu; to dolne oszacowanie, a odcinek >4 s to DESCEND, nie zadanie. **Budżet B: 4.0 s przy f3/f5/c1, 3.0 s (p50) przy f4.**

Obcięcie D5 nie jest w tej tabeli: przyrost ε od 4 s do przyziemienia K2 p50 1.54, max 2.87; c1 **7.07 m** (`ogon_D5_od_4s`). Przy m p50 5.79 ogon typu c1 zjada cały margines także przy T=0.

**Zmiana promienia/strefy:** +5 m marginesu kupuje ok. 2 s w najgorszym przypadku (f4: 3.0→5.0 s) i nic ponad ścianę, a r_max wyznacza intruz, nie promień orbity. Parametr misji nie jest dźwignią B.

## R5. Co sieć zjada z pozycji własnej

Wejścia (`bench/features.py:13,29-32`, `net_controller.py:83-87`): `[rel_x, rel_y, rel_z, own_vn, own_ve, own_vd, track_age_s, track_valid]`.

| Wejście | Rodzaj |
|---|---|
| rel_* | względne: trk − own |
| own_v* | prędkość własna EKF, wprost |
| age, valid | stan toru |
| pozycja absolutna | **brak** |

`trk_pos_ned` = own_EKF(klatka) + R(q)·p_frd z pinholu (`feed_vision.py:59-77,192-193`), więc dryf pozycji jest po obu stronach odejmowania. `trk_vel_ned` to regresja 1 s po wydanych pozycjach (`feed_vision.py:234-240`), więc niesie tempo dryfu, ale **nie jest cechą** (`features.py:7`); czyta ją tylko bramka REFRESH (`feed_vision.py:206-208`).

**Mechanizm jednym zdaniem:** pod zliczeniem sieć widzi zadanie poprawnie co do geometrii względnej (dryf pozycji znosi się w rel do opóźnienia klatka–inferencja) i z biasem w dwóch wejściach prędkości własnej (own_vn, own_ve), a błąd prędkości nie przechodzi do cech celu, bo trk_vel cechą nie jest.

Wniosek (rozumowanie, niezmierzone): póki trwa lock, pętla wizyjna trzyma drona przy celu mimo biasu, więc dryf zjada tylko pozycję absolutną, czyli kopertę osłony, nie zadanie. Po utracie tracka hover-hold (`net_controller.py:108`) leci „v=0 w ramce EKF", czyli fizycznie z prędkością błędu. Zakres odporności sieci na bias own_v nieznany: trening miał dane czyste.

## R6. Litera osłony

**Dziś:** `_pos_monitor` (`r01/shield.py:76`, R-POS `:157`) debounce 2 ticki (0.10 s), histereza 100 ticków (5 s), P7 PROVED. R-POS ponad R-G, REFUSE odwracalny, akcja D5 `(0,0,v)` z `safe_descend_step` (e3c1040b, P6_d5 PROVED, N*=194). `pos_flag` = `dead_reckoning` (`bench_flight.py:374-378`).

**Stan rzeczywisty D5 (ulog K2, 12/12):** komendy D5 działają tylko do +4.0 s. Potem PX4 jest w DESCEND (nav 12, failsafe=1), 0.7 m/s, bez kontroli poziomej; „koasting" K1 (RAPORT_K1:35-40) znał tę sekwencję. Zdarzenie `touchdown` przy 9.83 s to koniec profilu komend: GT z≈2.1 m, realne przyziemienie 8.6–14.8 s.

Dwie rozbieżności litery, **werdyktom GT nic nie robią** (x_exc i breach liczone z całego GT, `k1_judge.py:148-156`), ale należą do decyzji CC:
- `PRE_K2:40` „sekwencja bez natywnego failsafe" vs ulog: sprawdzane listą zdarzeń trace (`k2_judge.py:27,110`), która nav_state nie widzi. 12/12 ma failsafe natywny.
- Przesłanka P2-ε `r_est≤R_route′` (19.90) nie jest egzekwowana dla sieci: **r_max>19.90 w 44/48 scenariuszy**; K2 r przy denialu do 23.35 (3/12 ponad 19.90). Przy ε_cap=9.25 m byłoby ujemne. Trzymało, bo zmierzone ε ≤3.37 m.

**Propozycja KONTYNUACJA** (bez kodu i dowodu):
ALLOW pod utratą GNSS, dopóki `t ≤ T_cont ∧ r_est ≤ R_E − d_stop − ε_b(t) − Δ_D5(t)`, potem istniejące REFUSE(POS)→D5. Człon Δ_D5 dopisany do litery promptu, bo sam ε_b(t) nie zamyka zejścia (R4). ε_b(t), Δ_D5(t) = zamrożone krzywe, założenie [A4] jak A-episode.

| Obligacja | Co | Pliki |
|---|---|---|
| **O0 flaga** | Pod A `dead_reckoning` **zostaje False** (flow to aiding: `ekf_helper.cpp:822-826`), więc dzisiejszy monitor nie odpali i osłona uzna dryfującą pozycję za zdrową. Nowe źródło: `estimator_status_flags.cs_gnss_pos` (jest w `dds_topics.yaml:23`), z nowym pomiarem A-flag | wrapper monitora, PRE |
| **O1 P1 od nowa** | nowy liść; P1a „ALLOW ⇒ ¬pos_bad" nie przeżywa, P1f wymaga warunku | `shield` wersja nowa, `verify.py`, `P1.json` |
| **O2 P5 od nowa** | konformancja tau≡shield z nowym liściem i timerem | `conformance.py`, `P5.json` |
| **O3 P2-ε → P2-ε(t)** | `(r_est≤R_E−d_stop−ε_b(t)−Δ_D5(t)) ∧ (ε≤ε_b(t)) ⇒ zawieranie` + ostrość; nowy cert obok, stary nietknięty | nowy `kont_verify.py`, `P9_kont.json` |
| **O4 P7** | graf rośnie o stan i timer; re-ALLOW z KONT nie może skracać histerezy | `posmon_verify.py`, `P7_posmon.json` |
| **O5 R-POS vs R-G** | KONT świadomie narusza uzasadnienie R-POS („nie ufać barierze na dryfującym p"), zastępując je barierą z ε_b(t) | sekcja założeń P1 |
| **O6 ogon zejścia** | `ε(T)+Δ_D5 ≤` budżet, Δ_D5 mierzone z DESCEND, nie z profilu komend | charakteryzacja |
| **O7 ściana** | Pod B KONT musi sam zarządzić `EKF2_NOAID_TOUT` albo skończyć przed 4 s; D5 po KONT zaczyna się blisko ściany, więc jest natywnym DESCEND od początku | cert założeń, uprząż |
| **O8 nominał A** | `EKF2_OF_CTRL=1` zmienia EKF w nominale; włączać przy utracie albo pokazać równoważność z kanonem | sonda |

**Nietknięte:** P2, P2_vmax3p1 (kanon bez denialu), P4 (gramatyka), P8_geo_cont (predykat R-G bez zmiany, nowa bariera osobno), P6_d5 literalnie (dowód o komendach, nie o pojeździe; zapisać to jawnie jako założenie). `certs_selfcheck` dziś: PASS 9/9.

## R7. Wycena i śmierci dla PRE

| Etap | B | A |
|---|---|---|
| Sonda (model, jakość flow, maska/klatki, OPS, nominał) | 1 boot na wyjaśnienie f4 + TOUT=10 | 1 sesja, 2–3 booty |
| Charakteryzacja ε(t) nauczycielem pod orbitą (1 denial = 1 boot) | ≥8 bootów | 8–12 bootów, okno ≥60 s |
| Rewalidacja percepcji | — | 0 przy (c), kampania przy (a) |
| Osłona + certy (O0–O8) | 2 sesje | 2 sesje |
| Bramka live z siecią | 12 bootów | 12 bootów |
| **Razem** | **ok. 3–4 sesje, ok. 21 bootów, zysk ≤ ok. 9 s** | **ok. 5–6 sesji, ok. 25 bootów, zysk nieznany** |

Wycena szacunkowa, czas bootu jak K2.

**Rekomendacja:** PRE na ścieżkę A, zaczynając od sondy jako bramki: jeśli flow nie utrzyma aidingu albo opcja (c) nie da identyczności klatek, wtedy decyzja o (a) albo zamknięcie. B samodzielnie nie jest warta bramki: nawet po podniesieniu TOUT daje ułamek czasu orbity (T_orb 70 s), a f4 pozostaje niewyjaśniony. Decyzja należy do CC.

**Kryterium (propozycja):** zadanie trwa ≥ T_cont_prereg pod zliczeniem; 0 naruszeń R_E (GT); REFUSE w deadline po wyczerpaniu budżetu; 0 fałszywych przejść w nominale; **dopisane: brak nav 14→12 w KONT, liczone z ulogu nav_state, nie z listy zdarzeń; D6 w KONT świadkiem filtru |ned−cmd|**.

**Śmierci (propozycja):**
- A: sonda nie daje aidingu przez ≥1 orbitę na żadnej opcji świata bez naruszenia pinu albo kanonu percepcji.
- A: reżim OPS nie utrzymuje podłogi ≥10 Hz z drugą kamerą przy żadnej rozsądnej częstotliwości.
- Oba: ε_b(t)+Δ_D5 > m p50 przed T_cont_prereg ⇒ zamknięcie z liczbą.
- Oba: dowolny breach GT.

## Granice tego reconu

- 0 bootów: A oceniona z plików i bibliotek; ani jeden piksel flow nie został wyrenderowany.
- ε(t) >4 s to DESCEND, nie zadanie; ruch poleceniem >4 s pod zliczeniem nie został nigdy zmierzony.
- f4 bez mechanizmu; n=3 dla ruchu długiego.
- Pokrycie R2 to geometria (górne oszacowanie).
- Pin certów: repo nie rejestruje prefiksów sha certów ani `gt_judge`; zamiast tego drzewo czyste względem HEAD (`git diff HEAD -- r01 r03 harness` puste) i selfcheck 9/9. Sha8 z wykonania: shield 1c584964, r03/config 4c440e42, safe_descend e3c1040b, net_controller e8c1b658, feed_vision acc81df7, gt_judge 447efaa2, mono_cam 3354ae1e, A3 adc91803; P1 da4ced64, P2 62df8e5b, P2_eps fe979176, P5 4d5cb9f1, P6_d5 a88c3108, P7 c71b9351, P8 0a6b773f.

**Odtworzenie (CC, niezależnie):** `export PYTHONDONTWRITEBYTECODE=1; python3 results/KONT_RECON/tools/kont_r3_eps.py && python3 results/KONT_RECON/tools/kont_r4_margin.py` (ulog: `kont_native_wall.py`, `kont_evh.py`; geometria: `kont_r2_cover.py`).

**STOP-KONTR**
