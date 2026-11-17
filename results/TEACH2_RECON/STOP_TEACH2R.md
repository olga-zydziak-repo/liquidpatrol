# STOP-TEACH2R — recon TEACH-II przy biurku: lot długi na mapie z pierwszego przebiegu wzoru

LiquidPatrol · wykonawca · 17.11.2026 · PROMPT_TEACH2_S0 (sha256 644e037a,
sygnał Olgi „otwieram lot długi”), CO-TEACH2-0 `936cab8c`. **0 bootów.**

**Żadna śmierć nie zachodzi.**
- Ś1: 24 z 24 par na każdej łacie.
- Ś2: zamknięcie mapy ze 146 s trwa najwyżej 0.21 s.
- Ś3: przewidywany promień drona w c10 to 22.17 m, przy progu 23.8 m.
- Ś4: lot da się złożyć bez zmiany w `harness/` i w osłonie. Wymaga
  jednak nowych narzędzi i zmian w narzędziach (R1).

**Wierność przyrządu zdana na obu lotach.**

| lot | przyjęte (okno) | max: recon / lot | Δ max | p50: recon / lot | Δ p50 |
|---|---|---|---|---|---|
| p01 | 552/552 | 0.721 / 0.730 m | −0.009 | 0.423 / 0.428 m | −0.005 |
| p02 | 552/552 | 0.438 / 0.436 m | +0.002 | 0.249 / 0.251 m | −0.002 |

Mapa recon wyszła kadr w kadr jak w locie: 177 kadrów i 9 klatek
kluczowych w p01, 185 i 10 w p02. Zamknięcie przy tej samej klatce co
w locie.

**Znalezisko R4, poza śmierciami.** W fazie mapy nowa klatka kluczowa
uruchamia dopasowania do wszystkich kadrów, w których trójce się
znalazła:
- przy 15. klatce kluczowej (158 s epizodu) to 145 dopasowań;
- czas takiej jednej klatki: S 0.62 s, M 1.81 s, J 1.72 s;
- przy nauce 146 s najdłuższa klatka fazy mapy trwa 1.07 s (M) i 1.18 s
  (J).

W locie kolejka procesu producenta ma długość 1
(`harness/nadir_obs.py:104`), więc taka klatka oznacza zgubione klatki
w fazie mapy (~9 przy 1.8 s). Klatek lokalizacji to nie dotyczy.

## R1 — inwentarz

1. **Cięcie późne `KONT_INJECT_T` = 200.**
   - Ustawienie: argument `INJECT_T` w `results/TEACH/tools/teach_boot.sh:50`,
     przekazywany do env w `:108`. Driver czyta go w
     `results/TEACH/tools/teach_flight.py:154`, a hook w `:686–688` tnie
     przy `t_entry + KONT_INJECT_T`. Wystarczy parametr.
   - Koniec epizodu cięcia: po `T_CONT_S` od `t_inj_sim` (`:802`), bez
     T_ORB.
   - Czas ścienny: bezpiecznik `NAD2_WALL_MAX_CUT_S` (`:149`) ma
     domyślnie 300 s. Lot potrwa około 5 + 200 + 600.5 + ~10 ≈ 815 s sim,
     przy tempie 0.95 to około 860 s ściennych. Wystarczy env 1000, jak
     w NAD2 S4 (`results/NAD2/tools/nad2_s4_run.py:41`).
   - Strażniki tempa i zegara: bramka zdrowia i próbnik zegara działają
     przed bootem, niezależnie od długości lotu. Telemetria kolejki ma
     okno 3600 s (`teach_s3_run.py:218`).
   - Wystarczy parametr.
2. **Kontynuacja 600.5 s.** Env `NAD2_T_CONT_S` w
   `teach_flight.py:148` (domyślnie 110.5). Wystarczy parametr.
