# PRE_NET — noga sieci (pozycja 3: trening NCP-20 + tiny-MLP · pozycja 4: loty pod osłoną)

LiquidPatrol · CC 5.09.2026 · **status: do ratyfikacji przez Olgę (N1–N8 + pole DAgger)** · wejście:
ławka (+) PASS (ANEKS_BENCH-4), zbiór 114 demonstracji, mianownik p_exec = 0.9167 ⇒ próg sieci 0.825
(≥ 40/48). Wszystko poniżej zamraża się PRZED pierwszą epoką treningu — także protokół lotów pozycji 4,
żeby nie dopasować go do wyników treningu.

## §0. Teza i czego nie twierdzimy

Teza pozycji 4 (teza programu): kontroler wymienia się pod NIEZMIENIONYMI certami — sieć lata przez to samo
gniazdo `CONTROLLER=net`, pod tą samą osłoną, tym samym sędzią, na tym samym feedzie; piny nietknięte.
Sieć jest ładunkiem demonstracyjnym; null NCP↔MLP jest wynikiem raportowalnym (prior z LiquidWatch/3d:
różnicy może nie być). Nie twierdzimy: autonomii, percepcji (feed emulowany — etykieta na każdej tabeli),
przewagi „liquid" przed pomiarem. REFUSE osłony wobec złej sieci to nie porażka programu, tylko druga
połowa tezy — raportowany osobno jako zadziałanie osłony (epizod dla sieci = FAIL).

## §1. Decyzje do ratyfikacji

N1 Architektury (obie, zamrożone kodem przed treningiem): (a) **NCP-20** — komórka CfC, ~20 neuronów,
wejście = kanoniczny wektor 8 cech per tick, stan ukryty ciągły w epizodzie, reset na starcie epizodu;
(b) **tiny-MLP** — te same 8 cech w oknie k = 5 ticków (40 wejść, zero-padding na starcie), 2 × 32 ukryte.
Liczba parametrów obu do raportu. Głowa wyjścia obu: tanh × V_MAX (saturacja architektoniczna) + `clip_v`
w kontrolerze (pas i szelki); test kontraktu 10⁴ losowych wejść dla każdej sieci przed jakimkolwiek lotem.
Pamięć jest jedyną różnicą ramion — dynamika ciągła vs okno; to jest całe pytanie „liquid".

N2 Dane: WYŁĄCZNIE 114 udanych demonstracji; ticki `stall=1` i faza reset wykluczone (deklarowane od ANEKS-0);
wejścia = `bench/features.py` (ta sama funkcja w treningu i locie — zero rozjazdu); cel = `cmd_v_ned`.
Podział zamrożony: TEST = seed % 4 == 0 (ziarna 4 i 8) — dotykany RAZ na ramię, po zamknięciu treningu;
walidacja do selekcji modelu = ziarno 2 z TRAIN; reszta TRAIN. Strata: MSE. Hiperparametry w
`net/train_config.json` commitowane PRZED startem; ziarna treningu logowane; żadnego strojenia na TEST.

N3 Bramka offline pozycji 3 (per ramię, po treningu, przed jakimkolwiek lotem):
(i) rollout zamknięty w modelu punktowym z FEED-B (przyrząd z buildu ławki, `point_model`) na komórkach
siatki × ziarna TEST: analog D6 (wejście ≤ 25 s ∧ frac ≥ 0.85 ∧ d_min ≥ 4) w **≥ 10/12 komórek** = PASS
bramki; (ii) RMS(v̂ − v_nauczyciel) na TEST raportowany per epizod (mediana + IQR) — diagnostyka, NIE bramka
(błąd akcji słabo przewiduje zachowanie zamknięte, składanie błędów łapie rollout); (iii) test kontraktu.
Ramię bez PASS po wyczerpaniu capu sesji = nie lata. Oba ramiona bez PASS ⇒ pozycja 4 nie otwiera się,
slot skryptowy na stałe (konsekwencja z planu, wynik pełnoprawny).

N4 **Pole DAgger (Twoja decyzja — trzeci raz, teraz blokuje ratyfikację):** [ TAK / NIE ].
TAK = w capie 2 sesji dozwolona JEDNA runda offline-DAgger per ramię: rollouty sieci w modelu punktowym
z FEED-B → etykiety z zamrożonego egzekutora-wyroczni (840514361e) na stanach sieci → dotrenowanie na
TRAIN+DAgger; trigger wyłącznie FAIL bramki N3(i) w sesji 1; TEST nadal dotykany raz, po wszystkim.
NIE = czysta imitacja; FAIL bramki = ramię odpada bez ratunku. Żadnego DAggera na lotach SITL — to miesza
pozycje i budżety.

