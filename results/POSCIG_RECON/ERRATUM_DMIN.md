# ERRATUM-DMIN — tranzient teleportu w gt_intruder a werdykty sędziego D6

Data: 2026-10-20 (CO-POSCIG). Podstawa: ANEKS_POSCIG-1 §3/§5 (po STOP-POSCIGR,
dowód mechanizmu w `RECON_POSCIG.md` §R2a). Format jak `ERRATUM_VMAX.md` /
`ERRATUM_42M.md`: ten plik + adnotacje DOPISANE na końcu raportów dotkniętych
(treść oryginałów NIETKNIĘTA). **Sędzia `bench/bench_judge.py` FROZEN (8ec0fcfb),
zdania zamrożone kampanii pozostają LITERĄ** — wszystkie liczby niżej to what-ify
OBOK liter, nie podmiany.

## §1. Mechanizm — trzy twarze artefaktu

Bramka startu epizodu teleportuje intruza na pozę startową i weryfikuje go
≤TOL_START=0.20 m PRZED t0 (`bench_flight.py:276`, `intruder_motion.py:30`), ale
pierwsze 1–2 próbki `gt_intruder.jsonl` epizodu niosą w polu `ned` pozę SPRZED
teleportu (bufor subskrypcji, `intruder_motion.py:102-109`; klasa znana z shakeoutu
„max 21 m = tranzient teleportu granicznego", dotąd nieskojarzona z sędzią).
Pole `cmd_ned` jest poprawne od t0. Zamrożony sędzia (`bench_judge.py:88-96`) liczy
na tych próbkach i na interpolacji liniowej przez skok (`bench_judge.py:34-47`):

1. **fałszywe d_min** — bogus poza (często poza poprzedniego epizodu, bywa blisko
   trasy drona) daje fikcyjne zbliżenie <4 m ⇒ fałszywy FAIL `d_dmin`;
2. **fałszywe t_entry → przesunięte okno frac/sweep** — bogus poza wpada w pasmo
   [6,10] ⇒ t_entry=0.0 zamiast realnego ⇒ okno orbity liczone od złej chwili;
   działa w OBIE strony (fałszywy FAIL `b_frac`/`c_sweep` ALBO fałszywy PASS
   `c_sweep` — wzór c07_s01 niżej);
3. **interpolacja przez skok** — odcinek bogus-poza→prawdziwa poza przechodzi przez
   geometrię, której intruz nigdy nie przebył (wzmacnia twarze 1 i 2).

## §2. Marker-świadek i reguła-odtąd

**Marker:** `|ned − cmd_ned|_xy > 1.0 m` (intruz nie śledzi komendy ⇒ próbka sprzed
teleportu). **Filtr-świadek:** werdykt sędziego FROZEN policzony drugi raz na
próbkach z `|ned − cmd_ned|_xy ≤ 1.0 m`.

**Reguła od teraz (ANEKS_POSCIG-1 §3):** każdy werdykt sędziowany na `gt_intruder`
dostaje ODTĄD OBOK litery kolumnę `d_min_filtered` + flagi flip OBU kierunków
(FAIL→PASS i PASS→FAIL). Świadek nie podmienia werdyktu — nazywa artefakt.
Utwardzenie u źródła = pozycja katalogowa GT-CZYSTOŚĆ (ANEKS_POSCIG-1 §4; dotyk
frozen bencha wymaga własnego łańcucha z FREEZE).

## §3. Pełna tabela flipów — wszystkie zbiory sędziowane na gt_intruder, oba kierunki

Sweep: `tools/erratum_sweep.py` → `erratum_sweep.json` (530 epizodów: AKW S3 96,
FANTOM S2 92, DET S4 96, LIQ/W1′ 96, K2 12+12, ławka blok1+2 126). Kierunek:
F→P = fałszywy FAIL (po filtrze PASS), P→F = fałszywy PASS (po filtrze FAIL).

| zbiór:ramię | epizod | boot | kier. | d_min pełny→filtr | t_entry pełny→filtr | sweep pełny→filtr | powody pełne→filtr | ważny |
|---|---|---|---|---|---|---|---|---|
| AKW S3:V2 | c06_s04 | r11_V2 | F→P | 3.233→7.601 | 11.364 | 659.9 | d_dmin→— | tak |
| AKW S3:V2 | c09_s02 | r6_V2 | F→P | 1.299→7.623 | 4.544 | 639.6 | d_dmin→— | tak |
| AKW S3:V2 | c09_s03 | r9_V2 | F→P | 2.517→7.413 | 0.04→4.832 | 618.5→678.7 | c_sweep,d_dmin→— | tak |
| AKW S3:V2 | c10_s03 | r9_V2 | F→P | 3.884→5.400 | 5.28 | 688.4 | d_dmin→— | tak |
| **AKW S3:V2** | **c07_s01** | r2_V2 | **P→F** | 6.696→7.798 | **0.0→9.572** | **703.3→619.9** | —→c_sweep | tak |
| AKW S3:B | c09_s02 | r6_B | F→P | 1.089→6.443 | 2.056 | 799.0 | d_dmin→— | tak |
| AKW S3:B | c11_s02 | r6_B | F→P | 0.427→7.125 | 0.0→1.82 | 1026.5→869.2 | d_dmin→— | tak |
| FANTOM S2:V2 | c05_s02 | r5_V2 | F→P | 3.840→6.352 | 6.6 | 791.0 | d_dmin→— | tak |
| FANTOM S2:V2 | c09_s02 | r6_V2 | F→P | 1.594→7.005 | 5.136 | 739.3 | d_dmin→— | tak |
| FANTOM S2:B | c09_s03 | r9_B | F→P | 1.190→7.764 | 1.9 | 797.6 | d_dmin→— | tak |
| FANTOM S2:B | c11_s02 | r6_B | F→P | 0.629→6.770 | 0.0→2.084 | 1042.1→886.8 | d_dmin→— | tak |
| FANTOM S2:B | c11_s01 | r3_B | F→P | 3.346→5.668 | 0.08→2.06 | 759.4→748.0 | d_dmin→— | **NIE** (poza n_common — bez wpływu na liczby) |
| **DET S4:B** | **c09_s03** | r9_B | F→P | 1.172→7.616 | 1.98 | 816.7 | d_dmin→— | tak |
| LIQ:ncp | c07_s02 | r5_ncp | F→P | 3.907→7.281 | 2.316 | 968.8 | d_dmin→— | tak |
| LIQ:ncp | c09_s02 | r6_ncp | F→P | 1.221→6.522 | 2.08 | 900.6 | d_dmin→— | tak |
| LIQ:ncp | c11_s02 | r6_ncp | F→P | 1.257→6.520 | 0.0→2.264 | 1046.7→866.7 | b_frac,d_dmin→— | tak |
| LIQ:ncp | c09_s03 | r9_ncp | F→P | 0.352→7.298 | 2.02 | 808.3 | d_dmin→— | tak |
| LIQ:ncp | c10_s04 | r12_ncp | F→P | 2.292→7.035 | 1.936 | 855.2 | d_dmin→— | tak |
| LIQ:gru | c05_s02 | r5_gru | F→P | 4.978→7.347 | 0.06→2.248 | 616.3→633.8 | c_sweep→— | tak |
| LIQ:gru | c07_s02 | r5_gru | F→P | 3.978→7.120 | 2.38 | 663.7 | d_dmin→— | tak |
| LIQ:gru | c09_s02 | r6_gru | F→P | 1.400→6.793 | 2.136 | 640.4 | d_dmin→— | tak |
| **LIQ:gru** | **c11_s02** | r6_gru | **P→F** | 6.402 (bez zmiany) | **0.0→2.272** | **697.8→514.0** | —→c_sweep | tak |
| ławka b1 | c05_s01 | **boot11** (att2) | F→P | 2.988→7.597 | 2.716 | 942.0 | d_dmin→— | tak |
| ławka b1 | c07_s02 | boot5 | F→P | 3.875→7.703 | 0.1→2.496 | 910.0→891.7 | d_dmin→— | tak |
| ławka b1 | c09_s02 | boot6 | F→P | 1.178→7.288 | 2.336 | 834.9 | d_dmin→— | tak |
| ławka b1 | c09_s03 | boot11 | F→P | 2.521→7.176 | 2.092 | 846.2 | d_dmin→— | tak |
| ławka b2 | c05_s08 | b2b9 | F→P | 2.861→7.706 | 0.0→3.524 | 1047.7→868.9 | d_dmin→— | tak |
| ławka b2 | c09_s06 | b2b17 | F→P | 2.725→7.190 | 1.9 | 954.7 | d_dmin→— | tak |

Dwa flipy PASS→FAIL (c07_s01 AKW V2, c11_s02 LIQ gru) to w obu przypadkach twarz 2:
bogus próbka w paśmie [6,10] ⇒ fałszywe t_entry=0.0 ⇒ okno sweep otwarte za wcześnie
⇒ zaliczony sweep, którego w realnym oknie nie było (619.9 i 514.0 < 630).

## §4. Zasięg artefaktu bez flipów

Próbki artefaktu (≥1 zła próbka na starcie epizodu) występują szeroko, flipują
rzadko — tylko gdy bogus poza leży blisko trasy drona albo w paśmie [6,10]:

| zbiór:ramię | epizodów | z artefaktem | flip F→P | flip P→F |
|---|---|---|---|---|
| AKW S3:B / V2 | 48 / 48 | 25 / 28 | 2 / 4 | 0 / 1 |
| FANTOM S2:B / V2 | 44 / 48 | 25 / 32 | 3 (2 ważne) / 2 | 0 / 0 |
| DET S4:B / V2 | 48 / 48 | 27 / 27 | 1 / 0 | 0 / 0 |
| LIQ ncp / gru | 48 / 48 | 28 / 25 | 5 / 3 | 0 / 1 |
| ławka b1 / b2 | 54 / 72 | 32 / 42 | 4 / 2 | 0 / 0 |
| K2 (k2c) | 12 | **0** | 0 | 0 |
| K4b | 12 | 8 | 0 | 0 |

**K2 jest CZYSTY** (0 próbek artefaktu w 12 epizodach kampanii k2c) — werdykt 12/12
nietknięty nawet hipotetycznie; nadto kanon K2 to REFUSE/touchdown/breach, nie D6.
K4b: artefakt obecny (8/12), zero flipów, kanon również nie-D6. **Fałszywa bliskość
NIGDZIE nie wytworzyła breach** — „breach 0" pozostaje prawdą bez gwiazdki.

## §5. What-ify obok liter (zdania zamrożone NIETKNIĘTE)

- **AKW S3 (`RAPORT_AKW.md`, Δ_new=12 ŚMIERĆ-AKW):** pass_B 46→48, pass_V2 34→37
  (+4 F→P, −1 c07_s01) ⇒ **Δ 12→11; ŚMIERĆ-AKW ODPORNA na erratum (11 ≥ 10)**.
- **FANTOM S2 (`RAPORT_FANTOM.md`, Δ_new2=7):** na n_common=40: B 38→40, V2 31→33 ⇒
  **Δ 7→7** (skład zmieniony); **N6 3/6→4/6** (c05_s02 artefakt) — strefa opisowa bez
  zmiany progowej; nota: AKW-owa porażka c06_s04 też artefaktowa ⇒ jej „konwersja"
  w FANTOM nie była zasługą kwarantanny; flip c11_s01 (B) poza n_common — bez wpływu.
- **DET S4 (`RAPORT_DET.md`, Δ=34):** pass_B 47→48, pass_V2 13→13 ⇒ **Δ 34→35** —
  werdykt „percepcja limituje wykonanie" ODPORNY i minimalnie WZMOCNIONY
  (jedyna „porażka wyroczni" kampanii była artefaktem: wyrocznia realnie 48/48).
- **LIQ/W1′ (`RAPORT_LIQ.md`, NCP 43/48 vs GRU 27/48):** **NCP 43→48 (48/48!),
  GRU 27→29** (+3 F→P, −1 c11_s02 P→F) ⇒ rozstęp 16→19 — **W1′ ODPORNY
  i WZMOCNIONY**; świeże NCP po erratum równa się i przewyższa kanon NET 45/48
  (nota dryfu ławki do odczytu z tym świadkiem).
- **ławka blok1+2 (`RAPORT_KAMPANIA_BLOK1.md`, nauczyciel 114/120):** wszystkie
  6 porażek D6 = artefakt ⇒ **nauczyciel realnie 120/120** (blok1 p_exec what-if
  44/48→48/48 = 1.0; CI litera nietknięta); klasa „proximity wejścia <3 s" NIE
  istnieje — kolumna `d_min_orbit` raportu już we wrześniu pokazywała prawdę
  (7.597/7.703/7.288/7.176 = wartości po filtrze co do 0.001); nota diagnostyczna
  „nauczyciel zawodzi na proximity wejścia c05/c07/c09" — bezprzedmiotowa.
- **D0 (korpus treningowy):** 6 wykluczeń artefaktowych (m.in. 3×c09 v=1.0) —
  korpus ZUBOŻONY o dobre dema, nie skażony; bez przebudowy D0 teraz.
- **RE-AKW (`RECON_REAKW.md`):** klasa „czysty pościg bez utraty tracku" **5→3**
  (c06_s04, c09_s02 = artefakt); werdykt recon (0/14, dźwignia sfalsyfikowana)
  NIETKNIĘTY.

## §6. Noty reprodukcyjne sweepa (uczciwość przyrządu)

- **Reprodukcja sędziego:** DET S4 — zgodność z `detS4_summary.json` 94/96 co do
  (werdykt, d_min±0.01); 2 niezgodności WYŁĄCZNIE w d_min przy zgodnych werdyktach
  i powodach (r4_V2 c01_s02: 15.082 vs 15.103; r4_V2 c02_s02: 13.735 vs 15.035 —
  epizod z próbką artefaktu max_dev 21.2 m; oba FAIL a_entry, d_min >13 m, daleko
  od progów — nie-werdykto-nośne). LIQ — sumy pełne odtworzone CO DO SZTUKI
  (ncp 43/48, gru 27/48). Ławka — porażki odtworzone 6/6 zgodnie z agregatami
  (blok1 44/48, blok2 70/72).
- **Korekta atrybucji (vs narzędzie recon `poscig_artefakt.py`):** kanoniczna
  porażka c05_s01 ławki to **boot11 (attempt 2** wg `campaign_aggregate.json`**)**,
  nie boot2 (attempt 1, requeue; epizod boot2 był zresztą PASS 8.118). Lista CASES
  nauczyciela w poscig_artefakt wskazywała boot2 — wartości flipa c05_s01 w
  `artefakt_dmin.json` pochodzą więc z niekanonicznego epizodu; sweep niniejszy
  liczy kanoniczny boot11 (2.988→7.597 — zgodny z `d_min_orbit` 7.597 raportu).
  Werdykt „nauczyciel 120/120" bez zmiany (oba epizody c05_s01 po filtrze PASS).
- Wystąpienie c05_s01 w `boot0_diag` (diagnostycznym) ma 2 próbki artefaktu bez
  flipa — poza kampanią, odnotowane dla kompletności.

## §7. Odsyłacze

Mechanizm i dowód pierwotny: `RECON_POSCIG.md` §R2a (reprodukcja co do 0.001).
Narzędzia: `tools/poscig_artefakt.py` (pomiar pierwotny), `tools/erratum_sweep.py`
(pełny sweep CO, oba kierunki) → `erratum_sweep.json`; `sweep_artefakt.json`
(sweep pierwotny AKW/FANTOM, tylko F→P), `artefakt_dmin.json`. Decyzje i zasady:
`ANEKS_POSCIG-1.md` §1–§5. Wzór formatu: `ERRATUM_VMAX.md`, `results/K1/ERRATUM_42M.md`.
Pozycja utwardzenia u źródła: GT-CZYSTOŚĆ (`KIERUNKI_PO_PLANIE.md`).
