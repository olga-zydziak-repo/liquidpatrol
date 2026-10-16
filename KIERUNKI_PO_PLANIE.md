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

## Backlog §8 (bez zmian, porządkowe)

Polityka git dla .ulg (decyzja od tygodni odroczona, nieblokująca) · martwe inicjalizacje w gate (przy
następnym uprawnionym dotknięciu pinu) · allowlista procesów jako plik żywy · rozpoznawanie atrap
(nota z triggerem z 23.08, warunki bez zmian).
