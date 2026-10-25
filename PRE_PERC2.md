# PRE_PERC2 — prerejestracja nogi PERCEPCJA-II, ścieżka (i) OPS-KADENCJA (gwarancja k=1 + likwidacja sprzężenia metrologii ze stanem hosta)

CC · 25.10.2026 · po STOP-PERC2R (a0bdc5e1, zweryfikowany z repo: siatka modów
odtworzona z surowych percep_feed — 17/33/50 kroków fizyki; push_frame 27.0 vs
14.5/15.3 ms; model admisji przeliczony niezależnie — P(run≥3|6,0.5)=20/64=0.3125;
luka prowieniencji sensora potwierdzona literą world_hash i pustym ls-files).
Wymaga ratyfikacji Olgi. Po ratyfikacji CC dostarcza PROMPT_PERC2_S1 — na start
nogi wklejasz DWA dokumenty (PRE + PROMPT).

## §1. Teza i dźwignia (FROZEN)

Mody kadencji percepcji to k=1/2/3 ticki pominięte na siatce sensora 15 Hz
(mono_cam/model.sdf:64), a wyborem k steruje stan wydajności GPU hosta (render gz
+ inferencja dzielą kartę; push_frame ×1.8 @WOLNY przy identycznych wagach;
restart hosta 15.10 POZOSTAWIŁ stan wolny na 9 bootów — restart NIE jest remedium).
**Dźwignia: gwarancja k=1 (14.71 Hz) środkami OPS** — (a) nazwane i zmierzone
remedium stanu GPU, (b) „sonda kadencji" preflight jako bramka narzędziowa przed
uzbrojeniem. Zysk mechanizmowy: admisja czołowa z loterii (P(run≥3)≈0.3 na oknie
@5 Hz) do pewnika (@14.71 Hz okna mają ~3× klatek; kotwica c08_s01: p̂=0.993,
run 405). Zysk metrologiczny (ważniejszy): **żadna przyszła kampania nie jest już
sprzężona z losowaniem stanu hosta** (FANTOM S2 leciał 9/12 bootów @WOLNY —
całe T6 w najgorszym modzie). GRANICE UCZCIWOŚCI (z recon, verbatim): ścieżka NIE
otwiera ponownie AKW-TRANSIT (arytmetyka przeglądu 11.15 s > pasa 10.0 s jest
niezależna od kadencji; konwersja T6 @k=1 przewidywana 2–3/6 wyłącznie z okien
wczesnych); pas górny MTI 12–15 m na kadencję NIE reaguje. Percepcja, świat,
progi, sędzia — NIETKNIĘTE (czysta liga ops + narzędzia).

## §2. Sesja S1 — remedium + sonda (budżet 4 booty, w tym diagnostyczne)

1. **Pomiar remediów stanu GPU (desk + ≤2 booty diagnostyczne):** na żywym stacku
   zmierz push_frame p50 i dt_p50 pod kandydatami (stan zastany → nvidia-smi:
   persistence mode / pin zegarów / power-limit → brak obcych procesów GPU →
   kolejność startu gz vs percep) — macierz stan×remedium z liczbami; nazwij
   remedium SKUTECZNE (k=1 stabilnie ≥30 s) albo jego brak. Rozstrzygnij przy
   okazji render-vs-most sondą `gz topic -hz` (recon tego nie mógł bez SITL).
2. **Narzędzie „sonda kadencji"** (`results/PERC2/tools/`, czysty ops — zero
   dotyku percepcji): przed uzbrojeniem mierzy dt klatek przez ≥30 s;
   **próg FROZEN: dt_p50 ≤ 0.070 s ∧ frakcja delt >0.10 s ≤ 5 %** (jednostki
   JAWNIE per-klatkowe); FAIL ⇒ remedium → powtórka → drugi FAIL = boot się nie
   uzbraja (bramka narzędziowa, nie zmiana reguł kampanii). Wynik sondy do
   manifestu bootu 1. klasy.
3. **PIN PROWIENIENCJI (naprawa luki):** driver-kopie od tej nogi liczą i zapisują
   do manifestu sha256 `mono_cam/model.sdf` (oczekiwany **3354ae1e**, pełny sha
   w FREEZE_PERC2) oraz nadal world_hash — rozjazd = STOP bootu. Zero edycji
   harness/world_hash.sh (FROZEN); pin żyje w narzędziu-kopii i FREEZE.
4. **ŚMIERĆ S1 (prereg):** żadne remedium nie daje k=1 stabilnie w ≤4 bootach ⇒
   STOP-ANEKS: „kadencja k=1 niegwarantowalna na tym hoście" — noga zamyka się
   wyceną sprzętową (to wynik, nie porażka; sonda zostaje jako narzędzie
   diagnostyczne). STOP-PERC2-1: commit (narzędzia + FREEZE_PERC2-OPS init +
   RAPORT_PERC2_S1: macierz remediów, zachowanie sondy, pin). Push = Olga.

