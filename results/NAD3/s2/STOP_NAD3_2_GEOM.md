# STOP-NAD3-2-GEOM-NOMINAL — bramka r_max przechodzi 6/6, kryterium nominału 5/6: w N2 epizod c03 bez akwizycji intruza (track 0.0) — STOP i aneks według ANEKS_NAD3-1 §3.8

15.11.2026 · wykonawca · PROMPT_NAD3_S2 z ANEKS_NAD3-1 (sha256 66eef7e6, „ratyfikuję NAD3-1”). **Booty S2: 2 z 4**, noga NADIR-III 2 z ≤ 22.

**Werdykt.** STOP z regułą aneksu, nie śmierć. Na 6 ważnych epizodach nominalnych:
- **Bramka r_max ≤ 19.5 m przechodzi 6/6** (max 18.87 m).
- **Kryterium nominału spełnione w 5/6.** Odpada c03_s01 (N2): przez całe 40 s epizodu nie było akwizycji intruza — track 0.0, pasmo 0.329, dron w zawisie z r_max 0.49 m.
- Według §3.8 jeden niespełniony epizod ⇒ STOP i aneks; dwa lub więcej ⇒ śmierć geometrii.
- Bezpieczeństwo czyste: B1–B5 OK w 8/8 epizodach obu nominałów, zero REFUSE, zero breach.
- Kolejka zatrzymała się sama po N2 (`STOP-NAD3-2-GEOM-NOMINAL`). B3 i B4 nie poleciały.

## Wznowienie po ANEKS_NAD3-1

- **[CO-NAD3-1] `10a35625`:** aneks verbatim (byte-check 66eef7e6), KSIĘGA §5 append-only.
- **[S2-V2] `d7aad182`** (0 bootów):
  - manifest v2, 120 epizodów, sha256 2f3b4a94;
  - pozycja = `episode_id` 120/120;
  - 6 używanych wpisów identycznych z S1;
  - testy wiążące 6/6, pozostałe 114: 0 niespełnionych;
  - plik S1 nietknięty;
  - strażnik boota i kolejka na v2 (numery kanonu, asercja niezmiennika przed każdym bootem);
  - test S1 10/10;
  - **próba na sucho na v2 PASS 5/5** — nowa część 5 to driver ↔ proces intruza, zgodne dla N2 (2, 3, 5, 10) i cięć (5); negatyw na S1 wykrywa rozjazd [5, 10].
- **Naprawa potwierdzona lotem:** w N2 log intruza ma etykiety (2, c02), (3, c03), (5, c05), (10, c10), zero `IndexError`. Tor c05 w oknie misji ≤ 10.0 m, c10 ≤ 10.998 m.

## N2 — `results/NAD3/s2/n2_nominal`

- Bramka zdrowia:
  - g1 (A): NO-GO, tempo 0.8885 — Chrome na iGPU i ChatGPT otwarte;
  - g2 (C): GO, tempo 0.9208.
- Chrome i ChatGPT zamknięte przez Olgę w trakcie: `tasklist.exe` o 12:18 nie pokazuje żadnego z nich (o 12:15 było 15 procesów `ChatGPT.exe` w tle po zamknięciu okna).
- Lot: tempo 0.9632, rc 0, breach brak. Litera NAD2 = osłona. `nad3_degradacja`: bez degradacji, zgodna. Tabela P1.
- Analizator: ważny, bezpieczeństwo OK, B5 OK w 4/4.

## Geometria — 6 ważnych epizodów nominalnych (ANEKS_NAD3-1 §3.7)

| epizod | boot | okno misji [s] | r_max GT [m] | intruz max (log) [m] | dron − intruz [m] | intruz zadany max: nominał / okno cięcia [m] (okno cięcia od startu) | track | pasmo | B1–B5 | kryterium |
|---|---|---|---|---|---|---|---|---|---|---|
| c00_s01 | N1 | 74.02 | 18.326 | 10.0 (stoi) | 8.33 | 10.0 / 10.0 (0–144.5 s) | 0.891 | 0.931 | OK | ✓ |
| c01_s01 | N1 | 81.70 | 18.143 | 10.0 (stoi) | 8.14 | 10.0 / 10.0 (0–152.2 s) | 0.896 | 0.987 | OK | ✓ |
| c02_s01 | N2 | 82.78 | 18.271 | 10.0 (stoi) | 8.27 | 10.0 / 10.0 (0–153.3 s) | 0.885 | 0.962 | OK | ✓ |
| **c03_s01** | N2 | 40.03 (koniec bez wejścia) | **0.485** | 10.0 (stoi) | — | 10.0 / — (brak t_entry) | **0.000** | **0.329** | OK | **✗** |
| c05_s01 | N2 | 82.20 | 15.997 | 10.0 (ruch 0.5 m/s, do środka) | 6.00 | 10.0 / 10.0 (0–152.7 s) | 0.873 | 0.954 | OK | ✓ |
| c10_s01 | N2 | 76.12 | 18.870 | 10.998 (ruch 1 m/s) | 7.87 | 10.9996 / 11.0 (0–146.6 s) | 0.946 | 0.941 | OK | ✓ |

