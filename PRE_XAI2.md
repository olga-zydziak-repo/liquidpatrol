# PRE_XAI2 — prerejestracja nogi XAI-II: mechanizm pierścienia (H-echo vs H-gen) + prawo pościgu sformułowane poprawnie (0 bootów)

CC · 28.10.2026 · po ERRATUM_XAI-1 (commit erraty wymagany przed S1).
Zamyka pozycje katalogu XAI-FLOQUET (T3′) i XAI-ZNAK (T4′). Wymaga
ratyfikacji Olgi; po niej PROMPT_XAI2_S1 — na start DWA dokumenty.

## §1. Obiekt, wielkości, korpus (FROZEN)

- Sieć: `net/frozen/ncp.npz` **0337d5ea** (kopią), krok CfC models.py:127-138.
  Wejście literą `bench/features.py` **9adc1505**: x₀ rel_n, x₁ rel_e,
  x₂ rel_d, x₃ own_vn, x₄ own_ve, x₅ own_vd, x₆ age (clip AGE_CAP), x₇ valid;
  normalizacja input_mean/std z npz. Wyjście y = (v_n, v_e, v_d) z głowy
  (przed clip_v).
- **Asercja mapowania (warunek wejścia S1, lekcja ERRATUM §4):** S1 wypisuje
  indeks → nazwa → (mean, std) z npz i sprawdza std[0] ≈ 6.10, std[1] ≈ 6.03
  (rel_n, rel_e), std[2] ≈ 0.503 (rel_d). Rozjazd ⇒ STOP.
- Wielkości T4′ liczone z wartości SUROWYCH (odnormalizowanych):
  r_h = (rel_n, rel_e), d = |r_h|, r̂ = r_h/d, t̂ = (−r̂_e, r̂_n);
  v_h = (y₀, y₁); **v_rad = v_h·r̂** (> 0 = zbliża się), **v_tan = v_h·t̂**.
  Znaki v_rad i v_tan są te same przed i po clip_v (skalowanie dodatnie).
- Korpus jak w S1 nogi XAI: 53 epizody / 74 708 ticków inferencji (indeks
  erratum_sweep + FANTOM r1_V2 + DEMO_C d1_proba), xai_replay **ac9551ab**
  importem; semantyka stanu literą replayu — stan zmienia się wyłącznie na
  tickach inferencji.

## §2. Lista testów i twierdzeń ZAMKNIĘTA

**T3′ — mechanizm pierścienia (para hipotez z ERRATUM §1):**

- (a) **ZAPOMINANIE:** dla każdego epizodu N = 32 losowe h₀ ~ U(−0.99, 0.99)²⁰
  (ziarno 0) plus referencja h₀ = 0; replay na zalogowanych wejściach (bez
  pętli). D_t = max po h₀ ‖h_t − h_t^ref‖₂. Para (epizod, h₀) ZBIEŻNA ⇔
  D < 10⁻⁶ na końcu epizodu. Raport: frakcja par zbieżnych, rozkład czasu
  zbieżności τ (sekundy czasu symulacji), max |Δy| po τ. Wersja lokalna:
  największy warunkowy wykładnik Lapunowa λ₁ metodą QR, per epizod i per faza.
- (b) **AUTONOMIA:** K = 200 zamrożonych wejść x* losowanych (ziarno 1)
  z ticków orbity korpusu plus 50 z podejścia (kontrola); dla każdego
  M = 5000 iteracji z 10 startów (0, h z logu, 8 losowych). Klasy: PUNKT STAŁY
  jedyny (‖h_{k+1} − h_k‖∞ < 10⁻¹⁰ i wszystkie starty w tym samym punkcie
  ±10⁻⁶), WIELOSTABILNY (punkty różne o > 10⁻³), OKRESOWY (brak punktu; nawrót
  min po p ≤ 500 z ‖h_M − h_{M−p}‖ < 10⁻⁸ ⇒ okres p), INNY. Przy punktach
  stałych promień spektralny ∂f/∂h.
- **Werdykt (prereg):** H-ECHO ⇔ (a) ≥ 95% par zbieżnych ∧ (b) ≥ 95%
  orbitalnych x* z jedynym punktem stałym; H-GEN ⇔ (b) ≥ 50% orbitalnych x*
  okresowych; w pozostałych przypadkach MIESZANY z liczbami klas. Każdy z trzech
  werdyktów jest WYNIKIEM.

**T4′ — prawo pościgu od nowa (ERRATUM §5):**

- **T4a (daleko ⇒ zbliża się):** d ≥ 12 m ⇒ v_rad > 0.
- **T4b (blisko ⇒ nie zbliża się):** d ≤ 4 m ⇒ v_rad < 0.
  Progi = pasmo D6 6–10 m z marginesem 2 m, zamrożone przed pomiarem.
