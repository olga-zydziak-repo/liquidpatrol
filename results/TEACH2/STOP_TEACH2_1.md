# STOP-TEACH2-1 — lot długi L1: 200 s nauki z GNSS, potem 600 s bez GNSS i bez znaczników nad parkingiem

LiquidPatrol · wykonawca · 18.11.2026 · PRE_TEACH2, PROMPT_TEACH2_S1,
ANEKS_TEACH2-1 (sha df5909ab, „ratyfikuję TEACH2-1”).

**Werdykt PRE §5: L-A.** Kontynuacja od cięcia wyniosła **600.52 s**
(`t_inj_sim` 345.936 → zejście planowe 946.456). Naruszeń B1–B4 brak,
REFUSE w misji brak, (D-L) spełnione. **Booty: 1 z 3**, rezerwy
nietknięte. Lot jest ważny w pierwszym podejściu.

Commity tej sesji:
- [CO-TEACH2-1A] `004de58a`;
- [L-MANIFEST-1A] `44650ca9` (sprawdziany manifestu według ANEKS
  §3: krok 0.100017 ≤ 0.101 m, promień 11.000052 ≤ 11.001 m, PASS).

## 1. Ważność, litera, (D-L)

**Ważność:** wszystkie warunki spełnione.
- Detekcje znaczników zgodne z manifestem: 0. Surowe: 2 (ID 37, bok do
  5.0 px), żadna nie odpowiada znacznikowi z manifestu.
- Po fladze nie ma żadnego kadru mapy, klatki kluczowej ani wiązania.
  Zamknięcie było jedno.
- Cięcie po wejściu: `t_entry` 6.28 s, cięcie przy 206.28 s epizodu.
- Sprawdzian lotu: 100% (16 927 ticków osłony, 3037 poprawek,
  georeferencja 5e-7° / 4.9e-7 m).
- Meta zgodna: tabela, tor, sumy producenta (db96a4a7 / 4eefedda), świat
  S, model, cień 0, etap s3 (odchylenie 1 ze STOP-MANIFEST), manifest
  d0841872, `T_CONT_S` 600.5, `WALL_MAX_CUT_S` 1000, `KONT_INJECT_T`
  200.

**Litera:**
- **B1:** 0 przekroczeń na 12 638 ocenionych tickach (12 696 ticków
  utraty), max e′/U′ 0.236. Nieocenionych ticków 58: wszystkie po
  zatrzasku τ* w zejściu planowym, z przyczyną „przedział None”;
  w misji 0.
- **B2:** największy r_GT 19.48 m, margines do R_E 32 m wynosi 12.52 m.
- **B3:** 0 złych na 12 696 tickach.
- **B4:** `nav_state` 14, failsafe 0, REFUSE(POS) 0, breach brak.

**(D-L):** kontynuacja 600.52 s ≥ 600 s, track 1.000, pasmo 0.971,
REFUSE w misji 0. **Odmów w misji nie było.**

## 2. Obserwable

**Cała misja od flagi z ULG:** okno 345.948–946.408 s, czyli 600.46 s.
- **Błąd poprawki wobec GT:** p50 0.234 m, p95 0.352 m, max 0.450 m.
  Przyjęte 3003 z 3003 kadrów (100%), największa przerwa 0.2 s,
  przerw ponad 1.15 s 0.
- **e′:** p50 0.256 m, p95 0.403 m, max 0.658 m. Max e′/U′ 0.236.
- **τ w misji:** p50 0.128 s, p95 0.216 s, max 0.38 s.
- **Bariera i tor:** r_max GT 19.48 m, najmniejszy zapas bariery
  4.87 m, track 1.000, pasmo 0.971. Punkty zgodne: p5 152, p50 241.

**Okna po 100 s od flagi:**

