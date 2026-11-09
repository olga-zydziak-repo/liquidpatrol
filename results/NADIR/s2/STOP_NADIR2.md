# STOP-NADIR2 — charakteryzacja piły pod misją: rama B+ w pętli, 4 cięcia GNSS pod osłoną 2d; żadna śmierć S2 nie zachodzi

Wykonawca · 9.11.2026 · łańcuch NADIR, PROMPT_NADIR_S2. Bramka §0: origin/master = 9f7cdd74, `origin/master..HEAD` puste.
Budowa `debcdd94`, poprawka przyrządu `a91bb94e`, dane i raport w commicie STOP-NADIR2.

## Raport płaski

- **R1 warunek ważności B: 0 przekroczeń w wymogu.**
  - Okna z GNSS: 723, max przyrost 0.42 ε_b(⌊τ⌋).
  - Okna bez GNSS (t_flag → REFUSE): 439, max przyrost **0.94** ε_b (c11_s02), 0.93 (c08_s02), 0.86 (c02_s01), 0.60 (c05_s01).
  - Okna zejść D5, raportowane osobno i poza wymogiem: 93, w tym 3 z przekroczeniem (max 1.15). W każdym epizodzie jest jedno okno z τ > 2 s: przy zejściu poprawek nie ma, zgodnie z literą PRE.
- **R2 ε_fix na żywo:** poprawka użyta w trybie 12 to w 87% para (1020/1162 w misji).
  - Użyta poprawka, p95 per koszyk r_h:

    | koszyk r_h | z GNSS | bez GNSS |
    |---|---|---|
    | 0–2 | 0.105 | 0.152 |
    | 2–4 | 0.093 | 0.108 |
    | 4–6 | 0.074 | 0.113 |
    | 6–8 | 0.086 | 0.388 (n = 20) |
    | 10+ | 0.235 (n = 1) | — |
    | 8–10 | brak danych | brak danych |

  - Max dla FREEZE (użyta, oba reżimy): 0.203 / 0.195 / 0.151 / 0.388 / — / 0.235 m.
  - Tryb 1 osobno, p95 bez GNSS: 0.18 / 0.34 / 0.43 / 0.47 m. Para osobno: 0.08 / 0.11 / 0.11 / 0.11 m.
  - Klatki epizodu z przyjętą poprawką: 90–94%. Odrzucenia: krawędź stożka (~85% odrzuconych detekcji), bok < 18 px, klatki bez przyjętych 22–37 na epizod. Odrzuceń „reszta ≥ s/2” i „ID poza manifestem”: 0.
  - **Bias kursu z par nie dryfuje bez GNSS:**
    - p50 δψ przed / po cięciu: c08 −3.36° / −3.53°, c11 −1.46° / −1.48°, c05 −4.29° / −4.56°, c02 −2.23° / −2.16°;
    - trend |·| ≤ 0.27°/s;
    - bias jest stały w epizodzie, a między bootami różny (−1.5…−4.6°). Para go zdejmuje.
- **R3 sieć na p_corr: ENTRY w 4/4.**
  - Czasy ENTRY (S2 vs KONT S4 tego samego scenariusza): c08 8.53 vs 2.62 s, c11 6.74 vs 6.75, c05 2.16 vs 2.47, c02 7.16 vs 8.86.
  - Orbita do REFUSE(T*) w 4/4: kontynuacja 21.96–21.97 s (KONT 21.97–21.99).
  - (c) track / pasmo 1.0 / 1.0, a dla c11 1.0 / 0.903 (KONT 1.0 / 0.911).
  - REFUSE poza barierą 0, naruszenie strefy 0.
  - Skoki p_corr przy poprawkach: p50 0.03–0.04, p95 0.14–0.19, max 0.57 m. Skala szumu GNSS ramienia nominalnego KONT (|Δe| po 0.2 s): p50 0.013 / p95 0.034 m. Skoki ramy są ~5× większe od szumu GNSS i sieć to znosi.
  - Bramka tempa settle: 0.966 / 0.941 / 0.954 / 0.953.
  - V2′ (dsim/dwall): 0.955 / **0.923** / 0.949 / 0.955.
