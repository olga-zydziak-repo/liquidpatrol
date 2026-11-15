# STOP-NAD3-2 — S2 zamknięte: geometria PASS (5/5 epizodów z misją, max 18.870 m), B3 i B4 czyste — zero naruszeń B1–B4, replay 100%, pierwszy lot z degradacją P1 zgodny z tabelą; 4/4 booty

15.11.2026 · wykonawca · PROMPT_NAD3_S2 z ANEKS_NAD3-1 (66eef7e6) i ANEKS_NAD3-2 (0ba434f0, „ratyfikuję NAD3-2”). **Booty S2: 4 z 4** (N1, N2, B3, B4), rezerwa z §3.5 nieużyta. Noga NADIR-III: 4 z ≤ 22.

**Werdykt.** S2 przeszło bez śmierci i bez naruszenia.
- Bramka promienia PASS na 5 epizodach z misją (ANEKS_NAD3-2 §3.2).
- **B3 (cięcie c05 bez degradacji):**
  - B1–B4 OK;
  - zestaw kluczy wierszy i meta jak w NAD2;
  - replay producenta i osłony 100%.
- **B4 (cięcie c05, P1, bias na zewnątrz — pierwszy lot z degradacją):**
  - B1–B4 OK, max e′/U′ 0.420;
  - decymacja na żywo jedna poprawka na slot, odstęp t_fix 1.000 s;
  - replay fx i fx_deg oraz osłony 100%;
  - meta zgodna z punktem P1.
- REFUSE w misji: 0 w obu cięciach. Odmowa osłony zapadła w obu po komendzie zejścia planowego (opis niżej).
- r_max GT w cięciach: 15.53 i 15.48 m.

## Przebieg S2

| boot | lot | commit przed lotem | bramka zdrowia | tempo | wynik |
|---|---|---|---|---|---|
| 1 | N1 (c00, c01, c05, c10) | `e90346f0` [S2-BUDOWA] | A GO 0.903 | 0.940 | c05 i c10 z niewłaściwym intruzem ⇒ STOP-NAD3-2-MANIFEST (`d4958c04`) |
| — | — | ANEKS_NAD3-1: [CO-NAD3-1] `10a35625`, [S2-V2] `d7aad182` (manifest v2, 120 epizodów, sha 2f3b4a94) | | | |
| 2 | N2 (c02, c03, c05, c10) | `d7aad182` | A NO-GO 0.889 (Chrome, ChatGPT), C GO 0.921 | 0.963 | c03 bez akwizycji ⇒ STOP-NAD3-2-GEOM-NOMINAL (`ad7614e0`) |
| — | — | ANEKS_NAD3-2: [CO-NAD3-2] `d19ddb9c`, [S2-KOLEJKA-NAD3-2] `b792ecaf` (cięcie bez wejścia, §3.5) | | | |
| 3 | B3 (c05, cięcie, bez degradacji) | `b792ecaf` | A GO 0.928 | 0.975 | PASS |
| 4 | B4 (c05, cięcie, P1, na zewnątrz) | `b792ecaf` | A GO 0.927 | 0.977 | PASS |

Przed B3 i B4 stanowisko sprawdzone z WSL (`tasklist.exe`): Chrome i ChatGPT nie działały, obciążenie 0.09.

## Geometria — bramka promienia (ANEKS_NAD3-2 §3.2)

| epizod | boot | r_max GT [m] | intruz max [m] | track | pasmo | B1–B5 | do bramki |
|---|---|---|---|---|---|---|---|
| c00_s01 | N1 | 18.326 | 10.0 (stoi) | 0.891 | 0.931 | OK | ✓ |
| c01_s01 | N1 | 18.143 | 10.0 (stoi) | 0.896 | 0.987 | OK | ✓ |
| c02_s01 | N2 | 18.271 | 10.0 (stoi) | 0.885 | 0.962 | OK | ✓ |
| c03_s01 | N2 | 0.485 (zawis, brak akwizycji) | 10.0 (stoi) | 0.000 | 0.329 | OK | pusty (§3.1–§3.2) |
| c05_s01 | N2 | 15.997 | 10.0 (ruch 0.5 m/s) | 0.873 | 0.954 | OK | ✓ |
| c10_s01 | N2 | 18.870 | 10.998 (ruch 1 m/s) | 0.946 | 0.941 | OK | ✓ |
| c05_s01 cięcie | B3 | 15.529 | — | 1.000 (D1) | 1.000 (D1) | B1–B4 OK | obserwabla (≤ 19.5) |
| c05_s01 cięcie | B4 | 15.479 | — | 1.000 (D1) | 1.000 (D1) | B1–B4 OK | obserwabla (≤ 19.5) |

