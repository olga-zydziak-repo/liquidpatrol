# STOP-NAD3R — recon NADIR-III przy biurku: kierunek **żyje** (Ś1–Ś4 nie zachodzą); rachunek CC odtworzony do 0.022 m, ale ma trzy dziury: zrealizowane τ ≠ (K+1)/f + 0.05, błąd źródła liczy się drugi raz w dostępności, a świeże G z NAD2 przekracza tabelę od τ = 0.85 s

13.11.2026 · wykonawca · PROMPT_NAD3_S0 (sha256 51d1c6b5 PASS, z wklejki). **0 bootów.** Bramka §0: origin = HEAD = `4f026892`,
porcelain czysty poza zastanymi ?? `results/DEMO_C`, blok NADIR-II „lot długi rozliczony” w KSIĘDZE i dopisek CO-NAD2-4
w KIERUNKACH obecne, blok §4 dopisany osobnym commitem `2c1b6ed1` [S0-KSIEGA] (append-only, przed pierwszym wynikiem).
Nietknięte: wagi, EKF/PX4, kanon percepcji, `r01/shield.py`, `harness/nadir_fix.py`, `freeze_U.json`, manifest v2 — diff 0
poza `results/NAD3_RECON/`. Żadna liczba poniżej nie jest zamrożeniem.

**Werdykt: żyje.**
- **Ś1 nie zachodzi:** wierność 100% na 13/13 lotach (21 993 datagramy producenta, 41 854 ticki utraty).
- **Ś2 nie zachodzi:** jest droga przez manifest (intruz bliżej środka) bez dotykania wag i kanonu percepcji.
  - Jest niezmierzona: z r_max ≤ 20 m leci dziś jeden lot, c05_s01, 19.6 m.
- **Ś3 nie zachodzi na powierzchni bezpieczeństwa:** f = 1 Hz, K = 1 daje E_max ≥ 1 m przy r ≤ ≈ 20.98 m (G z tabeli) albo
  r ≤ 20.2 m (G świeże z NAD2).
  - Na powierzchni dostępności przy biasie na zewnątrz ten sam punkt ma E_max 0.99 m przy r = 20. Tu Ś3 byłoby na włos.
- **Ś4 nie zachodzi:** 0 ticków e′ > U′ we wszystkich 2 080 przebiegach replayu R4 i 429 przebiegach R7.
  - Max e′/U′ wynosi 0.67 w wariancie (a) i 0.87 w (b).

## R1 — rachunek wymagań (`nad3_r1.py` ⇒ `r1_wymagania.json`; uzupełnienie `nad3_r7.py` ⇒ `r7_kandydaci.json:powierzchnia_tau_proj`)

**Reguła.** m(r) = R_E − d_stop − r. Wykonalne ⇔ u′(τ_max) ≤ m.
- (a) F_max = (m − Δ_D5)/1.5 − G, E_max = F_max − F_zn.
- (b) E_max = m − Δ_D5 − 1.5·(F_zn + G).
- F_zn najgorsze z `freeze_U.json`: jeden 0.4527, para 0.2577.
- Powierzchnia: r 14…27 × f {4, 2, 1, 0.5} × K {0…3}, dwie wersje wyboru przedziału — „cc” (τ) i „osłona” (τ + 0.012 s).

**Porównanie z §1 promptu (wariant a, wersja cc):**

| punkt | CC | odtworzone | Δ | przedział (cc / osłona) | F_max wersją osłony |
|---|---|---|---|---|---|
| r 20, 1 Hz K0 | 3.0 | 3.020 | +0.020 | 4 / **5** | **2.318** |
| r 20, 1 Hz K1 | 2.1 | 2.106 | +0.006 | 6 / 6 | 2.106 |
| r 20, 4 Hz K0 | 4.0 | 4.012 | +0.012 | 1 / 1 | 4.012 |
| r 22, 1 Hz K0 | 1.7 | 1.687 | −0.013 | 4 / **5** | **0.985** |
| r 22, 4 Hz K0 | 2.7 | 2.679 | −0.022 | 1 / 1 | 2.679 |
| r 24, 4 Hz K0 | 1.35 | 1.345 | −0.005 | 1 / 1 | 1.345 |
| r 24, 1 Hz K1 | niewykonalne | −0.561 | — | 6 / 6 | −0.561 |
| r 26, 4 Hz K0 | ≈ 0 | 0.012 | +0.012 | 1 / 1 | 0.012 (E po F_zn: −0.25…−0.44) |

Wszystkie różnice wersji cc są ≤ 0.05 m. Liczby CC odtwarzają się co do litery. Dziury rachunku:

1. **D1 — przedział przy 1 Hz.** τ = 1.05 leży na krawędzi. Osłona dobiera przedział z τ + 0.012 s
   (`r03/nadir_shield.py:74-80`), więc 1 Hz bez zgubień wpada w (1.05, 2] z G = 2.766.
   - F_max spada o 0.70 m (r 20: 3.02 → 2.32; r 22: 1.69 → 0.99).
   - Dzisiejszy REFUSE(τ*) przy τ ≥ 0.95 s (:190) wyklucza 1 Hz w ogóle (R6).