| okno [s sim] | błąd poprawki p50 / p95 / max [m] | przyjęte | max e′/U′ | e′ max [m] | τ max [s] | błąd EKF p50 / max [m] | błąd kursu EKF p50 / max [°] | r_max GT [m] | zapas bariery min [m] | track / pasmo | zgodne p5 / p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 346–446 | 0.246 / 0.333 / 0.369 | 500/500 | 0.186 | 0.519 | 0.38 | 1.92 / 3.56 | 4.61 / 6.60 | 18.86 | 5.60 | 1.000 / 0.968 | 163 / 250 |
| 446–546 | 0.242 / 0.378 / 0.450 | 500/500 | 0.203 | 0.566 | 0.236 | 2.68 / 5.53 | 2.43 / 4.87 | 17.65 | 6.82 | 1.000 / 0.972 | 179 / 240 |
| 546–646 | 0.250 / 0.354 / 0.432 | 500/500 | 0.236 | 0.658 | 0.232 | 6.38 / 8.05 | 0.74 / 3.09 | 18.73 | 5.63 | 1.000 / 0.985 | 117 / 227 |
| 646–746 | 0.253 / 0.348 / 0.393 | 500/500 | 0.206 | 0.574 | 0.236 | 6.61 / 10.28 | 0.69 / 4.44 | 18.29 | 6.06 | 1.000 / 0.956 | 171 / 251 |
| 746–846 | 0.169 / 0.289 / 0.411 | 500/500 | 0.202 | 0.564 | 0.236 | 11.33 / 15.21 | 4.49 / 7.92 | 19.48 | 4.87 | 1.000 / 0.942 | 147 / 245 |
| 846–946 | 0.252 / 0.355 / 0.401 | 500/500 | 0.216 | 0.602 | 0.232 | 14.40 / 17.45 | 2.25 / 3.89 | 17.65 | 6.72 | 1.000 / 1.000 | 146 / 232 |
| 946–946.4 | 0.190 / 0.195 / 0.195 | 3/3 | 0.106 | 0.295 | 0.22 | 17.05 / 17.08 | 2.68 / 2.72 | 11.57 | 13.01 | 1.000 / 1.000 | 196 / 198 |

Błąd własny EKF rośnie z 3.6 do 17.4 m, a błąd poprawki z mapy zostaje
w 0.37–0.45 m w każdym oknie. Połowy okna: max 0.450 m w pierwszej,
0.411 m w drugiej.

**Mapa i oś czasu:**
- Mapa: 1041 kadrów, 15 klatek kluczowych, 3119 wiązań (wszystkie
  przyjęte), 0 dopasowań późnych.
- **Zamknięcie: 382.6 ms**, w tym rozwiązanie 341.9 ms. Od klatki flagi
  do gotowej georeferencji 388.1 ms.
- Chwila flagi z ULG 345.948. Wejście osłony w utratę 346.040 (+0.092 s).
  Klatka zamknięcia 346.0 (+0.052 s). Ostatni kadr mapy 345.6
  (−0.348 s).
- Opóźnienie pierwszej poprawki 0.052 s (czas klatki), skok Δ przy
  pierwszej poprawce 0.300 m.
- Kurs klatek kluczowych wobec GT: przed georeferencją do 5.19°, po
  do 1.08° (15 KF).

**Faza mapy:**
- Klatek dłuższych niż 0.2 s: **0**. Najdłuższa klatka fazy mapy trwała
  133 ms, a czas producenta w mapie p50 / p95 wynosił 24.7 / 29.9 ms.
- Klatek zgubionych: **0** w fazie mapy, 0 w lokalizacji; `summary
  n_drop` 0 przy 4784 obrazach.
- W chwili flagi nie trwała żadna wolna klatka. Reguła powtórki nie
  miała zastosowania.

**Producent:**
- Lokalizacja: p50 12.3 ms, p95 14.2 ms, max 18.2 ms na klatkę.
- Pamięć procesu `nadir_obs` przy zamknięciu: VmRSS 608 MB, w całym
  locie max 615 MB (1012 próbek).