- Max w nominałach z misją: **18.870 m** (c10), zapas do bramki 0.63 m. Epizody N1 c05 i c10 są nieważne (ANEKS_NAD3-1 §3.6), wyłącznie opisowo.
- **Okna:** misja nominalna trwa 74–83 s. Cięcie trwa od startu epizodu do zejścia 143.6 s (B3) i 143.6 s (B4) — t_inj 33.07 s od startu, kontynuacja 110.50 / 110.53 s.
- **Promień intruza na torze zadanym:** w oknie cięcia c05 10.0 m, c10 11.0 m — tyle samo co w oknie nominału.
- **Dwa cięcia c05 w pełnym oknie:** r_max 15.53 i 15.48 m. To poniżej nominału c05 z N2 (16.00 m) i poniżej bramki.

## B3 — cięcie c05 bez degradacji (`results/NAD3/s2/b3_c05_bez_degradacji`)

- **Klucze:** wierszy z `fx_deg` 0, meta producenta bez `nad3`. Zbiory kluczy meta, wiersza nf i fx są identyczne z lotem NAD2 (`results/NAD2/s3/c05_s01_r2`).
- **Replay** (`nad3_s2_spr.py` (r)):
  - producent: 1483 fx, 0 niezgodnych, max |Δ| 0.0;
  - osłona przez `nad3_krok`: 3121 ticków, przedział / τ / R_k / faza / decyzja / reguła / d_ne — 0 niezgodnych;
  - zatrzask w zapisie i w replayu: tick 3074. **100%.**
- **Litera bezpieczeństwa na tabeli P1** (sha 806f5e90):
  - **B1:** 0 przekroczeń, ocenionych 2402 z 2447 ticków utraty, max e/U 0.103, e_corr p50 / p95 / max 0.128 / 0.217 / 0.324 m;
  - **B2:** margines do R_E min 16.47 m;
  - **B3:** 0 złych z 2447;
  - **B4:** nav_state 14, failsafe 0, REFUSE(POS) 0.
- **D1:** kontynuacja 110.50 s, track 1.000, pasmo 1.000, REFUSE w misji 0.
- **B1 nieocenione: 45 ticków.** Przyczyna jedyna: przedział None, bo τ + 0.012 s wyszło poza ostatnią krawędź po zatrzasku τ*. Wszystkie po zejściu planowym, 0 w fazie misji. Pierwszy tick 3076.

## B4 — cięcie c05, P1, bias na zewnątrz (`results/NAD3/s2/b4_c05_p1_na_zewnatrz`)

- **(s1) Decymacja na żywo:**
  - 155 poprawek dostarczonych, numery slotów ściśle rosnące (najwyżej jedna na slot);
  - odstęp t_fix dostarczonych: min / p50 / max = 1.000 / 1.000 / 1.000 s;
  - τ max w misji 1.024 s (przedział (0.95, 1.15], zapas do krawędzi 0.114 s), p50 0.52 s.
- **(s2) Replay:**
  - producent czysty → `Degradacja` z konfiguracją i ziarnem z meta: 1494 fx, fx i fx_deg 0 niezgodnych (slot, E, d_ne, p_fix), max |Δ| 0.0;
  - osłona: 3106 ticków, 0 niezgodnych, zatrzask tick 2997 = 2997. **100%.**
- **(s3) Meta:**
  - meta producenta `{bias_rad, na_zewnatrz, E_max 1.0, f 1, K 0, ziarno 1}`;
  - tabela z meta lotu = FREEZE P1 (sha 806f5e90), E 1.0;
  - zdarzenie drivera `nad3_degradacja` zgodna = true.
- **Litera bezpieczeństwa na e′ i U′:**
  - **B1:** 0 przekroczeń, ocenionych 2326 z 2433, **max e′/U′ 0.420**, e′ p50 / p95 / max 1.173 / 1.498 / 1.840 m (bias 1.0 m wliczony);
  - **B2:** margines min 16.52 m;
  - **B3:** r_est = |p_corr zdegradowane| w 2433/2433;
  - **B4:** nav_state 14, failsafe 0, REFUSE(POS) 0.