2. **D2 — τ zrealizowane ≠ (K+1)/f + 0.05.** Klatka bazowa nadir ma 5 Hz (przerwa 0.2 s w 1 487/1 488 klatek c10_s01).
   Przerwa przy f zaokrągla się w górę do wielokrotności 0.2 s. Do tego dochodzi opóźnienie dostarczenia ≤ 0.03 s.
   Max τ w misji przy E = 0 na 13 lotach (`r4_replay.json:_tau_proj`):

   | (f, K) | τ CC | τ zrealizowane |
   |---|---|---|
   | (4, 0) | 0.30 | **0.428** |
   | (2, 0) | 0.55 | **0.628** |
   | (1, 0) | 1.05 | 1.028 |
   | (1, 1) | 2.05 | 2.028 |
   | (4, 1) | 0.55 | 0.808 |

   - Przy 4 Hz przedział zostaje ten sam (0.428 + 0.012 = 0.440 ≤ 0.45). Zapas do krawędzi wynosi 10 ms, a 1 Hz ma 10 ms do 1.05.
   - To ta sama kruchość co pytanie 3 PRE_NAD2: jedna spóźniona klatka zmienia przedział.
3. **D3 — dostępność liczy E drugi raz.** Reguła R1 gwarantuje przesłankę bezpieczeństwa.
   - Bias źródła na zewnątrz przesuwa r_est o E, więc komórka jest dostępna dopiero przy u′ + E ≤ m.
   - Granica dostępności (a): E_d = (m − Δ_D5 − 1.5·(F_zn + G))/2.5. Wariant (b) ma mianownik 2.
   - Replay to potwierdza: przy 4 Hz bias na zewnątrz daje REFUSE w 8/13 lotów już 0.5 m **pod** granicą bezpieczeństwa i w 2/13 na
     granicy dostępności. Te 2 to loty niewykonalne przy własnym promieniu.
4. **D4 — G tabeli nie ogranicza świeżych danych.** Tabela (`r5_tabela.json`) to G_kum z 12 cięć NADIR S4. Odtworzyłem ją co do
   bitu (max |Δ| = 0). Te same okna na 13 lotach NAD2 (EKF bez poprawek — rama B+ nie karmi estymatora):

   | krawędź τ [s] | 0.25 | 0.45 | 0.65 | 0.85 | 1.05 | 2 | 3 | 5 | 10 | 22 |
   |---|---|---|---|---|---|---|---|---|---|---|
   | tabela | 0.625 | 1.072 | 1.458 | 1.789 | 2.064 | 2.766 | 2.978 | 3.721 | 4.847 | 5.514 |
   | NAD2 12 cięć | 0.576 | 1.024 | 1.440 | **1.823** | **2.144** | **3.033** | **3.185** | 3.729 | 4.742 | **6.173** |
   | NAD2 lot długi | 0.584 | 1.014 | 1.449 | **1.872** | **2.216** | **3.200** | **3.525** | **4.558** | **6.456** | **7.271** |

   - Od 0.85 s świeże G przekracza tabelę o 0.03–0.55 m w (0.85, 3] i do 1.76 m przy 22 s (lot długi).
   - Przesłanka NAD2 trzymała (max e/U 0.41) dzięki zapasowi 1.5. To nie erratum NAD2, ale tabela nie jest górnym ograniczeniem
     przy τ ≥ 0.85 s.
5. **Pochodzenie G przy τ > 1.05 s** (`r1_wymagania.json:G_pochodzenie_NADIR_S4`):
   - Do 2 s każde maksimum pochodzi z **jednego lotu** (NADIR S4 c08_s01; τ′ = krawędź). Potem kolejno c10_s01, c11_s02, c10_s02,
     c10_s01, c08_s01; 2–7 lotów ≥ 0.9·G.
   - Okna rozłączne n = Σ⌊110 s / τ⌋: 659 przy 2 s, 432 przy 3 s, 263 przy 5 s, 131 przy 10 s.
   - **Pola o małym n: τ > 12 s (n = 96 → 59 przy 22 s).** G jest tam płaskie (5.022 od 11 do 16 s z jednego okna c10_s01 τ′ = 10.84).

**Powierzchnia przy τ zrealizowanym** (wariant a, F_zn 0.4527; E_s bezpieczeństwo / E_d dostępność / E_s ze świeżym G):

| r | 4 Hz K0 | 2 Hz K0 | 1 Hz K0 | 1 Hz K1 |
|---|---|---|---|---|
| 18 | 4.89 / 2.94 / 4.94 | 4.51 / 2.70 / 4.51 | 3.90 / 2.34 / 3.75 | 2.99 / 1.79 / 2.44 |
| 20 | 3.56 / 2.13 / 3.61 | 3.17 / 1.90 / 3.18 | 2.57 / 1.54 / 2.42 | 1.65 / 0.99 / 1.11 |
| 22 | 2.23 / 1.33 / 2.27 | 1.84 / 1.10 / 1.85 | 1.23 / 0.74 / 1.08 | 0.32 / 0.19 / −0.23 |
| 24 | 0.89 / 0.54 / 0.94 | 0.51 / 0.30 / 0.52 | −0.10 / −0.06 / −0.25 | −1.01 / −0.61 / −1.56 |

Przy 1 Hz K0 τ zrealizowane (1.028) mieści się w przedziale 4. Wymaga to jednak τ* jako parametru (R6), nie dzisiejszej reguły.

## R2 — promień zadania (`nad3_r2.py` ⇒ `r2_promien.json`)

