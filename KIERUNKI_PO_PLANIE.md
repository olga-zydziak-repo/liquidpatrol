# KIERUNKI_PO_PLANIE — kolejka nóg LiquidPatrol v2

CC · 10.09.2026 · stan wejściowy: pozycje 1–6 planu CLOSED, teza zmierzona z obu stron, piny 5/5,
ledger 12 wpisów. Reguła nadrzędna bez zmian: jedna noga naraz, każda z reconem i PRE, kryteria przed
pomiarem. Ten dokument jest KOLEJKĄ z triggerami, nie bufetem.

## Warstwa 0 — nie-nogi, do zrobienia najpierw (dni, nie tygodnie)

0a FOLLOW-UP SPRIND. Nie eksperyment — list. Brief z 30.08 obiecywał trajektorię; jest wykonana w 11 dni
z domknięciem tezy z obu stron. Materiał gotowy: brief + DEMO_V2.mp4 + RAPORT_NET + RAPORT_K2. Koszt:
pół wieczoru redakcji. Rekomendacja: teraz, póki daty są świeże. Kryterium porażki nie istnieje —
najgorszy wynik to brak odpowiedzi, a materiał i tak zostaje.

0b NOTA SYNTEZY (whitepaper wewnętrzny, kandydat na publiczny). Jeden dokument, który składa K1 + nogę
sieci + K2 w miniaturę assurance case: certyfikowana osłona + wymienny kontroler uczony + zmierzone
przejęcie + prowieniencja. To jest artefakt, który pracuje na Twój pivot niezależnie od SPRIND
(rozmowy, portfolio, ewentualna publikacja warsztatowa). Koszt: ~1 tydzień wieczorów, zero bootów.
Piszę szkielet na sygnał.

## Warstwa 1 — nogi wzmacniające istniejące roszczenia (tanie, dowodowe)

1a KONTROLA ARCHITEKTURY: GRU o budżecie ~1.9k parametrów + MLP k=20, ten sam zbiór, ten sam protokół
(wszystko istnieje: dane, sędziowie, kolejki). Pytanie: czy przewagę dała SPECYFIKA liquid, czy
jakakolwiek rekurencja, czy po prostu dłuższe okno. Trigger: decyzja o publicznym twierdzeniu
„pamięć-przez-dynamiką transferuje" — bez kontroli to twierdzenie nie przetrwa recenzji; z kontrolą
odwraca null LiquidWatch z mechanizmem. Koszt: 1–2 sesje + ~24 booty. Śmierć kierunku: GRU dorównuje
NCP ⇒ roszczenie spada do „rekurencja > okno" — nadal publikowalne, mniej efektowne. Każdy wynik
wartościowy, więc to najlepszy stosunek ceny do dowodu w katalogu.

1b WERYFIKACJA FORMALNA. Dwie części o różnej trudności: (i) osłona w Z3 — dowód, że implementacja
REFUSE/geofence odpowiada specyfikacji (Twój warsztat ProofGate przenosi się wprost; kod osłony jest
mały i pinowany, czyli stabilny cel); (ii) własności sieci — przy 1.9k parametrach i 8 wejściach
narzędzia weryfikacji sieci są w zasięgu; kandydackie własności: ograniczoność wyjścia (już
architektoniczna), zachowanie przy track_valid=0, monotoniczność składowej radialnej przy małym d.
Trigger: faza 2 SPRIND albo roszczenie publiczne. Koszt: 2–4 sesje, zero bootów. Śmierć: własność
niedowodliwa narzędziem ⇒ wynik częściowy (lista dowiedzionych + kontrprzykłady) — też raportowalny.

## Warstwa 2 — nogi nowej zdolności (każda zdejmuje jedną gwiazdkę z roszczeń)