- **R4 piła: max u ≤ m we wszystkich komórkach.**

  | komórka | u_max | m |
  |---|---|---|
  | c08_s02 | 2.235 | 2.99 |
  | c11_s02 | 2.082 | 3.02 |
  | c05_s01 | 2.042 | 10.33 |
  | c02_s01 | 2.024 | 5.79 |

  - Ticków z u > m: 0.
  - τ misji: p95 0.20–0.21 s, max 0.22–0.23 s.
  - Ogonów τ > 1 s w fazach misji: 0, więc przy węzłach koron nic się nie dzieje. Rezerwa „manifest v3” się nie uruchamia.
  - Ticki misji bez żadnej poprawki: 0–2 na epizod (przed pierwszą poprawką).
- **R5 bramka predykcji: zero odrzuceń prawdziwego intruza** (klasa „intruz przy tracku na intruzie”: 0/4).
  - Odrzucenia boxów nie na intruzie: c02 35, pozostałe po 1–2. To zysk.
  - Odrzucenia intruza przy tracku zastanym: c08 21, c05 7.
- **Werdykt S2: żadna śmierć S2 nie zachodzi.** R1 0 przekroczeń, max u < m, misja na p_corr z ENTRY i orbitą do T* w 4/4, walidacja sucha PASS. ε_fix ≤ 0.39 m nie pustoszy rachunku R5 (decyzja CC przy FREEZE).
- **Budżet:** S2 6/6. Ważne loty: c08_s02, c11_s02_r2, c05_s01_r2, c02_s01. Dwa booty przerwała bramka tempa przed uzbrojeniem: c11_s02 0.910 i c05_s01 0.925. Noga NADIR 10/≤30. Breach 0, REFUSE fałszywy 0. Jedna blokada ENV-BLOCK przed startem bootu, bez zużycia: pliki `envblock_*`.

## Do CC — nazwane, nie ukryte

1. **Bramka predykcji kosztuje ENTRY przy tracku zastanym (c08: +5.9 s względem KONT).**
   - Mechanizm: track sprzed epizodu (ENTRY −0.28 s, intruz w starej pozie) → teleport do pozy startowej → 21 odrzuceń 14–16 m od predykcji → FEED_EXPIRE po 2.96 s → ponowna admisja w 8.5 s.
   - Bramka zachowuje się zgodnie z projektem (fizycznie niemożliwy przeskok), ale artefakt startowy kosztuje czas.
   - W c05 ten sam mechanizm (7 odrzuceń) nie opóźnił ENTRY.
2. **c11_s02_r2: litera KONT (b) FAIL na krzywej 2d.**
   - Dryf EKF od cięcia przekroczył obwiednię ε_b o ≤ 6% (max 1.06, przy wieku 4.0 s i 7.4 s, 92 próbki). Δ zejścia 0.59 ≤ 1.524.
   - To ten sam, nietknięty EKF. Drugi taki przypadek po KONT c11_s01 (1.113): obwiednia ε_b dla wieku > 2 s nie jest ostra.
   - Rama B+ korzysta wyłącznie z ε_b(0), ε_b(1) i ε_b(2) w oknach ≤ 0.23 s, a tam max 0.94. Osłona 2d (T*) jako siatka bezpieczeństwa stoi jednak na całej krzywej.
