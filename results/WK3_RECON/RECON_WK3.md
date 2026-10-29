# RECON_WK3 — recon nogi WK-III „porywy": wiatr zmienny w czasie w skalibrowanym habitacie (k ≈ 0.49 /s)

CC-wykonawca · 29.10.2026 · PROMPT_WK3_S0.
- **Booty: 2/≤2, wyłącznie nauczyciel** (egzekutor orbity, feed emulowany, c00_s01). Sieć nie leciała,
  a z bootów nie raportuję miar misji.
- Pomiar litery wiatru robiłem na samym serwerze gz (bez PX4 i bez drona), co §1 dopuszcza jako
  „pomiar wind_info”.
- Zero treningu i zero edycji istniejących plików. Habitat oporu bez zmian: s = 0.63.

## §0. Bramka

- origin/master == HEAD == **d9f5c500** (CO-WK2); gate pusty; porcelain czysty poza `??` DEMO_C.
- FROZEN wykonaniem, wszystko zgodne:
  - komplet z PROMPT_WK2_S1 §0.3 (profil a68a450b, sonda 8df528bb, pin mono_cam 3354ae1e, FREEZE_DET,
    x500_base 13c9174d, w_judge e68040ae, sędzia 8ec0fcfb, bench 05137098, ncp 0337d5ea,
    net_controller e8c1b658, fantom_scan e435ed7e, rejestr 87203d29, akw_scan b94cdeae,
    orbit_executor 84051436, wk_boot ecf8071c, wk_judge c33c3ff8);
  - wk2_gen_world 632db3c1, wk2_k 09e4b440;
  - światy WK2 s063: s0 73205686, s1p5 b8a9c8b7, s3 f8ccc51c;
  - piny osłony 5/5, certy 9/9.
- **Uwaga:** RAPORT_WK2_S1 nie podaje sha drivera `results/WK2/tools/wk2_boot.sh`. Plik jest zgodny
  z wersją z commita `3b64c4e0` (porcelain czysty), a jego sha256(16) to **cf0959ef**.

## §R1. LITERA PORYWU — **sinus deterministyczny (faza od t_sim = 0), szum niedeterministyczny ⇒ szum wypada**

**Źródło lokalnie:** brak `WindEffects.cc`; gz-sim 8.14.0 jest wyłącznie binarny (RECON_WK2 §R1).

**Litera z pluginu** (`strings libgz-sim8-wind-effects-system.so.8.14.0`):
- parametry: `horizontal`, `magnitude`, `direction`, `time_for_rise`, `sin`, `amplitude_percent`,
  `amplitude`, `period`, `noise`, `vertical`;
- `/wind` to subskrypcja `gz.msgs.Wind`;
- **`/wind_info` to SERWIS** (`Node::Advertise…Service`, Empty → Wind), a nie topik;
- komponenty `LinearVelocitySeed` / `WorldLinearVelocitySeed` to bazowy wektor wiatru, nie ziarno RNG;
- szum idzie przez `gz::sensors::NoiseFactory`.

**`wind_info` NIE jest prawdą o wietrze chwilowym.** Pomiar: przy sinusie magnitudy serwis zwraca stale
(2.0, 0, 0) przez 266/266 próbek (`probe/sinmag_a.json`, pole `probki_t_vx_vy_vz`). Zwraca więc
wektor bazowy (seed).

**Metoda pomiaru zamiast tego:**
- ciało-sonda w świecie testowym (`probe_worlds/*.sdf`: link `enable_wind`, 1 kg, bez grawitacji,
  PosePublisher 100 Hz), serwer `gz sim -s -r` z izolowanym `GZ_PARTITION` (`tools/wk3_windprobe.py`);
- wiatr chwilowy odtwarzany jako w = v + a/f (`tools/wk3_wind_rekon.py`);
- f kalibrowane wiatrem stałym: **f = 0.397** przy s = 0.63. Prawo z RECON_WK2 dla ogniwa
  (k_wiatr/udział masy = 0.989·s^1.96) daje 0.399, więc prawo F ∝ m·s^1.96·(w − v) potwierdza się
  na innym ciele i innej masie.