3. **Wahadło intruza na manifeście v2.**
   - Generator `results/NAD2/tools/nad2_s4_manifest.py` ma na sztywno
     zapisane wejście (manifest NADIR S4, `:33`), wyjście (`:34`) oraz
     `EP_DUR_S_L` = 800 (`:32`). Nie stosuje się więc wprost.
   - Sama funkcja `wahadlo(ep)` (`:47`) jest ogólna: działa na odcinkach
     epizodu, a v2 c05 i c10 mają odcinki w [0, 200] s. Liczba nóg to
     `round(EP_DUR_S_L / 200)` (`:54`).
   - Do ok. 830 s potrzeba długości ≥ 1000 s, czyli 5 nóg. R2 sprawdził
     to importem: ciągłość kroku 0.05 / 0.1 m na 0.1 s.
   - Ruch intruza w `harness/intruder_motion.py:179` prowadzi do
     `ep["ep_dur_s"]` z manifestu. Harness się nie zmienia.
   - Manifest i jego suma wchodzą przez env `NAD3_MANIFEST` /
     `NAD3_MANIFEST_SHA` (`teach_boot.sh:72`).
   - **Potrzebne nowe narzędzie:** mały generator z importem `wahadlo`
     i nowy plik manifestu.
4. **Wyciąg ULG.**
   - Limit: `results/NAD2/tools/nad2_ulg.py:23`, env
     `NAD2_ULG_LIMIT_MB`, domyślnie 3 MB, z asercją w `:58`.
   - S3 dał 1.23–1.27 MB na okno ok. 160 s, więc ok. 830 s da ok. 6.5 MB.
   - Wystarczy env 10 w procesie kolejki przed importem, jak w NAD2 S4
     (`nad2_s4_run.py:42`). Parametr.
5. **Nominał długi w cieniu.**
   - Koniec epizodu nominalnego to `t_entry + T_ORB`, a `T_ORB = 70.0`
     jest stałą w `teach_flight.py:147` (użycie w `:802`). Bezpiecznik
     ścienny nominału to stałe 180 s w `:658`.
   - Wydłużenie do ok. 410 s wymaga **zmiany drivera**: dwie stałe na env.
     Driver leży w `results/TEACH/tools/`, nie w `harness/`.
   - Chwila cienia: `BOOT_T_CIEN` (`teach_boot.sh:65–71`) trafia do
     `TEACH_T_CIEN` w `harness/nadir_obs.py:93–97`. To czas sim
     bezwzględny, ustawiany przed bootem.
   - Start epizodu w S3 wypadał przy sim 135.6–141.9, więc „start + 200”
     da się ustawić z dokładnością ±3 s. Chwili względnej harness nie
     zna, a jej dodanie byłoby zmianą w `harness/`. Z tego powodu
     nominał bierze czas bezwzględny.
6. **Producent (`harness/teach_map.py`).**
   - Liczba kadrów, klatek kluczowych i wiązań nie ma żadnego limitu
     (listy `kadry`, `kf`, `dop`, `:98–103`).
   - Z długością fazy mapy rosną:
     - cechy wszystkich kadrów trzymane do zamknięcia (`:229–231`);
     - pętla nowej klatki kluczowej po wszystkich kadrach
       (`_wlacz_do_mapy`, `:190–194`) — źródło znaleziska R4;
     - zamknięcie: pętla po kadrach (`:206–221`) i Gauss–Newton po
       klatkach kluczowych.
   - Kolejka obrazu ma długość 1 (`nadir_obs.py:104`): klatki
     z przerwy liczone są jako `n_drop`.
   - Zmiana nie jest potrzebna.
7. **Analizator, sędzia, sprawdzian.**
   - `teach_analyze.py:68`: `T_CONT` = 110 s, stała D1. Litera lotu
     600 s wymaga zmiany narzędzia (env albo nowa stała).
   - Sędzia `teach_s3_lot.py`: plan 14 pozycji (`:43`) i meta
     `etap == "s3"` (`:79`), więc lot długi potrzebuje nowej kolejki
     i sędziego (kopie S3), jak NAD2 S4.
   - Okna analizatora liczone są do końca misji, ogólnie. Sprawdzian
     `teach_s3_spr.py` nie ma limitu długości: odtwarza wszystkie ticki.