**r_max faktyczny** = max r_GT w tickach misji po fladze (kanon B2):

| lot | r_max misja | orbit przed / po fladze | intruz max | r_max r4_margin |
|---|---|---|---|---|
| c01_s01 | 23.13 | 23.46 / 23.13 | 15.0 (stoi) | 23.38 |
| c01_s03 | 23.14 | 23.38 / 23.14 | 15.0 | 23.05 |
| c02_s01 | 23.04 | 23.34 / 23.04 | 15.0 | 23.36 |
| c02_s03 | 23.07 | 23.32 / 23.07 | 15.0 | 23.38 |
| **c05_s01** | **19.59** | 15.74 / 19.59 | 15.0 | 18.82 |
| c05_s02 | 23.08 | 14.01 / 23.08 | 17.2 | 24.70 |
| c08_s01 | **25.57** | 23.00 / 25.57 | 18.0 | 23.98 |
| c08_s02 | 21.71 | 22.59 / 21.71 | 18.0 | 26.16 |
| c10_s01 | 23.79 | 12.33 / 23.79 | 18.0 | **20.77** |
| c10_s02 | 24.61 | 20.67 / 24.61 | 17.8 | 23.98 |
| c11_s01 | 25.37 | 23.24 / 25.37 | 18.0 | 22.68 |
| c11_s02 | 23.43 | 16.08 / 23.43 | 18.0 | 26.13 |
| L_c10_s01 | 24.37 (per 100 s w JSON) | 13.15 / 24.37 | 18.0 | 20.77 |

- **r_max > 20 m: 11 z 12 cięć; > 22 m: 10 z 12; > 24 m: 3 z 12.** Faza: zawsze orbita. approach i hold < 21.6 m, zejście
  ≤ 23.11 m.
- `r4_margin` (`results/KONT_RECON/tools/kont_r4_margin.py`, faza orbity starszych kampanii, n_ep 1–3) myli się o −4.45…+3.02 m
  wobec lotów NAD2 (c08_s02 21.71 vs 26.16; c10_s01 23.79 vs 20.77). Na przykład c10_s01 20.77 vs 23.79. **Wybór komórek z tej tabeli nie gwarantuje promienia.**

**Skąd promień (kod):**
- Generator `bench/scenarios.py:18-24`: RANGE0 = 15 m (start intruza), DISK_R = 18 m. `:53-56` przy r > 14 m kurs ku środkowi.
  Komórki c00–c03 stoją, c04–c07 0.5 m/s, c08–c11 1.0 m/s.
- Bramka S3: manifest `results/NADIR/s4/scenario_manifest_s4.json` (`nad2_s3_run.py:50-56`). Lot długi: wahadło
  `nad2_s4_manifest.py:44-67`.
- Sieć widzi tylko rel = trk − own_net, prędkość własną, wiek i ważność tracku (`bench/features.py:29-32`). Nie ma wejścia
  promienia ani pozycji bezwzględnej.
- Promień drona ≈ promień intruza + orbita nauczyciela r_orb = 8 m (`r03/controllers/orbit_executor.py:80,98-100`; pasmo 6–10).
  Dane się zgadzają: intruz stoi na 15 m ⇒ 23.0–23.1 m; intruz do 18 m ⇒ 21.7–25.6 m.
- Jedyne radialne cięcie to R-G-NOM przy r_est > R_NOM = 27.30 (`r03/kont_shield.py:43,201-205`). Nie działa poniżej 27.3 m.
  R_ROUTE_P 19.90 (`r03/config.py:25`) dotyczy tylko trasy kwadratowej R0.3.

**Drogi do r ≤ 20 / 22 m bez wag i kanonu percepcji:**
1. **Intruz bliżej środka.** RANGE0 i DISK_R oraz próg zawracania 14 m w generatorze, potem regeneracja manifestu narzędziem
   `nadir_s4_manifest.py` / `nad2_s4_manifest.py`.
   - Szacunek z danych: intruz ≤ 12 m ⇒ r ≤ ~20 m; ≤ 14 m ⇒ ≤ ~22 m.
   - Manifest zmienia `start_pos` i `segments[].x0/y0`, a nagłówek `range0_m` / `disk_r_m`.
   - Trening (`net/d0_dataset.py`, 114 demo egzekutora orbity, ten sam generator z EP_DUR 110 s): intruzi ruchomi przechodzili przez
     promienie 0–18 m, więc rel tego rozkładu sieć widziała. **Intruz stojący widziała tylko na 15 m.** Stojący na 12 m to rozkład
     nowy co do absolutu. Wejścia są względne, więc dla sieci wygląda tak samo — wniosek, nie pomiar.
   - Droga wymaga pomiaru r_max w nominałach (R7).
2. **Wybór komórek.** Ze zmierzonych: c05_s01 (19.6) przy r ≤ 20; c08_s02 (21.7) i c05_s01 przy r ≤ 22.
   - Z `r4_margin` dochodzą kandydaci c10_s04 14.75, c05_s03 16.04, c07_s03 17.6, a przy ≤ 22 dziewięć komórek 20.0–21.8. Ta tabela
     jest jednak zawodna (wyżej).
   - Manifest bez zmian generatora. To ten sam rozkład treningowy.