2a PERCEPCJA W PĘTLI. Zastąpienie emulowanego feedu prawdziwym torem: kamera gz → detektor → tracker →
ten sam interfejs feedu (kontrakt już istnieje — feed był projektowany jako wymienny). To jest
największa pojedyncza gwiazdka w dzisiejszych roszczeniach („pod emulowanym feedem"). Wejście: artefakty
toru C. Koszt: duży, 2–3 tygodnie (detektor w pętli 20 Hz, latencja, kampania porównawcza feed-emulowany
vs feed-realny na tych samych ziarnach — parowanie gotowe). Śmierć: tracker nie trzyma kadencji/latencji
w kopercie SITL ⇒ wynik „percepcja limituje", ważny sam w sobie.

2b WIATR I RANDOMIZACJA DOMENY. Model wiatru w SITL + kampania odporności sieci i osłony. Tanie-średnie
(1 tydzień), a odpowiada na pytanie z rozmowy o lotnictwie: czy osłona zaczyna fałszywie odmawiać
w realnym szumie świata — bo jeśli tak, ścieżka 1:N pada na DOSTĘPNOŚCI, nie na bezpieczeństwie.
Ramię (−) z K4b daje bazę porównawczą. Śmierć: fałszywe REFUSE pod wiatrem = znalezisko pierwszej wagi.

2c INTRUZ ADWERSARYJNY (ucieka, manewruje przeciwko). Zmienia klasę zadania: nauczyciel skryptowy
przestaje wystarczać (pościg to nie orbita), więc to jest noga z nowym nauczycielem albo pierwszym
prawdziwym użyciem DAgger/RL. Duża (3+ tygodnie). Wejście: po 2a albo świadomie na feedzie emulowanym.

2d KONTYNUACJA PO UTRACIE GPS (nie lądowanie — powrót po zliczeniu/VIO). Jedyna noga, która ROZSZERZA
osłonę (nowa akcja bezpieczna ≠ D5), czyli dotyka certów i wymaga nowego dowodu klasy P2. Poważna,
dopiero po 1b(i), żeby rozszerzać rzecz już zweryfikowaną formalnie.

2e SPRZĘT / MULTI-DRON — poza horyzontem solo-SITL; trigger zewnętrzny (partner, finansowanie, faza
sprzętowa SPRIND). Zapisane, żeby istniało; nie planujemy, dopóki trigger nie padnie.

## Kolejność rekomendowana i kryterium wyboru

Najpierw 0a i 0b (dni, zero bootów, maksimum dźwigni na to, co już jest). Potem JEDNA noga, wybrana
jednym kryterium — co chcesz z programu mieć w horyzoncie 2 miesięcy:
- zdolność (system bliżej realności) ⇒ 2a percepcja, z 2b jako tanim przedsionkiem;
- dowód (faza 2 / rozmowy poważne) ⇒ 1b weryfikacja formalna;
- publikacja (twierdzenie o liquid) ⇒ 1a kontrola architektury.
Wszystko inne czeka w kolejce z triggerami. Otwarcie drugiej nogi przed zamknięciem pierwszej wymaga
zdania, które przekona CC — dotychczas takie zdanie nie padło ani razu zasadnie.

## Dopisek stanu katalogu — 08.10.2026 (CO-DET, ANEKS_DET-4 §8)

- **detektor-v2** (pozycja katalogu z `results/2A/RAPORT_2A.md` §8) → **CLOSED**:
  noga DET wykonana w całości (S0–S4, 37/≤45 bootów, breach 0 / REFUSE 0), werdykt
  i kanon obowiązujący w `results/DET/RAPORT_DET.md` — „detektor naprawiony
  i zmierzony; runtime rozwiązany architekturą; koszt pełnej percepcji = akwizycja,
  nie śledzenie" (Δ=34/48, w całości akwizycyjny).
- **AKW (akwizycja)** — NOWA pozycja katalogu (ANEKS_DET-4 §8). **Trigger:** przed
  jakimkolwiek roszczeniem pełnogeometrycznym kamery („dron lata na kamerze w pełnej
  geometrii"). Zakres: skan yaw w zawisie przedakwizycyjnym jako zachowanie warstwy
  misji PRZED ENTRY (nie zmiana sieci, nie zmiana osłony); warianty pre-aim/gimbal
  jako alternatywy. Aktywa gotowe: cały tor V2, kampania-wzorzec do powtórki
  parowanej AKW-vs-bez, 29 ślepych epizodów jako zbiór odniesienia
  (`results/DET/RAPORT_DET.md` §8). Najkrótsza ścieżka od Δ=34 do pełnej geometrii:
  jedno zachowanie przedakwizycyjne, zero nowych komponentów uczonych.

## Dopisek stanu katalogu — 11.10.2026 (CO-AKW, ANEKS_AKW-3 §7)

- **AKW (akwizycja)** → **CLOSED**: noga wykonana w całości (S0–S3, 29/≤32 bootów,
  3 sesje lotne + 2 deski, breach 0 / REFUSE 0 w 25 uzbrojonych bootach), werdykt
  i kanon obowiązujący w `results/AKW/RAPORT_AKW.md` — „luka geometryczna domknięta
  zachowaniem; skan nie wystarcza na cel szybki; następne ogniwo: re-akwizycja
  kierunkowa" (Δ_new=12 ⇒ ŚMIERĆ-AKW progiem zamrożonym; ΔΔ=22 z kwalifikatorem
  dwóch kampanii; bearingi zrównane 3/3/3/3, rezyduum w całości v=1.0).
  **NOTA-ERRATUM (ANEKS_REAKW-1 §3, 12.10):** zdanie „następne ogniwo: re-akwizycja
  kierunkowa" było inferencją CC z mechanizmu regresji c08, NIE pomiarem — desk recon
  RE-AKW zmierzył dźwignię jako fałszywą (konwersja górna 0/14; regresje c08 =
  interakcja fantom×skan, `results/REAKW_RECON/RECON_REAKW.md`). Werdykt AKW (Δ=12,
  ŚMIERĆ-AKW) NIETKNIĘTY — erratum dotyczy wyłącznie uzasadnienia pozycji katalogowej.
- **RE-AKW (re-akwizycja kierunkowa)** — NOWA pozycja katalogu (ANEKS_AKW-3 §7).
  **Trigger:** przed roszczeniem pełnej geometrii z celem szybkim. Zakres: dwell +
  obrót w kierunku ekstrapolowanym z trk_vel_ned (dane już w kontrakcie feedu) przed
  wznowieniem pełnego skanu — jedno zachowanie w TYM SAMYM wrapperze (akw_scan.py),
  zero nowych komponentów uczonych, zero zmian osłony/sieci. Aktywa gotowe:
  3 regresje c08 + 14 porażek V2 jako zbiór odniesienia, dwie kampanie-wzorce
  (DET S4 + AKW S3), profil II FROZEN b94cdeae, cała ewaluacja
  (`results/AKW/RAPORT_AKW.md` §8). Najkrótsza ścieżka od 34/48 do pytania
  „ile naprawdę zostało".

## Dopisek stanu katalogu — 12.10.2026 (CO-REAKW, ANEKS_REAKW-1 §5)

- **RE-AKW (re-akwizycja kierunkowa)** → **CLOSED-BY-RECON** (0 bootów, 1 sesja
  deskowa — pierwsze pełne zabicie kierunku deskiem w programie): dźwignia „pamięć
  kierunku z trk_vel_ned" SFALSYFIKOWANA przy biurku — górna granica konwersji 0/14
  na zbiorze odniesienia (5 porażek bez utraty tracku, w 6 pamięć kierunku =
  antysygnał fantomu stagingu, 2 odrzuca konieczna brama plauzybilności, 1 bez
  znaczenia); kampania w dowolnym wariancie potwierdziłaby zero z desku za ≥24 booty
  (`results/REAKW_RECON/RECON_REAKW.md`). KSIĘGA bez rozliczenia (PRE nie powstało).
- **FANTOM-START** — NOWA pozycja katalogu (ANEKS_REAKW-1 §4; flaga: mechanizm
  ZMIERZONY tym deskiem). Jeden mechanizm niesie 6/9 utrat w porażkach kampanii AKW:
  lock F2 na stagingu przed startem epizodu → expire → ślepy start 9.5–26.8 s.
  Dźwignia po stronie KONSUMENTA/choreografii (percepcja FROZEN): kandydaci do recon
  — ignorowanie przez konsumenta tracków zaadmitowanych przed startem epizodu;
  choreografia stagingu w narzędziu-driverze. **Trigger:** przed kampanią wymagającą
  czystego startu epizodu. Aktywa: 6 nazwanych epizodów + rekordy
  `results/REAKW_RECON/dir_replay.json`.
- **POŚCIG-V1** — NOWA pozycja katalogu (ANEKS_REAKW-1 §4; flaga: mechanizm nazwany
  danymi — track żywy, D6 pada — dźwignia **[MECHANIZM NIEZMIERZONY]**, recon od
  niej zacznie). 5/14 porażek przy TRZYMANYM tracku + obie porażki ramienia B
  (wyrocznia pada tak samo) ⇒ deficyt pościgu za celem v=1.0, liga sieci/egzekutora
  — nie percepcji i nie skanu. **Trigger:** przed roszczeniem pełnej siatki z celem
  szybkim. Aktywa: 5+2 epizodów z telemetrią obu kampanii (DET S4 + AKW S3).
  **DOPISEK AKTYWÓW (CO-FANTOM, 16.10):** aktywa ROSNĄ — +9 porażek V2 kampanii
  FANTOM S2 (wszystkie z wczesną akwizycją: pościg czysty, start wyeliminowany
  jako zmienna zakłócająca) + 2 B-FAILe + telemetria trzech kampanii
  (DET S4 / AKW S3 / FANTOM S2) + kwarantanna K1 FROZEN e435ed7e w rejestrze
  (`results/FANTOM/RAPORT_FANTOM.md` §8). Trigger bez zmian.

## Dopisek stanu katalogu — 16.10.2026 (CO-FANTOM, ANEKS_FANTOM-2 §6)

- **FANTOM-START** → **CLOSED**: noga FANTOM wykonana w całości (S0–S2, 28/≤30
  bootów, breach 0 / REFUSE 0 ×28), werdykt i kanon obowiązujący
  w `results/FANTOM/RAPORT_FANTOM.md` — „mechanizm startu domknięty pomiarem
  14/14; konwersja epizodowa 3/6 ograniczona pościgiem; Δ 12→7" (werdykt
  dwuwarstwowy: pozycja N6 3/6 + regresje 1 = strefa opisowa; siatka Δ_new2=7
  strefa opisowa, n_common=40; rezerwa programowa 2 nienaruszona — decyzja
  ANEKS_FANTOM-2 §5: booty kupują wyłącznie informację zmieniającą werdykty).
  **NOTA (20.10, ANEKS_POSCIG-1 §5): łańcuch Δ 34→12→7 — z erratum DMIN:
  what-ify obok liter (35→11→7), `results/POSCIG_RECON/ERRATUM_DMIN.md`.**
  **NOTA (25.10, ANEKS_TRANSIT-1 §2): rezyduum kamery (33/40 po erratum) jest od
  tego aneksu w całości rozliczone — zdanie kanoniczne sufitu profilu misji
  w dopisku CO-TRANSIT poniżej (`ANEKS_TRANSIT-1.md` §2,
  `results/TRANSIT_RECON/RECON_TRANSIT.md`).**

