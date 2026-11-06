# RAPORT_KONT_S2 — STOP-KONT2-BUDZET: 1 lot ważny z wymaganych 8, budżet 14/14 wyczerpany

**Diagnoza S2.0:** to nie błąd skali przepływu (s = 1.013 z rzutu, 1.027 ze średnich prędkości; ε(72 s) ≈ 7.1 m to średni błąd prędkości ~0.10 m/s), a źródło dryfu pozostaje nieustalone [MECHANIZM NIEZMIERZONY]; bez STOP-KONT2a, diagnoza przyjęta przez CC.

**Werdykt S2 według PRE §4: BRAK.** Ani „dalej do S3”, ani „CLOSED z liczbą”. Twardy STOP budżetu. T*, R_nom, ε_b i Δ_D5 nie istnieją: PRE §3 wymaga ≥ 8 ważnych lotów.

Ten wynik nie mówi nic o przepływie. 13 z 14 bootów nie wystartowało z powodu awarii przyrządu percepcji, a przepuszczenie budżetu przez 13 identycznych awarii to wada mojej kolejki (§3).

## 1. Tabela lotów

Jedyny lot, który wzbił się w powietrze:

| scenariusz | ważność | ε(0⁺) p95 nominału | ε 10 s | ε 20 s | ε 30 s | ε 60 s | ε 70 s | Δ max | r_GT max | xy_valid | przeskoki |
|---|---|---|---|---|---|---|---|---|---|---|---|
| c08_s02 (`c08_s02a_r2`, ep. 20) | **ważny** | 0.030 m | 0.80 m | 1.34 m | 1.06 m | 1.25 m | 1.83 m | 1.03 m | 22.71 m | całe okno 72 s | 0 |

Ten sam lot: V2′ 0.9584, zegar 0 skoków, test przyrządu PASS, track nauczyciela przed odcięciem 1.000 (mediana błędu 0.37 m), nav 14 do przyziemienia, opóźnienie flagi 0.016 s, zejście z końca okna, kadencja w locie 15.15 Hz, breach 0, REFUSE 0, nominał w powietrzu 56.4 s.

Pozostałe 13 bootów: stos wstał, sonda przed uzbrojeniem ZA_MALO_DANYCH, boot się nie uzbroił, brak ulogu, brak wartości do tabeli:

| boot | nazwa | n_img_cb | n_frames | sim_last [s] | sonda | reinity EKF2 |
|---|---|---|---|---|---|---|
| 1 | c08_s02a_r2 | 3851 | 3827 | 260.3 | PASS 14.71 Hz | 0 |
| 2 | c11_s02 | 575 | **0** | 41.3 | ZA_MALO_DANYCH | 0 |
| 3 | c02_s01 | 566 | **0** | 40.7 | ZA_MALO_DANYCH | 0 |
| 4 | c08_s04 | 571 | **0** | 41.1 | ZA_MALO_DANYCH | 0 |
| 5 | c11_s03 | 583 | **0** | 41.8 | ZA_MALO_DANYCH | 0 |
| 6 | c00_s02 | 570 | **0** | 41.0 | ZA_MALO_DANYCH | 0 |
| 7 | c11_s04 | 571 | **0** | 41.0 | ZA_MALO_DANYCH | 0 |
| 8 | c08_s02b | 581 | **0** | 41.8 | ZA_MALO_DANYCH | 0 |
| 9 | c11_s02_r2 | 568 | **0** | 40.9 | ZA_MALO_DANYCH | 0 |
| 10 | c02_s01_r2 | 576 | **0** | 41.3 | ZA_MALO_DANYCH | 0 |
| 11 | c08_s04_r2 | 573 | **0** | 41.3 | ZA_MALO_DANYCH | 0 |
| 12 | c11_s03_r2 | 572 | **0** | 41.1 | ZA_MALO_DANYCH | 0 |
| 13 | c00_s02_r2 | 571 | **0** | 40.9 | ZA_MALO_DANYCH | 0 |
| 14 | c11_s04_r2 | 570 | **0** | 40.9 | ZA_MALO_DANYCH | 0 |