3. **Inne:** zmniejszenie `r_orb_m` / `band_hi_m` w `bench/executor_params.json` nie działa na sieć (ignoruje je).
   Zaostrzenie R_NOM to zmiana zamrożonego kodu osłony. **Odrzucone.**

## R3 — miejsce i model degradacji (`nad3_degrad.py`)

**Miejsce:** `harness/nadir_obs.py:142-143`, między `fx = _rama.obserwacja(...)` a `_send(fx)` ⇒ `_send(_deg.przetworz(fx))`.
- `nadir_fix.py` się nie zmienia.
- Producent (Δ wewnętrzne, bramka reszty < s/2 = 5 m, r_h, T1) liczy na poprawce czystej.
- **Oba gniazda konsumentów dostają ten sam stan zdegradowany:** driver i percep_proc (`nad2_boot.sh:112`;
  `harness/percep_proc.py:129-151` liczy track z p_corr).
- Wyłączony env `NAD3_DEGRAD` ⇒ `przetworz` zwraca ten sam obiekt. Replay sprawdza to asercją `o is fx` na 13 lotach.
- Rejestr: `row["fx"]` zostaje czyste, zdegradowane idzie do osobnego pola (projekt).
- Uwaga: to zmiana pliku producenta (`nadir_obs.py`), nie zakazanego `nadir_fix.py` — do potwierdzenia w PRE.

**Rodzina błędu (|E| ≤ E_max w NE, ziarno):**
- **bias_rad:** E = ±E_max·p̂_fix. „Do środka” to najgorszy przypadek dla przesłanki (prawda na zewnątrz estymaty). „Na zewnątrz” to
  najgorszy przypadek dla dostępności.
  - Prompt mówi „na zewnątrz strefy” — liczę oba kierunki.
- **biały:** jednostajny w kole, niezależny per dostarczona poprawka.
- **wolny:** 2D Ornstein–Uhlenbeck, T_c 2 s i 10 s, σ na oś = E_max/2, obcięty radialnie do koła.
- **Decymacja:** sztywna siatka slotów t₀ + n/f (średnio f; przerwa zaokrąglona w górę do 0.2 s).
- **Gubienie:** K kolejnych dostarczonych slotów, „okresowo” z fazą z ziarna albo „losowo” paczkami.
- Datagramy nieprzyjęte wychodzą ze stanem ostatnio dostarczonym (d_ne, t_fix; kosz/tryb z ostatniej dostarczonej).
- **Poza kontraktem (nazwane, niemodelowane):** skok poza E_max (fałszywe dopasowanie mapy).

## R4 — replay (`nad3_r4.py` ⇒ `r4_wiernosc.json`, `r4_replay.json`)

**Wierność — PASS 13/13:**
- **(A) Producent.** `Rama(litera NAD2)` na wierszach nf odtwarza zapisane fx w 100%: ok, tryb, ids, kosz, t_fix, max |Δd_ne|,
  |Δp_fix| = 0.0.
- **(B) Klient i bramka.** Działa i w passthrough, i z `{model: zero}` (E 0, pełna częstość, K 0). Emulacja RamaKlient po seq ticku i
  zatrzask `_nad2_barrier` (`r03/nadir_shield.py:174-193`, funkcje osłony importowane).
  - |Δd_ne| = 0, |Δτ| ≤ 1e-3 s, przedział 0 niezgodnych.
  - Zatrzask REFUSE w tym samym ticku co w zapisie w 13/13 (np. c10_s01 tick 2348, lot długi 12 244).
  - max e/U z replayu = raporty S3/S4 (c10_s02 0.374 … lot długi 0.4117).

**Degradacja.** Tabela U′ regułą R1 z krawędziami r5 do 22 s. τ*′ = τ_proj + 2·dt + 1 ms — parametr, nie krawędź (odchylenie 2).
Na każdy lot r = jego r_max misji. E_b z F_zn najgorszym. Punkty: pod / granica / nad (± 0.5 m) i „dost” (granica dostępności).
5 modeli × (f, K) ∈ {(4,0), (2,0), (1,0), (1,1)} × warianty a/b.

**Liczba lotów z REFUSE w misji / z e′ > U′, wariant (a), 13 lotów (12 cięć + lot długi):**

| (f, K) — wykonalnych przy r lotu | punkt | bias do środka | bias na zewnątrz | biały | wolny 2 s | wolny 10 s |
|---|---|---|---|---|---|---|
| 4 Hz K0 — 11 | pod | 1 / 0 | 8 / 0 | 3 / 0 | 2 / 0 | 3 / 0 |
| | dost | 1 / 0 | 2 / 0 | 2 / 0 | 1 / 0 | 1 / 0 |
| | granica | 1 / 0 | 12 / 0 | 9 / 0 | 9 / 0 | 8 / 0 |
| | **nad** | **2 / 0** | **13 / 0** | **13 / 0** | **12 / 0** | **13 / 0** |
| 2 Hz K0 — 11 | nad | 2 / 0 | 13 / 0 | 13 / 0 | 13 / 0 | 13 / 0 |
| 1 Hz K0 — 9 | pod | 5 / 0 | 7 / 0 | 6 / 0 | 6 / 0 | 5 / 0 |
| | nad | 7 / 0 | 13 / 0 | 13 / 0 | 13 / 0 | 13 / 0 |
| 1 Hz K1 — 2 | pod | 11 / 0 | 12 / 0 | 12 / 0 | 12 / 0 | 12 / 0 |