- **T4c (kierunek orbity, OPISOWO):** w paśmie 6–10 m znak v_tan per epizod;
  frakcja epizodów ze stałym kierunkiem; zestawienie z kierunkiem nauczyciela,
  który losuje CW/CCW z ziarna (bench/scenarios.py:70), a sieć nie ma takiego
  wejścia — czyli sieć wybiera kierunek sama.
- Reżim jak w nodze XAI: najpierw różnicówka na wszystkich tickach korpusu
  w dziedzinie; kontrprzykład ⇒ COUNTEREXAMPLE z przykładem i czasem od startu
  tracku. Przy n < 30 tickach w dziedzinie ⇒ NIEROZSTRZYGALNE na korpusie. Po
  przejściu różnicówki dowód arytmetyką przedziałową (xai_proofs importem albo
  nowym plikiem): na ε-rurach wokół ticków dziedziny (ε_x = 0.02 w jednostkach
  znormalizowanych, ε_h = 0.01) → % ticków certyfikowanych; dodatkowo próba
  globalna na pudełku dziedziny (d w dziedzinie, kierunek w sektorach, reszta
  wejść p1–p99, h ∈ Box_h) z budżetem 20k komórek → % objętości. Statusy:
  PROVED (ε-rury 100%) / PARTIAL(x%) / COUNTEREXAMPLE / NIEROZSTRZYGALNE.

**Czułość (reżim FV):** mutanty wyłącznie w pamięci. M6_odwrócenie (Wo, bo →
−Wo, −bo) MUSI obalić każde T4a/T4b, które przeszło. M7_rekurencja (wiersze
stanu w Wb × k, k ∈ {2, 3, 5}) — raport werdyktu T3′ per k. M1–M5 z S1 obok.

## §3. Śmierć, zamknięcie, granice

- **ŚMIERĆ S1 (prereg) = niewiarygodne narzędzie:** (i) replay z h₀ = 0
  w nowym narzędziu różni się od xai_replay (max |Δy| > 10⁻¹²); (ii) asercja
  mapowania z §1 nie przechodzi; (iii) klasyfikator (b) myli się na kontrolach
  syntetycznych — obrót 2D o kąt 2π/50 MUSI dać OKRESOWY z p = 50, a
  kontrakcja h′ = 0.5h + c MUSI dać PUNKT STAŁY. Którekolwiek ⇒ STOP-ANEKS
  z diagnozą. Wszystkie statusy T3′/T4′ to WYNIKI, nie śmierć.
- **ZAMKNIĘCIE (prereg):** każdy werdykt zamyka obie pozycje (XAI-FLOQUET,
  XAI-ZNAK). Noga NIE otwiera nowych pozycji katalogu; wynik MIESZANY albo
  H-GEN zapisuje się jako nazwane pytanie we FREEZE_XAI2, nie jako pozycja.
- Granice: twierdzenia o SIECI na korpusie i pudełkach, nie o misji (zero
  roszczeń D6). Test (a) jest warunkowy na zalogowanych wejściach — inny h₀
  w prawdziwej pętli zmieniłby lot. Zamrożone wejście w (b) to sonda
  matematyczna, nie sytuacja z lotu.

## §4. Predykcje CC (do KSIĘGI)

- **P-XA2-1 (0.60):** werdykt T3′ = H-ECHO.
- **P-XA2-2 (0.55):** T4a — różnicówka 0 kontrprzykładów.
- **P-XA2-3 (0.60):** T4b — 0 kontrprzykładów przy n ≥ 30 (n < 30 ⇒ n.r.).
- **P-XA2-4 (0.50):** każde T4a/T4b po różnicówce certyfikowane przedziałowo
  na ≥ 80% ε-rur.

## §5. Budżet, higiena, cytowanie

Budżet nogi: **0 bootów; 1 sesja + CO.** Env `XAI2_*`, katalog
`results/XAI2/`, narzędzia wyłącznie nowe pliki (xai_replay, xai_thm_diff,
xai_proofs importem). NIETYKALNE: wagi i kod sieci, features, komplet FROZEN
programu, raporty wstecz (errata w przód). Cytowanie na zewnątrz zawsze ze
statusem: T4a/T4b z dziedziną i % certyfikacji, T3′ z werdyktem i liczbami
(a)/(b). Nakładka demo „32 starty zlewają się w jedną trajektorię" przy
H-ECHO — osobna decyzja, nieprekomitowana.

Ratyfikacja: „ratyfikuję". Sygnały bez numeru wykonawca odrzuca.
