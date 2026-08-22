# PRE_K1 — kontrast osłony z natywnym failsafe PX4 pod utratą GNSS

LiquidPatrol · noga K1 · 22.08.2026 · **status: RATYFIKOWANE przez Olgę 22.08.2026**
(D1–D6 w wersji §8; **D5: tak** — jeden bieg informacyjny δ = 10 s w punkcie 0.5, poza kryterium).
Build startuje od §0 (erratum), potem §3.1–3.3; żaden boot przed commitem erratum i hashem sędziego.

## 0. Erratum „42 m" — pierwszy commit po ratyfikacji

Audyt K1 (RAPORT_K1_AUDIT.md, 2bd76d9) wykazał, że liczba „AUTO.LAND ucieka
42 m" jest asercją bez zachowanego biegu: brak kodu wariantu, trace i ulogu;
występuje wyłącznie w FINDING_clock_and_regime.md:97 i komentarzu
b1bis_fly.py:118. Tymczasem była cytowana jako pomiar.

0.1 Inwentarz cytowań przez grep po repo (co najmniej: RAPORT_R03A §II,
RAPORT_D_B5 §FINAL, spec plansz CONTRAST w gen_subtitles, KIERUNKI_SOTA.md §1,
FINDING, b1bis_fly.py). Każde miejsce dostaje adnotację w miejscu cytowania:
„asserted 09.08, run not preserved — superseded by K1 measurement (PRE_K1)".
Nic nie jest kasowane; tagi v1.0/v3.x nietknięte.

0.2 ERRATUM_42M.md w results/K1/: co, gdzie, dlaczego przeszło (stała w spec
zamiast odczytu z pliku wyników), i reguła naprawcza: liczby na planszach
pochodzą wyłącznie z plików wyników z identyfikatorem biegu, nigdy ze stałych
w kodzie. Generator plansz dostaje asercję: każda liczba ma pole `source_run`.

0.3 Re-montaż plansz z zamiennikiem dopiero po §6 — jeden montaż, z liczbą
zmierzoną, nie z pustym miejscem.

## 1. Pytanie i obiekt roszczenia

Pytanie: czy pod utratą GNSS w trakcie patrolu domyślny failsafe PX4 v1.16.2
(komenda lądowania z warstwy misji) zawiera dron gorzej niż osłona z R0.3a
(REFUSE(POS_DEGRADED) + zejście prędkościowe z v_xy=0), na tej samej
trasie, w tych samych punktach wstrzyknięcia, tym samym habitacie.

Obiekt roszczenia: zawieranie względem R_E = 32 m i wielkość wychylenia
poza punkt wstrzyknięcia. Nie „ile dryfuje estymata" (to R0.3a) i nie
„ile trwa reakcja" (zmierzone: 0.091 s).

Mechanizm, o który pytamy, z kodu v1.16.0 (do potwierdzenia diffem na
v1.16.2 w §3.1): po utracie aidingu EKF2 po `valid_timeout_max` 5 s
(common.h:482) gasi `xy_valid` (ekf.h:231); commander stawia
`local_position_invalid_relaxed` (EstimatorChecks.cpp:748–752); AUTO_LAND
traci warunek (mode_requirements.cpp:139–144) i spada do DESCEND
(framework.cpp:574–587), gdzie kontroler pozycji daje „blind land": zerowe
przyspieszenie poziome + MPC_LAND_SPEED (mc_pos_control.cpp:649–661).
Do tego momentu AUTO_LAND utrzymuje position-hold na dryfującej estymacie.
Przewidywany kształt natywnego przebiegu: ~5–6 s pościgu za estymatą, potem
koasting bez hamowania. Osłona: hamowanie w ≤0.15 s, d_stop ≈1.8 m.

## 2. Ramiona i protokół parowany

Ramię N (natywne): dron w OFFBOARD na trasie R_route' = 19.90 m (ANEKS-4)
z v_max 3.0 m/s; w punkcie wstrzyknięcia harness ustawia `EKF2_GPS_CTRL=0`
(scope D8: clean loss, nie jamming) i w tym samym ticku wysyła
`action.land()` (δ = 0). Harness po wysłaniu komendy przestaje publikować
setpointy (inaczej ramię mierzy harness, nie PX4 — lekcja audytu, czytanie (c)).
Od tej chwili PX4 robi, co robi domyślnie. Żadne parametry failsafe nie są
dotykane: snapshot parametrów z ulogu jest częścią wyniku.

Ramię S (osłona): identyczny bieg do punktu wstrzyknięcia, dalej ścieżka
R0.3a: flaga → debounce → REFUSE(POS_DEGRADED) → zejście D5 (v_xy=0
równocześnie, profil dwufazowy z ANEKS-3quater). Kod r03 bajt-w-bajt jak
w bramce 4/4; sanity `certs_selfcheck` przed serią.