- Lotów niewykonalnych przy własnym r (E_b < 0, E = 0): przy 4 Hz c08_s01 (25.57) i c11_s01 (25.37). Przy 1 Hz K0 cztery. Przy
  1 Hz K1 wykonalne tylko c05_s01 i c08_s02.
- **Przekroczeń przesłanki: 0** w każdym punkcie, modelu i wariancie. max e′/U′ 0.67 (a) i 0.87 (b).
- Wszystkie REFUSE mają przyczynę „bariera”. REFUSE(τ*) = 0 przy τ*′ = τ_proj + 0.101.
- **Lot długi osobno** (r 24.37, 4 Hz, E_b 0.65): pod (E 0.15) 0 REFUSE i 0 przekroczeń we wszystkich modelach. Granica:
  REFUSE przy biasie na zewnątrz i obu wolnych. Nad (E 1.15): REFUSE we wszystkich poza biasem do środka.
  - 1 Hz przy r 24.4 jest niewykonalne (REFUSE już przy E = 0).

**Czego replay nie widzi (pętla otwarta):**
1. **Reakcja sieci na skok rel.** Track percepcji odświeża Δ dopiero z nową klatką, więc rel skacze o −ΔΔ na ≥ 1 tick
   (`harness/feed_vision.py:269-278` hold-last).
2. **Odrzucenie odświeżenia tracku przez bramkę predykcji.** Próg |Δ| > 6.0 m + 2 m/s·dt (`feed_vision.py:63`,
   sprawdzenie ~:217-221). Przy białym E = 3 m skok Δ sięga 5.9 m (R5).
3. **Przesunięcie toru drona przy biasie do środka.** Sieć leci w ramie p_corr, więc prawda ląduje E dalej na zewnątrz.
   - r_GT rośnie o E. Przesłanka i dowód to pokrywają, margines B2 nie.
   - Replay pokazuje dla tego modelu najmniej REFUSE właśnie dlatego, że tor się nie przesuwa.
4. **Ścieżka D5 po REFUSE** (replay jedzie dalej zapisem) i R-G-NOM przy r_est > 27.3.
5. **Sprzężenie producenta.** Degradacja za producentem ⇒ bramka reszty i T1 liczą na czystym Δ. Źródło mapowe tej separacji
   mieć nie będzie.

## R5 — skok nastawy (`nad3_r4.py` ⇒ `r5_skok.json`; `nad3_r5_trening.py` ⇒ `r5_trening.json`)

**Co skacze (kod).** Wyjście sieci to prędkość. `tgt = own_net + v·1.0` (`r03/controllers/net_controller.py:117-118`), więc
sp_EKF = own + v (`harness/nadir_fix.py:264-266`).
- **Nastawa w ramie EKF nie skacze o ΔΔ.**
- ΔΔ wchodzi do sieci przez rel = trk − own_net (`bench/features.py:29`; std rel ≈ 6.1 m) jako przejściowy błąd −ΔΔ do odświeżenia
  tracku (≈ 15 Hz).

**|ΔΔ| na dostarczoną poprawkę, okno bez GNSS** (p50 mediana lotów / p95 max po lotach / max):

| źródło | p50 | p95 | max |
|---|---|---|---|
| NAD2 naturalnie 5 Hz | 0.084 | 0.266 | **0.508** |
| NAD2 zdecymowane E 0, 4 Hz / 1 Hz | 0.097 / 0.384 | 0.321 / 1.213 | 0.919 / **2.040** |
| biały E 1 / 2 / 3, 4 Hz | 0.94 / 1.89 / 2.84 | 1.68 / 3.30 / 4.94 | 2.13 / 4.00 / 5.93 |
| biały E 1 / 2 / 3, 1 Hz | 0.89 / 1.61 / 2.42 | 1.95 / **3.37** / 4.92 | 2.48 / 4.16 / 5.83 |
| wolny 2 s E 2, 4 Hz / 1 Hz | 0.54 / 0.99 | 1.25 / 2.45 | 2.60 / 3.45 |
| wolny 10 s E 2, 4 Hz / 1 Hz | 0.26 / 0.61 | 0.64 / 1.44 | 1.59 / 2.57 |
| bias radialny E 2, 4 Hz / 1 Hz | 0.12 / 0.49 | 0.47 / 1.58 | 4.0 / 4.3 |

Max biasu ≈ 2E przy przejściu p_fix blisko środka (zmiana kierunku p̂).

**Trening.** Demo egzekutora orbity (BENCH, BLOCK1 + BLOCK2, 172 668 wierszy), |Δrel_xy| per tick:
- p50 0.13, p95 1.52, p99 2.02, p99.9 2.65 m;
- frakcja > 2 m: 1.1%, > 3 m: 0.07% (szum FeedB σ 0.5 m @ 10 Hz);
- max 31.2 m (przeskok tracku).
- Uwaga: w treningu skok rel to szum o średniej zero. Skok ramy to trwałe przesunięcie own_net, które track dogania po odświeżeniu.

