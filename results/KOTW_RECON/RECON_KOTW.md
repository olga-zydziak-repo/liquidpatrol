# RECON_KOTW — kotwica wizyjna: patrol bez GNSS bez limitu czasu — STOP-KOTWR

Egzekutor · 8.11.2026 · wykonanie PROMPT_KOTW_S0. **0 bootów, 0 SITL, 0 renderów, 0 treningu, 0 edycji istniejących
plików; nowe pliki wyłącznie `results/KOTW_RECON/**`.** Bramka §0: origin/master = `9db3ad8a` (CO-KONT-Z),
`ANEKS_KONT-5.md` sha256 848dade1… ✓, `origin/master..HEAD` pusty, porcelain czysty poza zastanymi `??` DEMO_C.
FROZEN tylko odczytem, sha256 plików zgodne: det_v2.pt 775ead15, r02/mti.py 0889ab39 (z RECON_DET3:6),
mono_cam/model.sdf 3354ae1e (FREEZE_PERC2_OPS:27), s2_freeze_bf.json ae19f66c.

## Raport płaski

- **Najdłuższa przerwa widoczności per faza** (kotwica h = 2 m, stożek centralny admisji, 148 epizodów z 4 kampanii):
  **start epizodu (hold + skan + dolot) p50 24.2 / p95 44.2 / max 67.6 s · orbita (przerwy wewnętrzne) p50 1.1 /
  p95 21.1 / max 39.9 s · koniec (cenzurowana) max 55.5 s.** W hold kotwica jest niewidoczna z konstrukcji
  (frac 1.4%); h = 5 m: orbita max 37.1 s, h = 0.5 m: 42.9 s.
- **Błąd jednej poprawki przy 25 m** (h 2 m, W 1 m): **1.57 m (OPT: ±1 px, δψ 2°) · 2.98 m (ZMIERZ: ±2 px,
  δψ 5.5° = max |błędu| yaw w kontynuacjach S4) · 5.31 m przy zmierzonym biasie wysokości 2d S1 1.8 m.**
  Dominuje człon poprzeczny D·tan δψ (2.59 m z 2.98).
- **Werdykt R5: PIŁA SIĘ NIE DOMYKA.** Żadna z 27 kombinacji (h × W × wariant błędu) nie spełnia warunku. Najlepsza
  (h 5, W 2, OPT) domyka 20/48 komórek (< 24), a najgorsza przerwa orbity całej siatki (37.1 s, c05_s01) nie domyka
  się **nawet przy idealnej poprawce**: ε_b(37) 4.567 + Δ_D5 1.524 = 6.09 > m_p50 5.79, **o 0.30 m przy ε_fix = 0**;
  z ε_fix zmierzonym 1.72 m przekroczenie wynosi 2.02 m (suma 7.81). Mediana komórek też pada: typowa najgorsza
  przerwa orbity w komórce 18.9 s ⇒ ε_b 3.478 ⇒ przy m 5.79 dopuszczalny ε_fix ≤ 0.79 m, a poprawka z okna
  poprzedzającego ma p50 1.15 m (D p50 20.1 m, OPT).
  **⇒ śmierć przy biurku wg preregu R6 (R5 pusty).**
- **R3: rekomendacja B** (poprawka po stronie osłony, EKF nietknięty) — rozstrzyga inwentarz, nie preferencja: EV
  w PX4 v1.16.2 przy obserwacjach 1–2 s co ~20 s działałby w trybie start/timeout/reset co okno (§R3).
- **R4 jednym zdaniem:** fałszywa admisja na kotwicy **nie jest wykluczona literą**: brama ENTRY nie ma progu
  minimalnego ruchu, a MTI wprost nie kompensuje paralaksy translacyjnej (`r02/mti.py:4`). Do tego refresh tracku
  przyjmuje każdy box central∧MTI (`harness/feed_vision.py:202`), więc dochodzi ryzyko przejęcia tracku na orbicie.
  Rozstrzygnąć może tylko sonda.
