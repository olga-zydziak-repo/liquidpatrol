# STOP-TEACH-2-FLAGA — S2: świat i oba cienie zaliczone; STOP przed smoke — chwila flagi w kodzie lotu jest w czasie epoki, nie w czasie sim

17.11.2026 · wykonawca · PROMPT_TEACH_S2 (sha256 39de0cdf) z ANEKS_TEACH-2 (sha256 878fce80, „ratyfikuję TEACH-2”). **Booty nogi: 4 / 24** (S2: 4 / 7 — ST1, ST2, C1, C2; jeden nieważny stanowiskowo, niepoliczony).

**Werdykt: STOP przed bootem SM (§5: zmiana kodu lotu poza §1 ⇒ STOP przed zmianą).**

- **Świat (ST1/ST2):** PASS. Kamera misji i przepływu identyczne piksel w piksel, lidar bez różnicy. Świadek statyczny: ST1 15 detekcji zgodnych z manifestem, ST2 0.
- **Cień C1 (łata S, c05) i C2 (łata J, c10):** bramka obrazu spełniona za pierwszym razem:
  - max błąd przyjętej poprawki 0.49 / 0.36 m;
  - przyjęte 100% / 100% kadrów okna;
  - 0 / 0 detekcji zgodnych z manifestem.
- **Usterka:** sprawdzian F1 na żywo pokazał, że chwila flagi, którą `harness/nadir_obs.py` bierze z `m.timestamp` wiadomości `/fmu/out/estimator_status_flags`, jest w czasie epoki (np. 1 794 869 493.39 s przy sim 105.8 s), a nie w czasie symulacji. W locie z cięciem producent przyjąłby tę liczbę jako chwilę flagi i t_fix łańcucha. τ wyszłoby ujemne (≈ −1.8·10⁹ s), więc bramka przyjęcia odrzuciłaby każdą poprawkę i osłona zatrzasnęłaby REFUSE(τ*) po 2.05 s. Tryb cienia tego nie widzi (chwila z env), próba na sucho też nie (podawała czas sim). Naprawa to zmiana kodu lotu, więc decyzja należy do CC.

## §2 — bramka (po ANEKS_TEACH-2)

| commit | treść |
|---|---|
| `54e4ebec` [CO-TEACH-2A] | ANEKS_TEACH-2 verbatim w korzeniu (byte-check 878fce80), §5 do KSIĘGI (14 linii); bramka origin = `e0ac58f6` |
| `8f902dd0` [S2-SUCHO-2A] | §4.3: analizator ze świadkiem „zero detekcji zgodnych z manifestem” |

Sprawdziany §4.3:
- **p01 NAD3:** 3932 detekcje zgodne (= liczba CC, różnica 0%), odległość p95 0.025 m, max 0.069 m.
- **Recon 32 937 kadrów:** 22 surowe, **0 zgodnych**.

**Próba na sucho §2.6 powtórzona w całości: PASS.**
- Lot syntetyczny ważny: 2 detekcje surowe, 0 zgodnych.
- B1–B4 OK, max e′/U′ 0.27.
- Producent z `NADIR_FLIP=0` jak w boocie.

## Świat — ST1, ST2 (`teach_st.py` ⇒ `st1/`, `st2/`, `st_porownanie.json`, commit `5cfbf3c2`)

**Boot statyczny** = serwer gz bez PX4 (ta sama konfiguracja co stos: `env_gpu.sh`, `gz_env.sh`, `gz sim -r -s`). Dron jest wstawiony usługą `create` jako model statyczny (kopia `model.sdf` z `<static>true</static>`). Poza (25, 0, 11) m, kurs 0, nad znacznikami 31 i 35. Po 4 s sim zapisane po 3 klatki każdej kamery i 3 pomiary lidaru.

| | ST1 (x500_nadir2_flow, world_nadir2_A3) | ST2 (x500_teach_flow, world_teach_S) | różnica |
|---|---|---|---|
| kamera misji 640 × 480 | 3 klatki | 3 klatki | 0 pikseli różnych (3/3) |
| kamera przepływu 100 × 100 | 3 klatki | 3 klatki | 0 pikseli różnych (3/3) |
| lidar | 11.18075 m | 11.18075 m | 0.00000 m (≤ 0.002) |
| kamera w dół | szachownica, znaczniki, bryły | teren łaty S i bryły | — |
| detekcje zgodne z manifestem | **15** (ID 30, 31, 32, 35, 36 × 3) | **0** (surowych 0) | świadek OK |

