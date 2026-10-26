# PRE_WABIK — prerejestracja nogi WABIK, ścieżka (iii) WABIK-W-ŚWIECIE (rozpoznanie behawioralne na realnym wabiku + manewr pod orbitą)

CC · 26.10.2026 · po STOP-WABIKR (c09c38cb, zweryfikowany z repo: litera spawnu
run_boot.sh:122-124 wprost — EntityFactory runtime, world_hash niewrażliwy;
agregaty NULL odtworzone z 263 rekordów co do trzeciego miejsca; zero klasy
stacjonarnej potwierdzone niezależnym cięciem; arytmetyka R4 sprawdzona —
cięciwa 2·√(18²−5²)=34.6 s ✓). Ścieżka (i) skonsumowana reconem; (ii) v3 na
trigger dalekiego wzroku — OSOBNY PRE. Wymaga ratyfikacji Olgi; po niej
PROMPT_WABIK_S1 — na start nogi wklejasz DWA dokumenty (PRE + PROMPT).

## §1. Teza i dźwignia (FROZEN)

**Wabik = droga (a) z recon:** druga instancja wizualiów intruza (EntityFactory,
`name="wabik"`, ten sam r02/intruder_model.sdf — wizualnie IDENTYCZNY), NOWY
pusher `wabik_motion.py` (kopia wzoru intruder_motion pod nową nazwą, set_pose
20 Hz, własny log cmd/applied = GT wabika poza sędzią) z własnym plikiem
trajektorii; scenariusze manewrowe = NOWY plik manifestu przez env
`BENCH_MANIFEST` (istniejący manifest nietykalny). Zero dotyku zamrożonych.
**Rozpoznanie = klasyfikator sygnatur ruchu, WARUNKOWY NA RUCHU** (lekcja NULL:
bez warunku klasa v=0 daje 100% FP): cechy online z toru śledzenia — v_rad,
frac_closing, dh_min dotychczasowe, czas w strefie — wszystkie na oknie
wygładzonym ≥1 s (tick-po-ticku = szum estymaty); **krzywizna POZA zestawem**
(NULL: nie separuje, generator sam skręca). Progi FROZEN z kwantyli NULL
(p95 + margines) wpisane do FREEZE_WABIK per cecha, jednostki jawne, ZANIM
poleci jakikolwiek test. Klasyfikator żyje jako sidecar na strumieniu trk
(diagnostyczny — **NIE steruje lotem w tej nodze**; wyjście = etykieta
w telemetrii). GRANICE UCZCIWOŚCI: wabik lecący jak atak jest nierozróżnialny
z definicji — nie testujemy niemożliwego; TP mierzymy na rodzinach zachowań
wabikowych; multi-target poza zakresem (scenariusze z rozdzieleniem
azymutalnym — w fazach werdyktowych co najwyżej jeden obiekt w FOV; zachowanie
trackera przy dwóch obiektach = POMIAR smoke, nie założenie); reakcja wabika
na manewr obrońcy niemierzona (interakcyjna — katalog); zasięg ~15 m
obowiązuje.

## §2. Sesja S1 — budowa + smoke (budżet ≤3 booty)

1. **Narzędzia (nowe pliki):** `wabik_motion.py` + manifest WABIK z rodzinami
   trajektorii wabika — **W-LOITER** (krążenie na promieniu 8–12 m, nie
   schodzi pod 5), **W-STYCZNY** (cięciwa b≥5), **W-ZBLIŻ-ODSKOK** (podejście
   do ~7 m i odejście) — oraz scenariuszami manewrowymi intruza: **M-ŁUK**
   (łuk do home) i **M-POD-ORBITĄ** (radialny → zmiana kursu po ENTRY);
   polilinie w istniejącej semantyce segmentów.