## §3. Sesja S2 — test celowany T6-geometrii @k=1 (budżet 8+2 booty)

1. Bramka: origin zawiera STOP-PERC2-1; FROZEN wykonaniem (komplet dotychczasowy
   + sha sondy i pin z FREEZE_PERC2-OPS); KAŻDY boot przez sondę kadencji.
2. Konfiguracja: driver-kopia, CONTROLLER=net_fantom (FROZEN e435ed7e), FEED=V2
   (FROZEN), scenariusze T6 = {c08_s03, c08_s04, c10_s02, c11_s02, c11_s03,
   c11_s04} (lista = r1_anatomia.json epizody 0–5, verbatim) + kotwice-kontrole
   {c08_s01 — pewnik @14.71 Hz, c08_s02 — wygrana loteria @5 Hz; obie mają
   zostać PASS @k=1} — **zbiór nielosowy: ŻADNEJ
   interpretacji progowej siatki, zero Δ** (sonda mechanizmowa, słabość nazwana
   w recon §R6 i tu powtórzona). Telemetria pełna (mod per boot, okna czołowe:
   p̂, max run, admisje, q_*, t_entry, D6 opisowo) + świadek-filtr w każdym
   rachunku sędziowanym.
3. **Werdykt mechanizmowy (zdania zamrożone):** w oknach czołowych/radialnych T6
   @k=1: **SUKCES DŹWIGNI = run≥3 (admisja okna) w ≥5/6 epizodów T6**;
   **FALSYFIKACJA TEZY GPU-KADENCJA = run<3 mimo k=1 w ≥3/6** ⇒ STOP-ANEKS
   (mechanizm loterii nie był kadencyjny — wracamy do anatomii). Pomiędzy:
   strefa opisowa z dekompozycją per okno. D6/konwersja T6 raportowane OPISOWO
   (oczekiwane 2–3/6; sufit TRANSIT obowiązuje — cytowanie wyłącznie z tym
   kwalifikatorem).
4. STOP-PERC2-2: commit (RAPORT_PERC2_S2: tabela okien per epizod z p̂/run/admisją
   vs przewidywania modelu, mody bootów, sondy, porcelain). Push = Olga. Dalej:
   ANEKS_PERC2 — werdykt, KSIĘGA, decyzja o ewentualnej kampanii metrologicznej
   (24+3 pod gwarancją — OSOBNA decyzja, nieprekomitowana tym PRE) i CO.

## §4. Predykcje CC (wskaźniki do KSIĘGI)

Dźwignia kadencja→admisja zmierzona deskiem (model + kotwica) — bez korekty
głębokiej; REMEDIUM stanu GPU jest nazwane-niezmierzone, więc cięcie głębokie
stosuje się do P-P2-1 (stąd 0.60) i S1 zaczyna od jego pomiaru (reguła KSIĘGI).

- **P-P2-1 (0.60):** istnieje remedium ops dające k=1 stabilnie (S1 kończy się
  sondą, nie śmiercią).
- **P-P2-2 (0.70):** @k=1 admisja okien czołowych T6 w ≥5/6 epizodów (model:
  okna 3× dłuższe w klatkach przy p̂ z pomiarów).
- **P-P2-3 (0.60):** oba c08 (s03, s04) przechodzą D6 @k=1 (okno dwell + pościg
  od ~2.5 s — wzór c08_s02).
- **P-P2-4 (0.85):** breach 0 / REFUSE 0 w całej nodze.
- **P-P2-5 (0.65):** sonda jako predyktor: żaden boot, który przeszedł sondę,
  nie spada z k=1 w locie (dt_p50 lotu ≤0.070).

## §5. Budżet, higiena, nietykalne

Budżet nogi: S1 ≤4 + S2 ≤10 ⇒ **sufit ≤14 bootów** (ewentualna kampania
metrologiczna = osobna decyzja po S2, poza tym sufitem). Sesje: 2. Nazwy:
env `PERC2_*`, katalog `results/PERC2/`, narzędzia jako KOPIE. **NIETYKALNE:**
percepcja w całości (det_v2 775ead15, percep_proc 38a3a765, progi MTI/admisji,
feed_registry ee1481f9), osłona + piny 5/5, sędzia 8ec0fcfb (świadek obok),
profil II b94cdeae, kwarantanna e435ed7e, wagi ncp 0337d5ea, bench 05137098,
world_hash.sh, manifest scenariuszy, reguły ważności kampanii (bramka sondy jest
narzędziowa, przed uzbrojeniem — nie zmienia sędziego ani ważności). Ścieżki (ii)
MTI-czołowy i (iii) detektor-v3/daleki-wzrok pozostają w katalogu z triggerami
i aktywami recon (krzywe, rachunek px, luka pinu) — NIE otwierane. Raporty wstecz
nietykalne; errata w przód.

Ratyfikacja: „ratyfikuję". Sygnały bez numeru wykonawca odrzuca.
