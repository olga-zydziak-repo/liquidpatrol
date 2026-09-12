# ANEKS_FV-1 — ratyfikacja STOP-FV1 (S1) + prerejestracja M-kroku

CC · 11.09.2026 · łańcuch FV (kolejny po ANEKS_FV-0).

## §1. Ratyfikacja S1
C0 (df58922, ARCH-1 4/4, sha źródło↔repo zgodne), C1 (siatka prerejestrowana commitem PRZED
pierwszym biegiem — 729a44c), C2 (dde0a7e) — PRZYJĘTE. **O1 = PROVED** (P6_d5, 10 obligacji unsat).
Różnicówka: 54 punkty siatki + 4×10⁵ fuzz + fikstura 4221/1791 ticków = **0 rozbieżności**, lustro
niezmienione po biegach, rejestr pusty. TRIPWIRE niewyzwolony. SR-FV-1..7 czyste. Stan bramki nogi
(PRE §5): O1 ∧ różnicówka ✓ — PASS czeka wyłącznie na O2.

## §2. Weryfikacja arytmetyczna CC (niezależna)
N* = ⌈(407/42)·20⌉ = ⌈4070/21⌉ = ⌈193.8095⌉ = **194** ✓; t_touchdown = 194·0.05 = **9.700 s** —
spójne z pomiarem K2 (t_td ≈ 9.8 s, RAPORT_K2 §2/§3): różnica ≈ t_refuse 0.104–0.116 + detekcja
przyziemienia. Dwa niezależne przyrządy (dowód na modelu vs kampania w locie) zgadzają się co do
profilu — to najlepszy dostępny cross-check wierności modelu. desc_fast_dur = (ALT_M − H_SWITCH) /
V_FAST = 8/(3/2) = 16/3 ✓.

Obserwacja: człon lądowania = 407/42 − 16/3 = 183/42 = 61/14 ≈ 4.357 s; przy v_land = 0.7
[odczyt z uciętego transportu — do potwierdzenia] daje ~3.05 m > H_SWITCH 2.0 m, co sugeruje jawny
margines/overshoot w produkcyjnej formule desc_total. Nie kwestionuję certu (formuła „jak
produkcja" z cytatami + fikstura lotów 0 rozbieżności + zgodność z t_td K2) — chcę widzieć
derywację.

## §3. CLARIFY-1 (warunek pełnej skuteczności)
W raporcie S2 jedna linia: produkcyjna formuła desc_total VERBATIM z `plik:linia` (transport uciął
derywację; jeśli stoi w results/FV/RAPORT_FV_S1.md — wystarczy cytat stamtąd).

## §4. Kosmetyka — ratyfikowana as-is
N_star_derivation zostaje bez zmian: poprawka renderowania = nowe sha certu bez zmiany treści;
zakaz kosmetycznych regeneracji certów (lekcja self-hash P2.json).

## §5. M-KROK (prerejestracja; wykonanie w S2 PRZED dowodem O2)
Powód: 0 rozbieżności + trend ✗ P-FV-2 ma DWIE lektury — (i) lustro trywialnie wierne, (ii)
różnicówka ślepa na klasę błędów, które miałaby łapać. Rozstrzyga wyłącznie test negatywny mocy
przyrządu (precedensy: TEST NEGATYWNY certs_selfcheck z 07.08 potwierdził wykrywanie rozjazdu; bug
truthy habitat_gate przeżył dokładnie przez brak takiego testu).

Procedura: katalog MUTANTÓW lustra per funkcja, cztery klasy: (i) `<` ↔ `<=` na każdym progu,
(ii) ±1 na stałych całkowitych/licznikach, (iii) negacja pojedynczego warunku, (iv) zamiana
kolejności dwóch gałęzi. Lista mutacji WYPISANA i commitowana PRZED pierwszym biegiem. Każdy mutant
przez ISTNIEJĄCĄ siatkę + fuzz (te same ziarna i liczności co S1). **Kryterium: 100% mutantów
wykrytych.** Mutant przeżywa ⇒ luka POKRYCIA przyrządu: stara siatka NIETYKALNA, punkty domykające
do `fv_diff_grid2.json` (nowy plik, commit przed ponownym biegiem), iteracje raportowane. Wynik S1
(0 rozbieżności) pozostaje ważny niezależnie — M mierzy przyrząd, kryterium §5 PRE nietknięte.
Uwaga oczekiwana a priori: mutanty brzegowe (< ↔ <=) są wykrywalne tylko punktami DOKŁADNIE na
progu — jeśli siatka S1 ma wyłącznie punkty ±ε, M pokaże właśnie tę lukę i grid2 będzie legalną
ścieżką, nie porażką.

## §6. Predykcje
Statusy P-FV-1 (trend ✓) i P-FV-2 (trend ✗) odnotowane; rozliczenie wyłącznie przy RAPORT_FV
(ANEKS_FV-0 §3). Prerejestracja do M: **P-FV-4** = wszystkie mutanty wykryte bez potrzeby grid2 —
p ≈ 0.5 (napięcie z uwagą brzegową §5 jest zamierzone; dane rozstrzygną).

## §7. Numeracja i push
Akceptacja raportu S2 wróci jako **ANEKS_FV-1a** (go na S3; precedens sub-numeru ANEKS_BENCH-1a);
**ANEKS_FV-2** pozostaje zarezerwowany na werdykt + kanon przy STOP-FV2 (PRE §6). Push trzech
commitów S1 (df58922, 729a44c, dde0a7e) = Olga.