## Dopisek stanu katalogu — 20.10.2026 (CO-POSCIG, ANEKS_POSCIG-1 §5)

- **POŚCIG-V1** → **CLOSED-BY-RECON (rozpuszczenie mechanizmu)** (0 bootów, 1 sesja
  deskowa + CO — trzecie pełne zabicie kierunku deskiem): „deficyt pościgu za celem
  szybkim" nie istnieje jako mechanizm — zbiór odniesienia (11 V2 + 2 B) rozpada się
  na 3+2B artefakt przyrządu (realnie PASS), 6 akwizycja-transit i 2 near-missy
  omiatania; sufit kinematyczny nie istnieje (ideał 13/13 od t0), nauczyciel po
  erratum 120/120. Werdykt i dowody: `ANEKS_POSCIG-1.md` §2,
  `results/POSCIG_RECON/RECON_POSCIG.md`. Owoc uboczny werdykto-nośny:
  **ERRATUM-DMIN** (`results/POSCIG_RECON/ERRATUM_DMIN.md`) — artefakt tranzientu
  teleportu w gt_intruder, 28 flipów w 6 zbiorach, wszystkie werdykty nóg ODPORNE;
  filtr-świadek |ned−cmd_ned|_xy>1 m liczony ODTĄD obok każdego werdyktu
  sędziowanego na gt_intruder.
- **AKW-TRANSIT** — NOWA pozycja katalogu (ANEKS_POSCIG-1 §4; mechanizm ZMIERZONY
  reconem POŚCIG). 6 epizodów modu B (c08_s03, c08_s04, c10_s02, c11_s02, c11_s03,
  c11_s04): późna akwizycja 19.5–31.2 s, cel wchodzi <4 m pod ślepy zawis zanim
  track istnieje — okno sędziego płonie PRZED akwizycją. Dźwignia [NIEZMIERZONA] —
  poza percepcją (FROZEN): choreografia skanu lub wyżej. **Trigger:** przed
  roszczeniem pełnej siatki. Aktywa: `results/POSCIG_RECON/r1_feasibility.json` +
  `r2_behavior.json` + telemetria trzech kampanii (DET S4 / AKW S3 / FANTOM S2).
- **GT-CZYSTOŚĆ** — NOWA pozycja katalogu (ANEKS_POSCIG-1 §4; narzędziowa, niski
  priorytet). Utwardzenie u źródła: czystość pierwszych próbek gt_intruder (start
  logowania po świeżości bufora); wymaga zgody na dotyk frozen bencha /
  intruder_motion ⇒ własny łańcuch z FREEZE. Do tego czasu filtr-świadek wystarcza.

## Dopisek stanu katalogu — 25.10.2026 (CO-TRANSIT, ANEKS_TRANSIT-1 §2/§3)

- **AKW-TRANSIT** → **CLOSED-BY-RECON (zmierzony sufit profilu misji)** (0 bootów,
  1 sesja deskowa + CO — czwarte rozstrzygnięcie kierunku deskiem): sufit o trzech
  składowych, każda przybita do rzeczy zamrożonej — (1) admisja, nie pokrycie:
  klasa (ii) 6/6, koincydencja central∧MTI @5 Hz to zmierzona loteria (4/7),
  @14 Hz pewnik; (2) strefa martwa dh<5.01 m i pas admisji [5,18] m = odbicie
  korpusu etykiet, cel radialny opuszcza pas o t=10.0 s; (3) przegląd perymetru
  w nietykalnych kończy okno najgorszego azymutu ≥11.15 s > 10.0 s i > t\*
  w 3/6 — nie istnieje choreografia skanu bez prioru gwarantująca okno
  admitowalne (CH90/CH87 „6/6" = overfit do korytarzy siatki: stres +45° 0/6
  + regresja 5/6 kontroli). Sonda R5(iii) ODRZUCONA (rachunku sufitu żadna stopa
  nie uchyla). Werdykt i dowody: `ANEKS_TRANSIT-1.md` §2,
  `results/TRANSIT_RECON/RECON_TRANSIT.md`.
  **Zdanie kanoniczne (do cytowań):** „Z 7 pozostałych par kamery: 6 to zmierzony
  sufit PROFILU MISJI — zawis na home + separacja ≥4 m + cel przecinający dysk,
  przy zamrożonej percepcji i reżimie skanu — o trzech składowych (deterministyczny
  najazd generatora; loteria admisji czołowej @5 Hz / strefa martwa dh<5; przegląd
  perymetru 11.15 s > pas admisji 10.0 s); 1 to wariancja pościgu na komórce
  granicznej. Podniesienie sufitu wymaga dotknięcia rzeczy zamrożonych — to
  pozycja PERCEPCJA-II, nie choreografia."
- **PERCEPCJA-II (admisja niezawodna / daleki wzrok)** — NOWA pozycja katalogu
  (ANEKS_TRANSIT-1 §3; flaga **[MECHANIZM ZMIERZONY / DŹWIGNIE NIEZMIERZONE]**).
  Jedyny następca realnie podnoszący sufit, bo adresuje jego zamrożone składowe —
  nowa era percepcji z własnym FREEZE (wzór nogi DET). **Mechanizm ZMIERZONY**
  (recon TRANSIT, poziom klatki): koincydencja central∧MTI @5 Hz ma margines
  ~2 klatek na cały łańcuch (k=3 + persystencja 3/4 + warmup), @14.3 Hz działa
  w setkach; pas admisji [5,18] m = odbicie korpusu etykiet (97% w 5–10 m,
  max 14.9). **Dźwignie nazwane, NIEZMIERZONE** (recon zaczyna od ich pomiaru):
  (a) podłoga kadencji percepcji — skąd mody 5.10/7.58/14.71 Hz i co kosztuje
  gwarancja ≥10 Hz (tor percep_proc / compute, nie progi admisji);
  (b) persystencja MTI nad celem czołowym (residuum derotacji pod
  diff_thr/min_area — progi dziś FROZEN); (c) zasięg i rozdzielczość: krzywa
  P(detekcja|Z) na istniejących klatkach (desk, zero lotów), potem ewentualnie
  rozdzielczość sensora / korpus dystansowy / imgsz — detektor-v3 pod nową nazwą,
  taśma etykiet projektowych działa na każdej odległości za darmo.
  **Zbieżności (jawnie):** TRANSIT (podniesienie sufitu 6 par), daleki wzrok
  i rozpoznawanie WABIKÓW (ta sama dźwignia rozdzielczości/korpusu), przyszłe
  sim-to-real (szum realnej kamery w tym samym torze). **Trigger:** przed
  roszczeniem pełnej siatki v=1.0 ponad dzisiejszy sufit albo przed jakimkolwiek
  wątkiem wymagającym detekcji >15 m (wabiki, dystans). Aktywa: r1_anatomia
  (klatka po klatce), progi empiryczne (podłoga dh 5.01, dryf p99 5°/kl), stopa
  loterii 4/7, korpus Z-stats, T6 jako zbiór odniesienia.

## Dopisek stanu katalogu — 26.10.2026 (CO-PERC2, ANEKS_PERC2-2 §5)