- **D1:** kontynuacja 110.53 s, track 1.000, pasmo 1.000, REFUSE w misji 0.
- **Błąd zakotwiczenia a′** (poprawka zdegradowana wobec GT): 149 poprawek, p95 1.123 m, max 1.174 m, max a′ / (1.5·(F + E)) = 0.628.
- **Przedziały τ w utracie:** 0: 743, 1: 464, 2: 465, 3: 467, 4: 187, None: 107 (po zatrzasku). Wszystkie pięć przedziałów tabeli zostało użytych.
- **B1 nieocenione: 107 ticków** — przedział None po zatrzasku τ* w zejściu, 0 w misji, pierwszy tick 2999.

## Odmowy osłony (obserwacja, ANEKS / PROMPT §4)

| lot | tick | sim [s] | faza | po zejściu planowym | przyczyna | τ [s] | przedział | r_est [m] | bariera R_k [m] |
|---|---|---|---|---|---|---|---|---|---|
| B3 | 3074 | 293.07 | approach (D5) | tak (zejście 284.06) | τ* | 1.072 | 4 | 11.495 | 22.099 |
| B4 | 2997 | 291.46 | orbit (D5) | tak (zejście 286.08) | τ* | 1.060 | 4 | 12.041 | 22.099 |

W obu lotach odmowa zapadła 9.0 s i 5.4 s po komendzie zejścia planowego: przy ziemi znaczniki wychodzą z kadru, τ rośnie ponad 1.05 s (próg zatrzasku 21 ticków). To ten sam wzór co w bramce NAD2 („REFUSE w zejściu”). W misji REFUSE 0. Zakończenie: przyziemienie GT przy r_gt 11.87 m (B3) i 10.81 m (B4).

## Obserwable PRE §6

| | B3 (bez degradacji) | B4 (P1, na zewnątrz) |
|---|---|---|
| τ w misji p50 / p95 / max [s] | 0.116 / 0.204 / 0.224 | 0.520 / 0.968 / 1.024 |
| skok Δ′ per zmiana ramy p50 / p95 / max [m] | 0.076 / 0.153 / 0.261 (n 592) | 0.464 / 0.792 / 1.050 (n 115) |
| odrzucenia bramki predykcji tracku | 12 | 23 |
| r_max GT w misji po fladze [m] | 15.529 | 15.479 |
| max e′/U′ | 0.103 | 0.420 |
| zapas bariery min (misja) [m] | 8.824 | 5.413 |

- **Różnica r_max między B3 (E = 0) a B4 (E = 1.0 m na zewnątrz): 0.05 m.** Pary o przeciwnym znaku biasu (P-NAD3-4) poleci S3.
- Skok Δ′ w B4 (max 1.05 m przy 1 Hz) mieści się w zakresie treningowym rel (p99 2.02 m, recon R5).
- Odrzuceń bramki predykcji jest 23 wobec 12 — opisowo, próg 6 m nie był bliski.

## Odchylenia od promptu (nazwane)

1. **Raport w trzech plikach**, bo S2 zatrzymywało się dwa razy:
   - `STOP_NAD3_2.md` (MANIFEST);
   - `STOP_NAD3_2_GEOM.md` (GEOM-NOMINAL);
   - ten plik (zamknięcie S2).
2. **Kolejka zmieniona dwa razy w trakcie S2**, za każdym razem aneksem i commitem przed lotem:
   - manifest v2 i numery kanonu (`d7aad182`);
   - cięcie bez wejścia (`b792ecaf`).
   Kod lotu, osłony i degradacji bez zmian od `69128dba`.
3. **Bramka zdrowia N2 g1:** pliki `results/NAD3/s2/bramka/n2_nominal_g1/` z przerwanej próby 00:45 nadpisała próba 12:08 (ta sama nazwa tagu). Zapis 00:45 zostaje w `bramka_ksiega.jsonl` i w historii commitu `d4958c04`.
4. **Kod 9 drivera** (bramka tempa / niezgodność degradacji) bez zmian (ANEKS_NAD3-1 §3.9). W S2 nie wystąpił.

## Licznik bootów

| etap | zużyte | budżet |
|---|---|---|
| S2 | 4 (N1, N2, B3, B4) | 4 (+1 rezerwa §3.5, nieużyta) |
| noga NADIR-III | 4 | ≤ 22 |

Nieważnych stanowiskowo: 0. Cięć bez wejścia: 0.

**Sygnał: STOP-NAD3-2.** Push robi Olga. CC weryfikuje z repo i oddaje ANEKS_NAD3-3 (zgoda na bramkę S3).
