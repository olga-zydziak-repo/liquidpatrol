# PRE_XAI — prerejestracja nogi XAI-SIECI, ścieżka (ii)+(i): atlas → twierdzenia klasy dowodowej (0 bootów)

CC · 27.10.2026 · po STOP-XAIR (61528b5e, zweryfikowany z repo: kotwica
przeliczona z rekordów per-epizod — p95 1.317e-3 / max 2.455e-3 / 0 rozjazdów
hold w 21 epizodach; PCA top2 87.8% z var_top5; lista przewagi 19 z literą
c_sweep 19/19; replayer czyta FROZEN wagi i wejścia demo.jsonl literą).
Wymaga ratyfikacji Olgi; po niej PROMPT_XAI_S1 — na start DWA dokumenty.

## §1. Teza i dźwignia (FROZEN)

Obiekt: zamrożona sieć NCP-20 (wagi 0337d5ea, modele importem) jako obiekt
matematyczny + atlas XAIR jako mapa pomiarowa. **Dźwignia: zamiana czterech
obserwacji atlasu w TWIERDZENIA, reżimem nogi FV (dowód + różnicówka +
mutanty). Lista twierdzeń ZAMKNIĘTA:**

- **T1 — ograniczoność wyjść:** |v_cmd| ≤ V_MAX dla KAŻDEGO wejścia
  (architektonicznie: tanh × V_MAX — litera models.py). Dowód strukturalny.
- **T2 — lemat stanu:** |h_i| < 1 dla wszystkich neuronów i wszystkich
  wejść (krok CfC jako wypukła kombinacja tanh — models.py:130-134).
  Dowód symboliczny.
- **T3 — twierdzenie warunkowe bramek (assumption-backed, jawnie):** przy
  g ∈ [pasmo zmierzone w orbicie ustalonej ± δ z pomiaru] zachodzi własność
  stabilności kroku stanu, którą S1 sformalizuje z równań (prereg wymogu:
  własność musi być falsyfikowalna różnicówką na korpusie; kandydat:
  kontrakcja/ograniczenie ||Δh||). Założenie przedziałowe POCHODZI Z POMIARU
  i jest tak podpisane — to nie jest dowód uniwersalny.
- **T4 — znak prawa pościgu interwałowo:** na zmierzonym pudełku wejść
  (percentyle korpusu replay, liczby w FREEZE) pochodna ∂v_n/∂sin_brg
  zachowuje znak — arytmetyka przedziałowa przez sieć; podział pudełka
  DOZWOLONY; wynik może być CZĘŚCIOWY (znak na X% pudełka) i tak raportowany.

**Reżim prawdy (FROZEN):** (1) każde twierdzenie NAJPIERW różnicówka
empiryczna na pełnym korpusie replay (wszystkie kampanie, ≥67k ticków;
kontrprzykład ⇒ twierdzenie odpada PRZED dowodem — wynik, nie wstyd);
(2) dowód skryptowalny, narzędzia nazwane w S1 (symbolika / SMT / arytmetyka
przedziałowa — wzór warsztatu FV); (3) **mutanty wag**: ≥3 mutacje (znak
losowej wagi / skala / zerowanie) — każdy dowód musi PAŚĆ na ≥1 mutancie,
inaczej dowodzi trywialność, nie własność. GRANICE UCZCIWOŚCI: twierdzenia
o SIECI, nie o misji (zero roszczeń D6); role/saliency z atlasu NIE wchodzą
do twierdzeń (korelacyjne); „pełna wyjaśnialność" nie jest tezą — tezą jest
ATLAS + CZTERY TWIERDZENIA z jawnym statusem każdego.

## §2. Sesja S1 — formalizacja, różnicówka, dowody, mutanty (0 bootów)

1. Formalizacja T1–T4 z litery kodu (stałe z wag KOPIĄ; zapis w raporcie).
2. Różnicówka: test każdego twierdzenia na korpusie replay (xai_replay
   importem — narzędzie z recon, FROZEN ac9551ab); liczby kontrprzykładów
   per twierdzenie (oczekiwane 0 dla T1/T2).
3. Dowody: T1/T2 symbolicznie; T3 po sformalizowaniu (wybór własności
   uzasadniony strukturą równań, zapisany PRZED dowodzeniem); T4 interwałowo
   z raportem pokrycia pudełka.
4. Mutanty: wyniki per dowód × mutant (tabela czułości).
5. **`results/XAI/FREEZE_XAI.md`:** statusy PROVED / PARTIAL(x%) /
   COUNTEREXAMPLE / NIE-SFORMALIZOWANE per twierdzenie, pudełka wejść
   liczbowo, pasmo bramek z δ, sha narzędzi.
6. **ŚMIERĆ S1 (prereg):** T1 lub T2 nie domyka się dowodem — to sygnał
   błędu formalizacji (architektura je gwarantuje), ⇒ STOP-ANEKS z diagnozą
   zamiast brnięcia. T3/T4 w statusie PARTIAL/NEGATIVE to WYNIKI, nie śmierć.
7. STOP-XAI1: commit (FREEZE_XAI + RAPORT_XAI_S1: formalizacje, różnicówki
   z liczbami, dowody/skrypty, tabela mutantów, diff-stat, porcelain).
   **Push = Olga.** Po weryfikacji CC (różnicówkę i ≥1 dowód przeliczę
   niezależnie): ANEKS_XAI-1 — werdykt, KSIĘGA, CO (nakładka demo „co myśli
   sieć" wyceniona w recon — osobna decyzja, nieprekomitowana).

## §3. Predykcje CC (wskaźniki do KSIĘGI)

- **P-XA-1 (0.85):** T1+T2 PROVED, różnicówka 0 kontrprzykładów.
- **P-XA-2 (0.55):** T4 — znak globalny na ≥80% zmierzonego pudełka
  (interwały przez tanh bywają luźne — cięcie za metodę).
- **P-XA-3 (0.60):** T3 — istnieje falsyfikowalna własność przechodząca
  różnicówkę i dowód warunkowy (forma nazwana-niezmierzona — cięcie).
- **P-XA-4 (0.80):** czułość: każdy dowód FAIL na ≥1 mutancie.

## §4. Budżet, higiena, nietykalne

**Budżet nogi: 0 bootów; 1 sesja + CO.** Env `XAI_*`, katalog
`results/XAI/`, narzędzia nowe pliki (replayer recon importem). NIETYKALNE:
wagi 0337d5ea i kod sieci (wyłącznie kopie/import), GRU 5ec02755, komplet
FROZEN programu, raporty wstecz (errata w przód). Twierdzenia cytowane na
zewnątrz ZAWSZE ze statusem i założeniami (T3 nigdy bez przedziału bramek).

Ratyfikacja: „ratyfikuję". Sygnały bez numeru wykonawca odrzuca.