- **PERCEPCJA-II, ścieżka (i) OPS-KADENCJA** → **CLOSED (SUKCES DŹWIGNI, 5 bootów)**:
  noga wykonana w całości (recon S0 + PRE + S1 + S2 + CO; 5/≤14 bootów, breach 0 /
  REFUSE 0, KSIĘGA 5/5), werdykt zdaniem zamrożonym — admisja okna run≥3 w 6/6
  epizodów T6 @k=1 (falsyfikacja 0/6; kotwice 2/2 PASS); kanon i dowody:
  `results/PERC2/RAPORT_PERC2_S2.md`, przyrząd ops zamrożony
  w `results/PERC2/FREEZE_PERC2_OPS.md`.
  **Zdanie kanoniczne (do cytowań):** „Kadencja percepcji była stratą transportu
  DDS (klatka 307 kB > segment SHM 512 kB / bufor UDP 208 kB, BEST_EFFORT), nie
  GPU; gwarancja k=1 środkami ops — profil FastDDS + sonda kadencji + pin
  prowieniencji — zamienia admisję czołową z loterii w pewnik (6/6 T6, oba c08
  odzyskane w D6), nie uchyla sufitu przeglądu perymetru (c11/270° FAIL realne,
  11.15 s > 10.0 s niezależnie od kadencji) i odsprzęga metrologię każdej
  przyszłej kampanii od stanu hosta."
  **REŻIM OPS = WARUNEK WEJŚCIA każdej przyszłej nogi kampanijnej** (profil
  a68a450b + sonda 8df528bb + pin model.sdf 3354ae1e — FREEZE_PERC2_OPS
  §checklist). **Decyzja o kampanii metrologicznej 24+3: NIE TERAZ**
  (ANEKS_PERC2-2 §4) — zbiór S2 nielosowy, żadnych roszczeń siatkowych z tej
  nogi; następna kampania werdyktowa odnowi bazę w czystym reżimie; odwracalne
  osobnym PRE na kampanię bazową. Ścieżki **(ii) MTI-czołowy** i **(iii)
  detektor-v3/daleki-wzrok** ZOSTAJĄ w katalogu z triggerami bez zmian
  (dopisek 25.10 wyżej).

## Dopisek stanu katalogu — 27.10.2026 (CO-WABIK, ANEKS_WABIK-2 §4)