- **Wycena (warunkowa, gdyby CC/Olga otworzyli wbrew R5):** 4 etapy, ~20–27 bootów; ale przy obecnej geometrii
  misji etap S2 jest z góry przegrany. Każda droga przez R5 wymaga dźwigni POZA zakresem tego reconu (§R6).
- Diff-stat i porcelain: na końcu. Sygnał: **STOP-KOTWR**.

## §R1. Widoczność kotwicy w istniejących lotach

**Źródła i metoda** (`tools/kotw_r1.py`, wynik `r1_widocznosc_raw.json`, agregat `r1_widocznosc.json`):
- poza GT drona z `trace.jsonl` rekordów `"gt"` (gz, ~50 Hz, x/y/z + kwaternion); ramka ustalona empirycznie na
  nom_b1_r5: **ENU** (N = gt.y, E = gt.x, U = gt.z), yaw_NED = 90° − yaw_ENU, zgodność z EKF heading do ~2°;
- fazy z `demo.jsonl` (`phase` ∈ hold/approach/orbit, `episode_id`, `scenario_id`);
- kamera z pinu: `mono_cam/model.sdf:53-56` (horizontal_fov 1.74 rad, 640×480) ⇒ f = 320/tan(0.87) = 269.5 px
  (zgodnie z `r02/mti.py:15` fx = 270); montaż `x500_mono_cam/model.sdf:9` (.12 .03 .242, rpy 0) — **kamera poziomo
  do przodu, sztywno**; ten sam montaż w `x500_mono_cam_flow/model.sdf:6-15` (KONT);
- stożek centralny = `edge_dist ≥ 0.10` (`r02/config_r02.py:36`, `r02/target_channel.py:103`) ⇒ ±43.5° poziomo,
  ±35.4° pionowo;
- kotwica = punkt (E 0, N 0, U h), h ∈ {0.5, 2, 5} m; świat płaski bez okluzji; dziury < 0.25 s łączone;
- opcjonalny próg rozdzielczości f·W/D ≥ 10 px (**ZAŁOŻENIE**, niezmierzone) ⇒ D_max 13.5 / 26.9 / 53.9 m dla
  W 0.5 / 1 / 2 m.

**Korpus:** FANTOM S2 104 epizody (`results/FANTOM/camp/r*`), KONT S4 28, PERC2 S2 8, SKAN2 S1 8 — razem 148,
epizod p50 74 s.

**Tabela (stożek centralny, bez progu rozdzielczości):**

| h | frac widoczna hold / approach / orbit | start p50 / p95 / max [s] | orbita wewn. p50 / p95 / max [s] | okno orbity dł. p50 / p95 [s] | zasięg w oknie orbity (min p50; zakres) [m] |
|---|---|---|---|---|---|
| 0.5 | 0.013 / 0.088 / 0.215 | 26.6 / 54.9 / 68.0 | 1.1 / 22.9 / 42.9 | 1.2 / 9.3 | 21.7; 10.7–29.1 |
| 2 | 0.015 / 0.096 / 0.262 | 24.2 / 44.2 / 67.6 | 1.1 / 21.1 / 39.9 | 1.7 / 10.7 | 19.3; 10.6–28.4 |
| 5 | 0.017 / 0.118 / 0.350 | 18.8 / 41.8 / 67.6 | 5.4 / 18.7 / 37.1 | 5.9 / 13.8 | 14.3; 8.4–27.2 |

Przerwa „start” liczona od t0 epizodu do pierwszego okna (obejmuje hold, skan i dolot); końcowa przerwa
cenzurowana max 57.4 / 55.5 / 24.3 s. Wewnętrzne przerwy poza orbitą: 1–3 sztuki w całym korpusie
(hold ≤ 0.75 s, approach 6.9 s). Każdy epizod ma ≥ 1 okno. Z progiem W = 0.5 m (D ≤ 13.5 m) przy h ≤ 2 m okna
orbity praktycznie znikają (min zasięg p50 19–22 m); W = 1 m obcina tylko ogon > 26.9 m (tabela
`r1_widocznosc.json` → `central_W*`).

**Geometria najgorszego przypadku** (`tools/kotw_r1_geom.py` → `r1_geometria.json`, h = 2 m, wszystkie próbki GT):