| pytanie | wynik pomiaru | dowód |
|---|---|---|
| (a) jednostki | `period` w **sekundach czasu symulacji**: okres z FFT 5.00 / 5.04 s przy zadanych 5. `amplitude_percent` to **UŁAMEK**: 0.5 daje amplitudę 0.999 przy średniej 2.0, czyli ±50%. `amplitude` kierunku w **stopniach**: ±29.98° przy zadanych 30. `time_for_rise` w s, **tylko rozruch** po starcie świata: bez bloku t95 rozruchu = 3.0 s; przy rise = 2 po t > 12 s amplituda 0.9989 i faza 0.3° jak przy rise = 0.01 | `probe/rekon_*.json`, `probe/analiza_dodatkowa.json` |
| (b) czy `<noise>` deterministyczny | **NIE.** Dwa starty bez ziarna różnią się maks. **0.375 m/s**; z `--seed 7` dwa starty identyczne (0.0). Launcher PX4 nie podaje `--seed` (`PX4-Autopilot/ROMFS/px4fmu_common/init.d-posix/px4-rc.gzsim:54`: `gz sim --verbose=… -r -s <świat>`), a jego zmiana to edycja zamrożonego. Szum jest też biały na krok fizyki (czas korelacji ≤ 0.09 s, std zrealizowane 0.075 przy stddev 0.5), więc fizycznie nie przypomina porywu ⇒ **szum wypada z nogi** | `probe/noise_*.json` |
| (c) czy `<sin>` deterministyczny i od jakiej fazy | **TAK.** Dwa starty identyczne co do 0.0 m/s. Faza względem sin(2π·t_sim/P): **0.3°** (magnituda), **0.3°** (kierunek), czyli **od t_sim = 0 (start świata), nie od spawnu**. Faza porywu w danym epizodzie wynika z t_sim startu epizodu: deterministyczna przy danej osi czasu bootu, ale nie ustawiana per epizod | `probe/rekon_sinmag_*.json`, `rekon_sindir.json` |
| (d) składanie z `<wind><linear_velocity>` | `linear_velocity` = **średnia (seed)**; blok `<horizontal>` moduluje wokół niej: |w| = |w̄|·(1 + A·sin(2πt/Pm)), θ = θ̄ + Ad·sin(2πt/Pd). Sinusy magnitudy i kierunku są niezależne: przy obu naraz amplituda 1.597 / 1.6 i 30.01° / 30°, fazy 0.4° / 0.2° | `probe/p2.json` |
| (e) źródło lokalnie | brak — wszystko z pomiaru | — |

## §R2. PROFIL Z FIZYKI I LITERATURY — dwa poziomy (litera SDF zapisana przed lotami sieci)

**Ocena propozycji CC:**
- **amplitude_percent** to ułamek. 0.8–1.0 daje porywy do 3.6–4.0 m/s przy średniej 2, ale też
  **ciszę do 0.0–0.4 m/s**, bo sinus jest symetryczny.
- **Współczynnik porywu** G = maks/średnia = 1 + A. Przy A = 0.4 wynosi 1.4, przy A = 0.8 wynosi 1.8.
  To dolna i górna granica pasma CC 1.4–1.8. Wartości literaturowe nie są zweryfikowane przy biurku
  (brak źródeł offline); przyjmuję pasmo CC jako kontekst.
- **Okres:**
  - stała czasowa odpowiedzi drona na opór to 1/k ≈ 2.0 s;
  - okres orbity ~2π·8 m / 1.8 m/s ≈ 28 s;
  - pętle stabilizacji PX4 działają w setnych części sekundy.
  Okres 4–8 s jest więc szybszy niż orbita, porównywalny z 2–4 × 1/k (dron częściowo podąża)
  i wolniejszy niż pętle. Propozycję przyjmuję.
- **Kierunek** ±30° z okresem 11 s, niewspółmiernym z 4 s, żeby wzór się nie powtarzał. Dryden /
  von Kármán tylko jako kontekst; sinus nie jest widmem turbulencji.

| poziom | średnia | amplitude_percent | Pm [s] | |w| min–max | G | kierunek | świat | sha256 |
|---|---|---|---|---|---|---|---|---|
| **P1 „łagodny"** | 2.0 m/s (+x ENU) | 0.4 | 8 | 1.2–2.8 m/s | 1.4 | stały | `worlds/world_wk3_p1.sdf` | `fe96b0965ccce76aa49db44cd1d5200761356a7a1829efc996359a90e69f2105` |
| **P2 „ostry"** | 2.0 m/s (+x ENU) | 0.8 | 4 | 0.4–3.6 m/s | 1.8 | ±30°, Pd = 11 s | `worlds/world_wk3_p2.sdf` | `e47ef38030c5095d9a5f09e86349a07a2aadda5c7ec2c085d906553dcbb179dc` |

**Pełna litera bloku** (wewnątrz pluginu WindEffects, po `<force_approximation_scaling_factor>0.63</…>`):