**Ś4 nie zachodzi.** Zmiany w `harness/` i w osłonie: brak. Narzędzia do
zrobienia:
- generator wahadła v2;
- env drivera dla nominału długiego (tylko jeśli nominał ma być długi);
- `T_CONT` analizatora;
- kolejka i sędzia lotu długiego.

## R2 — geometria (`r2.json`)

| komórka | promień intruza [0, 400] s | max dron–intruz (6 cięć / 12 cięć) | promień przewidywany | zapas do 24.84 m | zmierzony r_max drona |
|---|---|---|---|---|---|
| c05 | 10.99 m | 10.52 / 11.17 m | 21.52 m (z 12: 22.17) | 3.33 m (z 12: 2.67) | 16.39 m |
| c10 | 11.00 m | 11.17 / 11.17 m | 22.17 m | 2.67 m | 19.16 m |

- **Promień intruza:** największy w 0–200 s, w 0–400 s i w 0–830 s jest
  ten sam, bo wahadło jest lustrem.
- **Poprawka rachunku CC:** dron–intruz do 11.17 m (p07 M c10 a), nie
  10.7 m, więc dron do 22.17 m, nie 21.7 m.
- **Sprawdzian ramy:** udział odległości 6–10 m zgodny z pasmem
  sędziego do 0.02.

## R3 — nauka z innego przebiegu (`r3.json`, `r3_czesci/`)

72 przebiegi: 4 loty uczące × 6 powtarzających × 3 łaty. Mapy nauki:

| lot uczący | kadry mapy | klatki kluczowe | wiązania | zamknięcie (z ostatnim kadrem) |
|---|---|---|---|---|
| c05 | 372–373 | 10 | 1116–1119 | 79–117 ms (149–266 ms) |
| c10 | 387–390 | 12 | 1161–1170 | 96–130 ms (150–227 ms) |

Koniec nauki: 73.0–73.1 s epizodu dla c05, 75.8–76.2 s dla c10. Koniec
misji lotów powtarzających: 140.5–146.3 s epizodu.

| łata | pary z warunkiem Ś1 | max „wspólne” (para) | max „dalej” (para) | przerwy > 1.15 s wsp. / dal. | przyjęte „dalej” łącznie / c10 |
|---|---|---|---|---|---|
| S | 24/24 | 0.422 m (c1 → p06) | 0.646 m (c1 → p13) | 0 / 0 | 100% / 100% |
| M | 24/24 | 0.419 m (c1 → p13) | 0.632 m (c1 → p13) | 0 / 0 | 100% / 100% |
| J | 24/24 | 0.419 m (c1 → p13) | 0.627 m (c1 → p13) | 0 / 0 | 100% / 100% |

**Okno „wspólne”:**
- klatki: 27 540, przyjęte 27 540;
- p50 błędu per przebieg 0.105–0.208 m;
- punkty zgodne: p5 per przebieg co najmniej 139, p50 223–747;
- max błędu przed flagą lotu powtarzającego 0.387 m, po fladze 0.422 m.

**Okno „dalej”:**
- klatki: 24 846, przyjęte 24 846;
- największa przerwa 0.2 s, przerw ponad 1.15 s brak, więc „czas do
  pierwszej przerwy” nie występuje;
- punkty zgodne: p5 co najmniej 134;
- max błędu: c05 0.646 m, c10 0.380 m.

W c05 „dalej” błąd rośnie do 0.65 m przy wciąż setkach punktów. Okno
„dalej” obejmuje jednak tylko 73–146 s epizodu, bo dalej loty
powtarzające się nie ciągną.

## R4 — obciążenie (`r4_S.json`, `r4_M.json`, `r4_J.json`)