| faza | widoczna | ZA (za kamerą / poza azymutem) | POD (pod stożkiem) | r_GT p50 | depresja p50 |
|---|---|---|---|---|---|
| hold | 5.6% | 73.4% | 20.1% | 0.5 m | 87.3° |
| approach | 12.8% | 64.4% | 22.2% | 2.9 m | 68.8° |
| orbit | 26.3% | 49.1% | 21.0% | 12.2 m | 38.5° |

(Odsetki „widoczna” liczone tu po wszystkich próbkach w zakresie demo, także między epizodami, stąd wyżej niż
w tabeli epizodowej.)
- **Start (hold/skan):** dron wisi praktycznie nad kotwicą (r 0.5 m, depresja 87°), kamera pozioma ⇒ kotwica
  niewidoczna z konstrukcji; skan yaw tego nie zmienia (depresja, nie azymut).
- **Orbita:** kamera śledzi intruza na zewnątrz strefy ⇒ środek jest **za** dronem przez połowę czasu; okna pojawiają
  się, gdy dron jest po zewnętrznej stronie intruza i patrzy do środka. Najdłuższe przerwy: c05_s01 (42.9 / 39.9 /
  37.1 s dla h 0.5 / 2 / 5), c09_s01 (51.0 s przy h 5 z progiem W 0.5).
- **Prereg R6 „max przerwa orbity > 60 s”:** NIE zachodzi (max wewnętrzna orbity 51.0 s w najgorszej kombinacji,
  42.9 s bez progu). Przerwy > 60 s istnieją tylko jako przerwy startowe (67.6–68.0 s) i to jest osobny problem
  fazy startu (nazwany wyżej).

## §R2. Co daje jedna obserwacja

`tools/kotw_r2r5.py` → `r2_poprawka.json` (zasięgi 10–35 m × h × W × 3 warianty). Model to ograniczenia najgorszego
przypadku, nie σ, bo ε_b z 2d też jest obwiednią (×1.5):

- poprzecznie: e_lat = D·tan δψ + D·px/f;
- radialnie: e_rad = min(e_rozmiar, e_elewacja), gdzie
  - e_rozmiar = D²·px/(f·W) — zasięg z pozornej szerokości;
  - e_elewacja = Δz/sin²e·(px/f + δθ) + δz/tan e — zasięg poziomy z kąta depresji i wysokości, Δz = 12 − h;
- ε_fix = hypot(e_lat, e_rad).

Warianty błędów:
- **OPT:** px 1, δψ 2°, δθ 0.5°, δz 0.2 m.
- **ZMIERZ:** px 2, δψ 5.5°, δθ 0.5°, δz 0.2 m.
- **ZMIERZ_bias_h1.8:** jak ZMIERZ, ale δz 1.8 m.

δψ 5.5° to zmierzony max |EKF heading − GT yaw| w kontynuacjach S4 (`tools/kotw_yaw.py` → `r2_yaw_s4.json`:
12 cięć, średnie −0.8…−3.6°, zakres −5.5…+2.7°). Ten sam bias ~−3° jest przed cięciem, więc część to artefakt
złączenia po mono przy obrotach. δθ i δz to ZAŁOŻENIA. Bias wysokości 1.8 m to zmierzony bias z 2d S1 (pamięć
łańcucha KONT; wartość niepotwierdzona w tym reconie).

| D [m] | W 1 m: w_px | OPT ε_fix (τ_min) | ZMIERZ ε_fix (τ_min) | bias h 1.8 | składowe ZMIERZ: lat / rozmiar / elewacja |
|---|---|---|---|---|---|
| 15 | 18.0 | 0.77 m (2 s) | 1.66 m (4 s) | 2.28 m | 1.56 / 1.67 / 0.59 |
| 25 | 10.8 | 1.57 m (4 s) | 2.98 m (9 s) | 5.31 m | 2.59 / 4.63 / 1.47 |
| 35 | 7.7 | 2.58 m (6 s) | 4.49 m (23 s) | 8.80 m | 3.63 / 9.08 / 2.65 |

