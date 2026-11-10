# DIAGNOZA_STANOWISKA — ANEKS_NADIR-3 §3 + test przyrządu (sygnał CC 10.11): dzisiejsze sondy zaniżał zegar (timesyncd wznowiony przez kolejkę), maszyna po korekcie zdrowa, nowa sonda czyta ~0.05 niżej od przyrządu 9.11

Wykonawca · 10.11.2026 · łańcuch NADIR, po CO-N3 `42428887`. **0 bootów** (żadna próba nie startowała PX4 ani niczego nie uzbrajała). Księga S4 bez zmian: 5/19, noga 16/30.

## 1. Najważniejsze

1. **Dzisiejsze pomiary tempa sond są zaniżone przez skoki zegara ściennego, nie przez maszynę.**
   - Zegar realtime skacze o **+1.3–1.5 s co ~32–34 s**. Pomiar kontrolny realtime−monotonic, 75 s: skoki +1.352 i +1.315 s.
   - `acts.rtf_sampler` liczy ścianę z `time.time()`, więc każdy skok zawyża Δwall. Przy oknie 120 s to 3–4 skoki, czyli ok. 4%.
   - Przyczyna: **`systemd-timesyncd` aktywny od 07:30:44**. Zatrzymałam go o 07:22 przed kolejką, ale kolejka S4 przy końcu (`kont_s2_campaign_g.py:238`, wspólne z `kont_s4_campaign.py:196`) zawsze go uruchamia z powrotem. STOP-NADIR4-STANOWISKO-2 nastąpił o 07:30:44 i wtedy timesyncd wrócił. To ten sam mechanizm co w lekcji „Dryf zegara WSL” z 02.11.
   - Odniesienie 9.11 mierzono przy `timesyncd: inactive` (`results/NADIR/s1/n1/ab_kadencja.json`), a boot kampanii idą przy zatrzymanym timesyncd. Skoków nie mają ani `rtf_stream.jsonl` bootów S4, ani odniesienie.
2. **Po korekcie skoków maszyna jest dziś zdrowa:** oryginalny przyrząd A (`nadir_n1_ab.run`, rig A_5, 120 s) daje **0.937 / 0.920**, a odniesienie 9.11 to 0.9285 / 0.9277.
3. **Nowa sonda B czyta systematycznie niżej od przyrządu A**, także po korekcie: **0.867 / 0.874**, czyli ok. −0.05. Telemetria hosta tego nie tłumaczy, bo C (A z samą telemetrią) daje 0.924 / 0.909. Różnicy między A i B nie rozłożyłam: rig, świat, spawn, konsumenci i próbnik są te same. **Mechanizm niezmierzony.**
4. **Chorego stanu bootów (0.73–0.78) dziś nie odtworzono.** Żadna komórka matrycy go nie wywołała:
   - profil OEM turbo / wydajny, operator aktywny, terminal w tle, 30 min bezczynności;
   - częstotliwość procesorów stała przez cały dzień (mediana PercentofMaximumFrequency 94–98%);
   - w czołówce procesów Windows nic obciążającego (PredatorSense ≤ 0.4%);
   - GPU bez zmian powodów dławienia.
   Spowolnienie bootów z 9.11 21:21 i 10.11 07:27 jest prawdziwe: ich `rtf_stream` nie ma skoków, a dsim/dwall jest równo niski. Jego mechanizm pozostaje niezmierzony.

## 2. Stanowisko (§3.1(d), `stanowisko/sesja_20261110_093014.json`)

| | |
|---|---|
| Procesor | Intel Core Ultra 9 275HX, 24 rdzenie, 24 wątki (hybrydowy: 8 P + 16 E) |
| Windows | 11 Pro 10.0.26200 (build 26200.9711) |
| WSL | 2.7.10.0, jądro 6.18.33.2-2, WSLg 1.0.73.2 |
| GPU | RTX 5070 Ti Laptop, sterownik 577.13 (Windows 32.0.15.7713, data 2025-08-25); render gz = `D3D12 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)` (glxinfo -B w każdej sondzie); det_v2 = cuda |
| Zasilanie | zasilacz (BatteryStatus 2), 100%; schemat Windows „Acer” 31b9d370 |
| Ekran / uśpienie | VIDEOIDLE AC 0 / DC 0, STANDBYIDLE AC 0 / DC 0 (nigdy) — remedium R1 w tej części już spełnione |
| Planowanie hybrydowe | SCHEDPOLICY i SHORTSCHEDPOLICY AC/DC = 5 (Automatyczne) |
| powercfg /powerthrottling list | pusto |