P1:
```xml
      <horizontal>
        <magnitude>
          <time_for_rise>1.0</time_for_rise>
          <sin><amplitude_percent>0.4</amplitude_percent><period>8</period></sin>
        </magnitude>
      </horizontal>
    …
    <wind><linear_velocity>2 0 0</linear_velocity></wind>
```
P2:
```xml
      <horizontal>
        <magnitude>
          <time_for_rise>1.0</time_for_rise>
          <sin><amplitude_percent>0.8</amplitude_percent><period>4</period></sin>
        </magnitude>
        <direction>
          <time_for_rise>1.0</time_for_rise>
          <sin><amplitude>30</amplitude><period>11</period></sin>
        </direction>
      </horizontal>
    …
    <wind><linear_velocity>2 0 0</linear_velocity></wind>
```

Generator: `tools/wk3_gen_world.py` (A3 + stos systemów + WindEffects s = 0.63 z `wk2_gen_world.plugins_block`
importem + blok + średnia). Diff względem `world_wk2_s063_s0.sdf` to wyłącznie nazwa, komentarz, blok
`<horizontal>` i `linear_velocity`. `gz sdf --check` Valid ×2.

- **Szczyt P2 3.6 m/s przekracza** największy stały wiatr przebadany w WK-II (3 m/s) o 20%.
- Średnia 2 m/s leży między G1.5 a G3.

## §R3. POMIAR NA NAUCZYCIELU (2 booty) — **dron widzi literę; porywy nie zmieniają k**

Metoda (`tools/wk3_gust.py`):
- bilans sił poziomych jak `wk2_k` (import), okna phase == "orbit";
- k z MNK przy wietrze z litery SDF;
- wiatr odtworzony przez drona w_dr = v + D/0.4939, dopasowanie sinusa przy okresie z SDF.

| | P1 (kal1_p1) | P2 (kal2_p2) |
|---|---|---|
| świat (sha) | world_wk3_p1 (fe96b096) | world_wk3_p2 (e47ef380) |
| piny mono_cam / x500_base, world_hash | 3354ae1e / 13c9174d, zgodny | jw. |
| sonda kadencji / V2′ (dsim/dwall) | PASS / ✓ (0.9986) | PASS / ✓ (0.9986) |
| refuse / breach | 0 / 0 | 0 / 0 |
| **k przy wietrze z litery** (bez / z wyrazem wolnym) | **0.4951 / 0.4915** (kalibracja 0.4939) | **0.4890 / 0.4854** (−1.0 / −1.7%) |
| k przy naiwnym założeniu wiatru stałego | 0.4749 (−4%) | 0.4089 (−17%) |
| wiatr odtworzony: średnia / amplituda / faza | 2.018 / **0.814** / +1.8° (litera 2.0 / 0.8 / 0°) | 2.017 / **1.617** / −0.8° (litera 2.0 / 1.6 / 0°) |
| kierunek odtworzony: amplituda / faza | — | **31.4°** / +1.6° (litera 30° / 0°) |
| residuum |w_dr − w_sdf| p50 / p95 | 0.126 / 0.317 m/s | 0.318 / 0.666 m/s |
| odpowiedź prędkości (składowa E przy okresie porywu): amplituda / faza | 0.235 m/s / +10° | 0.361 m/s / −10° |
| przechył w orbicie p50 / p95 / max | 7.6 / 14.7 / 22.5° | 7.7 / 16.3 / **34.6°** |

- **Zgodność z literą:** zrealizowany wiatr widziany przez drona zgadza się z literą SDF co do
  amplitudy (+2%), średniej (+1%) i fazy (≤ 2°).
- **Kontrola oporu:** k przy znanym wietrze trzyma kalibrację w ±2%. W nodze z porywami kontrolę oporu
  trzeba liczyć z literą wiatru: metoda `wk2_k` (wiatr stały) zaniża k o 4–17%. To nowa wymagana
  procedura kontroli.
- **Odpowiedź prędkości:** amplituda w składowej E wynosi 0.24 / 0.36 m/s przy porywie ±0.8 / ±1.6 m/s,
  czyli dron tłumi poryw ~3.4–4.4× i nie ma zauważalnego opóźnienia fazy. Miara jest szumna:
  residuum ~1.2 m/s pochodzi z ruchu orbitalnego.
- **Przechył:** maks. 34.6° w P2 (p95 16.3°). Recon WK §R3 podaje pionowe pół-pole kamery 40.4° po
  marginesie MTI, więc chwilowy przechył P2 zbliża się do granicy, przy której cel poniżej horyzontu
  może wypaść z kadru dołem. Ryzyko nazwane, niezmierzone na kamerze.

## §R4. WAŻNOŚĆ I DRIVER

- **V2′:** oba booty dsim/dwall **0.9986**. Z sinusa nie widać kosztu, a wartość jest wyższa niż mediany
  WK/WK2 (0.92–0.94). Próbka to jeden epizod na boot, więc różnica to najpewniej stan hosta.
  Mechanizm: sinus to ewaluacja funkcji na krok, a WindEffects z s = 0.63 kosztował ~6–8% już wcześniej
  (RECON_WK2 §R4). Bez zmiany reguły V2′ zostaje propozycja re-append D9 / „dolecenia epizodu
  nieważnego" jak w PRE_WK2.