**Zakres zmierzony przekroczony:**
- biały E 2 przy 1 Hz: p95 3.37 m > max NAD2 0.51 m i > p99.9 treningu 2.65 m;
- biały E 3 przy obu częstościach;
- biały E 2 przy 4 Hz (p95 3.30).
- W zakresie treningu (p95 ≤ ~2): wolny 10 s do E 3, wolny 2 s do E 2 przy 4 Hz, bias do E 2 (poza przejściem przez środek).
- Sama decymacja 1 Hz bez błędu daje max 2.04 m — powyżej naturalnego NAD2, w zakresie treningu.

**Warianty (bez wyboru):**
- **(i) Ograniczenie tempa zmiany Δ (|dΔ/dt| ≤ v_Δ).** p_corr goni źródło, więc do błędu dochodzi niezastosowana część skoku. Przesłanka
  wymaga w U′ członu max(|ΔΔ| − v_Δ·τ, 0) — przy 1 Hz naturalnie do 2 m. Bariera traci, sieć zyskuje.
- **(ii) Filtr Δ (średnia ważona / Kalman na Δ).** Błąd filtrowany ≤ E_max + G(okno najstarszej wagi). U′ potrzebuje G na
  dłuższym horyzoncie; zysk tylko dla błędu nieskorelowanego (biały).
- **(iii) Bez filtra, zwężenie kontraktu źródła do widma wolnego (T_c ≥ ~2 s).** Przesłanka bez zmian, wymaganie przenosi się
  na źródło.
- **(iv) Bez zmian i tylko pomiar** reakcji sieci w locie. Ryzyko: odrzucenia bramki predykcji przy |ΔΔ| > 6 m.

## R6 — τ* i odmowa (kod)

**Dziś** (`r03/nadir_shield.py:174-193`): w utracie τ = max(0, now − t_fix). Przy τ ≥ TAU_STAR_NAD2 − 2·dt = 0.95 s (`:190`)
**albo** gdy przedział jest None (τ + 0.012 > 1.05, `:74-80`) zapada REFUSE(POS_DEGRADED), przyczyna „τ*”.
- Zatrzask trzyma do NOMINAL. Akcja D5 + trzymanie yaw (reguła R-KONT, `r03/kont_shield.py`).
- Brak poprawki od wejścia ⇒ pole (jeden, 4) (`:66,182`).

**Miejsca z τ* = 1.05 / krawędzią 1.05 jako stałą:**
- osłona: `r03/nadir_shield.py:58-63` (KRAW_NAD2, G_NAD2, TAU_STAR_NAD2), `:92-102` (`nad2_tabela_check`: tau_star_ok, sha),
  `:190`;
- tabela: `results/NAD2/s1/freeze_U.json` (`tau_star_s`, sha256_tabeli wkompilowane `:57`) i generator
  `results/NAD2/tools/nad2_freeze.py:32,38,108`;
- driver echo: `results/NAD2/tools/nad2_flight.py:446`; analizator B4: `nad2_analyze.py:181` (`TAU_STAR_NAD2 − 2·0.05`
  na sztywno); testy: `test_nad2_s1.py:64`;
- **P9_nad2** (`r01/proofs/p9_nad2_verify.py`):
  - `:125-134` asercje `tau_star_eq_last_edge`, `thr_plus_eps_le_last_edge`, **`thr_ticks_integer_19`**;
  - `:130` `u_prim_le_m_p50_all_fields` (cała tabela pod m_p50 = 5.79);
  - lustro `:159` (thr).
- **P5_nad2:** siatka brzegów `:445-448` (τ* ± 1 ms przez C["thr"]) i fikstura S4.
- **P7_nad2:** `:644-647` (próg w tickach z τ*, asercja całkowitości) — graf monitora z thr = 19.
- **P1_nad2:** deleguje do `p9_nadir_verify.prove_p1` (`:634-635`) z abstrakcyjnym kviol. Liczby τ* nie niesie (odczyt, bez
  uruchomienia).

**Żeby τ* było parametrem tabeli:**
1. Krawędzie i G do τ* (r5 ma do 22 s).
2. τ* w `freeze_U.json` i w osłonie z tabeli, nie stała.
3. **Reguła wyboru τ* z m(r_zadania), nie z m_p50.** Przy m_p50 = 5.79 żaden przedział powyżej 1.05 s nie mieści się już
   z F_zn ≈ 0.2: (1.05, 2] daje u′ ≥ 1.5·(0.2 + 2.77) + 1.52 = 5.98. Dzisiejsza reguła PRE §3 oddaje więc 1.05 z powrotem dla każdego
   źródła — asercja `:130` musi zmienić odniesienie.
4. Próg całkowity w tickach: τ* − 0.1 = n·0.05. Dla 1 Hz K0 τ* = 1.15 (thr 21 ticków). **Dla 1 Hz K ≥ 1 τ* = 2.15 (thr 41), nie
   2.05** — τ zrealizowane wynosi 2.028, a zatrzask odpala przy τ* − 2·dt.
5. P7 graf z nowym thr, P5 siatka i fikstura, analizator `:181` z tabeli.

## R7 — kandydaci i pytania do PRE (`nad3_r7.py` ⇒ `r7_kandydaci.json`)

**Promień r = 20 m** (droga R2.1; zapisany lot w tym promieniu tylko c05_s01_r2 19.59). Replay: 5 modeli, losowe × 3 ziarna = 11
przebiegów na punkt.