3. **V2′ c11_s02_r2 = 0.923 < 0.93** (PRE §3 (iii), prompt R3). Sędzia kanoniczny (D9 ≥ 0.90) uznaje epizod za ważny. Budżet wyczerpany, ważność epizodu dla R3 to decyzja CC. R1 i R4 tego epizodu nie zależą od tempa w sposób, który by je osłabiał: przyrosty liczone są po czasie sim.
4. **Odstępstwo od litery §R, decyzja Olgi przed lotami:** 1 cięcie na boot zamiast 2. Driver KONT S4 kończy boot po D5 („jeden cut na boot”), a 2 cięcia wymagałyby nowego mechanizmu ponownego startu. Efekt: 4 booty lotne zamiast 2, rezerwa zużyta na dwa przerwania bramką tempa.
5. **Wada §1.6 — prawdziwa przyczyna i naprawa.** W S1 i w pierwszym boocie S2 summary `nadir_obs` nie powstawał, bo **teardown launchera** zabijał proces przez SIGKILL (nazwa na liście `kont_inw KILL`), zanim boot wysłał TERM. Rozpoznałam to po braku zrzutu faulthandler i po czasach plików.
   - Naprawa `a91bb94e`: najpierw TERM, do 5 s na zamknięcie, potem KILL. Od bootu 3 summary ma `zamkniecie: koniec_petli`.
   - Summary okresowe (heartbeat) zabezpieczało dane w boocie 1.
6. **Errata walidacji suchej przed lotami.** Kryterium C(i) w pierwszej wersji (p95 trybu 1 ≤ p95 S1 w koszyku) było źle postawione: poprawki trybu 1 to podzbiór obserwacji S1. Koszyk 0–2: 0.209 vs 0.201 przy błędach identycznych wartość w wartość (≤ 5e−5 m). Zamieniłam je na tożsamość z wzorem S1. Kryterium z litery (|p_corr − GT| p95 0.093 ≤ 1.04) było PASS od początku. Szczegół jest w docstringu narzędzia.
7. **Decyzje wykonawcze w kodzie, nazwane:**
   - poprawka tylko poziomo, wysokość z EKF;
   - Δ trzymane między poprawkami, 0 przed pierwszą;
   - strażnik spójności pary: |skala − 1| ≤ 0.2 ∧ |δψ| ≤ 20°;
   - bramka predykcji M0 = 6.0 m + 2.0 m/s·Δt, skalibrowana na 20 bootach KONT/S1 przed lotami;
   - migawka EKF przy przybyciu klatki, bo znacznik PX4 `timestamp` dryfuje względem sim gz o ~7 s na boot;
   - `own_pos` ramy podmieniony w `percep_proc.py`, bo to on jest źródłem w ścieżce V2 (PRE wskazywał `feed_vision.py`, gdzie zmiana dotyczy tylko bramki).
8. **Testy:** wyniki identyczne przy HEAD i w drzewie roboczym. `test_cykl_zycia_percep_proc` (DET) jest niestabilny tak samo przy HEAD (1 z 3 przebiegów czerwony).

## §0 i §1 (0 bootów)

- **§0.2 świat v2:** identyczny poza maskami płyt — 10/10 póz, 0 px imagera poza maską, szum renderu 0, kamera przepływu bez zmian (`swiat/swiat_v2_identycznosc.json`).
- **§1.5 walidacja sucha PASS** (`walidacja_sucha.json`):
  - passthrough `NADIR_MODE=0`: 21 604 wiersze feedu w 6 bootach, 0 różnic, feed_sha bez zmian;
  - sp_EKF − sp_net = p_EKF − p_corr co do 1.8e−15;
  - |p_corr − GT| na logach S1: p95 0.093 m ≤ 1.04 m.
- **§0.3 dry-run PASS** (`dryrun/dryrun_s2.json`): main() drivera do uzbrojenia, bloki S2N w obu trybach, 0 nowych ostrzeżeń shellcheck.

## Pliki

- `r1_okna.json`, `r2_eps_fix.json` (wszystkie obserwacje i maksima dla FREEZE), `r3_siec.json`, `r4_pila.json` (z R5), `analiza_stdout.log`.
- Katalogi bootów: `rama.jsonl` (log ramy per tick), `nadir_obs.jsonl` (rekordy `fx`), `percep_feed.jsonl` (`pred_odrzut`, `nadir`), `wyniki_s4.json`.
- Narzędzia `results/NADIR/tools/nadir_s2_*`.

Sygnał: **STOP-NADIR2**. Push = Olga. CC przelicza R1 i R2 niezależnie i pisze ANEKS_NADIR-2 (FREEZE ε_fix albo aneks zamykający).
