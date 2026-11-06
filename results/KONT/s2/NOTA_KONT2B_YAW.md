# NOTA przed lotami drogi B (ANEKS_KONT-2): komenda zejścia obraca dron do yaw = 0, a obrót koreluje z odjazdem; loty wstrzymane do decyzji

**Stan:** droga B ratyfikowana przez Olgę, commit 1 `c8118e85` wykonany. Commitu 2 (probe_bf) i lotów nie ma. Budżet bez zmian: S2′ 5/12, noga 21/45. 0 bootów. To nie jest STOP-KONT2f.

## 1. Znalezisko

Zejście komenduje `VelocityNedYaw(0, 0, v_z, 0)` (`results/KONT/tools/kont_s2_probe.py`, pętla zejścia), czyli yaw = 0°. Na orbicie yaw idzie z `cmd["yaw"]`, więc wejście w zejście to skok yaw z heading orbity na 0°. Produkcyjne D5 robi to samo: `r03/gate_run_r03.py:284`, także `bench/bench_flight.py:389`. To nie jest artefakt sondy.

| lot | heading przy zejściu [°] | obrót w 3 s [°] | yaw rate max [rad/s] (orbita p99) | t yaw rate max [s] | t szczytu odjazdu [s] | wektor skoku [m] | rezyduum [m] | v styczna [m/s] |
|---|---|---|---|---|---|---|---|---|
| `c08_s02a_r2` | −124.5 | 123.2 | 2.97 (0.44) | +0.80 | +1.12 | 3.69 | 3.00 | 2.30 |
| `c11_s02_r3` | 50.1 | 51.1 | 1.59 (0.43) | +0.55 | +0.81 | 1.82 | 1.21 | 2.32 |
| `c11_s03_r4` | 116.4 | 112.4 | 2.92 (0.45) | +0.84 | +1.15 | 2.07 | 1.82 | 1.55 |
| `c08_s04_r3` | 138.1 | 134.4 | 3.10 (0.37) | +0.93 | +1.08 | 3.24 | 2.94 | 1.85 |
| `c00_s02_r3` | 55.0 | 56.0 | 1.73 (0.27) | +0.55 | +0.35 | 1.25 | 1.30 | 1.87 |

Korelacje, n = 5 (`results/KONT/s2/d4/d4_yaw.json`, narzędzie `results/KONT/tools/kont_d4_yaw.py`):

| para | Pearson | Spearman |
|---|---|---|
| obrót ~ wektor skoku | 0.84 | 0.80 |
| obrót ~ rezyduum | 0.91 | 0.90 |
| yaw rate ~ rezyduum | 0.87 | 0.90 |
| obrót ~ Δ kanon | 0.58 | 0.70 |
| v styczna ~ wektor skoku | 0.28 | −0.10 |

- W 4/5 lotów szczyt yaw rate wypada przed szczytem odjazdu, wyjątek to `c00_s02_r3`.
- **n = 5 i korelacja, bez mechanizmu.** [MECHANIZM NIEZMIERZONY]: nie wiem, jak obrót przechodzi na pozycję pod przepływem. Sensor przepływu jest blisko osi (`x500_flow/model.sdf:10`: 0.03 m, −0.1 m), więc samo ramię tego raczej nie tłumaczy, ale nie jest to policzone.

## 2. Co to zmienia w ANEKS_KONT-2

- **§3B: „równoczesność jest w danych jedynym wspólnym czynnikiem wszystkich pięciu odjazdów” nie jest prawdą.** Skok yaw też jest wspólny i w przeciwieństwie do prędkości skaluje się z odjazdem.
- **Reguła (a) może zamknąć nogę z fałszywym uzasadnieniem.** `v_ned = (0,0,0)` jako `VelocityNedYaw(0, 0, 0, 0)` zachowuje skok yaw. Jeśli przyczyną jest yaw, lot bf przekroczy kontrolę, a (a) orzeknie „transjent nie był przyczyną ⇒ CLOSED”, nie sprawdzając właściwego czynnika.
- **Moja wada w S2e:** `d4c` mierzył tylko rate roll/pitch, a `rate_max_rad_s` w `d4.json` (do 3.1) obejmował też oś z i tego nie rozłożyłam. §3.2 raportu S2e wskazał przez to hamowanie, bez skoku yaw.
- **W-A zostaje poprawny w brzmieniu prereg** (brak zależności od prędkości). Nie wynika z niego jednak, że odjazd jest nieusuwalną właściwością D5.