(h = 2 m; pełna siatka w JSON.) **τ_min** to najmniejsze τ, przy którym ε_b(τ) > ε_fix, czyli od kiedy obserwacja
z danego zasięgu poprawia stan. Wnioski:
- zasięg z rozmiaru przegrywa z elewacją przy każdym W ≤ 1 m;
- **błąd yaw jest dominującym członem** — kotwica punktowa nie mierzy kursu, więc namiar obraca się błędem
  estymatora;
- przy biasie wysokości 1.8 m poprawka z 25 m jest bezużyteczna (5.3 m ≈ cały budżet).

## §R3. Droga wstrzyknięcia (inwentarz)

PX4 `v1.16.2` (`git -C PX4-Autopilot describe --tags`).

**Wariant A — EV do EKF2:**
- **Interfejs:** `EKF2_EV_CTRL` to bitmaska (poz. poziomo / pion / prędkość 3D / yaw), domyślnie 0
  (`src/modules/ekf2/params_external_vision.yaml:5-17`). `EKF2_EV_DELAY` 0–300 ms, wymaga reboota (`:19-28`).
  Wejście przez `VehicleOdometry` z `pose_frame` NED albo FRD (`msg/versioned/VehicleOdometry.msg:8-11`).
  Alternatywa: `EKF2_AGP_*` (aux global position, `params_aux_global_position.yaml:5-40`).
- **Zachowanie przy rzadkich obserwacjach:**
  - fuzja EV ma timeout „no aid” 1 s (`EKF/aid_sources/external_vision/ev_pos_control.cpp:269`, komentarz
    „1 second”), więc przy oknach 1–2 s co ~20 s (R1) fuzja co okno startuje od nowa;
  - start z resetem stanu pozycji do wizji (`:217-224`, `reset_pos_to_vision`) — skok pozycji w EKF w każdym
    oknie;
  - przy aktywnej estymacji biasu EV pozycja przechodzi przez `_ev_pos_b_est` (`:152-163`).
- **Konflikt z kanonem:** to przestawianie kanonu estymatora (parametry EKF2 w kanonie; `EKF2_MAG_CHK_STR`
  nietykalne — konwencja K1) i ryzyko klasy „zadany ≠ faktyczny” na resetach.

**Wariant B — poprawka po stronie osłony:**
- **Co konsumuje bariera dziś:** nakładka KONT dostaje gotowe `cs_gnss_pos`, `r_est` i zegar `now`
  (`r03/kont_shield.py:25`). R-KONT: ALLOW ⇔ t_KONT < T* − 2·dt ∧ r_est ≤ R_E − d_stop − ε_b(⌊t_KONT⌋) − Δ_D5
  (`:13`, `_kont_barrier` `:149-160`, `r_kont` `:56`).
- **Odpowiednik B:**
  - zegar τ = czas od ostatniej PRZYJĘTEJ poprawki zastępuje t_KONT;
  - r_est = |p_fix + (p_EKF(t) − p_EKF(t_fix))|;
  - bariera ε_b(τ) + ε_fix(D_fix) + Δ_D5;
  - P9 „piła” = P9_kont z resetem zegara na zdarzeniu poprawki — ta sama krzywa, nowy zegar plus stały człon
    ε_fix.
  - Telemetria: rekord poprawki (t, D, ε_fix, p_fix) i τ w `tk`.
- **Warunek ważności B (nazwany, niesprawdzony):** ε_b(τ) z 2d zdjęto od chwili cięcia GNSS, czyli ze stanu
  zbieżnego EKF. W B to PRZYROST dryfu w oknie [t_fix, t_fix+τ] w dowolnym miejscu lotu bez GNSS. Czy przyrost
  późnego okna mieści się w ε_b(τ) — **niezmierzone** (te same dane 2d by to pokazały; zrobione nie zostało, bo
  R5 pada już na krzywej optymistycznej).

**Rekomendacja: B.** Mechanizm: B nie dotyka estymatora ani kanonu EKF, a rzadkość obserwacji (R1) w A
wywoływałaby cykl timeout→reset przy każdym oknie (cytaty wyżej). Dowód B to istniejący P9_kont z innym zegarem.

## §R4. Kotwica a kanon percepcji