- Największy promień drona w misji: **18.870 m** (c10). Zapas do bramki 0.63 m, do r_zad 1.13 m.
- **Okna:** misja nominalna trwa 74–83 s od startu epizodu. Okno cięcia (t_entry + 30 + 110.5 s) to 144–153 s. Na torze zadanym w oknie cięcia intruz nie wychodzi poza 10.0 m (c05) i 11.0 m (c10), czyli tyle samo co w oknie nominału. Nominały nie mierzą jednak promienia drona w drugiej połowie okna cięcia; tę część zmierzą B3 i B4 regułą „r_max > 19.5 m w cięciu ⇒ STOP”.

## c03_s01 — mechanizm (z zapisu, opisowo)

- Intruz stoi w NED (0, −10, −10), 10 m od środka, przez cały epizod (`gt_intruder`, 2040 wierszy z etykietą (3, c03)).
- Dron przez 40.03 s w fazie hold (861 ticków), z pełnym skanem kursu (komendy yaw −179°…179°). Epizod zakończony bez wejścia w pasmo (`t_entry` null), refuse 0.
- **Percepcja w oknie c03** (`percep_feed.jsonl`, 606 klatek):
  - detektor widzi cel: conf > 0.3 w 179 klatkach, max 0.846;
  - MTI potwierdziło 18 klatek;
  - bramka (gate) nie przepuściła żadnej, fresh 0, locked 0.
- **Dla porównania w tym samym boocie:** c02 (stoi, 10 m) i c05 przeszły bramkę w 1061–1088 klatkach na ok. 1250.
- **Bramka NAD2** (intruz na 15 m, `results/NAD2/s3/nom_b1`): c03_s01 miał akwizycję najpóźniej z czterech stojących (t_entry 16.72 s wobec 8.6–15.0 s).
- Mechanizm: brak admisji intruza stojącego w tej komórce — detekcja jest, potwierdzenia ruchu (MTI) zbyt mało, żeby bramka tracku przyjęła cel. Geometria NAD3 (intruz 10 m zamiast 15 m) to zmieniona okoliczność. **[MECHANIZM NIEZMIERZONY]** — dlaczego MTI nie potwierdza celu w c03 przy 10 m, nie rozstrzygam.
- Ten wynik nie dotyczy promienia: dron nie wyleciał z zawisu, r_max 0.49 m.

## Do decyzji CC (aneks ANEKS_NAD3-2) — drogi, bez wyboru

1. **c03 jako niespełnienie z mechanizmem akwizycji, nie geometrii.** Bramka geometrii sądzona na 5 epizodach z akwizycją i dalej B3, B4 (budżet S2: 2 booty zostały, dokładnie na B3 i B4).
2. **Powtórka c03** w osobnym boocie nominalnym. Wymaga budżetu ponad S2 (4/4 po B3, B4) albo zamiany kolejności. Pomiar admisji jest losowy, wynik niepewny.
3. **Manifest bez c03** w nominałach S3 — c03 nie jest komórką cięcia; dotyczy dwóch nominałów bramki S3.

Niezależnie od wyboru:
- komórki cięcia c05 i c10 mają akwizycję w N2 (track 0.873 / 0.946);
- danych S2 nie użyto do zmiany tabel ani punktów.

## Licznik bootów

| etap | zużyte | budżet | uwagi |
|---|---|---|---|
| S2 | 2 (N1, N2) | 4 | zostają 2: B3, B4 |
| noga NADIR-III | 2 | ≤ 22 | |

Nieważnych stanowiskowo: 0. NO-GO bramki zdrowia przed bootem nie jest bootem.

**Sygnał: STOP-NAD3-2-GEOM-NOMINAL.** Push robi Olga. Kolejka nie ruszy bez ANEKS_NAD3-2.