## 3. Matryca §3.2 z korektą Olgi (M3 = 30 min bezczynności, M5 = profil turbo)

Sonda B (`nadir_stanowisko.py sonda`): gz_a5 to rozgrzewka 20 s i okno 60 s. Kolumna „po korekcie” wyklucza przedziały skoków zegara (Δwall > 0.3 s przy Δsim < 0.2 s), `stanowisko/korekta_skokow.json`.

| komórka | profil | gz_a5 surowe | po korekcie | det_v2 p50 ms | CPU 1 / 8 proc ms | maxfreq % | GPU SM MHz |
|---|---|---|---|---|---|---|---|
| M0_1 (poza matrycą) | turbo | 0.908 | 0.931 | 6.52 | 50.0 / 48.1 | 95.2 | 367 |
| M0 | wydajny | 0.865 | 0.905 | 3.91 | 51.4 / 50.8 | 94.8 | 277 |
| M1_1 | wydajny | 0.873 | 0.906 | 3.62 | 51.1 / 52.0 | 95.3 | 277 |
| M5_1 | turbo | 0.836 | 0.867 | 4.40 | 55.9 / 49.1 | 96.4 | 367 |
| M1_2 | wydajny | 0.859 | 0.896 | 3.62 | 49.7 / 49.6 | 95.1 | 277 |
| M5_2 | turbo | 0.867 | 0.895 | 5.01 | 50.0 / 49.1 | 95.1 | 277 |
| M2_1 | wydajny | 0.889 | 0.930 | 3.85 | 48.1 / 47.8 | 94.8 | 277 |
| M3 (11 sond, co 3 min) | wydajny | 0.875–0.899 | 0.917–0.934 | 3.60–7.66 | 41.9–53.9 / 47.3–49.7 | 94.3–98.2 | 277 |

- Uwaga do M0_1: sonda poszła w profilu turbo ustawionym rano, zanim Olga zdecydowała, że M0–M4 idą w profilu „wydajny”. Jest oznaczona w pliku i nie wchodzi do reguły.
- **Reguła §3.2** (X ≤ 0.90 × M1 w obu powtórzeniach): żadna komórka jej nie spełnia, ani surowo, ani po korekcie.
- **M3:** przez 30 min bez skoku, sprawdzone w obu kierunkach. Seria tempo(t) jest płaska, a w telemetrii nic nie zmieniło się w żadnej chwili (`stanowisko/seria_M3.json`, `telemetria_M3.jsonl`).
- **M4** (bateria) nie wykonana, bo M1–M3 są płaskie, ale chory stan nie został odtworzony. Decyzja należy do CC.

## 4. Test przyrządu (sygnał CC po M3), kolejność A, C, B, A, C, B, profil „wydajny”

`stanowisko/przyrzad/przyrzad.json`:
- A = `nadir_n1_ab.run(i, "A5", e)` z importu, bez zmian kodu. Przekierowane są tylko katalogi wyjścia modułu, żeby nie nadpisać plików 9.11. Rig wygenerowany tą samą `rig(5)` ma sha zgodne z `results/NADIR/s1/zrodla/n1/rig_ab_5hz.sdf` (`rig_zgodny: true`).
- C = to samo z samą telemetrią hosta.
- B = sonda z matrycy.

Tempo liczone tą samą metodą okna co 9.11 (`nadir_ab.regresja`, rozgrzewka 20 s). Dla B dostępne jest tylko okno 60 s, bo sonda zapisuje 83 s.

| przebieg | okno 120 s | okno 60 s | po korekcie skoków | skoki w oknie |
|---|---|---|---|---|
| odniesienie 9.11 rtf_1_A5 | 0.9283 | 0.9265 | 0.9285 | 0 |
| odniesienie 9.11 rtf_7_A5 | 0.9271 | 0.9265 | 0.9277 | 0 |
| 0 A | 0.9019 | 0.9068 | **0.9371** | 3 (3.8 s) |
| 1 C | 0.8881 | 0.8873 | **0.9235** | 4 (5.1 s) |
| 2 B | — | 0.8284 | **0.8671** | 2 (2.6 s) |
| 3 A | 0.8810 | 0.8783 | **0.9195** | 4 (5.6 s) |
| 4 C | 0.8783 | 0.8828 | **0.9090** | 4 (5.2 s) |
| 5 B | — | 0.8443 | **0.8744** | 2 (2.6 s) |