(i) **Admisja bez ruchu własnego obiektu — NIE wykluczona literą.**
- **Brama ENTRY** = struktura ∧ MTI (`harness/feed_vision.py:125-126`, assert `entry_require_mti`).
  - Struktura: top-1 det_v2 centralny (`r02/target_channel.py:103,124`).
  - Spójność serii k = 3: `ENTRY_MOVE_THR` to **MAKSYMALNE** przesunięcie środka między klatkami
    (`r02/config_r02.py:28-30`, `target_channel.py:142`), więc obiekt statyczny spełnia je trywialnie.
  - Brak progu minimalnego ruchu.
- **MTI:** kompensuje tylko rotację ego-motion, „translacja/paralaksa NIE kompensowana — nazwana słabość”
  (`r02/mti.py:3-4`). Kotwica na tle gruntu przy orbicie 2–3 m/s na 15–25 m ma paralaksę translacyjną względem
  tła, więc może dać komponent MTI.
- **Zmierzone dotąd:** tło gruntu w locie daje koincydencje central∧MTI, ale rzadko — C1r: 256 boxów tła,
  central∧mti 4/256, nigdy k = 3 (`results/2A/RAPORT_2A.md:84`). Kotwica to nowy, kontrastowy, stały obiekt
  w tym samym miejscu kadru przez okno 1–14 s (R1) — dokładnie przypadek, którego ta statystyka nie obejmuje.
- **Ryzyko przejęcia tracku:** refresh tracku przyjmuje box spełniający central∧MTI **bez sprawdzania
  predykcji** (`harness/feed_vision.py:196-203`, gałąź (a)). Kotwica jest w stożku centralnym 21–35% czasu orbity
  (R1), a więc właśnie wtedy, gdy track żyje. Warunkiem jest top-1 det_v2 na kotwicy zamiast na intruzie.

(ii) **Czy det_v2 ma prawo widzieć maszt/płytę jako drona.**
- Detekcja wymaga tła nieba; obiekt nad gruntem nie jest wykrywany przez klatter (`r02/config_r02.py:74-77`).
  Kotwica przy h ≤ 5 m z patrolu 12 m jest zawsze poniżej horyzontu (depresja p50 38.5° na orbicie), na tle
  gruntu.
- det_v2 zawsze emituje top-1 (conf telemetryczne, nie bramka przy require_mti — `config_r02.py:100-104`), więc
  pytanie brzmi „czy top-1 trafi kotwicę”, a nie „czy przekroczy próg”.
- Pomiarów FP det_v2 na statycznych obiektach naziemnych w korpusie nie znalazłam (grep raportów DET/2A/R02/DET3:
  tylko sceny statyczne bez obiektu — `results/R02/RAPORT_G_R02.md:99`, 0 boxów).
- **Wniosek: wymaga sondy.**

**Co mierzy sonda (S1):** para światów identycznych poza kotwicą (wariant addytywny jak dekal KONT); na tych samych
trajektoriach orbity:
- (a) odsetek klatek, w których top-1 det_v2 leży na kotwicy;
- (b) mti_ok na kotwicy;
- (c) serie central∧MTI ≥ 3 (ENTRY) i refresh z gałęzi (a) przy żywym tracku;
- (d) różnica względem świata bez kotwicy.

**Osobno:** do samej POPRAWKI potrzebny jest detektor kotwicy. det_v2 (FROZEN, trenowany na dronach) nim nie jest,
więc to nowy komponent percepcji poza kanonem.

## §R5. Piła w budżecie

`tools/kotw_r2r5.py` → `r5_pila.json`.

**Warunek per komórka (48 komórek siatki, m z `results/KONT_RECON/r4_margin.json`):**
ε_fix(D okna poprzedzającego) + ε_b(τ) + Δ_D5 1.524 ≤ m_komórki, gdzie τ to najdłuższa wewnętrzna przerwa orbity
w komórce. ε_b z `s2_freeze_bf.json` `eps_b_obwiednia` (×1.5 wliczone — `results/KONT/tools/kont_s2_freeze_bf.py:3`),
koszyki 1 s do 69 s, bez ekstrapolacji.