Punkty wstrzyknięcia (parowanie): pięć pozycji na prostej nodze trasy,
w ułamkach długości nogi {0.2, 0.35, 0.5, 0.65, 0.8}, zawsze ta sama noga
(wybór nogi deterministyczny: pierwsza noga po pierwszym narożniku).
Oba ramiona dostają dokładnie te pięć punktów. Dodatkowo dwa punkty
narożnikowe (cięcie w narożniku na v_max, jak S4) — informacyjne, poza
kryterium, bo worst-geometria nie była w audycie i nie chcę jej w kryterium
bez prioru.

Definicja biegu ważnego (wzorem ANEKS-H i ANEKS_D7): headless z dowodem,
`HARNESS_PARAM_PREFLIGHT` przeszedł (assert-on-entry), 90 s konwergencji EKF,
timejump = 0, Δsim/Δwall ≥ 0.95 w epizodzie, ulog PX4 włączony i zachowany
w results/K1/<arm>/<point>/boot<n>/ (nigdy /tmp), stempel wstrzyknięcia
w sim-time. Bieg nieważny habitatowo nie liczy się do budżetu.

Budżet: ≤3 booty na (ramię, punkt), pierwszy ważny jest wynikiem. Razem
nominalnie 10 biegów kryterialnych + 4 informacyjne; z mnożnikiem
doświadczenia 2–3 sesje.

## 3. Instrumentacja i antyselekcja

3.1 Przed pierwszym biegiem: diff plików cytowanych w §1 między v1.16.0
a v1.16.2 (ten sam zestaw ścieżek). Różnica w łańcuchu → do PRE-uzupełnienia
cytatem, zanim cokolwiek poleci. Zero różnic → jedna linia w raporcie.

3.2 Sędzia K1 (`k1_judge.py`) zamrożony commitem PRZED pierwszym biegiem,
hash w ANEKS_K1-1. Czyta GT z gz (streaming sim-time, parowanie jak gt_judge
w r03) i ulog. Liczy dla każdego biegu:
- r_max: maksymalny promień od home w epizodzie (GT),
- r_td: promień touchdownu (GT),
- x_exc: maksymalne oddalenie od punktu wstrzyknięcia (GT),
- t_td: czas wstrzyknięcie→touchdown (sim),
- breach: r_max > R_E,
- sekwencja nav_state z czasami (ulog `vehicle_status`), czas zgaśnięcia
  `xy_valid` (ulog `vehicle_local_position`), ack komendy land
  (ulog `vehicle_command_ack`),
- dla S: czas REFUSE od flagi, ε_pos na touchdown (jak D13).
Unit-test sędziego na syntetycznej trajektorii z podstawionym home i skew.

3.3 Skrypt agregujący (parowanie po punkcie, mediana i rozrzut Δ, pooled_std
po punktach) commitowany razem z sędzią. Po pierwszym biegu nic w sędzi,
agregacie ani progach się nie zmienia.

3.4 Predykcja CC, prerejestrowana: N — Descend po ~5 s, x_exc rzędu
10–15 m (pościg + koasting), breach możliwy przy punktach 0.65/0.8, ale
nie pewny; S — x_exc 2–4 m, 0 breach. Czyli spodziewam się przewagi
ilościowej, a nie pewnego naruszenia granicy. Nota kalibracyjna jak
w PROMPT_K1_AUDIT: predykcje CC w tym programie trafiały rzadziej niż co
drugą.

## 4. Kryteria — zamrożone, dwustronne

Liczone wyłącznie na pięciu punktach prostej, parowane.

(+) KONTRAST STOI: breach_S = 0/5 ∧ breach_N ≥ 1/5 ∧ mediana(Δx_exc = N−S)
> pooled_std. Roszczenie w raporcie: „domyślny failsafe PX4 pod utratą GNSS
narusza R_E w k/5 zmierzonych punktów; osłona zawiera w 5/5; różnica
wychylenia mediana X m (IQR)". Plansza CONTRAST dostaje te liczby i
identyfikatory biegów.

(±) PRZEWAGA ILOŚCIOWA BEZ NARUSZENIA: breach_N = 0/5 ∧ breach_S = 0/5 ∧
mediana(Δx_exc) > pooled_std. Roszczenie degraduje się do ilościowego:
osłona ogranicza wychylenie, ale domyślny PX4 w tej geometrii również
zawiera. Plansza CONTRAST traci „ucieczkę", zostaje różnica wychylenia
z etykietą, że obie konfiguracje zawierają.