Profil tempa co 10 s:
- **Odniesienie 9.11** jest płaskie: 0.90–0.95, zero okien < 0.85.
- **Dziś A i C** mają medianę okien 0.90–0.94, ale co ~33 s jedno okno spada do 0.75–0.83 (3–4 z 12 okien). Odstępy między zacięciami w próbkach (0 A: 13.4 → 46.9 → 80.5 → 114.0 s) to dokładnie skoki realtime, bo symulacja w tych przedziałach przesuwa się o < 0.08 s.
- **B** ma medianę 0.867 / 0.871, czyli niższy poziom bazowy, plus te same skoki.

Pełne profile są w `przyrzad.json`, pole `profil10`.

**Zmiany w Windows od 9.11 10:00** (`przyrzad.json`, pole `windows`):
- Windows Update:
  - aktualizacje definicji Defendera KB2267602: 9.11 11:57, 9.11 17:32, 10.11 06:19;
  - pakiet Microsoft.WindowsAppRuntime.2 (9NRZT3Q9R3DL): 9.11 **22:35**, czyli po wieczornym spowolnieniu (21:20–21:26), więc nie może być jego przyczyną.
- Get-HotFix: brak. Instalacje MSI (11707/1033): brak.
- Sterownik GPU: NVIDIA 32.0.15.7713 (577.13) z 2025-08-25, Intel Graphics 32.0.101.6629 z 2025-02-18. Brak zmiany.
- WSL 2.7.10.0, Windows 10.0.26200.9711.

## 5. Co zmieniono w Windows i z jakich wartości

- **Profil OEM (PredatorSense):** Olga przełączała go zgodnie z protokołem M1/M5: rano turbo, potem wydajny, turbo, wydajny, turbo, wydajny. **Stan końcowy: „wydajny”.**
- **powercfg:** niczego nie zmieniano. Ekran i uśpienie były już na 0, SCHEDPOLICY został na 5, powerthrottling nietknięty. Remediów R2–R5 nie stosowano, bo matryca nie wskazała przyczyny.
- **WSL:** `systemd-timesyncd` zatrzymany o 07:22 i wznowiony przez kolejkę o 07:30:44. Teraz jest aktywny i nie zmieniałam tego.

## 6. Do decyzji CC (progu bramki nie zmieniałam)

1. **Bramka §3.4 w obecnym kształcie**, czyli sonda B przy aktywnym timesyncd, dałaby dziś NO-GO prawie zawsze: surowo 0.83–0.91, po korekcie 0.87–0.93.
   - Pomiar trzeba wykonywać przy **zatrzymanym timesyncd**, tak jak boot i odniesienie. Kolejka zatrzymuje go przed bootami, więc bramka uruchamiana z kolejki byłaby w tym samym reżimie.
   - Do rozstrzygnięcia: czy bramką ma być przyrząd A (120 s, zgodny z odniesieniem), czy B, którego niższy odczyt ~0.05 jest niewyjaśniony.
2. **Kolejka przywraca timesyncd po każdym STOP-ie.** To zachowanie z KONT (ANEKS_SKAN2-0b: „stop na sesję, start na końcu”). Każda diagnoza między kolejkami ma więc skoki zegara, jeśli wykonawca sam go nie zatrzyma. Moja wada: przed sondami nie sprawdziłam stanu timesyncd, choć każda sonda go zapisuje (`"timesyncd": "active"` od M0).
3. **Chory stan bootów pozostaje nieodtworzony.** Telemetria §3.5 w tle bootów złapie go przy następnym wystąpieniu.

## Pliki

- `results/NADIR/tools/nadir_stanowisko.py`: sonda, bramka, seria, telemetria, sesja.
- `results/NADIR/tools/nadir_stanowisko_przyrzad.py`: test przyrządu.
- `results/NADIR/s4/stanowisko/`:
  - `stanowisko_*.json`, `rtf_*.jsonl`, `telemetria_*.jsonl`, `seria_M3.json`, `sesja_*.json`, `korekta_skokow.json`;
  - `przyrzad/` z `przyrzad.json`, rtf, telemetrią i podkatalogiem `sonda/`.

Sygnał: **STOP-NADIR4-DIAGNOZA**. Push = Olga.