- ST3 zbędny.
- **ST1, pierwsza próba** (`st1_niewazny_1/`): nieważna stanowiskowo, przed jakimkolwiek pomiarem. Przyrząd nie ustawił `GZ_IP=127.0.0.1`, który boot ustawia; zegar ani klatki nie dotarły do klienta, zebrano 0 klatek. Poprawiony przyrząd, jedna powtórka zgodnie z §5; próba nie liczy się do budżetu.

## Cień — C1, C2 (`teach_s2_run.py`, `teach_s2_cien.py` ⇒ `<boot>/cien_s2.json`)

**Stanowisko:**
- bramka zdrowia A GO (tempo 0.931 / 0.938);
- próbnik zegara 0 skoków (timesyncd zatrzymany na sesję);
- tempo w boocie 0.962 / 0.976;
- rc 0, breach 0;
- driver: producent zgodny (meta TEACH, tor 0ffd62e3…, cień prawda, bez `nad3`).

Rejestrator kadrów: 226 / 229 kadrów na stanowisku (`~/teach_stanowisko/`), po 6 w `<boot>/kadry/`.

| | C1 (S, c05, T 173.6) | C2 (J, c10, T 176.5) |
|---|---|---|
| okno [cień, koniec misji] | 173.6–212.16 s, 193 kadry | 176.5–216.22 s, 199 kadrów |
| **bramka: max błąd ≤ 1.00 m** | **0.486 m** | **0.360 m** |
| **bramka: przyjęte ≥ 90%** | **100%** (193) | **100%** (199) |
| **bramka: zgodne z manifestem = 0** | **0** (surowych 0) | **0** (surowych 0) |
| błąd p50 / p95 / max [m] | 0.339 / 0.422 / 0.486 | 0.166 / 0.318 / 0.360 |
| przerwy max / > 1.15 s | 0.2 s / 0 | 0.2 s / 0 |
| mapa: kadry / klatki kluczowe / wiązania (przyjęte) | 180 / 9 / 540 (540) | 191 / 10 / 573 (573) |
| reszta kursu klatek kluczowych p50 / max | 1.73° / 2.48° | 0.99° / 1.23° |
| reszta środka klatek kluczowych p50 / max | 0.18 / 0.25 m | 0.09 / 0.19 m |
| zamknięcie (od klatki flagi) | 67 ms | 70 ms |
| czas kadru: mapa p50 / p95 / max [ms] | 23.2 / 28.1 / 42.8 | 22.9 / 27.2 / 56.4 |
| czas kadru: lokalizacja p50 / p95 / max [ms] | 10.9 / 12.9 / 16.1 | 12.6 / 14.5 / 15.6 |
| klatki zgubione (n_drop) | 0 z 1094 | 0 |
| opóźnienie pierwszej poprawki | 0.0 s | 0.1 s |
| piksele nieruchome (38 / 37 kadrów rozstawionych ≥ 3 m) | 0.0% | 0.0% |

**Sprawdzian F1 na żywo** (wiersze `gnss_rz`, `t_flagi_rz`):

| | C1 | C2 |
|---|---|---|
| brak wiadomości | do 13.8 s | do 12.2 s |
| 1 | 14.6 s | 13.0 s |
| 0 | 65.6 s | 66.4 s |
| 1 | 68.0 s | 69.0 s |
| 0 | 105.8 s | 106.8 s |
| 1 | 107.2 s | 108.4 s |

- Pierwsza wiadomość to 1. Dwa spadki to restarty EKF (ok. 66 s i ok. 106 s, przedlot).
- Zatrzask w chwili startu (127.7 / 128.6 s) skasowany.
- Zamknięcie mapy jedno, w chwili cienia (173.6 / 176.6 s).

**F1 działa zgodnie z literą co do zdarzeń, ale `t_flagi_rz` przy spadkach to 1 794 869 451.44 / 1 794 869 493.39 (C1) i 1 794 870 099.45 / 1 794 870 140.98 (C2), czyli czas epoki.**
- Przesunięcie epoka − sim wynosi 1 794 869 387.6 s w C1 i 1 794 870 034.2 s w C2. Różni się między bootami o czas ścienny, więc pochodzi z zegara agenta: klient uXRCE-DDS synchronizuje stemple z agentem, a stemple w ULG są w czasie PX4.
- Analizator i ważność lotu liczą flagę z ULG (czas sim), więc ocena nie jest dotknięta. Dotknięty jest wyłącznie producent w locie.

