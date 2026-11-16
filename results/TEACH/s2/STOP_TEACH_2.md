# STOP-TEACH-2-SUCHO — S2 zatrzymany na próbie drivera na sucho (§2.6), 0 bootów: warunek „zero detekcji znaczników” łamią fałszywe detekcje ArUco na samej teksturze terenu

16.11.2026 · wykonawca · PROMPT_TEACH_S2 (sha256 39de0cdf PASS z wklejki). **Bootów nogi: 0 / 7.**

**Werdykt: STOP przed pierwszym bootem (§2.6: niepowodzenie próby na sucho ⇒ STOP bez bootu).** Poprawki F1–F3 są zrobione, zielone i w commicie. Próba na sucho przechodzi start drivera, odmowy, blok zgodności producenta, strażnik boota i epizod cienia. Epizod lotu przechodzi B1–B4, ale analizator unieważnia go jedynym warunkiem: „zero detekcji znaczników”.

Na kadrach z samą ortofotomapą (bez żadnych znaczników) detektor bootu zgłasza pojedyncze fałszywe znaczniki. Na kadrach reconu wychodzi:

| łata | detekcje / kadry | cięcia z ≥ 1 detekcją | ID | bok |
|---|---|---|---|---|
| S | 15 / 10 979 | 5 z 12 | 17, 37 | ≤ 13.4 px |
| M | 4 / 10 979 | 2 z 12 | 17 | ≤ 3.6 px |
| J | 3 / 10 979 | 1 z 12 | 17, 37 | ≤ 14.8 px |

Żadna nie ma boku ≥ 16 px, czyli żadna nie przeszłaby litery przyjęcia znacznika Rama NAD2 (bok ≥ 16 px). Według litery PRE §6 (ważność lotu) i bramki obrazu §4 (zero detekcji w całym boocie) na łacie S 5 z 12 cięć byłoby nieważnych z powodu tekstury, nie znaczników. Rozstrzygnięcie kryterium należy do CC. Kodu nie zmieniałem.

## §0 / §2 — bramka

| punkt | stan |
|---|---|
| §2.1 | origin/master = HEAD = `9808a8be`; drzewo czyste poza zastanymi |
| §2.2 | sha256 promptu 39de0cdf… = suma Olgi |
| §2.3 | **[S2-KSIEGA] `eeb8bcfd`** — §7 do KSIĘGI (19 linii), append-only, verbatim |
| §2.4 | §1 zielone ⇒ **[S2-POPRAWKI] `34fd058b`** |
| §2.5 | `teach_certs_selfcheck` 24/24 PASS; sumy tabeli (7a56ba1b…, w strażniku boota), `tor.json` (suma wewnętrzna zgodna, wariant K), światów S/M/J i modelu = `results/TEACH/s1/swiaty.json` |
| §2.6 | **FAIL** — epizod lotu nieważny (opis niżej) |

## §1 — poprawki (commit `34fd058b`)

**F1 — chwila flagi** (`harness/nadir_obs.py`):
- chwila flagi = czas ostatniego spadku `cs_gnss_pos` z 1 na 0; pierwsze 0 bez wcześniejszej 1 nie jest spadkiem;
- powrót do 1 przed zamknięciem mapy kasuje zatrzask;
- przed pierwszą wiadomością flaga nieznana;
- w trybie cienia wiersz niesie `gnss_rz` i `t_flagi_rz`;
- logika wydzielona do funkcji modułu `teach_flaga(cs, t)`, wołanej przez subskrypcję (żeby dało się ją testować bez ROS).

**F2 — pusta mapa się nie zamyka** (`harness/teach_map.py`): klatka w utracie przy mapie bez żadnego kadru ma fazę „przed_mapa”. Dotyczy to także sytuacji, gdy w buforze leży kadr z czasem ≥ chwila flagi — taki kadr jest odrzucany (odchylenie 1).

**F3 — wiązania w rejestrze:** `georef.wiazania` = [czas kadru, klatka kluczowa, r_E, r_N, zgodne, przyjęte] dla wszystkich wiązań.