## 2. Dlaczego 13 bootów nie poleciało

**Zmierzone:**

- Obraz docierał do `percep_proc` (~570 callbacków w ~41 s sim, czyli ~14 Hz), więc most i kamera działały.
- `n_frames = 0` przy `push_frame` p50 ~4.4 ms (16 ms w dobrym boocie). Jedyna droga w `harness/feed_vision.py:156` to `self._own is None`: proces percepcji nie dostał ani jednego stanu własnego z `/fmu/out/vehicle_local_position` lub `vehicle_attitude`.
- PX4 utworzył te same 24 writery XRCE co w dobrym boocie (`px4.log`), `agent.log` ma tę samą treść.
- Awaria jest powtarzalna od drugiego bootu sesji i zdeterminowana: 13/13. Pierwszy boot po restarcie WSL przeszedł.
- Komunikat „POD PODŁOGĄ” i powód „brak odcięcia, ulogu albo pętli” w `kampania.log` są mylące: kadencja nie była niska, klatek było zero.

**Niezmierzone [MECHANIZM NIEZMIERZONY].** Kandydaci, żaden niesprawdzony bootem:

1. **Zalegające segmenty FastDDS SHM po `kill -9`.** Boot 1 ruszył na pustym `/dev/shm` (WSL wstał 09:20), a każdy kolejny na plikach `fastrtps_*` po poprzednim. Port 7415 ostatnio dotknięty w boocie 1 (09:34:20), w kolejnych tylko 7000/7411/7413 (`shm_po_kampanii.txt`). Przeciw: WK3 i SKAN2 latały boot po boocie w jednej sesji z tym samym sprzątaniem i miały klatki, a nie wiem, jaki był wtedy stan `/dev/shm`.
2. **Wyścig kolejności startu.** W boocie 1 PX4 ma inną kolejność startu niż w boocie 2 (`lockstep_scheduler` i `Startup script` zamienione miejscami, `px4.log`), bo przy zimnym dysku stos wstaje wolniej. Most i percepcja startują przy pojawieniu się topicu gz, czyli w innej fazie względem agenta.

Sieroty (§3) nie są przyczyną: boot 2 padł po czystym zakończeniu bootu 1, kiedy żadnej jeszcze nie było.

## 3. Wady po mojej stronie

- **Kolejka nie zatrzymała się po powtarzalnej awarii.** Wzorzec, z którego kopiowałem (`perc2_s2_boot.sh`), mówi wprost: „drugi FAIL z rzędu egzekwuje wołający”. `kont_s2_campaign.py` tej reguły nie ma. Z nią kampania stanęłaby po boocie 3, przy budżecie 3/14. Koszt: ~11 bootów i ~75 min.
- **Nie patrzyłem w trakcie.** Czekałem na `kampania.json`, a nie na `kampania.log`, więc awarię z 09:46 zobaczyłem o 11:16.
- **Sieroty.** Ścieżka kill przy „pod podłogą” zostawiała `infra2_ekf_watchdog.py` (żył do ~15 min, sondował PX4 kolejnych bootów, tryb odczytu, reinity 0 we wszystkich 14) i `rtf_sampler`. Ostatnie trzy ubiłem TERM o 11:17, po końcu kampanii. Pliki `ekf_watchdog.json` tych bootów mają próbki z późniejszych bootów i nie nadają się na dowód.
- **Podczas sprzątania** moje `pkill -f` zabiło własną powłokę diagnostyczną (exit 144). Bez skutków dla danych.

## 4. Liczby n = 1: opis, nie zamrożenie

**`kont_s2_freeze.py` NIE został uruchomiony**, wbrew dosłownemu poleceniu „po lotach zamrożenie”. Skrypt nie ma strażnika liczby lotów i wydałby T* i R_nom z jednego lotu w `s2_freeze.json`, przy PRE §3 wymagającym ≥ 8. Decyzja jest do cofnięcia jednym poleceniem, skrypt jest gotowy.

Krzywa ε(t) lotu `c08_s02a_r2`: `c08_s02a_r2/wyniki.json` → `koszyki`. Maksimum ε w oknie 1.93 m przy 71 s.

