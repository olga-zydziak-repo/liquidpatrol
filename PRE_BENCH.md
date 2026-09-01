# PRE_BENCH — Verified Patrol Bench (egzekutor podejścia i orbity: nauczyciel + kotwica)

LiquidPatrol · pozycja 2 planu · CC 1.09.2026 · **status: do ratyfikacji (D1–D10)** · wejście: RECON_BENCH.md
(6b32b07), INFRA-3 CLOSED (gniazdo `SetpointSource`, wrapper `harness/run_boot.sh`)

## §0. Czym ławka jest, czym nie jest

Jest: skryptowym egzekutorem podejścia i orbity wokół ruchomego intruza, latającym w OFFBOARD przez gniazdo
`SetpointSource` pod NIETKNIĘTĄ osłoną P2-ε, z (a) ZMIERZONĄ skutecznością orbity pod zamrożonym sędzią
na zamrożonej siatce scenariuszy, (b) zbiorem demonstracji w zamrożonym schemacie, (c) per-scenariuszowymi
wynikami kotwicy do przyszłego parowania z siecią.

Nie jest: roszczeniem o percepcję (stan intruza pochodzi z track-feedu EMULOWANEGO przez harness — każdy
wynik ławki i każde późniejsze roszczenie o sieci nosi etykietę „pod emulowanym track-feedem (L, σ, f, p_drop)"),
roszczeniem o autonomię, ani nogą sieci — sieć dostaje własne PRE po ławce.

Innowacyjność: warstwa „znane prymitywy w nowej kompozycji" — orbit guidance to podręcznik; nowe jako
zdolność programu jest tylko: kontroler wymienny bez dotykania certów + pomiar mianownika dla sieci.
Żadnego „nowe koncepcyjnie".

## §1. Teza i kryterium dwustronne

Teza: skryptowy egzekutor osiąga na siatce scenariuszy skuteczność orbity p_exec wystarczającą, by służyć
za nauczyciela i kotwicę, nie wyzwalając osłony w nominale.

(+) PASS ławki: p_exec ≥ 0.80 na ≥ 36 ważnych epizodach siatki (§3) ∧ 0 REFUSE w nominale ∧ 0 breach
∧ zbiór ≥ 90 udanych demonstracji w schemacie §4 (train+test). p_exec jest MIANOWNIKIEM dla pozycji 3:
sieć musi osiągnąć ≥ 0.9·p_exec na tej samej siatce, tym samym sędzią, tym samym feedzie.
(−) ŚMIERĆ: po budżecie §3 p_exec < 0.60 ⇒ nauczyciel nieużyteczny; pozycja 3 traci warunek wstępny
(bez treningu na zbiorze, który uczy porażki); slot orbity zostaje skryptowy = wynik pełnoprawny; nowy
egzekutor = nowe PRE, nie łatka.
Środek (0.60 ≤ p_exec < 0.80): NIEROZSTRZYGNIĘTE, dokument CC. Werdykt zawsze trójwynikowy.
Dodatkowe zerwania (STOP dokumentem, nie strojeniem): breach w jakimkolwiek epizodzie (domena certów);
≥ 2 REFUSE w nominale w jednej sesji (albo orbita narusza założenia osłony, albo ruch orbitalny degraduje
EKF — obie rzeczy są znaleziskiem, nie usterką do dostrojenia).

## §2. Decyzje do ratyfikacji

D1 Stan intruza dla kontrolera = track-feed emulowany przez harness. Mechanizm: moduł `harness/track_feed.py`
(niepinowany, `feed_sha` per boot w manifeście i logu demonstracji) subskrybuje `/world/W/pose/info`
(49.8 Hz, R2) i dostarcza kontrolerowi w procesie gate'a próbki z: kadencją f = 10 Hz, opóźnieniem L = 0.20 s,
szumem σ_xy = 0.5 m / σ_z = 0.3 m (Gauss, iid), zanikiem p_drop = 0.05 na próbkę (hold-last, rośnie
`track_age`), prędkością trk_vel = EMA różnic skończonych zaszumionych pozycji (τ = 0.5 s). RNG feedu z ziarna
epizodu. Granica dyscyplinarna audytowalna testem: moduły kontrolerów (`r03/controllers/orbit*.py`, później
`net*.py`) nie importują niczego z gz i nie zawierają łańcuchów topików GT — test statyczny w commicie;
jedynym konsumentem GT po stronie kontrolera jest feed. Kiedy pęka: parametry feedu zbyt łaskawe ⇒ sieć
uczy się „prawie GT"; dlatego wartości są jawne, zamrożone i powtórzone w każdej tabeli wyników. Percepcja
runtime'owa (detector_node+mti) — poza zakresem; trigger do rewizji: percepcja odpalona w stacku z własnym
PRE. Wartości L/σ/f/p_drop: do Twojej ratyfikacji; mechanizm ważniejszy niż liczby.

D2 Intruz = model statyczny `r02/intruder_model.sdf` + `set_pose` 20 Hz (applied 19.6–19.9 Hz, ok_rate 0.87,
R1), trajektoria `scripted_pose(sim_t; seed)` deterministyczna w komendzie; GT sędziego = poza ZASTOSOWANA
z `pose/info` (nie komenda), więc chybienia set_pose (13 %) są w danych, nie ukryte. Ruch: odcinki stałej
prędkości, zmiana kursu co U(10, 20) s, prędkość v_intr ∈ {0, 0.5, 1.0} m/s, z = 10 m stałe, pozycja
ograniczona do dysku r ≤ 18 m wokół home (32 − 10 − 3.5 − 0.5: R_E minus r_hi minus dryf K1 minus zapas).
Aktor z `dynamic_pose` odrzucony: gładszy, ale trajektoria pieczona w SDF — brak ziarna per epizod.

D3 Orbita: r_orb = 8 m, pasmo [6, 10] m, prędkość styczna nominalna 1.8 m/s (okres ≈ 28 s; przy v_intr 1.0
|v| ≤ 2.8 < V_MAX 3.0), kierunek CW/CCW z ziarna, wysokość orbity z_orb = z_intr + 2 m = 12 m, minimalna
separacja 3D d_min ≥ 4 m (kryterium bezpieczeństwa epizodu). Prawo sterowania egzekutora (skrypt, bez
losowości): podejście — v = V_MAX·wersor(rel) z hamowaniem do wejścia w pasmo; orbita — składowa styczna
1.8 m/s + korekcja radialna k_r·(d − r_orb) obcięta + feedforward trk_vel + k_z·(z_orb − z); saturacja
|v| ≤ V_MAX. Wejścia egzekutora = DOKŁADNIE wejścia sieci (feed + własny stan z EKF), żadnego GT. Koperta z R5:
r_orb ≤ 15 m bezpieczne, home→intruz ≤ 18 m + 10 m + dryf 3.5 m = 31.5 m < 32 m; ciasno — dlatego dysk 18 m
jest twardy w skrypcie intruza. Stałe egzekutora (k_r, k_z, hamowanie) strojone WYŁĄCZNIE w fazie build
i zamrożone `executor_params_sha` przed pierwszym lotem kryterialnym.

D4 Schemat rekordu demonstracji — kontrakt danych modelu, §4. Logger po stronie kontrolera (R4: `v_ned` nie
jest logowany per tick w trace; logger w module kontrolera domyka lukę bez dotykania pinów).

D5 GT dla sędziego: harness pisze `gt_intruder.jsonl` z `pose/info` (poza zastosowana, czas sim); GT drona
= wiersze `gt` trace (jak dziś); wspólna ramka NED przez `common/frames.py:drv2ned`. GT wyłącznie sędzią.

D6 Sukces epizodu (wszystkie): (a) wejście w pasmo w ≤ 25 s od startu epizodu; (b) frakcja czasu w paśmie
≥ 0.85 w fazie orbity T_orb = 70 s; (c) skumulowany omiatany namiar względem intruza ≥ 630° w T_orb;
(d) d_min ≥ 4 m; (e) 0 REFUSE ∧ breach False. Wszystko w czasie SIM z GT. p_exec = udane / ważne na siatce.
Metryki (b)(c) są nienasycone — raportujemy medianę + IQR frakcji w paśmie i omiatania, nie tylko binarny sukces.

D7 Śmierć i zerwania: §1. Dodatkowo śmierć fazy build: egzekutor nie wchodzi w pasmo w 2 bootach shakeout ⇒
STOP, dokument (nie „jeszcze jeden boot").

D8 Budżety: build ≤ 1 sesja (bez lotów kryterialnych: egzekutor, feed, sędzia, logger, testy); shakeout ≤ 2 booty
(kind=diag, nie wchodzą do p_exec ani do zbioru); kampania ≤ 3 sesje / ≤ 40 bootów; epizody/boot = 4
(lot ≤ 10 min); env-fail booty i env-nieważne epizody nie liczą się, scenariusz wraca na koniec kolejki
(liczy się pierwsza ważna próba, próby numerowane w manifeście); zero wybierania epizodów.

D9 Ważność epizodu (reguła habitatu dla długich okien — ŚWIADOME odejście od K1 H2): K1 sądził okno ~4 s
i Δsim/Δwall ≥ 0.95; przy epizodzie ~100 s i 1–3 deep-stallach na boot (§7 INFRA1) ta reguła odrzuciłaby
większość epizodów. Mechanizm: metryki D6 są geometryczne i liczone w czasie sim z GT, więc stall (spójny
lockstep) ich nie zniekształca; zniekształca tylko pętlę kontrolera (wall-clock) w chwili stallu. Reguła:
H1 timejump = 0 w boocie; H2′ per epizod: liczba deep-stalli (rtf < 0.5) ≤ 3 ∧ najdłuższy stall ≤ 1.5 s wall
∧ Δsim/Δwall ≥ 0.90 na epizodzie (z `rtf_stream`). Ticki w stallu dostają flagę `stall=1` w logu demonstracji
(deklarowane wykluczenie w treningu). Kontrola: sukces vs liczba stalli raportowany (0 vs 1–3) — jeśli
stall obniża sukces, D9 jest do rewizji, nie do ukrycia.

D10 Świat: `world_demo_A3`, FILM=0 (kamera filmowa off — CPU); re-render (pozycja 5) odlatuje wybrane ziarna
z FILM=1, co umożliwia determinizm D2. Kadencja set_pose 20 Hz.

## §3. Protokół

Siatka: 3 prędkości intruza × 4 geometrie początkowe (intruz w zasięgu 15 m od home, namiar 0/90/180/270°)
= 12 komórek. Ziarna: k = 3 na komórkę do p_exec (36 epizodów), dalsze ziarna do zbioru (k do 10). Manifest
scenariuszy (komórka, ziarno, parametry trajektorii, kierunek orbity) WYGENEROWANY I COMMITOWANY przed
kampanią; kampania lata go w stałej kolejności. Epizod: start = dron w hoverze na home ± 1 m, |v| < 0.3 m/s,
pos_valid, intruz w pozie startowej; koniec = T_entry + T_orb albo REFUSE/breach; reset ≤ 30 s (powrót do
hoveru na home); niespełniona bramka resetu ⇒ boot kończy się lądowaniem, epizody dotąd ważne.

Fazy: build (1 sesja, bez lotów) → zamrożenie (§7) → shakeout ≤ 2 booty diag → STOP-1 (CC ratyfikuje
zamrożenie i shakeout) → kampania (≤ 3 sesje) z raportem po każdej sesji (tekst płaski) → STOP-2 → RAPORT_BENCH.
Wykonawca po każdej sesji: p_exec bieżące, tabela epizodów (komórka, ziarno, próba, ważność, sukces,
frakcja w paśmie, omiatanie, d_min, REFUSE, stalle), zero interpretacji.

Stop-rules: SR-1 git; SR-2 piny/sędziowie/wrapper nietknięte, sędzia ławki zamrożony SHA przed pierwszym
lotem kryterialnym; SR-3 strojenie egzekutora po zamrożeniu = nowa seria (nowy `executor_params_sha`,
stare epizody nie łączą się z nowymi); SR-4 wybieranie epizodów/bootów ⇒ seria nieważna; SR-5 breach ⇒ STOP
natychmiast; ≥ 2 REFUSE-nominal/sesję ⇒ STOP; SR-6 bramka procesowa wrappera obowiązuje, żadnych pilotów
na maszynie; SR-7 liczba bez przyrządu (sim/wall/nav) i pliku nie jest faktem; SR-8 zapisy tylko do
`results/BENCH/**`.

## §4. Schemat rekordu demonstracji (zamrożony kontrakt danych)

Plik `demo.jsonl` w katalogu bootu, pisany przez logger w module kontrolera, jeden wiersz na tick (20 Hz,
DT 0.05 s), zaokrąglenie 3 miejsca (jak trace). Pola:
- `t_sim`, `tick`, `episode_id`, `scenario_id`, `seed`, `attempt`
- własny stan (z EKF, jak w `step`): `own_pos_ned[3]`, `own_vel_ned[3]`
- feed: `trk_pos_ned[3]`, `trk_vel_ned[3]`, `track_age_s`, `track_valid`
- wyjście egzekutora: `cmd_v_ned[3]` (dokładnie to, co poszło do `set_velocity_ned`)
- flagi: `phase` (approach/orbit/reset), `stall` (0/1 z rtf_sampler, join po czasie wall), `controller`,
  `controller_sha`, `feed_sha`, `executor_params_sha`
Kanoniczny wektor cech (9): [rel_x, rel_y, rel_z, own_vn, own_ve, own_vd, trk_vn, trk_ve, track_age_s], gdzie
rel = trk_pos − own_pos w NED; liczony JEDNĄ funkcją `bench/features.py` używaną i w treningu, i w locie
(zero rozjazdu train/flight). Cel: `cmd_v_ned`. Podział: TEST = epizody z seed ≡ 0 (mod 4), TRAIN = reszta,
zamrożony teraz; PRE sieci może dodać analizę hold-out per komórka, nie może ruszyć podziału. Sędzia
demonstracji: do zbioru „udanych" wchodzą wyłącznie epizody z sukcesem D6; epizody nieudane zostają
w pliku z etykietą (materiał kontrolny), nie do imitacji.

## §5. Sędzia orbity — test przed przyrządem

`bench/bench_judge.py`, wejście: trace gt (dron) + `gt_intruder.jsonl` + `rtf_stream` + zdarzenia osłony
z trace; wyjście `episode_judge.json` per epizod. Zamrożony SHA przed pierwszym lotem kryterialnym.
Testy syntetyczne w commicie (bez SITL): idealny okrąg r = 8 wokół intruza jadącego 1.0 m/s ⇒ SUKCES;
hover na home ⇒ FAIL(a); okrąg r = 12 ⇒ FAIL(b); 1.5 okrążenia ⇒ FAIL(c); przelot przez intruza ⇒ FAIL(d);
wstrzyknięty REFUSE ⇒ FAIL(e); stall 2 s w połowie epizodu przy metrykach w czasie sim ⇒ metryki bez zmian
(dowód D9). Test feedu: statystyka L/σ/p_drop na syntetycznym GT zgadza się z deklaracją. Test granicy:
grep kontrolerów bez importów gz i bez łańcuchów topików GT. Test replay: egzekutor na nagranym feedzie
daje bit-identyczne `cmd_v_ned` (determinizm nauczyciela).

## §6. Predykcje CC (prerejestrowane; kalibracja: w programie trafia mniej niż co druga)

P-BE1 p_exec na siatce ≥ 0.85. P-BE2 REFUSE w nominale: 0 zdarzeń w kampanii. P-BE3 pierwsza klasa porażek
= frakcja w paśmie (b) przy v_intr 1.0, nie wejście (a). P-BE4 reguła D9 odrzuca ≤ 15 % epizodów.
P-BE5 największe ryzyko nienazwane wyżej: reset między epizodami (dryf wysokości/EKF po 3 epizodach) tnie
czwarty epizod częściej niż stalle.

## §7. Zamrożenie przed pierwszym lotem kryterialnym (SHA do ANEKS_BENCH-1)

`bench/bench_judge.py`, `bench/features.py`, `harness/track_feed.py` + parametry D1, `r03/controllers/orbit_executor.py`
+ `executor_params`, manifest scenariuszy, schemat §4 (wersja), piny bez zmian {1c584964, 4c440e42, c3ccabe0,
base.py}, `harness/run_boot.sh` bez zmian (delta harnessa dla `gt_intruder.jsonl` i intruza ruchomego =
osobny, mały plik wołany z wrappera przez env — jeśli wymaga edycji wrappera, to jedna linia i STOP-dokument).

## §8. Świadomie otwarte (należą do PRE sieci, nie tu)

Architektura NCP-20 / tiny-MLP, strata, liczba epok, cap 2 sesji, sposób lotu sieci (`CONTROLLER=net`,
ten sam feed, ten sam sędzia, te same komórki i ziarna — parowanie per scenariusz, lekcja K1).