- **Driver:** `results/WK2/tools/wk2_boot.sh` (cf0959ef) ma zaszytą listę 4 światów WK2 (`case`,
  D1) i katalog `results/WK2/booty` (D2). Edycja jest zakazana, więc noga WK3 potrzebuje **NOWEJ kopii**
  `results/WK3/tools/wk3_boot.sh`, w której zmieniają się wyłącznie:
  - (1) lista światów = `world_wk3_p1` (fe96b096…), `world_wk3_p2` (e47ef380…);
  - (2) katalog wyjścia `results/WK3/booty`;
  - (3) komunikaty i nagłówek.
  Piny, prepend `GZ_SIM_RESOURCE_PATH`, sonda, profil i blok manifestu `wk` zostają bez zmian.
  Kontrola oporu: nowe narzędzie liczące k przy wietrze z litery (wzór `wk3_gust.py`; tolerancja ±20%
  wobec 0.494), zamiast `wk2_kcontrol.py`, który dla wiatru ≠ 0 zwraca „n/d”.
  **Lekcja z ANEKS_WK2-1 §3(1):** PRE_WK3 powinien nazwać nowy driver jawnie, a nie „wk2_boot.sh bez zmian”.

## §R5. PROJEKT + WYCENA (PROPOZYCJE — rozstrzyga PRE)

- **Siatka:** c00–c07 × s01, 8 epizodów na poziom (4 na boot).
- **Kolejność:**
  1. **P1** (2 booty), bramka ≥ 6/8 (świadek);
  2. **P2** (2 booty) tylko po bramce.
- **Ramię odniesienia:** WK-II G1.5 (6/8) i G3 (8/8): stały wiatr, ten sam habitat, bez nowych lotów.
- **Dym:** zbędny. Złożenie (świat z blokiem + model + piny) potwierdziły 2 booty tego reconu,
  a zmienia się tylko litera bloku.
- **Kontrola per boot:**
  - k przy wietrze z litery w ±20% od 0.494;
  - wiatr odtworzony przez drona: amplituda w ±20% litery.
  - Poza tolerancją ⇒ STOP do adjudykacji; dwukrotnie ⇒ STOP-ANEKS.
- **Kandydaci werdyktów:**
  - **V-A3** (P1 ≥ 6/8 ∧ P2 ≥ 6/8): „…prowadzi pełną misję przy porywach sinusowych do G = 1.8
    (2 ± 1.6 m/s, okres 4 s, kierunek ±30°) w habitacie k ≈ 0.49 /s: D6 a/8 · b/8";
  - **V-B3** (P1 ≥ 6 ∧ P2 < 6);
  - **V-C3** (P1 < 6/8): „łagodny poryw już łamie misję" z mechanizmem.
  - Kwalifikator obowiązkowy: „poryw = sinus deterministyczny, nie turbulencja; szum wiatru wyłączony
    z powodu niedeterminizmu".
- **Kandydat śmierci:** kontrola wiatru/oporu poza tolerancją dwukrotnie (habitat nie jest taki, jak
  zamrożony).
- **Budżet:** P1 2 + P2 2 + dolecenia V2′ ≤ 2 + powtórki ≤ 2 = **≤ 8** (mieści się w ≤ 10);
  oczekiwane 4.
- **Ryzyko nazwane:** przechył chwilowy P2 do 34.6° wobec pionowego pół-pola kamery 40.4°; wymaga
  opisowego pomiaru „cel w kadrze” w nodze.

## Artefakty

- `tools/wk3_windprobe.py`, `tools/wk3_wind_rekon.py`, `tools/wk3_gen_world.py`, `tools/wk3_gust.py`
- `tools/wk3_calib_boot.sh`: kopia `wk2_calib_boot.sh`; zmiany wyłącznie wzorzec `world_wk3_*`,
  katalog `results/WK3_RECON/booty`, opis roli w manifeście.
- `probe_worlds/*.sdf` (światy testowe sondy, tylko serwer gz) + `probe/*.json` (surowe próbki,
  rekonstrukcje, `analiza_dodatkowa.json`)
- `booty/kal1_p1/`, `booty/kal2_p2/` (bez `boot.ulg`, gitignore) + logi driverów. `manifest.json`
  zawiera pola `bench_finalize` (m.in. `n_success_D6`), których nie odczytywałem.
- `gust_kal1_p1.json`, `gust_kal2_p2.json`
- `worlds/world_wk3_p1.sdf`, `worlds/world_wk3_p2.sdf`