**Kombinacja dopuszczalna ⇔ ≥ 24/48 komórek ∧ najgorsza przerwa orbity siatki domyka się przy m_p50 5.79.**

| h | W | OPT | ZMIERZ | bias h 1.8 | najgorsza orbita (komórka, τ, D) | suma przy ε_fix = 0 |
|---|---|---|---|---|---|---|
| 0.5 | 0.5 | 0/48 | 0/48 | 0/48 | brak okien w D ≤ 13.5 m | — |
| 0.5 | 1 | 18/48 | 11/48 | 4/48 | c05_s01, 42.9 s, 19.9 m | 6.54 |
| 0.5 | 2 | 18/48 | 11/48 | 9/48 | c05_s01, 42.9 s, 19.9 m | 6.54 |
| 2 | 0.5 | 0/48 | 0/48 | 0/48 | brak okien w D ≤ 13.5 m | — |
| 2 | 1 | 18/48 | 11/48 | 8/48 | c05_s01, 39.9 s, 18.3 m | 6.21 |
| 2 | 2 | 18/48 | 11/48 | 11/48 | c05_s01, 39.9 s, 18.3 m | 6.21 |
| 5 | 0.5 | 14/48 | 11/48 | 5/48 | c09_s01, 51.0 s, 12.8 m | 6.62 |
| 5 | 1 | 19/48 | 16/48 | 12/48 | c05_s01, 37.1 s, 14.7 m | 6.09 |
| 5 | 2 | **20/48** | 16/48 | 16/48 | c05_s01, 37.1 s, 14.7 m | **6.09** |

**Werdykt: PIŁA SIĘ NIE DOMYKA — 0/27 kombinacji dopuszczalnych.**
- **Zdanie śmierci:** „maksymalna przerwa orbity 37.1 s (najlepsza kotwica h 5 m) × dryf ε_b(37) = 4.567 m
  przekracza budżet 5.79 − 1.524 = 4.27 m o 0.30 m już przy idealnej poprawce; przy poprawce zmierzonej (1.72 m)
  o 2.02 m”.
- **Mediana też pada:** w h 2 / W 1 / OPT typowa najgorsza przerwa orbity komórki wynosi 18.9 s (zakres
  14.2–39.9). ε_b 3.478 zostawia na poprawkę ≤ 0.79 m przy m 5.79, a ε_fix z okna poprzedzającego ma w komórkach
  p50 1.15 m (0.58–1.39, D p50 20.1 m). Domyka się 18/48.

Z 30 niedomkniętych komórek 17 ma przerwę τ < 21 s i pada przez ε_fix, a 13 ma τ ≥ 21 s. Z tych 13 dziesięć
nie domknie się nawet przy poprawce idealnej (ε_b(τ) + Δ_D5 > m komórki). Trzy (c06_s04, c11_s01, c01_s03)
domknęłyby się dopiero przy ε_fix ≤ 0.90 / 0.26 / 0.01 m — poniżej każdego wariantu R2 z ich zasięgów.

## §R6. Wycena i śmierci dla PRE

**Prereg śmierci przy biurku:**
- R5 pusty — **ZACHODZI**;
- R4 nieusuwalne FP — nierozstrzygnięte (wymaga sondy, nie śmierć);
- R1 max przerwa orbity > 60 s — nie zachodzi (51.0 s).

**⇒ Pozycja KOTW w obecnej geometrii misji umiera przy biurku.**

Wycena warunkowa (gdyby otwierać mimo R5, np. z inną dźwignią — poniżej):

| etap | treść | booty | śmierć etapu |
|---|---|---|---|
| S1 sonda | świat z kotwicą (wariant addytywny jak dekal KONT) + identyczność klatek poza kotwicą + FP percepcji (R4 a–d) + pierwsza poprawka na żywo (nowy detektor kotwicy, poza det_v2) | 3–4 | ENTRY lub refresh na kotwicy ≥ 1 / identyczność klatek złamana / ε_fix na żywo > R2-ZMIERZ |
| S2 charakteryzacja piły | loty pod misją bez GNSS z poprawkami, rozkład przerw i przyrostów dryfu w oknach | 4–6 | przyrost dryfu w oknie > ε_b(τ) (warunek B z §R3) / R5 nie domyka się na danych |
| S3 osłona τ-zegar | nakładka B + certy piły (P9 z resetem zegara, P1/P5/P7) | 0–1 | cert nie przechodzi |
| S4 bramka z siecią | epizody ≥ 3 × T* (≥ 66 s) bez GNSS, siatka cięć jak KONT S4 | 12–16 | naruszenie piły / breach / FP admisji |

