# PRE_KONT — prerejestracja nogi 2d „kontynuacja zadania po utracie GNSS": przepływ optyczny trzyma pozycję lokalną, sieć dalej pilnuje intruza przez policzony czas, osłona z nową barierą czasową kończy lot w kopercie

CC · 6.11.2026 · po CO-KONT-0 (f680d071), zweryfikowanym z repo.
Wymaga ratyfikacji Olgi („ratyfikuję"); po niej PROMPT_KONT_S1 (sonda),
wklejany razem z tym dokumentem. Noga wieloetapowa: S1 sonda → S2
charakteryzacja → S3 osłona i certy → S4 bramka live. Każdy etap kończy
się STOP-em i weryfikacją CC z repo; nic nie przechodzi do następnego
etapu bez numerowanego sygnału.

**Stan wyjścia (z repo, nie z pamięci):** dziś po utracie GNSS osłona
odmawia w 0.104–0.116 s, przez 4.0 s prowadzi zejście D5, potem PX4 odbiera
offboard (xy_valid=False przy 4.00 s w 12/12, `results/K2/ulog_wyciag_k2c.jsonl`)
i robi blind land 0.7 m/s. Zawieranie w lotach sieci pod utratą jest
zmierzone (12/12 GT), nie dowiedzione, bo przesłanka P2-ε (r_est ≤ 19.90)
nie obowiązuje dla sieci (r_max > 19.90 w 44/48 scenariuszy; ANEKS_KONT-0 E3).
Recon (a606c115): samo IMU daje 4 s i ścianę natywną (ścieżka B zamknięta);
przepływ optyczny z dalmierzem jest w stosie bez przebudowy (x500_flow,
libOpticalFlowSystem 43df8c4f, GZBridge subskrybuje flow i lidar), ale grunt
world_demo_A3 jest jednolity (luki bez cechy p95 5.96 s, aiding gaśnie po
>1 s luki) i pod przepływem dzisiejsza flaga `dead_reckoning` nie odpali.

## §1. Teza i pytania (FROZEN)

Teza Olgi: **mała sieć umie latać** — tu: zadanie sieci nie zależy od GPS,
bo sieć widzi cel, nie mapę (R5: wejścia względne + prędkość własna EKF,
zero pozycji absolutnej). Pozycji absolutnej potrzebuje osłona. Noga pyta,
czy z przepływem optycznym da się utrzymać zadanie przez policzony czas
i zakończyć je w kopercie z dowodem, a nie tylko z pomiarem.

- **Q1 (S1, sonda):** czy przepływ + dalmierz utrzymuje ważną pozycję lokalną
  (xy_valid, brak nav 14→12) przez ≥ 70 s orbity po odcięciu GNSS w locie,
  na świecie, który nie zmienia tego, co widzi kamera przednia.
- **Q2 (S2):** jak rośnie ε(t) = |pos_EKF − (pos_GT ⊖ T_home)| pod orbitą
  nauczyciela z przepływem i ile dryfuje zejście D5 po kontynuacji (Δ_D5).
- **Q3 (S3):** czy osłona z nowym stanem KONTYNUACJA ma dowód zawierania
  z barierą zależną od czasu i czy obowiązuje on od pierwszej chwili utraty,
  także dla sieci (bariera nominalna, §2.5).
- **Q4 (S4):** czy sieć w pętli trzyma zadanie pod utratą przez T*, a potem
  osłona kończy lot w deadline, z zerem naruszeń.
- **Q5 (S2–S4, koszt):** ile scenariuszy siatki traci bariera nominalna.

## §2. Projekt (FROZEN)

1. **Model** (addytywnie): `Tools/simulation/gz/models/x500_mono_cam_flow/model.sdf`
   = `include` x500_mono_cam (pin mono_cam 3354ae1e nietknięty) + czujnik
   przepływu i lidar skopiowane z x500_flow. Częstotliwość kamery przepływu
   wolno obniżyć w kopii, wartość zapisana w manifeście. Airframe bez nowego
   pliku: `PX4_SYS_AUTOSTART=4010` + `PX4_SIM_MODEL=gz_x500_mono_cam_flow`.
2. **Parametry** przez nowy moduł konfiguracji nogi (`r03/kont_config.py`,
   NOWY; `HARNESS_PARAM_PREFLIGHT` w r03/config.py FROZEN): EKF2_OF_CTRL=1,
   EKF2_RNG_CTRL=1, EKF2_HGT_REF=0 (baro), assert-on-entry jak R-D1,
   echo w manifeście. Odcięcie GNSS w locie: EKF2_GPS_CTRL=0 jak w K2,
   z odtworzeniem na wejściu następnego bootu.
3. **Świat:** opcja (c) z reconu — dekal z teksturą na gruncie z
   `visibility_flags`, maska mono_cam przez `experimental:params` przy
   `include`. **Warunek dopuszczenia (ANEKS_KONT-0 §4):** identyczność klatek
   mono_cam, ta sama poza, A3 vs A3+dekal+maska, różnica ≤ szum renderu
   zmierzony w kontroli A3 vs A3. Brak identyczności ⇒ STOP i decyzja
   Olgi: opcja (a) (nowy świat + rewalidacja percepcji) albo zamknięcie.
   Plik świata A3 i pin nietknięte w każdym wariancie.
4. **Flaga utraty (O0):** źródło = `estimator_status_flags.cs_gnss_pos`
   (już w `dds_topics.yaml:23`), debounce i histereza jak `_pos_monitor`.
   Pomiar A-flag w S1: opóźnienie od odcięcia do flagi, 0 przeskoków w
   nominale. `dead_reckoning` zostaje logowane pasywnie.
5. **Bariera nominalna (ANEKS_KONT-0 §3):** w reżimie KONT osłona pilnuje
   od startu r_est ≤ R_nom := R_E − d_stop − ε_b(0⁺) − Δ_D5. Przekroczenie
   w nominale ⇒ odmowa ruchu na zewnątrz (gramatyka R-G, nowy próg),
   nie lądowanie. Bez tego przesłanka dowodu nie obowiązuje w chwili utraty.
   R_nom liczona regułą §3 po S2, zamrożona aneksem przed S3.
6. **Stan KONTYNUACJA (O1–O7 z reconu):** po fladze utraty ALLOW trwa,
   dopóki t_KONT ≤ T* ∧ r_est ≤ R_E − d_stop − ε_b(t_KONT) − Δ_D5;
   pierwsze naruszenie ⇒ istniejące REFUSE(POS) → D5. ε_b, Δ_D5, T* =
   zamrożone krzywe/liczby (założenie [A4] „A-kont", jak A-episode w R0.3a;
   przekroczenie ε_b w locie = FAIL nogi, nie strojenie). Certy: P1, P5,
   P7 od nowa; nowy P9_kont (P2-ε(t) z ostrością dwustronną) obok P2-ε;
   P2, P2_vmax3p1, P4, P6_d5, P8 nietknięte z uzasadnieniem; P6_d5
   cytowany jawnie jako dowód o komendach, nie o pojeździe.
7. **Przyrządy (lekcje ANEKS_KONT-0):** wyciąg z ulogu per boot commitowany
   jako jsonl (nav_state, xy_valid, failsafe, cs_gnss_pos, flow quality,
   t_offboard_lost) — każdy wniosek o stanie pojazdu z ulogu, nie z listy
   zdarzeń; GT przez gt_judge.py (ramka T_home, ENU/NED, skew); przyziemienie
   = GT z < 0.15 m, nie koniec profilu komend; higiena zegara jak
   ANEKS_SKAN2-0b (timesyncd stop, próbnik 60 s przed bootem); V2′ ≥ 0.90.

## §3. Reguły zamrożone przed danymi

- **ε_b(t):** z lotów S2 (ważnych, ≥ 8), dla każdego koszyka 1 s od flagi:
  1.5 × max ε, następnie obwiednia niemalejąca. **Δ_D5:** 1.5 × max po lotach
  przyrostu ε od REFUSE do przyziemienia GT.
- **T*:** największe t ≤ 70 s, przy którym ε_b(t) + Δ_D5 ≤ m_p50 = 5.79 m
  (R4 reconu, mediana marginesu po 48 scenariuszach, zamrożona tu).
  Jeśli ε_b(t)+Δ_D5 nie przekracza 5.79 do 70 s, T* = 70 s (cała orbita).
- **R_nom:** R_E − d_stop − ε_b(0⁺) − Δ_D5 z tych samych krzywych.
- Wartości wpisuje ANEKS_KONT-2 przed jakimkolwiek kodem S3. Zmiana
  reguły po danych = STOP dokumentem, nie poprawka.

## §4. Etapy, bramki, śmierci

**S1 — sonda (≤ 3 boote, budowa modelu i świata, 0 kodu osłony).**
PASS ⇔ (i) identyczność klatek mono_cam (§2.3); (ii) w locie nauczyciela
po odcięciu GNSS: xy_valid=True i brak nav 14→12 przez ≥ 70 s orbity,
z ulogu; (iii) cs_gnss_pos przełącza się ≤ 0.5 s od odcięcia i ma 0
przeskoków w nominale; (iv) sonda kadencji OPS ≥ 10 Hz z drugą kamerą;
(v) opisowo: jakość flow, luki aidingu, ε(t) z jednego lotu, różnica
estymaty nominalnej z flow i bez. **Śmierć S1:** (ii) nie zachodzi na
żadnej rozsądnej częstotliwości flow ⇒ 2d CLOSED z liczbą („przepływ na
tym gruncie nie utrzymuje pozycji lokalnej dłużej niż X s"); (i) FAIL ⇒
STOP z decyzją Olgi o (a); (iv) FAIL przy każdej częstotliwości ⇒ CLOSED.

**S2 — charakteryzacja (≤ 14 bootów, 1 odcięcie = 1 boot).** Nauczyciel
(orbit_executor) pod orbitą ≥ 60 s po odcięciu, potem REFUSE→D5 do
przyziemienia GT; komórki siatki z najmniejszym marginesem (z R4: m ≤ 3.5)
i z medianą. ≥ 8 ważnych lotów. Wynik: krzywe, T*, R_nom, koszt bariery
nominalnej (ile z 48 scenariuszy ma r_max > R_nom). **Śmierć S2:** T* < 10 s
⇒ CLOSED z liczbą T* (kontynuacja istnieje, ale jest za krótka, żeby mieć
sens operacyjny); R_nom < r_p50 mediana 11.0 m ⇒ CLOSED (bariera zabiera
zadanie, zanim cokolwiek się stanie).

**S3 — osłona i certy (0 bootów, ≤ 2 sesje).** Kod KONT + flaga + bariera
nominalna w nowej wersji osłony (stara nietknięta, tryb przez flagę jak
token_gated), P1/P5/P7 od nowa, P9_kont nowy, selfcheck ×2, testy
deterministyczne, różnicówka lustra jak FV. **Śmierć S3:** kontrprzykład
P9_kont, którego nie da się usunąć bez zmiany reguły §3 ⇒ STOP dokumentem.

**S4 — bramka live z siecią (≤ 16 bootów: 12 + 4 powtórki).**
12 epizodów z odcięciem, 6 komórek × 2 ziarna, w tym 4 komórki o
najmniejszym marginesie; odcięcie w fazie orbity (t_entry + 30 s jak K2);
plus ≥ 12 epizodów nominalnych z uzbrojonym monitorem. Sieć net_skan2.
PASS ⇔ wszystkie:
- (a) 0 naruszeń R_E (GT), całe epizody do przyziemienia;
- (b) ε(t) ≤ ε_b(t) przez całą KONT i Δ ≤ Δ_D5 w zejściu (walidacja A-kont);
- (c) zadanie trwa: w ≥ 10/12 sieć ma ważny track i odległość do intruza
  w paśmie orbity nauczyciela (z RAPORT_BENCH) przez min(T*, chwila
  legalnego wyjścia barierą);
- (d) REFUSE ≤ 0.15 s od wyczerpania T* albo naruszenia bariery;
- (e) brak nav 14→12 w KONT (ulog), offboard do REFUSE;
- (f) 0 fałszywych KONT/REFUSE w nominale.
Dokładnie jedno niepowodzenie (c) ⇒ NIEROZSTRZYGNIĘTE; (a), (b) albo (e)
⇒ FAIL; ≥ 2 × (c) ⇒ FAIL.

**Twarde STOPy verbatim we wszystkich etapach: breach ⇒ STOP; REFUSE(POS)
poza scenariuszem ⇒ STOP; budżet ⇒ STOP.** Budżet całkowity ≤ 33 booty,
≤ 6 sesji. Zero zmian kanonu percepcji, sieci, sędziego D6, pinów; zero
edycji istniejących plików poza dopiskami addytywnymi do rejestrów.

## §5. Zdania cytowalne (prereg)

- PASS: „Po utracie GNSS mała sieć dalej pilnuje intruza przez T* s na
  przepływie optycznym, a osłona z barierą zależną od czasu kończy lot
  w kopercie: 12/12, zero naruszeń; zawieranie dowiedzione (P9_kont) przy
  założeniu A-kont, zmierzonym w locie. SITL, grunt z dekalem pod
  przepływ, przepływ i dalmierz modelowane."
- CLOSED w S1/S2: zdanie z liczbą, która zamknęła („przepływ trzyma X s",
  „T* = X s").
- Nie wolno: „nawigacja bez GPS" bez dopisku „przepływ optyczny nad
  teksturą, SITL"; „jamming/spoofing" (odcięcie = clean loss, EKF2_GPS_CTRL=0);
  czegokolwiek o realnym sprzęcie; przenoszenia T* na inny grunt.

## §6. Predykcje CC (do KSIĘGI)

- **P-KONT-1 (0.50):** S1 przechodzi na opcji (c) — maska przez
  `experimental:params` działa i klatki mono_cam są identyczne.
- **P-KONT-2 (0.65):** przy teksturowanym gruncie aiding trzyma ≥ 70 s
  orbity bez nav 14→12.
- **P-KONT-3 (0.55):** T* ≥ 30 s.
- **P-KONT-4 (0.45):** bariera nominalna kosztuje 0 scenariuszy siatki
  (R_nom ≥ 26.2 m).
- **P-KONT-5 (0.60):** pod warunkiem dojścia do S4 — PASS.
- **P-KONT-6 (0.90):** breach 0 w całej nodze.
- Całość (S1→S4 PASS) ≈ 0.25–0.3; najbardziej prawdopodobny koniec poza
  PASS: zamknięcie w S1 na świecie albo w S2 na krótkim T*. Każdy z tych
  końców daje liczbę, której program dziś nie ma.

## §7. Kolejność i co nie wchodzi

S1 → STOP-KONT1 → weryfikacja CC → PROMPT S2 → … Łańcuch jedną nogą;
w trakcie nie otwiera się innych pozycji. Nie wchodzą: wiatr (kanon V-A3),
noc, VIO/SLAM (hydrauliki nie ma, x500_vision to wyrocznia GT), odporność
sieci na bias own_v poza tym, co pokaże S4 (trening miał dane czyste —
ryzyko nazwane dla (c)), lot f4 (nazwany, nieścigany).

Ratyfikacja: „ratyfikuję". Sygnały bez numeru wykonawca odrzuca.