| punkt | (f, K, E_max) | granice przy r = 20 (E_s / E_d; E_s świeże G) | c05_s01: REFUSE / przekroczenia | przewidywanie |
|---|---|---|---|---|
| **P1 zapas** | 4 Hz, 0, 1.0 m | 3.56 / 2.13; 3.61 | 0/11 / 0, max e′/U′ 0.46, zapas osłony ≥ 3.48 m | **PASS** (bezpieczeństwo i dostępność) |
| **P2 granica** | 1 Hz, 1, 1.0 m (τ* 2.15) | 1.65 / **0.99**; 1.11 | 1/11 (bias na zewnątrz, 11.6 s od flagi) / 0, max 0.45 | bezpieczeństwo PASS; dostępność na granicy |
| **P3 nad** | 1 Hz, 1, 2.0 m | 1.65 / 0.99; 1.11 | **10/11 REFUSE(bariera)**, 9.3–15.6 s od flagi / 0, max 0.53 | **odmowa osłony, nie naruszenie** |

- Bias do środka w P3: 0 REFUSE w pętli otwartej. W locie tor przesunie się o E na zewnątrz — R4 „czego nie widzi” pkt 3.
- Pozostałe 12 lotów (r 21.7–25.6) dają REFUSE w P2 i P3 we wszystkich, a w P1 w 11/12: zgodnie z r_lotu > r_zadania.

**Szkic litery:**
- **Bezpieczeństwo:** B1–B4 jak NAD2, B1 na U′, B3 r_est = |p_corr zdegradowane|. Sądzone w każdym punkcie, każde naruszenie =
  FAIL nogi. REFUSE w P3 jest oczekiwanym wynikiem i liczy się do B4 jako „zgodny z regułą”.
- **Dostępność osobno:** D1 jak NAD2 sądzona tylko w P1 (próg) i opisowo w P2. W P3 — liczba REFUSE(bariera) przed końcem misji jako
  przewidywanie, nie próg.
- **Rejestr:** fx czyste i zdegradowane, E per poprawka, ziarno w manifeście.

**Wycena bootów:**
- S1 budowa (degradacja w producencie, τ* z tabeli, certy P9/P5/P7) — 0;
- S2 smoke 2 (passthrough bitowy na żywo + punkt P1 jeden lot);
- geometria r ≤ 20: 2 nominały na nowym manifeście (pomiar r_max, jeszcze bez degradacji);
- S3: 3 punkty × 4 cięcia = 12, + 2 nominały, + rezerwa 3;
- **razem ≈ 21 (19–23).**
- Model w S3: jeden na punkt (pytanie 5), inaczej ×5.

**Pytania do PRE:**
1. **Geometria r ≤ 20:**
   - (A) nowy manifest, intruz ≤ 12 m (RANGE0 / DISK_R / próg zawracania);
   - (B) wybór komórek z listy r4_margin ≤ 20 m (c10_s04, c05_s03, c07_s03, c05_s01) — tabela zawodna o −4.5…+3.0 m.
2. **Składanie błędu:**
   - (a) U′ = 1.5·(F_zn + E + G);
   - (b) U′ = 1.5·(F_zn + G) + E — przy (b) E_max rośnie o ~40%, max e′/U′ 0.87.
3. **τ*:**
   - (A) parametr per zadanie z m(r) i próg całkowity w tickach (1.15 / 2.15 s);
   - (B) zostaje 1.05 — wtedy f = 1 Hz wypada, a noga mierzy tylko 4 / 2 Hz.
4. **G do FREEZE:**
   - (A) tabela r5 (NADIR S4) jak jest;
   - (B) G z unii NADIR S4 + 13 lotów NAD2 — świeże przekracza tabelę od 0.85 s, przy (2, 3] o 0.55 m.
5. **Model w lotach:**
   - (A) bias na zewnątrz (najgorszy dla dostępności, jeden przebieg na punkt);
   - (B) wolny 10 s (realistyczny dla dopasowania mapy, w zakresie treningu).
   - Bias do środka w obu tylko jako replay — w locie przesuwa tor.
6. **Granica w punkcie P2:**
   - (A) granica bezpieczeństwa E_s (dostępność sądzona opisowo);
   - (B) granica dostępności E_d (E liczone dwa razy) jako „granica” litery.
7. **Skok Δ (R5):**
   - (A) bez ograniczenia tempa, kontrakt źródła zwężony do E ≤ 2 m przy 4 Hz / wolnego;
   - (B) ograniczenie tempa zmiany Δ z członem w U′.
8. **Decymacja:**
   - (A) siatka na bazie 5 Hz (4 Hz = przerwy 0.2/0.4 s, τ 0.428);
   - (B) tylko f dzielące 5 Hz (5, 2.5, 1.25, 1) — znika kruchość 10 ms przy 4 Hz.
9. **Miejsce degradacji:**
   - (A) producent `nadir_obs.py:142-143` (oba konsumenty spójnie);
   - (B) tylko klient drivera — percepcja zostaje na czystym Δ, rel nie skacze. Mniej realistyczne, ale izoluje osłonę.

## Rozliczenie predykcji §4 (wpis należy do CC)