- **WABIK, ścieżka (iii) wabik-w-świecie** → **CLOSED** (5/≤11 bootów: S1 2 +
  S2 3; breach 0 / REFUSE 0; KSIĘGA 3/6): werdykt TRÓJDZIELNY zdaniami
  zamrożonymi — **T-W-TP: FALSYFIKACJA PROGÓW** (etykieta ≤15 s w ≤1/6;
  „progi z NULL nie przenoszą się na TP — wracamy do cech"), **T-W-FP:
  0/3 flag ✓**, **T-W-ORB: 2/2 ✓** (track na celu 1.000 pod zmianą kursu,
  D6 PASS — pytanie R4-niezmierzone domknięte pozytywnie). Kanon i dowody:
  `results/WABIK/RAPORT_WABIK_S1.md`, `RAPORT_WABIK_S2.md`, przyrząd
  w `FREEZE_WABIK.md`.
  **Zdanie kanoniczne (do cytowań):** „Rozpoznanie behawioralne wabika ma
  działającą warstwę cech (flagi na rodzinach krążących, zero fałszywych
  alarmów na poważnych) i sfalsyfikowaną regułę czasową: wymóg 12 s
  nieprzerwanej zgodności pada na pikach szumu estymaty toru — dwie
  implementacje tej samej zamrożonej litery różnią się czasem flagi o ±50% —
  a naprawa (reguła odporna na przerwy) iteruje się offline na zalogowanych
  feedach za zero bootów."
- **WABIK-II / REGUŁA CZASOWA** — NOWA pozycja (następca; ANEKS_WABIK-2 §2/§4).
  Aktywa: feedy 11 epizodów S2 w repo (`results/WABIK/s2/*/percep_feed.jsonl`
  + `wabik_sig_<sid>.jsonl`), trzy zmierzone mechanizmy padnięcia reguły
  (piki v_rad rwą streaki; ZBLIŻ strukturalnie < T_FLAG; stale-klatki brzegu).
  Ścieżka: iteracja reguły OFFLINE na zalogowanych feedach za **0 bootów**
  (tolerancja przerw / frac_closing w oknie decyzyjnym / zegar od ciągłego
  segmentu) → FREEZE nowej reguły → potwierdzenie w locie na ŚWIEŻYCH
  wariantach parametrów trajektorii (anty-overfit — lekcja CH90); wycena
  ≤4 booty. **Trigger: decyzja Olgi.**
- **MULTI-TARGET / TOŻSAMOŚĆ TRACKA** — NOWA pozycja (ANEKS_WABIK-1 §2).
  Aktywa: pomiar przeskoków 25.5 %/24.3 % (dwie implementacje), mechanizm
  REFRESH-admituje-każdy-box, para kontrastowa konfiguracji A/B
  (`results/WABIK/s1/*/wabik_smoke.json`). **Trigger:** przed jakimkolwiek
  roszczeniem z ≥2 obiektami w zasięgu detekcji naraz i przed warstwą decyzji.
- **IMITACJE / MIKRO-SYGNATURA** — NOWA pozycja (ANEKS_WABIK-2 §4). Krok 1
  DESKOWY: rachunek widzialności mikro-ruchu w px przy sylwetce ~9 px@15 m
  i kadencji 14.7 Hz (czy mikro-sygnatura ruchu jest w ogóle mierzalna
  sensorem programu). **Trigger: po WABIK-II.**
- **Dopisek do 1b(ii) weryfikacja sieci** (pozycja w Warstwie 1 wyżej —
  append-only tutaj): rozszerzenie o **XAI / replay aktywacji** — S0 deskowe:
  kopia modułu + wagi ncp 0337d5ea + replay feedów wszystkich kampanii,
  **0 bootów**; wchodzi w zakres przy otwarciu 1b(ii).

## Dopisek stanu katalogu — 27.10.2026 (CO-WABIK2, ANEKS_WABIK2-1 §4)

- **WABIK-II / REGUŁA CZASOWA** → **CLOSED-BY-DESK-DEATH (0 bootów)**:
  śmierć S1 literą PRE_WABIK2 §2.4 — zamknięta przestrzeń 26 wariantów A/B/C
  wyczerpana, zbiór dopuszczonych pusty (krawędź Pareto: TP≥5/6 ⇒
  NULL-final=15>13; NULL≤13 ⇒ TP≤1/6); pierwsza noga programu zamknięta
  w całości przy biurku PO pełnej prerejestracji. Dowody:
  `results/WABIK2/RAPORT_WABIK2_S1.md`, pełna mapa Pareto
  `results/WABIK2/s1_tabela.json` (26 wariantów × 126 epizodów).
  **Zdanie kanoniczne (do cytowań):** „Czysta agregacja czasowa nie domyka
  rozpoznania wabika przy tym szumie toru: na 26 wariantach zamkniętej
  przestrzeni TP≥5/6 i czystość populacji normalnej nigdy nie zachodzą naraz
  (krawędź Pareto: NULL≤13 ⇒ TP≤1/6) — wąskie gardło leży piętro niżej,
  w jakości predykatu klatkowego (piki v_rad estymaty toru); zero FP
  i poprawne odwołania trzymają we wszystkich 26 wariantach."
- **TOR-CECHY (wygładzenie v_rad przed predykatem / estymator toru)** — NOWA
  pozycja SCALONA, **zbieżna z MULTI-TARGET / TOŻSAMOŚĆ TRACKA** (oba wątki
  potrzebują porządniejszego toru; jedna pozycja, nie dwie). Aktywa:
  `s1_tabela.json` jako **bench akceptacyjny offline** (nowa warstwa cech
  musi dać wariant spełniający stare kryterium selekcji, zanim cokolwiek
  poleci), mapa przeskoków z WABIK (i) S1 (`results/WABIK/s1/*/
  wabik_smoke.json`), nota wędrowców v=0.5 (przyszła prerejestracja może
  rozdzielić tę klasę w kryterium NULL jawnie — ANEKS_WABIK2-1 §2).
  **Trigger: decyzja Olgi.**
- Pozycje **IMITACJE / MIKRO-SYGNATURA** i **ODPOWIEDŹ-EKONOMIA** — bez zmian
  (dopiski 26–27.10 wyżej).

## Backlog §8 (bez zmian, porządkowe)

Polityka git dla .ulg (decyzja od tygodni odroczona, nieblokująca) · martwe inicjalizacje w gate (przy
następnym uprawnionym dotknięciu pinu) · allowlista procesów jako plik żywy · rozpoznawanie atrap
(nota z triggerem z 23.08, warunki bez zmian).

## Dopisek stanu katalogu — 27.10.2026 (CO-XAI, ANEKS_XAI-1 §4)

- **Noga XAI-SIECI (ścieżka (ii)+(i) z RECON_XAI)** → **CLOSED, 0/0 bootów**
  (recon 0 + S1 0 + CO 0) — pierwsza noga programu zamknięta przy biurku
  SUKCESEM po pełnej prerejestracji (druga strona monety reżimu wobec
  desk-death WABIK-II). Dowody: `results/XAI/RAPORT_XAI_S1.md`,
  `results/XAI/FREEZE_XAI.md` (statusy + ZASADA CYTOWANIA),
  `results/XAI_RECON/RECON_XAI.md` (atlas + kotwica replayu).
  **Zdanie zamrożone (ANEKS_XAI-1 §2, do cytowań):** „NCP-20 ma dwa
  twierdzenia architektoniczne klasy dowodowej: T1 |y_k| < 3.0 i T2
  |h_i| < 1 (w IEEE754: ≤) — dowiedzione symbolicznie, potwierdzone
  różnicówką 0/74 708 ticków i czułe na mutanty — oraz dwa zmierzone
  kontrprzykłady-wyniki: (T3) lokalna kontrakcja kroku NIE zachodzi —
  każdy tick orbity jest krokowo ekspansywny (max ‖J‖₂ 2.58), więc
  stabilność pierścienia to pytanie o mnożniki Floqueta OKRESU
  (nazwane-niezmierzone); (T4) znak prawa pościgu NIE jest globalny
  (21.1% ticków ujemnych) — polityka z fazą orbitalną steruje stycznie,
  znak żyje per faza." Zdanie kanoniczne programu zyskuje literę:
  „dowiedziona osłona + sieć z dowiedzionymi twierdzeniami
  architektonicznymi" (certyfikaty osłony 9/9 + T1/T2 PROVED).
- **XAI-FLOQUET (T3′)** — NOWA pozycja: mnożniki Floqueta cyklu z replay
  (monodromia = iloczyn jakobianów po okresie orbity), deskowe 0 bootów;
  uzbrojone liczbą: krokowo max ‖J‖₂ 2.58, pytanie czy widmo monodromii <1.
  **Trigger: decyzja Olgi.**
- **XAI-ZNAK-PER-FAZA (T4′)** — NOWA pozycja: znak ∂y₀/∂sin_brg na pudełkach
  per faza (approach vs orbit) + przedziałówka wyłącznie na małych pudełkach;
  frakcje korpusowe już w ręku (21.1% globalnie). **Trigger: decyzja Olgi.**
- **Nakładka demo „co myśli sieć"** — era montażu; wycena z RECON_XAI §R6(iii)
  aktualna; nieprekomitowana. **Trigger: decyzja Olgi.**

## Dopisek 28.10.2026 — ERRATUM_XAI-1 (korekty A/B; zdanie zamrożone ZASTĄPIONE)

**Zdanie zamrożone do cytowań — zastępuje wersję 27.10 (wyżej) na mocy
ERRATUM_XAI-1 §3:**

> „NCP-20 ma dwa twierdzenia architektoniczne klasy dowodowej: T1 |y_k| < 3.0
> i T2 |h_i| < 1 (w IEEE754: ≤) — dowiedzione symbolicznie, potwierdzone
> różnicówką 0/74 708 ticków i czułe na mutanty — oraz jeden zmierzony
> kontrprzykład: (T3) kontrakcja w jednym kroku nie zachodzi — w każdym kroku
> orbity istnieje kierunek o wzmocnieniu ≥ 1 (max ‖J‖₂ 2.58), więc stabilność
> pierścienia to pytanie o zachowanie wielokrokowe (nazwane, niezmierzone).
> Znak prawa pościgu (T4) w S1 niezmierzony."

Mechanizm echo-vs-generator: **NIEROZSTRZYGNIĘTE** (korekta A — norma kroku
≥ 1 nie wyklucza kurczenia iloczynu jakobianów; macierze nienormalne).
T4: **NIE-SFORMALIZOWANE** — S1 zmierzyło ∂v_n/∂rel_d (x₂ = rel_d z litery
features.py), nie prawo pościgu (korekta B); T4 nie wolno cytować jako wyniku,
„prawo pościgu" wyłącznie jako opisowe dominanty saliency z atlasu
(FREEZE_XAI: wiersz T4 i pkt 3 zasady cytowania tracą ważność na mocy
ERRATUM_XAI-1). Zdanie kanoniczne programu i demo v5 BEZ ZMIAN.

**Pozycje XAI przeformułowane (ERRATUM_XAI-1 §5):**

- **XAI-FLOQUET (T3′)** — teraz para hipotez **H-echo / H-gen**, dwa testy
  przy biurku: (a) zapominanie — replay tych samych lotów z losowych stanów
  początkowych, warunkowo na zalogowanych wejściach, plus warunkowe widmo
  Lapunowa; (b) autonomia — wejście zamrożone na wartościach z pasma orbity:
  punkt stały czy oscylacja.
- **XAI-ZNAK-PER-FAZA → XAI-ZNAK (T4′)** — prawo pościgu od nowa, na
  wielkościach jednoznacznych: składowa radialna komendy względem celu jako
  funkcja dystansu (daleko ⇒ zbliża się; blisko ⇒ nie zbliża się) i kierunek
  orbity (opisowo). Przesłanka „znak żyje per faza" wycofana.
- Obie pozycje idą razem jako noga **XAI-II** (`PRE_XAI2.md`); **trigger
  spełniony decyzją Olgi 28.10.**

## Dopisek stanu katalogu — 28.10.2026 (CO-XAI2, ANEKS_XAI2-1 §5)

- **Noga XAI-II** → **CLOSED, 0 bootów** (S1 0 + CO 0); śmierć S1 nie zaszła
  (krok 0 PASS 3/3). Dowody: `results/XAI2/RAPORT_XAI2_S1.md`,
  `results/XAI2/FREEZE_XAI2.md` (statusy + ZASADA CYTOWANIA, pkt 3 zaostrzony
  przez ANEKS_XAI2-1 §2: T4b wyłącznie z „8/8 obserwacji przeczy").
  **Zdania zamrożone (ANEKS_XAI2-1 §2, do cytowań):**
  - **T3′ = H-ECHO:** sieć zapomina swój stan początkowy — 1696/1696 losowych
    startów (32 × 53 loty) zbiega do trajektorii referencyjnej (mediana 2 s,
    max 10.3 s, różnica komendy po zbieżności ≤ 3.4·10⁻⁶ m/s), λ₁ < 0
    w 53/53 lotach (orbita −1.8/s); przy wejściu zamrożonym z pasma orbity
    punkt stały w 193/200 (7 wielostabilnych, 0 okresowych, ρ ≤ 0.969).
    Pierścień = odbicie obracającego się wejścia, nie własny rytm sieci.
    Warunkowo na zalogowanych wejściach; zamrożone wejście = sonda.
  - **T4a PROVED na ε-rurach:** d ∈ [12, 17.3] m ⇒ v_rad > 0 na 1631/1631
    tickach (min 2.17 m/s), certyfikowane przedziałowo w otoczeniu każdego
    (ε_x 0.02, ε_h 0.01; 100%); próba globalna 0% — twierdzenie lokalne.
  - **T4b NIEROZSTRZYGALNE (n = 8)**, z dowodem przeciwnym w małej próbce:
    jedyne 8 ticków d ≤ 4 m to narodziny tracku i we wszystkich 8 sieć
    kieruje w stronę celu; zachowanie z bliska w ustalonym locie nieznane.
  - **T4c (opisowo):** sieć krąży zawsze w tę samą stronę (dominujący znak
    53/53, ściśle stały 6/53), zgodność z losowanym kierunkiem nauczyciela
    28/53 (przypadkowa); „CW" = etykieta konwencji kodu, na mapie z północą
    u góry ruch przeciwny do wskazówek zegara (ANEKS_XAI2-1 §1.4).
  **Zdanie programowe XAI po obu nogach:** „NCP-20: dwa twierdzenia
  architektoniczne (T1: komenda < 3 m/s, T2: |h| < 1) dowiedzione dla
  każdego wejścia; sieć-echo — na zalogowanych lotach zachowanie nie zależy
  od stanu początkowego (1696/1696 startów zbieżnych w ≤ 10.3 s); z daleka
  zawsze kieruje w stronę celu (certyfikowane wokół 1631 ticków)."
- **XAI-FLOQUET (T3′)** → **CLOSED** (H-ECHO; RAPORT_XAI2_S1 §2–§4).
- **XAI-ZNAK (T4′)** → **CLOSED** (T4a PROVED na ε-rurach / T4b n.r. /
  T4c opisowo; RAPORT_XAI2_S1 §5).
- **Nakładka demo „co myśli sieć"** → **CLOSED** (zrobiona w DEMOC v4/v5,
  STOP-DEMOC-4/5).
- **GT-CZYSTOŚĆ** → **backlog §8** (filtr-świadek wystarcza).
- **Pytanie nazwane (NIE pozycja katalogu, ANEKS_XAI2-1 §4):** czy GRU
  przegrywa z NCP (48/48 vs 29/48; 19 porażek = niedokręcona orbita), bo przy
  niejednoznacznym nauczycielu uśrednia dwa kierunki krążenia zamiast wybrać
  jeden (słabsza składowa styczna)? Test przy biurku: znak i moduł v_tan GRU
  w paśmie 6–10 m na jego lotach LIQ (replay ramienia GRU) i na wejściach NCP;
  jedna sesja, 0 bootów. Otwarcie wyłącznie decyzją Olgi, z PRE.
- Stan: wątek XAI zamknięty w całości (dwie nogi, 0 bootów); katalog
  11 → 8 otwartych pozycji. Następna noga wg kolejności z 28.10:
  TOR-CECHY ∪ MULTI-TARGET, decyzja Olgi. Opcjonalnie, nieprekomitowane:
  nakładka demo „32 starty zlewają się w jedną trajektorię".

## Dopisek stanu katalogu — 29.10.2026 (CO-WK, ANEKS_WK-1 §5)

- **Noga WIATR-KAMERA** → **CLOSED werdyktem V-C, 3/≤9 bootów** (dym 1 + WK0 2; 6 zaoszczędzonych
  bramką); śmierć nie zaszła (dym PASS za pierwszym podejściem); breach 0 / REFUSE 0. Dowody:
  `results/WK/RAPORT_WK_S1.md`, `results/WK_RECON/RECON_WK.md`; prerejestracja `PRE_WK.md`.
  Noga nie była pozycją katalogu (lista „co jeszcze" raportu programu).
  **Zdanie zamrożone (ANEKS_WK-1 §2, do cytowań):**
  > **V-C.** W habitacie z oporem aerodynamicznym (WindEffects ze skalą 1.0; zmierzony opór
  > k ≈ 1.05 /s, około 9× więcej niż w modelu stock), przy wietrze 0, sieć NCP-20 uczona bez
  > tego oporu zdaje egzamin misji D6 w 2/8 epizodów na komórkach v ≤ 0.5 (1/7 ważnych), wobec
  > 8/8 tych samych scenariuszy na kamerze w świecie stock. Mechanizm: orbita jest o ~1/3
  > wolniejsza — sieć komenderuje ~17% mniejszą prędkość styczną, a autopilot pod oporem realizuje
  > ~86% komendy — więc obrót wokół celu nie dobija do progu 630° w 70 s. Wszystko inne trzyma:
  > dystans 6–10 m przez 100% okna, d_min ≥ 7.0 m, cel w kadrze, zero ingerencji osłony,
  > breach 0. Wiatru 1.5 i 3 m/s nie latano — bramka wiatru 0 nie przeszła.

  **Interpretacja dla tezy „mała sieć umie latać" (cytować razem z V-C):** sieć w tym habitacie
  leci bezpiecznie i poprawnie, ale za wolno na egzamin tempa; opór habitatu najpewniej
  kilkukrotnie silniejszy niż dla realnego drona tej klasy (rachunek orientacyjny, do
  weryfikacji) — test przeciążeniowy przeniesienia między fizykami, nie werdykt o locie
  w realnym powietrzu.
  **Pełzanie wysokości (opisowo):** w trybie kamerowym nie wystąpiło (0 sejwów GEOFENCE);
  atrybucja z ANEKS_W-2 dostaje trzeci kandydujący czynnik: epokę harnessu (kampania W sprzed
  naprawy yaw N1). Zdanie z RECON_WK §R2 cytować wyłącznie z kwalifikatorem „kampania W,
  epoka przed N1".
- **WK-II / OPÓR REALNY** — NOWA pozycja katalogu (ANEKS_WK-1 §4), jedna pozycja, dwa etapy:
  (a) habitat z oporem skalibrowanym do zewnętrznego odniesienia fizycznego (nowe pliki świata;
  skala oporu wybrana z fizyki i zapisana w PRE, nigdy dostrajana pod wynik sieci), potem WK0
  i ewentualnie wiatr na tej samej siatce: 2–7 bootów; (b) tylko jeśli (a) też łamie misję:
  douczenie sieci w habitacie z oporem — nowe wagi, nowy FREEZE, duża noga. Aktywa: złożenie
  wiatru z kamerą bez dotykania zamrożonych (`worlds/world_wk_*`, `results/WK/tools/wk_boot.sh`,
  `wk_judge.py`). **Trigger: decyzja Olgi albo dowolne zdanie o locie w realnej fizyce.**
- Stan: katalog 8 → 9 otwartych pozycji (doszła WK-II).

## Dopisek stanu katalogu — 29.10.2026 (CO-WK2, ANEKS_WK2-1 §5)

- **WK-II / OPÓR REALNY** → **CLOSED werdyktem V-A2, 6/≤18 bootów** (schodek S niepotrzebny); śmierć
  nie zaszła; breach 0 / REFUSE 0 / sejwy 0. Dowody: `results/WK2/RAPORT_WK2_S1.md`,
  `results/WK2_RECON/RECON_WK2.md`; prerejestracja `PRE_WK2.md` (errata w przód do §2 — nowy driver
  `results/WK2/tools/wk2_boot.sh`, ANEKS_WK2-1 §1.2).
  **Zdanie zamrożone (ANEKS_WK2-1 §2, do cytowań):**
  > **V-A2.** NCP-20 (20 neuronów, 1903 parametry, uczona bez oporu) prowadzi pełną misję na własnej
  > kamerze w habitacie z oporem aerodynamicznym z górnego końca realnego pasma (k zmierzone 0.49 /s;
  > pasmo [0.15, 0.55] /s z PX4 EKF2_MCOEF i Faessler i in. 2018, z zastrzeżeniem masy) przy stałym
  > wietrze 0 / 1.5 / 3 m/s z jednego kierunku, komórki v ≤ 0.5: **D6 8/8 · 6/8 · 8/8**, breach 0,
  > sejwy osłony 0, przechył w zawisie 4.3° / 8.6°. Obie porażki przy 1.5 m/s to akwizycja (c03:
  > track po 30.7 s; c06: utrata tracka na 25 s z d_min 3.3 m po ponownej akwizycji), nie tor orbity
  > — oba scenariusze zdały przy 0 i 3 m/s. Tempo orbity: sweep 0.83–0.90 stocku (przy k = 1.05:
  > 0.67), komenda styczna 1.84–1.87 wobec 1.96 m/s, realizacja 0.94 wobec 1.05.

  **Dla tezy „mała sieć umie latać":** granica z nogi WK (k = 1.05 /s, 2/8) leżała 1.9× nad realnym
  pasmem; w górnym końcu pasma sieć zdaje 22/24. Zdanie do raportu: „sieć uczona w świecie bez oporu
  przenosi się na opór z górnego końca realnego zakresu i na stały wiatr do 3 m/s; pęka dopiero przy
  oporze ~2× ponad realny". Nie wolno: „odporna na wiatr", nic o porywach/turbulencji, nic o realnym
  sprzęcie (kanon W).
  **Fizyka (opisowo):** wyraz wolny bilansu sił przy wietrze = k·w co do 1–2% (0.745 / 1.49 m/s² przy
  1.5 / 3 m/s) ⇒ opór, także wirnikowy, liczony względem powietrza (rozstrzyga RECON_WK2 §R1).
- **WK-II etap (b) „douczenie w habitacie z oporem"** → **SKREŚLONY** (trigger V-D2 nie zaszedł).
- **PERCEPCJA-II (ii) MTI-czołowy** — dopisany przypadek (pytanie nazwane, NIE nowa pozycja): akwizycja
  pod wiatrem 1.5 m/s — 2/8 epizodów z późną/utraconą akwizycją (WK2 G1.5 c03, c06) wobec 0/8 przy
  0 i 3 m/s; przy n = 8 nierozróżnialne od wariancji.
- Bez zmian: TOR-CECHY ∪ MULTI-TARGET, IMITACJE, daleki wzrok, ODPOWIEDŹ-EKONOMIA, 2c, 2d, 2e.
- Stan: wątek wiatr+kamera zamknięty w dwóch nogach (9 bootów: 3 + 6), breach 0 / REFUSE 0;
  katalog 9 → 8 otwartych pozycji.

## Dopisek stanu katalogu — 30.10.2026 (CO-WK3, ANEKS_WK3-1 §5)

- **WK-III „porywy"** → **CLOSED werdyktem V-A3, 4/≤8 bootów; śmierć nie zaszła; breach 0 / REFUSE 0 /
  sejwy 0.** Dowody: `results/WK3/RAPORT_WK3_S1.md`, `results/WK3_RECON/RECON_WK3.md`; prerejestracja
  `PRE_WK3.md` (sha 3758b86f…); ANEKS `ANEKS_WK3-1.md` (sha f32eb8e7…).
  **Zdanie zamrożone (ANEKS_WK3-1 §2, do cytowań):**
  > **V-A3.** NCP-20 (20 neuronów, uczona w świecie bez oporu i bez wiatru)
  > prowadzi pełną misję na własnej kamerze pod wiatrem zmiennym w czasie,
  > w habitacie z realnym oporem (k ≈ 0.49 /s), komórki v ≤ 0.5: profil
  > łagodny (średnia 2 m/s, porywy 1.2–2.8 m/s, okres 8 s) **D6 8/8**; profil
  > ostry (0.4–3.6 m/s, okres 4 s, kierunek ±30° z okresem 11 s) **D6 7/8**,
  > breach 0, sejwy osłony 0. Jedyna porażka to spóźniona akwizycja celu
  > (wejście w pas po 26.2 s przy limicie 25 s), po której orbita była pełna.
  > Tempo orbity 0.89 stocku, przechył w epizodach ≤ 26.3°, cel nigdy nie
  > wypadł z kadru dołem przed porażką. Sinus deterministyczny — to „wiatr
  > zmienny o znanym profilu", nie turbulencja.

  **Dla tezy „mała sieć umie latać":** po WK-II wolno było mówić „przy stałym
  wietrze do 3 m/s"; od dziś: **„pod wiatrem zmiennym w czasie z porywami do
  3.6 m/s i obrotem kierunku, w habitacie z realnym oporem"**. Kanon W
  zostaje: nie „odporna na wiatr" (brak turbulencji stochastycznej, brak
  realnego sprzętu), nic o porywach ponad 3.6 m/s.

  **Mechanizm, który się powtarza (3 nogi):** w WK-II (G1.5) i WK-III (P2)
  wszystkie 3 porażki sieci na kamerze pod wiatrem to akwizycja/track w pierwszych
  sekundach (startowy track wygasa po ~3 s, ponowne złapanie trwa 15–20 s),
  nigdy tor orbity po akwizycji. Sieć lata; percepcja czasem spóźnia start.
  To wzmacnia istniejącą pozycję PERCEPCJA-II (ii), nie tworzy nowej.
- **PERCEPCJA-II (ii) MTI-czołowy** — dopisek (ANEKS_WK3-1 §4, NIE nowa pozycja): trzeci przypadek
  spóźnionej akwizycji pod wiatrem (WK3 P2 c01) obok WK2 G1.5 c03/c06; łącznie 3/32 epizodów
  kamerowych pod wiatrem.
- Stan: wątek wiatr+kamera (WK, WK-II, WK-III) zamknięty w całości: 13 bootów, breach 0; katalog
  8 otwartych pozycji, bez zmian.

## Dopisek stanu katalogu — 30.10.2026 (CO-WABIK3R, ANEKS_WABIK3-1 §4)

- **WABIK-III „tor i geometria zbliżenia"** → **CLOSED-BY-RECON+DESK (0 bootów,
  1 sesja deskowa + CO)**. Recon `results/WABIK3_RECON/RECON_WABIK3.md`
  (12b88e38): R1 feed = top-1 przed bramką, multi-target offline NIE; R2 kandydat
  DCPA/TCPA (dron·H10·R7·T4) TP≤15 5/6 · FP 0/3 · ORB 2/2 · NULL_final 10/115
  — odtworzony przez CC co do 0.1 s; R3 tor NIE (0/6 przy 8 estymatorach);
  R4 IMITACJE zamknąć (MAD 0.21 m ≈ 6.7 px, AUC 0.59); R5 13 NULL-final =
  12 wędrowców v=0.5 + 1 percepcja. **Pomiar CC (ANEKS_WABIK3-1 §2,
  odtworzony narzędziem `results/WABIK3_RECON/tools/wabik3_uderzajacy.py`):**
  115 NULL = 65 uderzających (GT < 5 m w oknie lotu) + 50 niedochodzących;
  kandydat podpisuje jako wabik **37/65 uderzających** (20 w chwili, gdy idą
  na home; cofnięcie medianowo 11.2 s później, przy podłodze; c08_s01 w 3/3
  kampaniach), baza v1 **11/65** (0 wchodzących, wszystkie w fazie oddalania);
  uczciwa krawędź Pareto (TP≤15 → min uderzających z etykietą, 100
  konfiguracji): 0→0, 3→16, 5→26 — poniżej poziomu bazy nie ma nic, co
  flagowałoby w czasie.
  **Zdanie kanoniczne:** „Geometria zbliżenia skraca etykietę wabika do ≤15 s
  w 5/6 przypadków, ale na zamrożonym benchu podpisuje jako wabik 37 z 65 celów,
  które uderzają — 20 z nich, gdy idą prosto na chroniony punkt. Reguła v1
  nigdy nie podpisuje celu wchodzącego (0/11). Przy jednym obiekcie tor sam
  w sobie nie odróżnia wabika od celu, który uderzy za chwilę — szybciej niż
  ten cel sam to pokaże."
  **Lekcja kryterium:** NULL_final (WABIK-II) nie widział etykiet na celach,
  które uderzają; każde przyszłe kryterium wabikowe liczy koszt na klasie
  UDERZAJĄCY (GT < 5 m w oknie lotu) jako „etykieta kiedykolwiek", osobno od
  wędrowców (klasa nazwana: niedochodzący v=0.5, dziś 14/50).