Lot NAD2 L_c10_s01, każda łata w osobnym procesie, taskset -c 3, cv2
jednowątkowo. Zamknięcie liczone ×3 na klonach stanu.

| łata | nauka | kadry / KF / wiązania | zamknięcie ms (3×) | max | mapa ms/kl. p50 pierwsze 30 s / ostatnie 30 s (max) | lokalizacja ms p50 / max | VmRSS przed zamkn. / VmHWM MB | klatek w trakcie zamkn. |
|---|---|---|---|---|---|---|---|---|
| S | 100 | 513 / 14 / 1499 | 127, 125, 115 | 127 | 29.5 / 34.5 (68) | 25.9 / 34.2 | 362 / 537 | 1 |
| S | 146 | 743 / 15 / 2163 | 152, 173, 170 | 173 | 29.5 / 34.7 (368) | 26.5 / 38.9 | 537 / 683 | 1 |
| S | 200 | 1013 / 16 / 2998 | 206, 198, 201 | 206 | 29.5 / 36.1 (68) | 26.5 / 37.7 | 683 / 841 | 2 |
| M | 100 | 513 / 14 / 1499 | 156, 163, 154 | 163 | 61.9 / 68.2 (147) | 59.9 / 94.7 | 538 / 900 | 1 |
| M | 146 | 743 / 15 / 2163 | 201, 210, 205 | 210 | 61.9 / 56.7 (1073) | 71.3 / 94.0 | 900 / 1164 | 2 |
| M | 200 | 1013 / 16 / 2998 | 267, 270, 262 | 270 | 61.9 / 86.3 (116) | 64.1 / 94.0 | 1164 / 1510 | 2 |
| J | 100 | 513 / 14 / 1499 | 160, 166, 158 | 166 | 53.4 / 68.4 (177) | 56.1 / 75.8 | 508 / 838 | 1 |
| J | 146 | 743 / 15 / 2163 | 189, 202, 204 | 204 | 53.4 / 65.9 (1179) | 60.0 / 121.8 | 838 / 1125 | 2 |
| J | 200 | 1013 / 16 / 2998 | 255, 235, 231 | 255 | 53.4 / 69.2 (91) | 61.7 / 103.7 | 1125 / 1426 | 2 |

- **Pamięć:** rośnie w procesie przez kolejne długości (klony
  poprzednich zamknięć), więc VmRSS przy 146 i 200 s to górna granica.
- **Wolne klatki fazy mapy (> 200 ms):** wszystkie to nowe klatki
  kluczowe.
  - S: 3, do 0.62 s;
  - M: 6, do 1.81 s;
  - J: 7, do 1.72 s;
  - czas idzie w dopasowania (`ms_dop`), od 16 dopasowań przy 8.–9. klatce
    kluczowej do 145 przy 15.
  Lista z `t_ep` jest w plikach.
- **Czas klatki na M i J:** w renderze ok. 2× wyższy niż na S. W lotach
  S3 z gz różnica wynosiła 2–4 ms przy p50 21–25 ms, więc render M i J
  daje więcej cech niż obraz gz (por. punkty zgodne w R3: M 2–3× S).
  Czasy M i J są tu górną oceną.

## Opcje do PRE (bez wyboru)

- **Długość nauki:**
  - 146 s: zamknięcie ≤ 0.21 s, 743 kadry, 15 KF;
  - 200 s: zamknięcie ≤ 0.27 s, 1013 kadrów, 16 KF, pełny przebieg
    wzoru.
- **Komórka:**
  - c05: promień do 21.5 m (z max 12 cięć 22.2 m), „dalej” max 0.65 m;
  - c10: promień 22.2 m, „dalej” max 0.38 m.
- **Łata lotu długiego:**
  - S: najniższy czas producenta;
  - M: najwięcej punktów zgodnych, najdłuższe klatki kluczowe w fazie
    mapy, do 1.8 s;
  - J: wyniki R3 pośrodku.