**Kadry:** 966 na stanowisku (`~/teach_stanowisko/L1_S_c10`), 12 w repo.

**Pliki:** w `results/TEACH2/s1/L1_S_c10/`:
- `sedzia_teach2.json`;
- `poprawki_teach2.jsonl` — każda przyjęta poprawka z klatką kluczową,
  wektorem, zgodnymi, innowacją, p_fix, migawką EKF i GT;
- `georef_teach2.json` — georeferencja z 3119 wiązaniami;
- `ulg.jsonl.gz` (6.51 MB);
- `pamiec_producenta.jsonl`.

## 3. Liczby do P-TEACH2-1 … 9 (bez rozliczenia)

- **1:** budowa i próba na sucho zatrzymane STOP-TEACH2-1-MANIFEST
  (rozliczone w ANEKS_TEACH2-1). Harness, osłona i driver bez zmian.
- **2:** werdykt L-A w pierwszym ważnym locie (boot 1).
- **3:** przekroczeń przesłanki B1 0, max e′/U′ 0.236.
- **4:** największy błąd poprawki w misji 0.450 m.
- **5:** przyjęte 3003 z 3003 kadrów okna misji (100%), przerw ponad
  1.15 s 0.
- **6:**
  - zamknięcie mapy w locie 0.383 s (od flagi do georeferencji
    0.388 s);
  - pierwsza poprawka 0.052 s po fladze w czasie klatki. Wynik zapisany
    przez producenta po zamknięciu.
- **7:** największy błąd w ostatnich 100 s okien pełnych (846–946 s)
  0.401 m wobec 0.369 m w pierwszych 100 s, czyli +0.032 m. Z resztką
  okna 946–946.4 s: max 0.401 m.
- **8:** klatek zgubionych w fazie mapy 0.
- **9:** promień drona (GT) w misji najwyżej 19.48 m.

## 4. Odchylenia od promptu (każde osobno)

1. **Meta „etap” = s3.** Przyjęte w ANEKS_TEACH2-1 §2: kopia boota ze
   strażnikiem s2/s3.
2. **Zamknięcie mapy w locie (383 ms) dwa razy dłuższe niż w R4
   (206 ms):**
   - mapa ma 15 KF i 3119 wiązań wobec 16 KF i 2998 wiązań w R4;
   - wiązania kosztowały tu 41 ms wobec 29 ms;
   - główna różnica leży w rozwiązaniu Gaussa–Newtona: 342 ms wobec
     136 ms;
   - stanowisko było pod obciążeniem symulacji, a R4 liczył na jednym
     rdzeniu bez niej.
   To obserwacja, nie zmiana.
3. **„Pierwsza poprawka po fladze”** liczona w czasie klatki, tak jak
   w S3. Klatka zamknięcia (346.0) dała poprawkę, ale datagram wyszedł
   dopiero po zamknięciu, czyli ok. 0.39 s ściennych później. Osłona
   weszła w utratę przy 346.04, a τ w misji nie przekroczyło 0.38 s.
4. **Ostatnie okno 100 s jest niepełne** (946–946.4 s, 3 klatki). P7
   podaję z okien pełnych i z tym oknem.
5. **„Klatka fazy mapy trwająca w chwili flagi”** to przedział
   w czasie sim [sim wiersza, + czas producenta], przyjęte
   w ANEKS_TEACH2-1. Brak wolnych klatek czyni to tu bezprzedmiotowym.

Kod lotu, osłona, driver, tor, tabela, świat i model pozostały bez
zmian. Danych lotu nie użyto do zmiany tabeli, toru ani progów.

## 5. Po sesji

`systemd-timesyncd` jest zatrzymany na sesję. Uruchom go:
`sudo systemctl start systemd-timesyncd`. Chrome i ChatGPT można już
otworzyć.