Razem ~20–27 bootów.

**Dźwignie, które mogłyby zmienić R5 (poza zakresem tego reconu — FROZEN albo zmiana misji; tylko nazwane,
niepoliczone):**
1. kamera skierowana w dół albo pochylona (kotwica w hold jest pod dronem: depresja 87°);
2. choreografia „spojrzenie wstecz” co ≤ 10 s (koszt: śledzenie intruza);
3. więcej kotwic lub kotwice na obwodzie, a nie w (0, 0);
4. kotwica mierząca kurs (wzór 2D), co usuwa dominujący człon D·tan δψ — przy 10 px na 25 m dekodowanie wzoru
   jest jednak nierealne.

## Pliki

- `RECON_KOTW.md` (ten raport).
- `r1_widocznosc_raw.json` (per epizod, okna i przerwy) i `r1_widocznosc.json` (agregat).
- `r1_geometria.json`, `r2_poprawka.json`, `r2_yaw_s4.json`, `r5_pila.json`.
- `tools/kotw_r1.py`, `tools/kotw_r1_geom.py`, `tools/kotw_yaw.py`, `tools/kotw_r2r5.py`.

Odtworzenie (z korzenia repo):

```
python3 results/KOTW_RECON/tools/kotw_r1.py results/KOTW_RECON/r1_widocznosc_raw.json "FANTOM_S2=results/FANTOM/camp/r*" "PERC2_S2=results/PERC2/s2/b*" "SKAN2_S1=results/SKAN2/s1/b*" "KONT_S4=results/KONT/s4/[cn]*"
python3 results/KOTW_RECON/tools/kotw_yaw.py results/KONT/s4/c0[1258]_s0? results/KONT/s4/c1[01]_s0? results/KONT/s4/c08_s01_r2 > results/KOTW_RECON/r2_yaw_s4.json
python3 results/KOTW_RECON/tools/kotw_r2r5.py results/KOTW_RECON
python3 results/KOTW_RECON/tools/kotw_r1_geom.py results/KOTW_RECON/r1_geometria.json "FANTOM_S2=results/FANTOM/camp/r*" "PERC2_S2=results/PERC2/s2/b*" "SKAN2_S1=results/SKAN2/s1/b*" "KONT_S4=results/KONT/s4/[cn]*"
```

## Diff-stat i porcelain

```
 results/KOTW_RECON/RECON_KOTW.md          |   ~280 +
 results/KOTW_RECON/r1_geometria.json      |    43 +
 results/KOTW_RECON/r1_widocznosc.json     |   847 ++
 results/KOTW_RECON/r1_widocznosc_raw.json |     1 +  (1.8 MB, jeden wiersz)
 results/KOTW_RECON/r2_poprawka.json       |  1484 ++++
 results/KOTW_RECON/r2_yaw_s4.json         |   182 +
 results/KOTW_RECON/r5_pila.json           | 12702 ++++
 results/KOTW_RECON/tools/kotw_r1.py       |   172 +
 results/KOTW_RECON/tools/kotw_r1_geom.py  |    53 +
 results/KOTW_RECON/tools/kotw_r2r5.py     |   141 +
 results/KOTW_RECON/tools/kotw_yaw.py      |    40 +
 11 plików, wyłącznie nowe; 0 linii usuniętych; żaden istniejący plik nie zmieniony
```

Porcelain przed commitem: `?? results/KOTW_RECON/` plus zastane `??` results/DEMO_C/** (bez zmian od początku sesji).

**STOP-KOTWR.** Push = Olga („wypchnięte” — CC przelicza niezależnie R1 i R5). Potem CC: PRE_KOTW albo aneks
zamykający.
