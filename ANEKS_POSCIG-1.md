# ANEKS_POSCIG-1 — rozpuszczenie mechanizmu pozycji + ERRATUM-DMIN (trzy twarze artefaktu) + zamknięcie (CO-POSCIG)

CC · 18.10.2026 · łańcuch POSCIG (po STOP-POSCIGR, commit d46df034 na origin).
Aneks zamykający POZYCJĘ na etapie recon, samowykonalny (§5): zero bootów wydanych,
zero do wydania; sesja CO jest deskowa. Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-POSCIGR

Przyjęte po weryfikacji CC z repo wykonaniem: zakres = wyłącznie
results/POSCIG_RECON/** (12 plików); **pełny sędzia odtworzony przeze mnie na
surowych logach obu kampanii — 0 niezgodności z zapisanymi werdyktami** (184 ważne
epizody); listy flipów FAIL→PASS odtworzone CO DO SIDA (AKW V2: c06_s04, c09_s02,
c09_s03, c10_s03; AKW B: c09_s02, c11_s02; FANTOM V2: c05_s02, c09_s02; FANTOM B:
c09_s03, c11_s02); mechanizm odtworzony na surowych próbkach (c09_s02 FANTOM:
2 próbki t_rel 0.092/0.112 z pozą końca c08_s02, fake d_min 1.594 → po filtrze
7.005; nauczyciel c09_s02 boot6: 1.178 → 7.288, c09_s03 boot11: 2.521 → 7.176);
**koronny dowód niezależny: kolumna `d_min_orbit` w RAPORT_KAMPANIA_BLOK1 (wrzesień)
= DOKŁADNIE wartości po filtrze (7.597/7.703/7.288/7.176)** — ławka zmierzyła prawdę
już wtedy, nazywając ją „proximity wejścia <3 s". Odchylenia przyjęte z uznaniem:
przesłanka §Z zmierzona zamiast przyjęta (obalona uczciwie); skaza dedupu nazwana.

**Znalezisko CC przy weryfikacji (dopisane do erratum): artefakt ma TRZECIĄ twarz
i działa w OBIE strony.** Pełny sweep CC znalazł 1 flip PASS→FAIL: **AKW V2
c07_s01** — bogus próbka (poza poprzedniego epizodu, 6.8 m od home) wpadła w pasmo
[6,10] ⇒ fałszywe t_entry=0.0 ⇒ okno orbity otwarte za wcześnie ⇒ sweep 703.3°
zamiast realnych 619.9° (<630) ⇒ fałszywy PASS (na ostrzu: −10°). Twarze artefaktu:
(1) fałszywe d_min, (2) fałszywe t_entry→przesunięte okno frac/sweep,
(3) interpolacja przez skok. Korekta what-ifów niżej.

## §2. WERDYKT: pozycja POŚCIG-V1 ZAMKNIĘTA wynikiem recon — ROZPUSZCZENIE MECHANIZMU

**„Deficyt pościgu za celem szybkim" nie istnieje jako mechanizm.** Zbiór odniesienia
(11 V2 + 2 B) rozpada się na: **3+2B artefakt przyrządu** (realnie PASS),
**6 akwizycja-transit** (t_acq 19.5–31.2 s; cel realnie przechodzi <4 m pod ślepym
zawisem i okno sędziego płonie PRZED istnieniem tracku — klasa akwizycji, nie
pościgu; niewykonalne nawet dla ideału OD akwizycji, wykonalne od t0),
**2 near-missy omiatania** przy żywym tracku (558.7° i 551.3°/630; frac i d_min OK).
Fakty zamykające: sufit kinematyczny NIE istnieje (ideał @3.0 m/s: 13/13 od t0,
intercept=ogon przy 3:1); hipoteza sufitu nadzoru OBALONA (nauczyciel po erratum
**120/120, w tym 40/40 na v=1.0** — 6/6 jego porażek to artefakt); sieć w pościgu
zbieżna-nigdy-rozbieżna, lecz poniżej koperty (p50 53–90% V_MAX — odziedziczone
prawo hamowania; kosztuje wyłącznie w 2 near-missach). **Dotrening nieuzasadniony
rachunkiem:** zysk górny 2 pary vs ~27–29 bootów i ryzyko regresji; skryptowy
pościgowiec odrzucony kosztem tezowym (gniazdo kontrolera = sieć — werdykty W1′/LIQ
przestałyby porównywać sieci). Pozycja zamyka się kosztem **0 bootów** (trzecie
pełne zabicie kierunku deskiem: RE-AKW → FANTOM-desk-wybór → POŚCIG). KSIĘGA bez
rozliczenia — PRE nie powstało.

## §3. ERRATUM-DMIN (werdykto-nośne w PIĘCIU zbiorach; wzór ERRATUM_VMAX)

Tranzient teleportu bramki startu: pierwsze 1–2 próbki `gt_intruder.jsonl` epizodu
niosą pozę SPRZED teleportu (bufor subskrypcji, intruder_motion.py:102-109; klasa
znana z shakeoutu, dotąd nieskojarzona z sędzią). Marker-świadek:
**|ned−cmd_ned|_xy > 1 m**. Zasady: **sędzia 8ec0fcfb FROZEN, zdania zamrożone
kampanii NIETKNIĘTE, raporty wstecz nietykalne** — erratum = plik + adnotacje
DOPISANE na końcu raportów dotkniętych (nigdy edycja treści); filtr-świadek liczony
ODTĄD OBOK każdego werdyktu sędziowanego na gt_intruder (kolumna d_min_filtered +
flagi flip), w obu kierunkach.

What-ify (świadek obok liter):
- **AKW S3: Δ_new 12 → 11** (pass_B 46→48, pass_V2 34→38−1: cztery FAIL→PASS,
  c07_s01 PASS→FAIL) — **ŚMIERĆ-AKW ODPORNA na erratum (11 ≥ 10)**;
- **FANTOM S2: Δ_new2 7 → 7** (B 38→40, V2 31→33; skład zmieniony); N6 3/6 → 4/6
  (c05_s02 artefakt) — strefa opisowa bez zmiany progowej; nota: AKW-owa porażka
  c06_s04 też artefaktowa, więc jej „konwersja" w FANTOM nie była zasługą kwarantanny;
- **nauczyciel: 114/120 → 120/120** (klasa „proximity wejścia" nie istnieje);
- **D0: 6 wykluczeń artefaktowych** — korpus zubożony (m.in. 3×c09 v=1.0),
  nie skażony; bez przebudowy D0 teraz (erratum-materiał);
- **zakres do DOMKNIĘCIA w CO (§5): sweep świadka na pozostałych kampaniach
  sędziowanych na gt_intruder** — DET S4 (Δ=34), LIQ/W1′ (43/48), K2 (12/12),
  ławka blok1+2 w całości — erratum bez pełnego zasięgu byłoby nieuczciwe; narzędzie
  istnieje (poscig_sweep), wyniki do tabeli erratum; zdania zamrożone tych nóg
  pozostają literą, what-ify obok.

## §4. Pozycje katalogowe (NIE otwierane tym aneksem)

- **AKW-TRANSIT** — 6 epizodów modu B (c08_s03, c08_s04, c10_s02, c11_s02, c11_s03,
  c11_s04): późna akwizycja 19.5–31.2 s, cel wchodzi <4 m pod ślepy zawis zanim
  track istnieje; mechanizm ZMIERZONY (ten recon), dźwignia [NIEZMIERZONA] — poza
  percepcją (FROZEN): choreografia skanu lub wyżej. Trigger: przed roszczeniem
  pełnej siatki. Aktywa: r1/r2_behavior + telemetria trzech kampanii.
- **GT-CZYSTOŚĆ** (narzędziowa, niski priorytet) — utwardzenie u źródła: czystość
  pierwszych próbek gt_intruder (start logowania po świeżości bufora); wymaga zgody
  na dotyk frozen bencha/intruder_motion ⇒ własny łańcuch z FREEZE. Do tego czasu
  świadek-filtr wystarcza.

## §5. Zlecenie CO-POSCIG — commit zamykający (samowykonalny; jeden commit, zero bootów, sesja deskowa)

Bramka: `git log origin/master..HEAD` puste ⇒ dalej; inny stan ⇒ STOP. Zakres:
1. Korzeń `ANEKS_POSCIG-1.md` (ARCH-1, verbatim, pierwszy w commicie).
2. **Sweep świadka na pozostałych zbiorach** (narzędzie-kopia poscig_sweep; desk):
   DET S4 {B,V2}, LIQ (booty W1′), K2, ławka blok1+2 — flipy OBU kierunków,
   wyniki do §3 tabeli.
3. NOWY `results/POSCIG_RECON/ERRATUM_DMIN.md`: mechanizm (trzy twarze), marker,
   pełna tabela flipów wszystkich zbiorów (z §1 + pkt 2, oba kierunki, w tym
   c07_s01), what-ify §3 z literami obok, reguła świadka-odtąd, odsyłacze.
4. Adnotacje-erratum DOPISANE na końcu (sekcja „NOTA-ERRATUM (ANEKS_POSCIG-1 §3)",
   treść oryginału nietknięta): `results/AKW/RAPORT_AKW.md`,
   `results/FANTOM/RAPORT_FANTOM.md`, `results/BENCH/RAPORT_KAMPANIA_BLOK1.md`,
   `results/REAKW_RECON/RECON_REAKW.md` (klasa „czysty pościg" 5→3) + inne zbiory
   dotknięte wg pkt 2.
5. EDYCJA `KIERUNKI_PO_PLANIE.md`: POŚCIG-V1 → **CLOSED-BY-RECON (rozpuszczenie
   mechanizmu)** z odsyłaczem i werdyktem jednozdaniowym §2; dopisane pozycje
   **AKW-TRANSIT** i **GT-CZYSTOŚĆ** wg §4; nota przy łańcuchu Δ 34→12→7:
   „z erratum DMIN — what-ify obok liter, ERRATUM_DMIN.md".
6. ŻADNYCH edycji KSIĘGI (PRE nie istniało), ŻADNEJ podmiany liczb kanonicznych,
   zero dotykania kodu poza narzędziem-kopią sweepa. Raport płaski: diff-stat,
   pełna treść ERRATUM_DMIN.md i zmian KIERUNKÓW, porcelain. STOP.
   Push = Olga („wypchnięte").

## §6. Status i dalej

Pozycja POŚCIG-V1: CLOSED (0 bootów, 1 sesja deskowa + CO). Owoc większy niż
pozycja: ERRATUM-DMIN prostuje przyrząd w pięciu zbiorach i uodparnia każdą przyszłą
kampanię (świadek obowiązkowy). Mapa rezyduum po erratum: **Δ_FANTOM co do liczby 7,
co do treści = 6 akwizycja-transit + 2 near-missy + regresja-wariancja** — kamera
realnie przegrywa z wyrocznią tylko tam, gdzie cel przechodzi pod ślepym skanem.
Katalog: AKW-TRANSIT (mechanizm zmierzony), GT-CZYSTOŚĆ (narzędziowa), 1b(ii)
weryfikacja sieci, 2d VIO, 2c adwersarz; warstwa 0 bez zmian. Breach 0 / REFUSE 0
pozostaje prawdą o wszystkim, co kiedykolwiek poleciało uzbrojone.