- **IMITACJE / MIKRO-SYGNATURA** → **CLOSED-BY-RECON** (R4: szum pozycji celu
  statycznego MAD 0.21 m ≈ 6.7 px @ 8.5 m, residuum 1 s 3–5 cm, AUC 0.59 —
  mikro-ruch poniżej rozdzielczości toru tej kamery).
- **TOR-CECHY** → **CLOSED-BY-RECON** (R3: żaden z 8 estymatorów v_rad przy
  niezmienionej regule nie przesuwa TP do ≤15 s; jump_0.5 czyści NULL kosztem
  2 TP). Pozycja scalona TOR-CECHY ∪ MULTI-TARGET rozpada się: zostaje
  **MULTI-TARGET / TOŻSAMOŚĆ TRACKA** jako jedyna otwarta droga wabikowa,
  z nową treścią: etykieta jako PRIORYTET między ≥2 obiektami, nie wyprzedzenie
  uderzenia. Warunek wstępny (R1 ii): zrzut klatek kamery + nowy replay det_v2
  wszystkich ramek (zero dotyku FROZEN), dopiero potem bench wieloobiektowy.
  **Trigger: decyzja Olgi po rozmowie z pilotem** (pytanie trzecie: czy obrona
  odróżnia wabik, czy zakłada uzbrojenie każdego celu — jeśli to drugie,
  priorytet między obiektami jest jedynym sensem etykiety).