**Sprawdziany po zmianach:**
- `test_teach_s2.py` 6/6:
  - 0 od początku → 1 → mapa → spadek: jedno zamknięcie przy spadku, mapa niepusta, wiersze sprzed mapy „przed_mapa”/„mapa”;
  - 0 przez cały czas: zero zamknięć, zero poprawek, zatrzask pusty;
  - restart EKF 0 → 1 → 0 → 1 → mapa → 0: zatrzask na spadku przy restarcie, skasowany powrotem, zamknięcie przy ostatnim spadku;
  - bufor niepusty zamyka mapę jednym kadrem, bufor po fladze nie zamyka;
  - F3: lista wiązań = wiązania producenta;
  - cień niesie flagę rzeczywistą.
- `test_teach_s1.py` 10/10.
- W1-obs: wynik identyczny z S1 (plik `w1_obs.json` bajtowo równy).
- W2 łata S, 13 lotów: 13/13 zgodne z reconem; części równe częściom S1 (klatki, θ_k, t_k).
- Nowe sumy:
  - `harness/nadir_obs.py` 74f962ab8e92695935063d55c78cf9b4c6723525471c73526aedbe87e158dbfd;
  - `harness/teach_map.py` c6cbff8faa73f8484a31cd7f6f97d5bb88c0094ba3241986b79004b6e6021b4f.

## §2.6 — próba na sucho (`teach_s2_dryrun.py` ⇒ `dryrun/dryrun_s2.json`)

**(1) `teach_flight.main()`** przez atrapy `kont_s4_dryrun_c.py` (ścieżka drivera podmieniona):

| przypadek | wynik |
|---|---|
| start | dochodzi do uzbrojenia; selfcheck TEACH PASS; meta `teach` z sumą tabeli TEACH |
| bez `TEACH_MODE` | kod 8 |
| tabela P1 NAD3 | kod 8 |
| bez `NADIR_OSLONA` | kod 8 |
| zła suma (kontrolnie) | kod 42 |

**PASS.**

**(2) Blok zgodności producenta** — dosłowny tekst z drivera, 9 przypadków:
- lot ⇒ start;
- cień bez datagramów ⇒ start;
- kod 9 dla:
  - datagramu Rama;
  - meta z `nad3`;
  - innej sumy toru;
  - meta cienia przy locie;
  - meta lotu przy cieniu;
  - meta bez litery TEACH;
  - lotu bez datagramów.

**PASS.**

**(3) Producent i strażnik:**
- `nadir_obs` kody 47 i 48;
- strażnik `teach_boot.sh` pod `bash -uo pipefail` daje kod 5 przed czymkolwiek ciężkim dla:
  - zmiennych: łata X / pusta, cień 2, cień bez T, maska bez pliku;
  - trybu: NM 0, PT 1;
  - etapu s9;
- poprawne kombinacje (lot i cień 173.6) dochodzą do kontroli profilu FastDDS;
- `bash -n` OK.

**PASS.**

**(4) Epizody syntetyczne z flagą w sekwencji bootu.** Proces `nadir_obs` (gałąź TEACH) dostaje każdą klatkę lotu NAD3 od 13 s sim, z renderem łaty S przy pozie GT. Flaga idzie przez `teach_flaga`:
- przed logiem ULG: 13 s → 0, 20 s → 1, 107.092 s → 0 (restart EKF, `kont_ekf_preflight.json`), 115 s → 1;
- potem zmiany z ULG.

**Cień** (p05 nominał, T 173.6) — **PASS:**
- 1239 klatek, wysłane 0 datagramów;
- jedno zamknięcie w 173.6 (175 kadrów mapy, 10 klatek kluczowych), 433 przyjęte poprawki w rejestrze;
- flaga rzeczywista w wierszach: 13.0 → 0, 20.0 → 1, 107.2 → 0 (zatrzask 107.092), 115.0 → 1;
- zatrzask w chwili startu skasowany.

**Lot** (p01, cięcie 173.696) — **FAIL ważności:**

| miara | wartość |
|---|---|
| klatki / datagramy | 1483 / 1483 |
| fazy przed startem | {przed_mapa, mapa} |
| zatrzask w chwili startu | skasowany |
| zamknięcie | jedno, w 173.8 |
| chwila flagi producenta | 173.696 = spadek ULG |
| wejście osłony w utratę | 173.796 |
| mapa | 176 kadrów, 9 klatek kluczowych, 528 wiązań w rejestrze |
| poprawki przyjęte | 586 |

