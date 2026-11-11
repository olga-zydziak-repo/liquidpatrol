# STOP-NAD2R — recon NADIR-II przy biurku: kierunek **żyje**; reguła wyboru wskazuje **C0 · A · (T1, Z2)** z 12/12 komórek dostępnych; opóźnienie klatki CC obalone; osłona S4 liczyła promień z EKF bez poprawki

11.11.2026 · wykonawca · PROMPT_NAD2_S0 (sha256 20bc43a2 PASS). **0 bootów**: żadnego uruchomienia gz / PX4 / kolejki.
Kod toru lotu, osłony i certów oraz dotychczasowe narzędzia nietknięte. Nowe narzędzia są w `results/NAD2_RECON/tools/`, wyniki
(JSON) w `results/NAD2_RECON/`, wyciągi ULG w `results/NAD2_RECON/ulg/`. Bramka §0 to commity `a5305026` [CO-N5] (ANEKS_NADIR-5,
sha256 286d2ac0 PASS) i `bca41179` (KSIĘGA §4 tego promptu).

## Werdykt §2

| | reguła A (1.5 × max) | reguła B (1.25 × max) |
|---|---|---|
| Z0 (T0 / T1, C0 / C1) | 9/12 — Ś1 i Ś2 (c08_s02, c10_s02, c11_s02 / c11_s01) | 11/12 — żywa (niedostępna c08_s02) |
| Z1 (T0 / T1, C0 / C1) | 10/12 — Ś2 (c10_s02) | 11/12 — żywa (c08_s02) |
| **Z2 (T0 / T1, C0 / C1)** | **12/12 — żywa** | 12/12 — żywa |

- **Kierunek nie umiera przy biurku.** Przy A żyją cztery pary (Z2 × T0/T1 × C0/C1), przy B wszystkie 12.
- **Reguła wyboru:**
  - oś czasu C0, bo mediana L = 0.004 s < 0.05;
  - zapas A, bo przy A istnieje para żywa;
  - wariant (T1, Z2), bo spośród maksimum 12/12 jest pierwszy w kolejności (T0, Z0), (T1, Z0), (T1, Z1), (T1, Z2).
- Para wskazana: **T1Z2C0 · A**. Ma 12/12 komórek dostępnych, 0 REFUSE w fazach misji, 0 ticków u′ > m. Sprawdzian S2:
  0 przekroczeń przesłanki na 1803 tickach, max e_corr′/U 0.23. Zapas na S4: max e_corr′/U = 0.398.
- Przejście reconu jest warunkiem koniecznym, nie dowodem; sądzi świeża bramka.

## R1 — łańcuch czasu (`nad2_r1.py` ⇒ `r1_czas.json`)

**Dopasowanie po wartości.** `vehicle_local_position` z ULG idzie z częstotliwością 125 Hz, a czas ULG = czas sim. p_ekf każdego
z 63 010 ticków misji 16 bootów dopasowuje się po wartości z resztą 0 (100% < 1e-3 m).
- Próbka ticku jest starsza od rama.sim o 8 ms (mediana; zakres −24…+12 ms). Konwencje `timestamp` i `timestamp_sample` dają
  ten sam wynik.
- **(b) Opóźnienie klatki** L = t_próbki EKF przy klatce − t_frame: **mediana 0.004 s, p95 0.016 s, n = 16 690**. Postawa
  daje to samo (mediana 0.004–0.008 s).

**Hipoteza CC obalona.** CC zakładał, że obserwator bierze EKF przy przybyciu klatki, a p_corr spóźnia się o ~0.09 s.
Obserwator rzeczywiście bierze migawkę przy przybyciu (`on_img`), ale klatka przychodzi 4 ms po ekspozycji. Opóźnienie jest
pomijalne. P-NAD2-R1 (0.07–0.14 s) — ✗.

**(c) e_corr** = |p_corr − GT(t próbki EKF)|:

| okno | n | p50 | p95 | p99 | max | max 3D |
|---|---|---|---|---|---|---|
| bez GNSS | 27 241 | 0.122 | 0.251 | 0.399 | **0.677 m** | 0.690 m |
| z GNSS (przed cięciem) | — | — | — | — | 0.402 m | — |
| nominały | — | — | — | — | 0.914 m | — |