N5 Budżety: pozycja 3 ≤ **2 sesje** (twardy cap z planu: sesja 1 = trening obu ramion + bramki offline;
sesja 2 = contingency/DAgger wg N4 + domknięcie); pozycja 4 ≤ **4 sesje / ≤ 45 bootów**.

N6 Kampania lotów pozycji 4 (zamrożona teraz): świat/feed/sędzia/instrument/kolejka = ławka bez zmian;
`CONTROLLER=net|mlp`, wagi zamrożone commitem, `controller_sha` + `weights_sha` w meta/manifeście, zero
uczenia w locie. Kryterialna siatka = **ziarna 1–4** (48 epizodów per ramię) — te same scenariusze co
mianownik ⇒ porównanie PAROWANE per scenariusz: sieć↔egzekutor i NCP↔MLP (lekcja parowania z K1); booty
ramion przeplatane (net/mlp naprzemiennie) przeciw dryfowi środowiska. Jawny konflikt nazwany: ziarna 1–3
były w TRAIN (lot to nie replay — feed losuje z ziarna epizodu inne szumy — ale uogólnienie trajektorii
jest tu testowane słabo); dlatego dodatkowo **ziarna świeże s11–s13** (36 epizodów) na ramię, które przeszło
próg — RAPORTOWANE jako luka uogólnienia, nie kryterium. Kolejność: najpierw pełne 48 NCP+MLP, potem świeże.

N7 Kryteria pozycji 4 (zamrożone): próg = **p_net ≥ 0.825 na ziarnach 1–4, czyli ≥ 40/48** (D6 tym samym
sędzią, ważność V2′, pierwsza ważna próba, cap attempt ≤ 3, kolejka C8). Breach = STOP natychmiast (domena
certów). REFUSE = FAIL epizodu sieci + osobny licznik „osłona zawiera zły kontroler" (bez limitu STOP —
to jest pomiar tezy, nie awaria). ŚMIERĆ slotu sieci: oba ramiona < 40/48 po budżecie ⇒ slot skryptowy
NA STAŁE, raport z pełną prowieniencją — wynik programu, nie wstyd. Porównanie NCP↔MLP: pary zgodne/
niezgodne per scenariusz, ŻADNEGO języka istotności przy n = 48 (zakaz klasy K1); różnice opisowe.

N8 Raportowanie: per sesja tekst płaski; tabele wyników z etykietą feedu; nota dziedziczenia granicy
nauczyciela (c05/c07/c09 proximity) — predykcja, że sieci padną tam samo, jest w §3 i jej potwierdzenie
NIE jest porażką nogi (zbiór nie zawierał lekcji na te przypadki).

## §2. Protokół

Sesja 1 (pozycja 3): commit `net/` (modele, trening, config) + testy kontraktu → trening NCP + MLP →
bramki N3 per ramię → STOP-N1 (raport: krzywe, RMS TEST, rollouty 12 komórek per ramię, werdykt bramek).
Sesja 2: wg N4/N3 → STOP-N2 (zamrożenie wag lecących ramion: `weights_sha` do FREEZE_NET.md).
Pozycja 4: sesje lotów wg N6/N7, raport per sesja, STOP-N3 = RAPORT_NET (werdykt progu, pary, świeże
ziarna, licznik REFUSE, luka uogólnienia). Wszystkie STOP-y ratyfikuje CC numerowanym aneksem
(łańcuch ANEKS_NET-n); kryterium bez źródła nie istnieje (W2 z ANEKS_BENCH-2).

## §3. Predykcje CC (prerejestrowane; kalibracja programu: trafność < 1/2)

P-N1 NCP przechodzi bramkę N3(i) w sesji 1: p ≈ 0.6. P-N2 MLP również: p ≈ 0.6. P-N3 w locie |p_net(NCP)
− p_net(MLP)| ≤ 3 scenariusze niezgodne netto — pamięć nie robi różnicy na tym zadaniu (prior LiquidWatch).
P-N4 p_net(NCP) ≥ 40/48: p ≈ 0.55. P-N5 klasa porażek sieci = te same komórki proximity c05/c07/c09: p ≈ 0.7.
P-N6 REFUSE osłony wobec sieci: 0–2 zdarzenia w całej kampanii (sieci z tego zbioru nie są aż tak złe).

## §4. Zamrożenie przed pierwszą epoką

`net/` (architektury, trening, config), `bench/features.py` (bez zmian, sha stoi), podział N2, bramki N3,
protokół i kryteria N6–N7, budżety N5. Piny {shield, config, gate c3ccabe0, base.py} nietknięte przez całą
nogę — to jest mierzony fakt tezy, nie deklaracja.