**Skutek w locie z cięciem** (`harness/teach_map.py`, ścieżka zamknięcia):
- tf = t_flagi ≈ 1.79·10⁹;
- kadr z bufora wchodzi do mapy (sim < tf), także gdyby leżał po prawdziwej fladze;
- t_flag = t_fix łańcucha ≈ 1.79·10⁹, więc τ = t − t_fix ≈ −1.79·10⁹;
- warunek 1.5 + 3τ < 0 odrzuca każdą poprawkę;
- datagram ma Δ = 0 i t_fix = None, osłona liczy τ od wejścia w utratę i daje REFUSE(τ*) po 2.05 s.

Bezpieczeństwo trzyma (B1 na czystym EKF, τ < 2.05 s), ale smoke byłby bezwartościowy, a S3 pustym wynikiem negatywnym.

**Pytanie do CC — możliwe naprawy, każda w kodzie lotu (`harness/nadir_obs.py`), bez rozstrzygania:**
- **N1:** chwila flagi = czas sim w chwili nadejścia wiadomości (subskrypcja zegara gz `/world/<W>/clock` w `nadir_obs`, opóźnienie rzędu ms);
- **N2:** chwila flagi = czas sim pierwszej klatki obrazu po nadejściu wiadomości (bez nowej subskrypcji, opóźnienie ≤ 0.2 s; kadr w buforze sprzed spadku liczony względem tej chwili);
- **N3:** przeliczenie stempla przez przesunięcie epoka − sim mierzone na bieżąco (np. z `vehicle_local_position.timestamp` i czasu klatki).

Sprawdzian, który by to złapał bez bootu: próba na sucho z flagą podawaną stemplem epoki, a nie czasem sim.

## Smoke — nie wykonany

STOP przed bootem SM. Narzędzie oceny smoke (replay, przeliczenie poprawek i georeferencji z wierszy) nie jest napisane — zbędne przed decyzją.

## Liczby do predykcji (bez rozliczenia)

- **P-TEACH-3** (boot statyczny — kamera przepływu i misji piksel w piksel jak w starym świecie, zero detekcji znaczników w kamerze w dół): 0 pikseli różnych w obu kamerach (3/3 klatek); kamera w dół ST2: 0 detekcji surowych, 0 zgodnych.
- **P-TEACH-4** (oba booty cienia przechodzą bramkę obrazu za pierwszym razem): C1 PASS (0.486 m, 100%, 0), C2 PASS (0.360 m, 100%, 0).
- **P-TEACH-5** (zero przekroczeń przesłanki w smoke i 12 cięciach, max e′/U′ ≤ 0.60): smoke nie poleciał.

## Odchylenia (nazwane)

1. **Boot statyczny bez PX4 i z modelem statycznym** (`teach_st.py`), a nie przez launcher lotu. Poza ustawiona z góry, nad znacznikami (ANEKS_TEACH-2 §3.4). Przyrząd nazwany w commicie `5cfbf3c2`.
2. **Pierwsza próba ST1 nieważna przez przyrząd** (brak `GZ_IP`). Policzona jako nieważna stanowiskowo przed pomiarem, powtórzona raz.
3. **Chwile cienia z promptu** (173.6 / 176.5 s). Mapa zamknięta w C2 w 176.6 s, czyli przy pierwszej klatce ≥ 176.5.
4. **Okno oceny cienia:** koniec misji = ostatni tick epizodu w fazie approach / hold / orbit bez zejścia (`rama.jsonl`).
5. **Piksele nieruchome:** kadry rejestratora z wysokości ≥ 6 m, rozstawione ≥ 3 m; piksel nieruchomy, gdy odchylenie jasności < 2.0. Udział 0.0% w obu cieniach, maska zbędna.
6. **Reszta kursu klatki kluczowej** liczona wobec błędu kursu EKF w chwili klatki (θ_k ma go znosić), reszta środka wobec punktu pod kamerą z pozy GT.
7. **Do repo idą** katalogi bootów C1 / C2 bez `boot.ulg` i gniazd (wzór NAD3), 6 kadrów na boot w `kadry/` i kadry ST. Kadry rejestratora zostają w `~/teach_stanowisko/`.
8. **Poprzedni raport STOP-TEACH-2-SUCHO** przeniesiony do `STOP_TEACH_2_SUCHO.md`.
9. **timesyncd zatrzymany** na czas sesji bootów (bramka zdrowia go wymaga), przywrócony po STOP.

Sieć: żadna. Bez pushu.