- Składowa wzdłuż toru bez GNSS ma średnią +0.054 m; regresja na v daje −0.032 s (r = −0.16), czyli brak zależności od
  prędkości. W poprzek toru p50 0.088 m.
- **Rozstrzygnięcie parowania z ANEKS_NADIR-5 §1.5:** fizyczne jest parowanie z GT w chwili próbki EKF, max 0.677 m (zgodne
  z „GT z chwili ticku" CC, 0.67). Przesunięcie `gt_judge` 0.10–0.12 s nie ma oparcia w łańcuchu czasu; to artefakt skośności
  mono, nie opóźnienie.

**(d) Postawa.** Zmiana postawy między t_frame a próbką postawy wnosi h·tan(Δ) z p95 0.013–0.025 m na boot. Max 0.13–0.42 m
na boot (nom_b3 1.34 m) pochodzi z pojedynczych klatek niejednoznacznego dopasowania q w zawisie — opis, nie przesłanka.

## R2 — przyrost błędu EKF, składnik G (`nad2_r2.py` ⇒ `r2_przyrost.json`)

Okno przesuwne po wszystkich t, od flagi do zejścia, 12 cięć, siatka 0.01 s. Wartości poziome, łącznie:

| τ [s] | p50 | p99 | p99.9 | max |
|---|---|---|---|---|
| 0.25 | 0.100 | 0.322 | 0.460 | **0.625** |
| 0.45 | — | — | — | 1.072 |
| 0.65 | — | — | — | 1.458 |
| 0.85 | — | — | — | 1.789 |
| 1.05 | 0.406 | 1.199 | 1.687 | **2.064** |
| 2 | — | — | — | 2.766 |
| 5 | — | — | — | 3.721 |
| 10 | — | — | — | 4.847 |
| 22 | — | — | — | 5.025 |

- **G_kum** (maksimum bieżące, do R5): 0.625 / 1.072 / 1.458 / 1.789 / 2.064 / 2.766 / 2.978 … 5.514 m. 3D przy 0.25 s:
  0.625 m.
- Przy τ = 0.25 s 61 okien przekracza 0.8·max, a 34 przekracza 0.9·max.
- Zależność od przyspieszenia GT przy τ = 0.25 s: |a| < 1 m/s² max 0.39 m; 1–2 m/s² max 0.53 m; ≥ 2 m/s² max 0.63 m
  (p99 0.23 / 0.30 / 0.46 m).
- **Rozbieżność wobec CC:** CC liczył okna od poprawki do poprawki i miał 3D max 0.51 m przy 0.2 s. Okno przesuwne łapie
  szczyty zrywów, które okna od poprawki rozcinają. Do R5 wchodzi wartość przesuwna, więc G jest ostrożniejsze.

## R3 — błąd poprawki F i litera przyjęcia (`nad2_r3.py` ⇒ `r3_poprawka.json`, `r3_wiernosc.json`)

**Wierność: PASS.** Replay bieżącej litery (T0Z0C0) na 29 801 klatkach 16 bootów odtwarza zapisane fx w 100%: ok, tryb, ids,
koszyk, d_ne, |Δp_fix| ≤ 5e-5 m (zaokrąglenie zapisu).

Okno bez GNSS, błąd zakotwiczenia a (poziomo):

| wariant | para — max | jeden — max | klatki misji bez przyjętej obserwacji | okna bez poprawki |
|---|---|---|---|---|
| T0Z0C0 | 0.215 m | 0.511 m (koszyk 4–6 m); geometryczny 0.501 | 20 (CC: 20) | 26 okien ≥ 0.4 s, max 1.0 s |
| T1Z0C0 | — | 0.437 m (koszyk 6–8 m) | — | — |
| T1Z1C0 | 0.234 m | 0.189 m, ale tylko n = 38 | — | — |
| **T1Z2C0** | 0.258 m | 0.27 m, tylko n = 11 | **0** | **max 0.4 s (2 okna)** |

- **Nominały, jeden znacznik:** T0Z0 0.890 m (CC: 0.89); T1Z0 0.654 m; T1Z2 0.410 m.
- **Błędne ID wobec GT** (punkt gruntu przy pozie GT dalej niż s/2): **0** we wszystkich wariantach Z1/Z2. Przy Z2 sprawdzono
  10 785 obserwacji spoza bieżącej litery.
- C1 (poza w t_frame z ULG) zmienia F o setne części metra, zgodnie z R1.
- Czułość T1 na wiek pary (1 s / 5 s): w `r3_poprawka.json`.
- **P-NAD2-R5** (T1 sprowadza błąd jednego znacznika do ≤ 0.40 m w koszykach < 8 m) — ✗. Sam T1 przy Z0 daje bez GNSS 0.437 m,
  w nominałach 0.654 m. Poniżej 0.40 m wynik schodzi dopiero z Z1/Z2, gdzie tryb jeden prawie znika.

## R4 — zrywy przy hamowaniu (`nad2_r4.py` ⇒ `r4_zrywy.json`)

13 serii CC w pięciu bootach.

**W seriach:**
- błąd prędkości EKF wobec GT 0.61–1.08 m/s (baza bootów max 0.59–1.08);
- |a_GT| 1.9–3.9 m/s², |ω| 0.52–0.78 rad/s;
- **przepływ fuzjonowany w 100% próbek, zero odrzuconych innowacji, test_ratio ≤ 0.34**;
- prędkość z przepływu odbiega od GT o 2.1–3.7 m/s.

**Na całym oknie bez GNSS:**
- błąd prędkości z przepływu rośnie z prędkością kątową: r(ω, |v_przepływ − v_GT|) = 0.52;
- p99 wynosi 0.96 m/s przy ω < 0.2 rad/s i 2.68 m/s przy ω ≥ 0.5 rad/s.

**Predyktor (opisowo):** zryw zdefiniowany jako |Δe| > 0.4 m w 0.25 s.
- Przy ω ≥ 0.5 rad/s P(zryw) = 6.0% wobec 0.11% poza tym stanem (×27); warunek obejmuje 51% zrywów.
- Hamowanie obejmuje 98% zrywów (P = 0.44%).

**Mechanizm częściowo zmierzony.** Przy obrocie kadłuba (pochylenie przy hamowaniu) prędkość z przepływu jest zła, a bramka
innowacji jej nie odrzuca. Dlaczego kompensacja obrotu zawodzi, pozostaje [MECHANIZM NIEZMIERZONY] wewnątrz estymatora.
Parametry PX4 nietknięte.

## R5 — tabela kandydacka i replay osłony (`nad2_r5.py` ⇒ `r5_tabela.json`)

**Budowa obwiedni.** U = z·(F + G), u′ = U + Δ_D5 (z mnoży oba składniki). F i G pochodzą wyłącznie z okna bez GNSS 12 cięć S4.

**Replay ticków (27 241):**
- Poprawka wariantu jest dostępna w ticku po zegarze mono: przybycie klatki + detekcja + 5 ms.
- Kalibracja na zapisie T0Z0C0: 26 798 ticków zgodnych, 2 ticki, w których replay widzi poprawkę wcześniej niż rama w locie,
  441 ticków ostrożniejszych o jedną klatkę.
- Pierwsze podejście (t_frame ≤ sim) dawało ~10% ticków optymistycznych i zostało odrzucone; wynik R5 się nie zmienił.
- τ_prawdziwe − τ_osłony: mediana −0.012 s, max +0.008 s. Przedział wybiera większa z dwóch wartości.

**T1Z2C0 · A:**
- F: para 0.197 / 0.237 / 0.237 / 0.237 / 0.258 m (koszyki 0–4, monotonicznie).
- F jeden = 0.27 m. Wszystkie koszyki mają n < 100 i nie ma wyższego koszyka z n ≥ 100, więc F wzięto z puli trybu (n = 11).
  **To odstępstwo od litery „dziedziczy wyższy koszyk"**; koszyk 4 pary dziedziczy z puli z tego samego powodu (n = 19).
- u′(τ ≤ 0.25 s) = 2.76–2.87 m.
- **τ* = 1.05 s** dla wszystkich (koszyk, tryb): już przedział (1.05, 2] daje u′ = 6.04 > m_p50 5.79.
- W replayu wszystkie ticki leżą w przedziale [0, 0.25], τ max 0.232 s.

**Wyniki per komórka:**
- (ii) 12/12 komórek dostępnych: 0 REFUSE, 0 ticków u′ > m.
- Zapas bariery min 1.71 m (c11_s02) w wersji przesłanki.
- **(iii) τ dopuszczalne:** c08_s02 i c11_s02 0.25 s (1 klatka), c05_s02 0.65 s, m ≈ 5.2–5.8 1.05 s, c11_s01 3 s,
  c10_s01 6 s, c05_s01 22 s.
- **(iv)** Tabela statyczna 48 komórek: u′(τ ≤ 0.25) najgorszego (koszyk, tryb) = 2.867 m ≤ m we wszystkich 48 (min zapas
  0.123 m).
- **(v)** Sprawdzian S2 (4 cięcia, 1803 ticki): 0 przekroczeń e_corr′ ≤ U, max e_corr′/U 0.14–0.23. Zapas na S4: max e_corr′/U
  = 0.398 (c08_s01).

**Znalezisko R5/R6 (nazwane wprost).** Osłona w S4 dostawała od drivera `own` = p_EKF bez Δ (`nadir_s4_flight.py:600`)
i liczyła r_est = |p_EKF| (`r03/kont_shield.py:172`).
- Przesłanka P9_nadir zakłada |r_true − r_est| ≤ ε z ε = błąd pozycji poprawionej. Przy dryfie EKF do 8.5 m ta przesłanka
  nie trzyma niezależnie od tabeli.
- Fikstura P5_nadir sprawdza zgodność lustra z produkcją na tych samych wejściach, więc tego nie wykrywa.
- W replayu obie wersje dają tę samą dostępność dla T1Z2C0 · A. Zapas „lot" spada jednak do 0.39 m (c01_s01) wobec 3.11 m
  „przesłanka", a przy T0Z0C0 · A wersja „lot" ma o 1 komórkę dostępną mniej.
- Komórka dostępna rozstrzygana jest wersją przesłanki: r_est = |p_corr′|.

## R6 — wejścia do PRE

**Zmiany kodu (wycena w liniach):**

| plik | zmiana | linie |
|---|---|---|
| `harness/nadir_fix.py` | litera Z2 (bok ≥ 16 px, najbliższy r_h < 10 m, partner bez limitu, koszyk 4) i korekta T1 (δψ pary ≤ 2 s); datagram niesie tryb | ~40 |
| `nadir_obs.py` | bez zmian (C0) | 0 |
| `r03/nadir_shield.py` | tabela U(przedział τ, koszyk, tryb) zamiast ε_fix_freeze + ε_b(⌊τ⌋); przedziały poniżej sekundy; τ* = 1.05 s | ~50 |
| driver | **r_est = \|p_corr\| (pos = own_net) do osłony**; kontynuacja od t_inj_sim z nastawą 110.5 s; WALL_MAX_CUT_S | ~10 |
| analizator | kontynuacja od t_inj_sim; domknięcie ostatniego okna końcem epizodu; e_corr per tick (GT w chwili próbki EKF) i błąd poprawki w raporcie płaskim; litera: e_corr ≤ U per tick oraz a ≤ F per poprawka | ~80 |

**Certy:**
- **P9_nadir:** przesłanka ε = U(przedział, koszyk, tryb) zamiast ε_fix + ε_b(k), r_est z p_corr. Obligacje per
  (koszyk 0–4 × tryb × przedział 0–4): ~50 + ostrość.
- **P1_nadir:** kviol z nową tablicą i progiem τ*.
- **P7_nadir:** graf zegara z τ*/dt = 21 ticków.
- **P5_nadir:** nowa siatka i fikstura (S4 zamiast S2) oraz obligacja, że r_est = |p_corr|.
- Passthrough T0 bez zmian.

**Etapy:** S1 budowa i certy (0 bootów) → S2 smoke 1–2 booty (Z2 na żywo, datagram trybu, r_est z p_corr) → S3 świeża bramka
12 cięć + 4 nominały + 2–4 rezerwy = **18–22 booty**, zgodnie z szacunkiem CC.

**„Długi lot" 600 s (sama wycena):**
- około 650 s epizodu + 140 s przed nim ≈ 790 s sim, co przy tempie 0.96 daje ~14 min ściany + ~2 min startu na boot;
- ULG ~230 MB (poza repo), pozostałe logi ~65 MB na boot (S4: 16 MB na 160 s);
- WALL_MAX_CUT_S 300 → ≥ 900;
- stanowisko: 16 min bez aplikacji okienkowych na boot.

**Pytania do PRE:**
1. Poprawka r_est do osłony jest warunkiem ważności P9 — czy wchodzi jako naprawa bez głosowania?
2. F trybu jeden z puli n = 11 (Z2) — przyjąć, czy w Z2 wyłączyć poprawkę jednym znacznikiem (11 klatek misji, 0 dziur
   przy samej parze?) — do policzenia.
3. **Kruchość najwęższych komórek.** c08_s02 i c11_s02 mają τ dopuszczalne 0.25 s, czyli jedna zgubiona klatka daje u′ > m.
   W S4 τ max 0.232 s, zapas 18 ms. Świeża bramka może je tracić — dopuszczalne jak Ś2?
4. τ* = 1.05 s przy A: każda dziura ≥ 0.95 s daje REFUSE(τ*). W Z2 dziury max 0.4 s.
5. G z okna przesuwnego S4 obejmuje zrywy (R4) tylko w próbie S4 — zapas A pokrywa S2 z 0.23 U.
6. T1 przy Z2 dotyczy 11 klatek. Reguła wybrała (T1, Z2) remisem kolejności; (T0, Z2) jest równy liczbowo i prostszy.

## Rozbieżności wobec liczb CC

- **Opóźnienie klatki:** CC przyjmował ~0.09 s (P-NAD2-R1 0.07–0.14 s). Pomiar daje 0.004 s (p95 0.016 s).
- **Parowanie:** fizyczne jest GT w chwili próbki EKF, max e_corr 0.677 m. Wariant z przesunięciem 0.10–0.12 s (max 0.73 m)
  nie jest fizyczny.
- **Przyrost G:** okno przesuwne daje 0.625 m przy 0.25 s, a CC liczył 0.51 m przy 0.2 s od poprawki do poprawki.
- **Zgodne co do sztuki:** para max 0.215–0.225 m, jeden znacznik bez GNSS geometryczny 0.501 m, nominały 0.890 m, 20 klatek
  misji bez obserwacji.
- **Nowe:** r_est osłony z EKF bez Δ.

## Predykcje KSIĘGI (stan po reconie; wpis należy do CC)

| predykcja | wynik |
|---|---|
| P-NAD2-R1 (opóźnienie 0.07–0.14 s) | ✗ |
| P-NAD2-R2 (kierunek przeżywa) | ✓ |
| P-NAD2-R3 (przeżywa przy A) | ✓ |
| P-NAD2-R4 (para 12/12) | ✓ |
| P-NAD2-R5 (T1 ≤ 0.40 m) | ✗ |

## Reprodukcja

```
python3 results/NAD2_RECON/tools/nad2_wyciag_ulg.py <16 bootów S4> s2:c02_s01 s2:c05_s01_r2 s2:c08_s02 s2:c11_s02_r2
python3 results/NAD2_RECON/tools/nad2_r1.py
python3 results/NAD2_RECON/tools/nad2_r2.py
python3 results/NAD2_RECON/tools/nad2_r3.py wszystko        # najpierw wierność (STOP przy braku)
python3 results/NAD2_RECON/tools/nad2_r4.py
python3 results/NAD2_RECON/tools/nad2_r5.py
```

Wyciągi ULG: 20 plików, 29 MB (≤ 3 MB na boot). diff-stat i porcelain — w commicie.

**Sygnał: STOP-NAD2R.** Push = Olga; CC przelicza R1–R3 i R5 niezależnie i pisze PRE_NAD2 albo aneks zamykający.