| predykcja | wynik |
|---|---|
| P-NAD3-R1 (0.85) R1(a) = §1 do 0.05 m | **✓** — max \|Δ\| 0.022 m w 8 punktach (wersja τ bez +0.012). Wersja osłony różni się przy 1 Hz K0 o 0.70 m (D1). |
| P-NAD3-R2 (0.70) ≥ 6/12 komórek r_max > 20 m | **✓** — 11/12 (10/12 > 22 m); r ≤ 20 tylko c05_s01. |
| P-NAD3-R3 (0.75) lot długi 0.5 m pod granicą, bias radialny ⇒ 0 ticków e′ > U′ | **✓** — 0 w obu kierunkach biasu (4 Hz, E 0.15 m; 0 REFUSE). Przy 1 Hz punkt niewykonalny przy r = 24.4 (E = 0, też 0 przekroczeń). |
| P-NAD3-R4 (0.65) 0.5 m nad granicą ⇒ REFUSE albo przekroczenie w ≥ 9/13 | **✗ jako całość.** Trzyma dla 4 z 5 modeli (12–13/13 przy 4 Hz, 13/13 przy 1 Hz). Pada dla biasu do środka (2/13 przy 4 Hz, 7/13 przy 1 Hz) — pętla otwarta. Granica nie jest też ostra od dołu: bias na zewnątrz daje REFUSE w 8/13 już 0.5 m pod (D3). Przekroczeń przesłanki 0 w każdym punkcie. |
| P-NAD3-R5 (0.70) biały, E 2, 1 Hz: p95 skoku > max krok NAD2 | **✓** — p95 3.37 m vs 0.51 m (5 Hz) i 2.04 m (NAD2 zdecymowane do 1 Hz); > p99.9 treningu 2.65 m. |
| P-NAD3-R6 (0.60) G dla τ ∈ (1.05, 3] z < 100 okien niezależnych | **✗ co do liczby:** 659 (2 s) i 432 (3 s) okien rozłącznych. Ale maksimum do 2 s pochodzi z jednego lotu, a świeże G NAD2 przekracza tabelę o 0.21–0.55 m w (1.05, 3] (D4). Wniosek „dosiać z logów NAD2 przed FREEZE” wynika z D4, nie z n. Pola n < 100: τ > 12 s. |

## Odchylenia od promptu (nazwane)

1. **τ_max.** Zamiast (K+1)/f + 0.05 replay i R7 używają τ zrealizowanego na siatce 5 Hz (`_tau_proj`). Powierzchnia R1 jest liczona
   formułą CC (obie wersje przedziału), a powierzchnia przy τ_proj osobno w `r7_kandydaci.json`.
2. **τ*′.** W replayu τ*′ = τ_proj + 0.101 s (parametr). Dzisiejsza reguła (τ* = krawędź, zatrzask przy τ* − 0.1) odcinała 2 Hz
   i 4 Hz przez REFUSE(τ*) — przebieg pierwszy, zastąpiony. Decymator miał pierwotnie tolerancję 0.1 s, która przy „4 Hz”
   przepuszczała każdą klatkę 5 Hz. Wymieniony na sztywną siatkę przed wynikami R4/R5.
3. **Bias radialny w dwóch kierunkach** (prompt: „na zewnątrz strefy … najgorszy dla bariery” — dla przesłanki najgorszy jest
   do środka, dla dostępności na zewnątrz).
4. **Dodany punkt „dost”** (granica dostępności, D3) obok pod / granica / nad.
5. **Granice per lot** liczone dla r = r_max faktycznego tego lotu i F_zn najgorszego (jeden 0.4527). U′ w replayu ma koszyk i
   tryb faktyczne. Lot długi liczony osobno (tabele R4).
6. **G w R1 i R4 = tabela r5 (NADIR S4).** Świeże G NAD2 tylko obok (D4), nie podstawione.
7. **„Decyzje bramki” w wierności** = przedział, τ, R, zatrzask REFUSE per tick (nakładka NAD2). Reguły PatrolShield poza
   barierą nie zależą od Δ inaczej niż przez pozycję i nie były odtwarzane.
8. **Ziarna:** R4 jedno (1), R7 trzy (1–3) dla modeli losowych.
9. **Kod R2 i R5 (generator, sieć, trening) czytał agent pomocniczy.** Linie kluczowe sprawdziłem sam: `bench/scenarios.py:18-24,53-56`,
   `r03/kont_shield.py:43,201-205`, `nad2_s3_run.py:50-56`, `bench/features.py:29-32`, `net_controller.py:109-118`,
   `feed_vision.py:63`, `percep_proc.py:129-151`.
10. **Pamięć podręczna loadera** (pickle) jest w scratchpadzie sesji, poza repo.

## Reprodukcja

```
export PYTHONDONTWRITEBYTECODE=1
python3 results/NAD3_RECON/tools/nad3_dane.py          # 13 lotów → pickle (NAD3_CACHE)
python3 results/NAD3_RECON/tools/nad3_r1.py            # r1_wymagania.json (G r5 odtworzone, świeże G NAD2)
python3 results/NAD3_RECON/tools/nad3_r2.py            # r2_promien.json
python3 results/NAD3_RECON/tools/nad3_r4.py            # wierność (STOP przy braku) → r4_replay.json, r5_skok.json (~45 s)
python3 results/NAD3_RECON/tools/nad3_r5_trening.py    # r5_trening.json
python3 results/NAD3_RECON/tools/nad3_r7.py            # r7_kandydaci.json
```

**Sygnał: STOP-NAD3R.** Push robi Olga. CC weryfikuje z repo własnym kodem i oddaje PRE_NAD3 do ratyfikacji.