- Analizator na pętli otwartej (rama odtworzona `nad3_krok` z datagramami TEACH):
  - B1 / B2 / B3 / B4 OK, max e′/U′ 0.27, D1 dostępne;
  - błąd poprawki p50 / p95 / max 0.36 / 0.58 / 0.68 m;
  - opóźnienie pierwszej poprawki 0.104 s, max przerwa 0.2 s, zamknięcie 64 ms.
- **Ważność: fałsz, powód `zero_detekcji_znacznikow`:**
  - 3 detekcje: ID 17 (bok 2.24 px), ID 17 (5.83 px), ID 37 (7.07 px);
  - trzecia przez próbę lustra (atrapa bez `NADIR_FLIP=0`; boot ustawia 0, więc ta jedna to artefakt próby);
  - dwie pierwsze — bez lustra, jak w boocie.

**Skan tekstury** (`teach_s2_aruco_tekstura.py` ⇒ `dryrun/aruco_tekstura.json`): detektor bootu (DICT_4X4_50, parametry domyślne, bez lustra) na wszystkich 32 937 kadrach reconu daje liczby z tabeli w pierwszym akapicie. Szczegóły:
- detekcje głównie po cięciu: S 14, M 3, J 3;
- w locie długim: S 6, M 2, J 2.

Teren w gz ma tę samą teksturę, więc tego samego trzeba się spodziewać w bootach C1, C2, SM i w bramce S3.

**Pytanie do CC (bez rozstrzygania):** warunek ważności PRE §6 i bramka obrazu §4 brzmią „zero detekcji znaczników”. Świadek tezy ma pokazać, że lot nie używa znaczników. Znaczniki są w tych światach niewidoczne z maski (flagi 4 wobec maski 8), a zmierzone detekcje to tekstura o boku 2–15 px. Możliwe brzmienia do decyzji CC, każde z liczbą do wyliczenia przed bootem:
- zero detekcji z bokiem ≥ 16 px, czyli progiem litery NAD2;
- zero detekcji przyjętych literą Rama NAD2 (ID z manifestu, stożek, bok, reszta do pozycji manifestu);
- zero detekcji w kadrze statycznym ST2 nad samymi znacznikami i liczba detekcji w lotach tylko jako obserwabla.

## Odchylenia (nazwane)

1. **F2 szerzej niż litera:** „pusty bufor” obejmuje też bufor z kadrem z czasem ≥ chwila flagi (taki kadr i tak nie wchodzi do mapy), żeby nigdy nie powstała mapa pusta.
2. **F1:** logika flagi w funkcji modułu `teach_flaga` zamiast ciała callbacku — jedyne wywołanie z subskrypcji, zachowanie jak w literze. Wiersz poza TEACH bez zmian (W1-obs).
3. **Próba na sucho:**
   - epizody syntetyczne zrobione wzorem `nad3_s2_dryrun` (prawdziwy kod producenta w procesie `nadir_obs` i prawdziwa ścieżka osłony `nad3_krok`), a nie przez `main()` drivera prowadzony przez epizod;
   - `main()` sprawdzony do uzbrojenia, jak w NAD3;
   - kody 47 / 48 to kody procesu producenta, nie drivera.
4. **Sekwencja flagi przed logiem ULG** złożona z faktów bootu (13 s, GPS po higienie przyjęty w 20 s, restart 107.092 s, powrót 115 s). Log ULG zaczyna się przy uzbrojeniu (140 s), więc dokładne chwile 20 s i 115 s są przyjęte, nie zmierzone.
5. **Atrapa nie ustawia `NADIR_FLIP=0`**, stąd jedna detekcja lustrzana w epizodzie lotu. Skan tekstury liczony bez lustra, jak w boocie.
6. **Strażnik boota nie sprawdza sum światów i modelu.** Launcher porównuje model z kopią w PX4 (`cmp`) i zapisuje hash świata. §2.5 sprawdzone tu wobec `swiaty.json`, bez zmiany boota.

0 bootów. Sieć: żadna. Bez pushu.