2. **`wabik_sig.py`** — klasyfikator progowy (sidecar; czyta trk, pisze
   cechy+etykiety do wabik_sig.jsonl). **FREEZE_WABIK:** lista zamknięta cech,
   progi z NULL (liczby jawnie), okno 1 s, warunek ruchu, reguła decyzji
   (ile sekund spełniania progów ⇒ etykieta „wabik").
3. **SMOKE (1 boot, reżim OPS):** intruz radialny (istniejący scenariusz) +
   wabik W-LOITER w innym sektorze. Pomiary: spawn obu OK; **werdykt sędziego
   epizodu intruza = PASS jak historycznie** (kotwica czystości — wabik nie
   może ruszyć werdyktu); zachowanie trackera przy wabiku w FOV (klatki boxa
   na wabiku, przeskoki admisji) — opisowo, pierwszy taki pomiar w programie.
4. **ŚMIERĆ S1 (prereg):** spawn drugiej instancji niemożliwy bez dotyku
   zamrożonych ALBO tracker w żadnej konfiguracji rozdzielonej nie utrzymuje
   intruza (przeskoki uniemożliwiają sędziowanie) ⇒ STOP-ANEKS z wyceną
   multi-target jako warunku wstępnego. STOP-WABIK1: commit (narzędzia +
   FREEZE_WABIK + RAPORT_WABIK_S1). Push = Olga.

## §3. Sesja S2 — testy celowane (budżet ≤8 bootów)

1. Bramka: origin zawiera STOP-WABIK1; FROZEN + FREEZE_WABIK wykonaniem;
   każdy boot: reżim OPS (checklist + pin + profil + sonda). Loty UZBROJONE —
   twarde STOPy verbatim: breach ⇒ STOP; REFUSE(POS) ⇒ STOP; budżet ⇒ STOP.
2. **T-W-TP (6 epizodów):** wabik jedynym obiektem, 3 rodziny × 2 warianty.
   **SUKCES = etykieta „wabik" w ≤15 s śledzenia w ≥5/6; FALSYFIKACJA PROGÓW =
   ≤2/6** ⇒ STOP-ANEKS (progi z NULL nie przenoszą się na TP — wracamy do
   cech). Pomiędzy: strefa opisowa z dekompozycją per cecha.
3. **T-W-FP (3 epizody):** intruzi poważni — c08_s03, c10_s02, M-ŁUK.
   **ZERO etykiet „wabik"** (twardy wskaźnik; każda flaga = falsyfikacja
   marginesu progów → dekompozycja, która cecha pękła).
4. **T-W-ORB (2 epizody):** M-POD-ORBITĄ — pomiar niezmierzonego z R4:
   utrzymanie tracka i separacji pod zmianą kursu celu; d_min, D6 opisowo
   (sufitu nie rusza — twierdzenie R4). Świadek-filtr obok każdego rachunku
   na GT; GT wabika = log wabik_motion.
5. STOP-WABIK2: commit (RAPORT_WABIK_S2: tabela epizodów z cechami/etykietami/
   czasem-do-flagi, kotwice sędziego, diff-stat, porcelain). Push = Olga.
   Po weryfikacji CC: ANEKS_WABIK-2 (werdykt, KSIĘGA, CO; materiał demo
   i ewentualne rozszerzenia — osobne decyzje).

## §4. Predykcje CC (wskaźniki do KSIĘGI)

Cięcie głębokie stosuje się tam, gdzie mechanizm nazwany-niezmierzony:
tracker przy 2 obiektach (P-WB-2) i TP na wabiku (P-WB-3 — w danych programu
nie ma ani jednego wabika).

- **P-WB-1 (0.70):** smoke czysty — spawn 2 obiektów działa, werdykt sędziego
  intruza niezmieniony.
- **P-WB-2 (0.55):** tracker przy rozdzieleniu azymutalnym utrzymuje intruza
  bez przeskoku na wabika w fazach werdyktowych.
- **P-WB-3 (0.65):** TP ≥5/6 w ≤15 s.
- **P-WB-4 (0.75):** FP 0/3 (progi wprost z rozkładów NULL z marginesem).
- **P-WB-5 (0.60):** M-POD-ORBITĄ: separacja ≥4 m i track utrzymany w 2/2.
- **P-WB-6 (0.85):** breach 0 / REFUSE 0 w całej nodze.

## §5. Budżet, higiena, nietykalne

Budżet ścieżki (iii): S1 ≤3 + S2 ≤8 ⇒ **sufit ≤11 bootów** (sufit całej nogi
≤32 z recon obejmuje przyszłą ścieżkę (ii) — osobny PRE na trigger). Env
`WABIK_*`, katalog `results/WABIK/`, narzędzia WYŁĄCZNIE nowe pliki.
**NIETYKALNE:** percepcja w całości (det_v2 775ead15, percep_proc 38a3a765,
progi MTI/admisji, feed_registry — ramię klasyfikatora additive), sędzia
8ec0fcfb (wabik poza gt_intruder i poza werdyktem), osłona + piny 5/5, bench
05137098, `intruder_motion.py` oryginał, manifest istniejący, `worlds/*.sdf`
(zero edycji — spawn wyłącznie runtime), kontroler e435ed7e + wagi 0337d5ea,
FREEZE_PERC2_OPS (reżim OPS w każdym boocie). Klasyfikator nie steruje lotem.
Raporty wstecz nietykalne; errata w przód.

Ratyfikacja: „ratyfikuję". Sygnały bez numeru wykonawca odrzuca.