- **DEMO-C v6 — errata forward do V-A3 (ANEKS_WK3-1 §2):** w reżimie demo
  (zrzut klatek, WindEffects) take1 c04@P2 był VALID (V2′ 0.950, k 0.490,
  breach 0) i padł na sędzim D6 przez sweep 570° < 630° — orbita zwalniała
  i zawracała (38 % ticków z ujemną prędkością styczną, 8 zmian znaku; take2:
  16 %, 2) — pierwsza porażka pod wiatrem, która nie jest akwizycją. Wynik
  reżimu demo pod P2: 1/2 (`results/DEMO_C/RAPORT_DEMO_C.md`, Akt 6). Kanon
  V-A3 (kampania WK-III 7/8) bez zmian; zdanie „jedyna porażka to akwizycja"
  dotyczy kampanii, nie reżimu demo. Plansza „~140 bootach" → „>150" przy
  następnym montażu.
- Stan: wątek wabikowy po trzech nogach i dwóch zamknięciach deskowych:
  5 bootów łącznie (WABIK S1+S2), breach 0 / REFUSE 0; katalog 8 → 7 otwartych
  pozycji (IMITACJE zamknięte; pozycja scalona TOR-CECHY ∪ MULTI-TARGET trwa
  jako MULTI-TARGET z nową treścią, człon TOR-CECHY skreślony).