## 3. Warianty do decyzji CC i Olgi

| wariant | akcja | co rozstrzyga |
|---|---|---|
| **Y (rekomendacja)** | D5 jak jest, ale yaw trzymany na bieżącym heading | jeden czynnik: yaw. Hamowanie równoczesne zostaje, więc wynik jest jednoznaczny |
| B-yaw | brake-first i trzymanie yaw | najlepsza szansa na mały Δ, ale dwa czynniki naraz: PASS nie powie, który zadziałał |
| B dosłownie | brake-first, yaw = 0 jak ratyfikowano | czysty test hamowania, ale (a) trzeba by przeformułować, bo yaw zostaje niesprawdzony |
| Z | zamknięcie bez lotów | wtedy zdanie kanoniczne powinno nazywać skok yaw jako niesprawdzony |

Każdy wariant poza „B dosłownie” zmienia ratyfikowany tekst, więc wymaga dokumentu. Yaw w D5 dotyka akcji D5: nie sprawdzałam, czy któryś cert zakłada yaw = 0.

## 4. Rozbieżności aneksu z narzędziami (do rozstrzygnięcia przy okazji, niezależnie od wariantu)

1. **`kont_s2_freeze_g.py` „nietknięty” liczy Δ ze wszystkich lotów** (`kont_s2_freeze_g.py:26`), więc da Δ = 2.80 i T* ≤ 4 s zawsze, wbrew regule (b). Propozycja: uruchomić go dosłownie „obok” i dodać kopię `kont_s2_freeze_bf.py` z Δ tylko z nowych zejść.
2. **`kont_d4.py` „bez zmian” ma stałą listę lotów** (`kont_d4.py:13`). Propozycja: nowa nakładka importująca `d4c`, metryka bez zmian.
3. **Okno metryki przy brake-first.** `descent_start` to chwila decyzji, a pionowe zejście zacznie się do 2.5 s później, więc okno 3 s od decyzji prawie nie obejmie odjazdu (+0.8–1.2 s od komendy). Propozycja: `descent_start` przy decyzji (Δ z `kont_s2_analyze.py:109` obejmie wtedy hamowanie, zgodnie z PRE §3 „od REFUSE”), a regułę (a) liczyć dla dwóch okien: od decyzji i od początku opadania.
4. **Launcher `kont_boot_s2d.sh:145` ma wpisany `kont_s2_probe.py`,** a wyjątek z 1d §2.2 już nie obowiązuje, bo ten plik wyprodukował loty. Propozycja: nowe kopie launchera i skryptu bootu.
5. **Kolejka:** `analyze` nietknięty liczy przeskoki także na ziemi, a 1e §2 każe od startu. Propozycja: nowa kopia kolejki filtrująca po czasie startu.
6. **Drogi Z, zdanie kanoniczne: „ε ≤ 2.4 m w 4/5”.** Zmierzone maksima to 1.93, 2.01, 2.49, 2.46, 4.02 m, więc poprawnie **≤ 2.5 m**.

## 5. Dane pomocnicze

- **Próg dla T* ≥ 10 s:** na obecnych krzywych Δ_bf ≤ ok. 1.85 m (T* 15 s przy 1.85 m, 8 s przy 1.90 m). Nowe loty mogą ten próg obniżyć.
- **Koszt bariery przy R_nom 24.83 m:** 6/48 scenariuszy ponad R_nom (`r4_margin.json`).
- **Asercja yaw sprawdzona na danych:** `heading` kontra kwaternion GT z trace daje na ziemi 6.36–6.42° i 20.5° w `c11_s03_r4`, zgodnie z D4a. Próg 10° odsiałby ten lot.

Liczby nie są zamrożone.