**Dwie rzeczy dla CC, bez wniosków:**

- ε(72 s) 1.93 m wobec 7.09 m w S1 przy tej samej kopii modelu, ale FEED=V2 zamiast B, inny epizod, inna wysokość. Rozrzut lub zależność od warunków: nierozstrzygalne z n = 1. Oceny z ANEKS_KONT-1 §3 ten lot ani nie potwierdza, ani nie obala.
- **R-2: przesunięcie pionowe się nie powtórzyło.** `z_off_m = −0.03` (okno 6.04 s, n = 125) wobec +1.835 m w S1 bootB. Kompensacja zadziałała, ale prawie nic nie korygowała; orbita GT z = 12.0 m jak w kanonie.

Rzecz do sprawdzenia: koszyk 0 ma ε 0.107 m przy p95 nominału 0.030 m, więc ε(0⁺) z dosłownego p95 nie pokrywa pierwszej sekundy. Regułę ε_b ten koszyk i tak pokrywa przez obwiednię.

## 5. Rozliczenie predykcji

- **P-KONT-3 (T* ≥ 30 s, 0.55): nierozstrzygnięta.** Brak T*.
- **P-KONT-4: nierozstrzygnięta.** Brak R_nom i kosztu bariery.
- **R-5 (nominał ≥ 60 s łącznie): niespełniony.** 56.4 s w jedynym locie, 0 przeskoków cs_gnss_pos.

## 6. Budżet, zegar, stan

- **Budżet S2: 14/14** (1 lot ważny + 13 bez uzbrojenia). Liczę dosłownie, bo stos wstawał. Budżet nogi: 2 (S1) + 14 = 16/33.
- **Boot nieliczony:** `c08_s02a` z 01:44. Host wyłączony (`systemd-poweroff` 01:45:07), 6.7 s po starcie, stos nie wstał, brak px4.log. Katalog zostaje jako dowód.
- **Zegar:** 14/14 próbników 0 skoków. timesyncd stop na czas kampanii, po niej `active` (`zegar_stan_po.txt`).
- **Twarde STOPy:** breach 0, REFUSE(POS) poza scenariuszem 0, przeskoki 0. Zadziałał tylko budżet.
- **`/dev/shm` nieczyszczony,** stan zapisany w `shm_po_kampanii.txt`. Restart WSL go wyczyści.
- **Nie dotknięto** kont_frames.py, certów, kodu osłony, parametrów EKF2 ponad trzy z kont_config. Push = Olga.

## 7. Decyzje nieprzesądzone przez prompt

- Nauczyciel `OrbitExecutor` podłożony pod kanon `net_skan2` przez lokalną podmianę nazwy.
- Okno 72 s (prompt: ≥ 60 s).
- ε(0⁺) = 1.5 × max p95 nominału (dosłownie R-1b, nie wariant addytywny).
- Próg tracka nauczyciela ≤ 3.0 m (`E_TRK_MAX`): mój.
- `kont_s2_campaign_r.py` to kopia kolejki z jedną zmianą, licznikiem prób, stąd nazwa `c08_s02a_r2`.

## 8. Do rozstrzygnięcia przez CC / Olgę

1. Czy 13 bootów bez uzbrojenia liczy się do budżetu S2. **Rekomendacja:** nie do wykonania bez nowego budżetu w aneksie. Kontynuacja S2 wymaga decyzji, sam jej nie podejmuję. Budżet nogi pozwala na nią (17 bootów zapasu).
2. Czy `c08_s02a_r2` zostaje jako lot 1/8. **Rekomendacja:** tak, spełnia wszystkie warunki ważności.
3. Warunki wznowienia. **Rekomendacja:** kolejka zatrzymana po 2 kolejnych FAIL sondy, strażnik n ≥ 8 w `kont_s2_freeze.py` (nowa kopia), sprzątanie sierot, oraz jeden boot diagnostyczny na czystym `/dev/shm` przed lotami, żeby rozdzielić kandydatów z §2.

**Liczby tego raportu nie są zamrożone** — zamraża je ANEKS_KONT-2 od CC po przeliczeniu z repo.

STOP.