(0) NULL — kryterium śmierci pozycji 1: breach_N = 0/5 ∧ |mediana(Δx_exc)|
≤ pooled_std. Domyślny fallback PX4 zawiera równie dobrze. Pozycja 1 umiera
jako kierunek SOTA; wartość osłony pozostaje w autoryzacji i dowodzie
formalnym, nie w zawieraniu. Plansza CONTRAST zostaje usunięta z montażu
(erratum pozostaje). Następny krok: PRE dla pozycji 2.

(−) WYNIK PRZECIW ZAŁOŻENIOM: breach_S ≥ 1/5. To nie jest „porażka K1",
to naruszenie twierdzenia P2-ε w jego deklarowanym scope — STOP, raport,
osobna decyzja; nie stroimy, nie powtarzamy.

Każdy inny układ liczb (np. breach_N ≥ 1 przy Δ ≤ pooled_std) raportowany
jako MIESZANY z pełną tabelą, bez zaokrąglania do którejś litery.

## 5. Zagrożenia wierności, nazwane z góry

- SITL ma quasi-idealne IMU; dryf w realu większy → obie liczby rosną,
  kierunek ryzyka dla N gorszy (dłuższy pościg za gorszą estymatą), dla S
  neutralny (hamuje niezależnie od estymaty). Pisać kierunek, nie
  „HIL potwierdzi".
- Koasting w Descend zależy od modelu oporu gz x500 — liczba nieprzenośna,
  mechanizm przenośny. Jedna linia w raporcie.
- δ = 0 jest najkorzystniejsze dla ramienia N (komenda land wchodzi, zanim
  xy_valid zgaśnie). Wariant δ = 10 s (land po zgaśnięciu → czytanie (c):
  komenda odrzucona, dron w OFFBOARD bez setpointów → COM_OF_LOSS_T →
  natywny fallback z innej ścieżki) jest realistyczny, ale to osobny tryb:
  jeden bieg informacyjny w punkcie 0.5, poza kryterium, z pełną sekwencją
  nav_state jako wynik opisowy. Decyzja D5.
- Denial przez `EKF2_GPS_CTRL=0` ≡ utrata danych dla flag EKF — potwierdzone
  w audycie §4b; scope roszczenia: clean loss, nie spoofing.

## 6. Produkt

RAPORT_K1.md: §I tabela 5 punktów × 2 ramiona z sekwencjami nav_state,
§II werdykt wg §4 z liczbami i identyfikatorami biegów, §III erratum 42 m
(odsyłacz do §0) i brzmienie, które zastępuje asercję, §IV zagrożenia §5,
§V informacyjne (narożniki, δ = 10 s). Plansza CONTRAST regenerowana
z pliku wyników zgodnie z regułą 0.2 i jeden re-montaż DEMO_B_A1_A3_v3_1
(B6-bis: zmiana planszy na osądzonych klatkach, zero nowych prób).

## 7. Stop-rules

SR-K1 `git log origin/master..HEAD` niepuste ⇒ STOP.
SR-K2 Erratum §0 przed pierwszym biegiem; brak commita erratum ⇒ biegi
nieważne z definicji.
SR-K3 Sędzia/agregat/progi po pierwszym biegu nietknięte; poprawka błędu
w sędzi = nowy hash + wszystkie dotychczasowe biegi przeliczone jawnie,
z tabelą „przed/po".
SR-K4 Ramię N z setpointami harnessu po komendzie land ⇒ bieg nieważny
(mierzy harness).
SR-K5 Trzeci boot nieważny na (ramię, punkt) ⇒ punkt raportowany jako
niewykonany, nie czwarty boot.
SR-K6 Jakakolwiek zmiana parametru PX4 poza `EKF2_GPS_CTRL` w epizodzie ⇒ STOP.
SR-K7 Wynik (−) ⇒ STOP po pierwszym wystąpieniu, bez dokończania serii.

## 8. Decyzje (RATYFIKOWANE 22.08.2026)

D1 Erratum §0 w brzmieniu jak wyżej (adnotacja in-place, nic nie kasowane). **TAK**
D2 Ramię N = `action.land()` przy δ = 0 z zatrzymaniem strumienia setpointów. **TAK**
D3 Pięć punktów na prostej nodze w ułamkach {0.2, 0.35, 0.5, 0.65, 0.8},
    narożniki ×2 informacyjnie. **TAK**
D4 Kryteria §4 dosłownie, z (0) jako kryterium śmierci pozycji 1. **TAK**
D5 Wariant δ = 10 s: jeden bieg informacyjny w punkcie 0.5, poza kryterium. **TAK**
D6 Budżet ≤3 booty na (ramię, punkt), 2–3 sesje, bez rozszerzeń bez dokumentu. **TAK**