- **Do rozstrzygnięcia aneksem:** kolejka 1 i zgubione klatki fazy mapy
  przy późnych klatkach kluczowych (znalezisko R4). To ograniczenie
  przepustowości, nie błędu.

## Liczby do P-TEACH2-R1 … R7 (bez rozliczenia)

- **R1:** wierność p01 i p02 zdana: Δmax −0.009 / +0.002 m, Δp50
  −0.005 / −0.002 m, przyjęte 100%.
- **R2:** pary z warunkiem Ś1: S 24/24, M 24/24, J 24/24.
- **R3:** największy błąd w oknie „wspólne” w 72 przebiegach: 0.422 m.
- **R4:** zamknięcie mapy z nauki 200 s, max z trzech:
  - procesy osobne: S 206 ms, M 270 ms, J 255 ms;
  - pierwszy bieg w jednym procesie: S 214 ms, M 265 ms, J 237 ms.
- **R5:** klatki kluczowe w mapie z 200 s: 16 na każdej łacie (lot
  NAD2). Mapy nauki R3 z ok. 75 s mają 10–12.
- **R6:** zmian w `harness/` i w osłonie nie ma. Zmiany narzędzi jak
  w R1 (generator wahadła, `T_CONT`, kolejka i sędzia lotu długiego;
  driver tylko dla nominału długiego).
- **R7:** przyjęte w oknie „dalej”: S, M i J po 100%, w parach c10 też
  100%.

## Odchylenia od promptu (każde osobno)

1. **Zamknięcie w R3 i R4** przez `Producent._wlacz_do_mapy` (ostatni
   kadr z bufora) i `Producent._zamknij`. To ta sama ścieżka co
   zamknięcie w locie, ale wywołana wprost, a nie klatką z flagą 0.
   W locie klatka z flagą 0 bez podanej chwili odrzuca kadr z bufora,
   a prompt każe zamknąć „po ostatnim kadrze”.
2. **Okno „wspólne”** zawiera też klatki lotu powtarzającego sprzed
   startu epizodu (wznoszenie od 6 m, t_ep < 0). Mapa nauki także
   zaczyna się przed startem epizodu.
3. **Zasięg okna „dalej”:** obejmuje tylko 73–146 s epizodu, bo loty
   powtarzające kończą misję po 110 s kontynuacji. Druga połowa wzoru
   i 600 s nie są tu sprawdzane.
4. **Pierwszy bieg R4** liczył trzy łaty w jednym procesie, więc pamięć
   M i J była skażona poprzednią łatą. Powtórzyłem każdą łatę w osobnym
   procesie i dopisałem listę wolnych klatek. Pierwszy bieg zostaje jako
   `r4_jeden_proces.json`; jego czasy zamknięcia są zgodne (różnica
   ≤ 25 ms).
5. **Pamięć w R4** to VmRSS i VmHWM procesu z klonami stanu, czyli
   górna granica, a nie pamięć samego producenta.
6. **Punkty zgodne p5 / p50** liczone ze wszystkich klatek okna; klatka
   bez dopasowania liczy się jako 0.
7. **Wierność** porównana z wartościami z promptu (p50 0.428 / 0.251).
   Sędzia lotu p01 podaje p50 0.4253 z wszystkich poprawek po fladze,
   co mieści się w tolerancji.
8. **Bez cache cech kadrów.** Każdy przebieg liczy cechy na nowo; budżet
   i tak został dotrzymany.
9. **Zegar:**
   - wierność 0.5 min;
   - R2 < 1 min;
   - R3 12.1 min na 8 procesach;
   - R4 7.5 + 6.5 min na jednym rdzeniu;
   - razem ok. 28 min, w budżecie 60 min.

Kod lotu, osłona, tor, tabela i światy pozostały bez zmian. Nowe pliki
są wyłącznie w `results/TEACH2_RECON/`.