## Dopisek stanu katalogu — 31.10.2026 (CO-WK4-0, ANEKS_WK4-0 §2–§4)

- **Noga WK-IV „turbulencja i sufit wiatru"** (pozycja 2b, otwarta 30.10:
  recon 1f61bc1b, PRE 1c0e1643) → **CLOSED-BY-DECISION przed lotami sieci
  (0 bootów sieci)**. Recon zweryfikowany przez CC (serie Drydena co do
  liczby, nauczyciel D6 4/4 przy D4 i D6, k 0.497/0.498). B0 wykonane
  częściowo w gołym gz (31.10, bez PX4; `results/WK4/`): **zacięcia
  symulacji z reconu to skoki zegara ściennego gościa WSL2** (realtime −
  monotonic +2.2–3.3 s co ~35 s, timesyncd; gz wg CLOCK_MONOTONIC 0 zacięć,
  dsim/dwall 1.000) — nie świat, nie publikator; etap PX4-bez-uzbrojenia
  i boot kontrolny nieodbyte; remedium `wsl --shutdown` przed sesją.
  Zamknięcie jest decyzją Olgi 31.10, nie koniecznością. **Kanon wiatru
  programu pozostaje przy V-A3 (ANEKS_WK3-1 §2):** wiatr zmienny o znanym
  profilu do 3.6 m/s, nie turbulencja, sufit niezmierzony. PRE_WK4 ważny
  literą; wznowienie = ponowna ratyfikacja + reszta B0. **Konsekwencja
  metodologiczna (forward):** V2′ liczony z zegara ściennego zaniża ważność
  przy skokach zegara, nigdy nie zawyża — werdykty zamkniętych nóg bez
  rewizji; próbnik RTF przy następnej nodze z lotami zapisuje oba zegary,
  V2′ z monotonicznego (własny pin). Aktywa: serie D2–D6 z sha, publikator
  746a958b, świat world_wk4 7acf407f, RECON_WK4, `results/WK4/` (B0). Wątek
  wiatru (W, WK, WK-II, WK-III, WK-IV) zamknięty w całości.
- **MULTI-TARGET / TOŻSAMOŚĆ TRACKA** → **CLOSED-BY-DECISION (31.10, Olga:
  „zamykamy wabik")**. Wątek wabikowy zamknięty w całości na tym stanowisku,
  z wynikiem: (1) reguła v1 (FREEZE_WABIK) nigdy nie podpisała celu
  wchodzącego na 65 uderzających (ANEKS_WABIK3-1 §2); (2) trzy dźwignie
  skrócenia etykiety (czas, tor, geometria) zamknięte deskiem za 0 lotów
  (ANEKS_WABIK2-1, ANEKS_WABIK3-1); (3) imitacje poniżej rozdzielczości toru
  kamery (RECON_WABIK3 R4); (4) priorytet między ≥ 2 obiektami nazwany
  i wyceniony (RECON_WABIK3 R1 ii), nieotwarty. Trigger ponownego otwarcia
  wyłącznie zewnętrzny: partner z realnymi lotami i sensorami poza kamerą
  albo odpowiedź praktyka, że obrona odróżnia wabik i chce tego jako
  polityki kolejności. Aktywa w repo: bench WABIK-II (126 lotów),
  wabik_sig 475c972e / wabik_sig2 a8397cb4 / wabik3_recon 5dbc94ec /
  wabik3_uderzajacy, klasa uderzający/niedochodzący.
- Stan: katalog **7 → 6 otwartych pozycji** (PERCEPCJA-II, ODPOWIEDŹ-EKONOMIA,
  1b(ii) weryfikacja sieci z pytaniem o GRU, 2c, 2d, 2e). Breach 0 / REFUSE 0
  programowo bez zmian. Program w trybie katalogu; następne ruchy poza
  stanowiskiem (warstwa 0: raport EN, karta technologii, rozmowa z pilotem).
