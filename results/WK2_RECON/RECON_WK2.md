# RECON_WK2 — recon WK-II „opór realny": kalibracja oporu habitatu do fizyki (S0)

CC-wykonawca · 29.10.2026 · PROMPT_WK2_S0. **Booty: 2/≤2, wyłącznie kalibracyjne z nauczycielem**
(egzekutor orbity, feed emulowany, wiatr 0). Sieć nie leciała. Z bootów kalibracyjnych nie raportuję
żadnych miar misji (D6, sweep). Zero treningu i zero edycji istniejących plików. Nowe pliki:
`results/WK2_RECON/**` oraz dwa światy kalibracyjne w `worlds/`.

## §0. Bramka

- origin/master == HEAD == **a22d5bfd** (CO-WK); gate pusty; porcelain czysty poza `??` DEMO_C.
- FROZEN wykonaniem, wszystko zgodne:
  - komplet z PROMPT_WK_S1 §0.3: profil a68a450b, sonda 8df528bb, pin mono_cam 3354ae1e, FREEZE_DET,
    x500_base 13c9174d, w_judge e68040ae, sędzia 8ec0fcfb, bench 05137098, ncp 0337d5ea,
    net_controller e8c1b658, fantom_scan e435ed7e, rejestr 87203d29, akw_scan b94cdeae, orbit_executor
    84051436;
  - piny osłony 5/5 (SHIELD FROZEN True), certy 9/9 PASS, world_hash.sh zgodny z HEAD;
  - światy WK s0 4c179a14 / s1p5 9713a8b1 / s3 3a605ca3, driver `results/WK/tools/wk_boot.sh` ecf8071c.

## §R1. PRAWO SIŁY — **opór liniowy w prędkości, proporcjonalny do masy ogniwa, NIELINIOWY w skali: k(s) ≈ k₀ + 0.936·s^1.96**

**Źródło lokalnie niedostępne.** Zainstalowany jest wyłącznie binarny gz-sim 8.14.0
(`/usr/lib/x86_64-linux-gnu/gz-sim-8/plugins/libgz-sim8-wind-effects-system.so.8.14.0`; `gz` = `/usr/bin/gz`;
równolegle istnieje vendor ROS 8.11.0 w `/opt/ros/jazzy/opt/gz_sim_vendor`). Brak `WindEffects.cc/.hh`.
Litera z symboli pluginu:
- `WindEffectsPrivate::ApplyWindForce` czyta komponenty `Link`, `Inertial` (masa), `WindMode`
  (`enable_wind`), `WorldPose`, `WorldLinearVelocity` i woła `Link::AddWorldForce`.
- Teksty parametrów: `force_approximation_scaling_factor`, `<horizontal><magnitude>`, `<direction>`,
  `time_for_rise`, `noise`.

Siła działa więc na ogniwo z `enable_wind`, zależy od jego masy i prędkości liniowej. W modelu
wiatrowym ma to tylko `base_link` o masie 2.0 kg (`worlds/wind_models/x500_base/model.sdf:9,21`). Masa
całkowita to 2.0 + 4 × 0.01608 (rotory, `:319,391,463,535`) + 0.050 (kamera, `mono_cam/model.sdf:10`)
= 2.114 kg; udział ogniwa z wiatrem wynosi 0.946.

**Pomiar (`tools/wk2_k.py`, bilans sił poziomych; metoda odtwarza liczby ANEKS_WK-1 §1.3):**

| habitat | skala s | boot | k [1/s] (CI95 bootstrap blokowy) | v_h p50 [m/s] |
|---|---|---|---|---|
| stock (A3, bez WindEffects) | — | FANTOM r1_V2 / r2_V2 / LIQ r3_ncp | 0.1176 / 0.1164 / 0.1164 (±0.001) | 2.05–2.11 |
| **WK2 kalibracja 1** | **0.46** | kal1_s046 (nauczyciel) | **0.3219** (0.3200–0.3232) | 1.77 |
| **WK2 kalibracja 2** | **0.63** | kal2_s063 (nauczyciel) | **0.4939** (0.4912–0.4964) | 1.70 |
| WK (world_wk_s0) | 1.0 | wk0_b1 / wk0_b2 (sieć, noga WK) | 1.0552 / 1.0530 (±0.007) | 1.40–1.42 |
| W (world_wind_s0) | 1.0 | orbit_s02 / s03, net_s01 / s02 / s03 | 1.047 / 1.032 / 1.067 / 1.070 / 0.998 | 1.08–1.71 |

- **Liniowość w prędkości:** k jest stałe w przedziałach |v_h| 0.3–1.0 / 1.0–1.5 / 1.5–2.0 m/s
  (stock 0.10–0.12; WK 1.00–1.06; kalibracje mają jeden przedział). Wyjątek to przedział > 2 m/s
  w WK0 (mało próbek, stany przejściowe). Opór jest liniowy, nie kwadratowy.
- **Odstający punkt:** W L0 orbit_s01 ma k = 0.537 z szerokim CI 0.41–0.67, dużym biasem (−0.21 m/s²)
  i jednym oknem orbity. To 1/5 bootów W; nie wchodzi do krzywej.
- **Zależność od skali NIE jest liniowa.** Krzywa k(s) = k₀ + a·s^p dopasowana log-log
  (`k_krzywa.json`): k₀ = 0.117, **a = 0.936, p = 1.958**. Predykcje 0.321 / 0.496 / 1.053 wobec
  zmierzonych 0.322 / 0.494 / 1.054.
  - a = 0.936 zgadza się z udziałem masy ogniwa 0.946, czyli przy s = 1 siła ≈ m_base · (v_wiatr − v).
  - Skala wchodzi w przybliżeniu **kwadratowo**. Prawo „F ∝ s" (interpolacja liniowa CC, PROMPT §R3)
    przewidywało k = 0.55 przy s = 0.46, a zmierzono 0.32 (−41%).
  - Mechanizm wykładnika jest nieustalony lokalnie (brak źródła). To fakt empiryczny z 3 punktów
    + stocku.

**Opór w modelu stock (k ≈ 0.12) to opór wirników z pluginu silnika, z litery i z rachunku:**
- `rotorDragCoefficient` 8.06428e-05, `motorConstant` 8.54858e-06 (`PX4-Autopilot/Tools/simulation/gz/models/x500/model.sdf:14,18`).
- Zawis: ciąg/rotor = m·g/4 = 2.114·9.81/4 = 5.185 N ⇒ ω = √(5.185/8.54858e-06) = 778.8 rad/s.
- Opór/rotor = ω · c_d · v = 0.0628·v N; 4 rotory: 0.251·v N; po normalizacji masą: **k = 0.119 /s**.
  Zmierzono 0.116–0.118.
- **Względem powietrza:** plugin `libgz-sim8-multicopter-motor-model-system` zawiera symbole komponentu
  `Wind` (`WindTag`) obok `rotorDragCoefficient`. Litera symboli wskazuje, że opór wirnika liczony jest
  względem wiatru świata, gdy ten istnieje. **Niezmierzone** (oba booty poszły na kalibrację).
  Światy WK2 mają encję `<wind>`, więc opór wirnika i WindEffects działają przy wietrze względem
  powietrza.

## §R2. ODNIESIENIE ZEWNĘTRZNE — pasmo realne **k ∈ [0.15, 0.55] /s przyjęte**, z kwalifikatorem masy

- **PX4 (lokalne źródło), `src/modules/ekf2/params_drag.yaml`:**
  - `EKF2_MCOEF` (opór pędowy wirnika, liniowy w prędkości): **domyślnie 0.15 /s**, zakres 0–1.0
    (`:54-74`). Opis: „scales with speed not speed squared".
  - `EKF2_BCOEF_X/Y` (opór bryły, kwadratowy w prędkości): **domyślnie 100 kg/m²** (`:24-51`).
    Ekwiwalent liniowy ½ρv/BCOEF przy 1.5–2 m/s wynosi ~0.009–0.012 /s, więc pomijalny wobec MCOEF.
  - Zastosowanie: `src/modules/ekf2/EKF/aid_sources/drag/drag_fusion.cpp:73-99` (MCOEF z korektą gęstości).
- **Literatura (podana przez CC, nieweryfikowana przeze mnie przy biurku):** Faessler, Franchi,
  Scaramuzza, RA-L 2018 (arXiv 1712.02402), quadrotor 610 g: d_x/d_y = 0.544/0.386 /s (okrąg),
  0.491/0.236 /s (lemniskata).
- **Ocena pasma:**
  - Dolna granica 0.15 = domyślne MCOEF PX4; model stock (0.117) leży tuż pod nią.
  - Górna 0.55 = maksimum Faesslera dla drona 610 g. Opór znormalizowany masą maleje z masą przy
    podobnej geometrii wirników, więc dla klasy x500 (2.1 kg) 0.55 jest wariantem pesymistycznym.
    To zgodne z intencją CC („jeśli sieć lata tam, lata w całym paśmie").
  - Korekty pasma nie proponuję. Dopisuję kwalifikator: górna granica pochodzi z drona ~3.5× lżejszego.
- **Wniosek wobec nogi WK:** habitat WK (s = 1.0, k = 1.05) leżał **~1.9× ponad górną granicą** pasma.
  ANEKS_WK-1 szacował „najpewniej kilkukrotnie" — w tych liczbach to ~2× górnej granicy i ~7× dolnej.

## §R3. KALIBRACJA — **wybrana skala s = 0.63, zmierzone k = 0.494 /s** (−10% wobec celu, w tolerancji ±20%)

| boot | świat (sha) | skala | k zmierzone | w tolerancji [0.44, 0.66]? | przechył orbita p50/p95 [°] | V2′ (dsim/dwall) | piny | sonda |
|---|---|---|---|---|---|---|---|---|
| 1 kal1_s046 | world_wk2_k055_s0 (ff60c065) | 0.46 | 0.322 ± 0.002 | **NIE** (−41%) | 5.3 / 10.2 | ✓ (0.906) | 3354ae1e / 13c9174d / sha świata OK | PASS 0.068 / 0.002 |
| 2 kal2_s063 | world_wk2_s063_s0 (73205686) | 0.63 | **0.494 ± 0.003** | **TAK** (−10%) | 6.3 / 11.1 | ✓ (0.927) | jw. | PASS |

- Oba booty: egzekutor orbity (`CONTROLLER=orbit`), feed emulowany B, scenariusz c00_s01 (cel stoi),
  wiatr 0, refuse 0, breach 0. world_hash.txt zgodny z sha świata, blok `wk2` w manifeście.
- **Boot 2:** skala poprawiona według litery PROMPT §R3 („liniowo z pomiaru"), czyli sieczną
  przez zmierzone punkty s = 0.46 → 0.322 i s = 1.0 → 1.05:
  s = 0.46 + (0.55 − 0.322)/(1.05 − 0.322)·0.54 = 0.63.
  Model potęgowy przewidywał 0.487, zmierzono 0.494.
- Wariant „boot 2 = zawis przy 3 m/s" nie wykonany: boot 2 poszedł na korektę skali.
- **Nazwa świata 1 jest myląca:** `world_wk2_k055_s0` to plan (k = 0.55), a faktycznie daje
  k = 0.32. Plik zostaje jako artefakt kalibracji i nie jest kandydatem do nogi.

**Rekomendacja poziomu do PRE_WK2: s = 0.63 (k zmierzone 0.494 /s)**, a nie s = 0.675 (k = 0.55
wyłącznie z krzywej). Wynika to z zasady nadrzędnej: poziom ma mieć zmierzone k, a 0.494 leży
w górnej części pasma i mieści się w tolerancji celu. Wybór s = 0.675 wymagałby kolejnego boota
kalibracyjnego.

Niepewność:
- statystyczna ±0.003 (CI95 bootstrap blokowy, jeden boot);
- systematyczna: k zmierzone przy v ≈ 1.7 m/s nauczyciela (sieć w WK0 leciała 1.4 m/s; liniowość w v
  sprawdzona wyżej);
- jedno ziarno i jedna komórka.

**Poziom pośredni (wariant schodkowy):** s = 0.46 ma już zmierzone k = 0.322, czyli −8% od środka
pasma 0.35. Kandydat na drugi poziom nie wymaga nowej kalibracji.

## §R4. WAŻNOŚĆ — WindEffects kosztuje ~6–8% czasu symulacji; zależności od skali nie widać

`tools/wk2_rtf.py` → `r4_rtf.json`, dsim/dwall per epizod z manifestów:

| grupa | n ep. | p10 | p50 | min | < 0.90 | ważne V2′ |
|---|---|---|---|---|---|---|
| A3 + percep (PERC2 S2, FANTOM V2) | 56 | 0.922 | **1.021** | 0.885 | 7.1% | 92.9% |
| A3 bez percep (LIQ, FANTOM B) | 92 | 0.921 | **1.000** | 0.877 | 4.3% | 95.7% |
| W (WindEffects, bez percep) | 16 | 0.911 | **0.938** | 0.908 | 0% | 100% |
| WK + percep (WindEffects 1.0) | 9 | 0.891 | **0.923** | 0.891 | 11.1% | 88.9% |
| WK2 kalibracja (s = 0.46 / 0.63) | 2 | — | 0.906 / 0.927 | — | 0 | 2/2 |

- **Źródło kosztu:** WindEffects (W bez percepcji p50 0.938 wobec A3 bez percepcji 1.000), a nie
  percepcja (A3 z percep 1.021 wobec bez 1.000). Stos systemów w WK/W jest identyczny z server.config,
  którego A3 używa domyślnie, więc jedyny dodatek to WindEffects i encja wiatru.
- Rozkład jest przesunięty o ~0.07, a próg V2′ = 0.90 leży ~1σ pod medianą. Oczekiwanie ~10%
  epizodów nieważnych na poziom.
- **Skala:** 0.906 (s = 0.46), 0.927 (s = 0.63), 0.89–0.94 (s = 1.0). Brak widocznej zależności,
  ale próbka to po jednym epizodzie.

**Propozycja bez zmiany reguły V2′:** przenieść regułę D9 kampanii ławki (FREEZE_CAMPAIGN §„D9 = V2′":
epizod V2′-nieważny ⇒ re-append, liczy się pierwszy ważny) do PRE_WK2 jako zapisany z góry slot
powtórki. Po każdym poziomie jeden boot uzupełniający, wyłącznie dla epizodów nieważnych, a werdykt
liczony na 8 ważnych. Plus checklista hosta (zasilanie AC, GPU wolne, proc_gate) bez zmian.

## §R5. PROJEKT + WYCENA (PROPOZYCJE — rozstrzyga PRE)

- **Świat nogi:** `world_wk2_s063_{s0,s1p5,s3}` wygenerowane `tools/wk2_gen_world.py` (s = 0.63,
  wiatr 0 / 1.5 / 3 m/s +x ENU).
  - Generator zwalidowany: przy s = 1.0 odtwarza `world_wk_s0` bajt w bajt poza linią komentarza.
  - Kopia s0 już istnieje (73205686). s1p5 i s3 to nowe pliki do wygenerowania w S1.
- **Driver:** `results/WK/tools/wk_boot.sh` ma zaszyte trzy światy WK (`case`). Noga WK2 potrzebuje
  nowej kopii z listą `world_wk2_s063_*` (ten sam wzór co tu w `wk2_calib_boot.sh`, sha świata
  jako argument/lista).
- **Siatka i kolejność:** c00–c07 × s01 (8 ep./poziom, 4 na boot), dym (s = 0.63, 3 m/s, c00) →
  WK2-0 → bramka 6/8 (świadek) → wiatr 1.5 / 3 m/s z przeplotem.

| wariant | booty |
|---|---|
| **A: tylko górny poziom** | dym 1 + WK2-0 2 + wiatr 4 + sloty V2′ ≤ 3 (po 1 na poziom) = **≤ 10** |
| **B: schodkowy** (drugi poziom s = 0.46, k = 0.322, tylko jeśli bramka na górnym nie przejdzie) | A + WK2-0@0.46 2 + ewentualnie wiatr@0.46 4 + sloty ≤ 2 = **≤ 18**; realnie przy porażce bramki górnej i przejściu dolnej: 1 + 2 + 2 + 4 + sloty ≈ 9–12 |

- **Kandydaci kryteriów (propozycje):**
  - bramka WK2-0 ≥ 6/8 (jak WK);
  - V-A / V-B / V-C jak w PRE_WK z kwalifikatorem „k = 0.494 /s (zmierzone), górna część pasma
    realnego";
  - w wariancie schodkowym dodatkowe zdanie „próg przeniesienia leży między k = 0.32 a 0.49".
- **Kandydat śmierci:** dym przy s = 0.63 nie ładuje wiatru albo sonda/admisja FAIL w 2 podejściach
  (jak PRE_WK).
- **Ryzyko nazwane:** dym WK przy 3 m/s miał w zawisie przechył 14.5° przy k = 1.05. Przy k = 0.49
  oczekiwanie jest mniejsze (opór wiatru ∝ k·Δv), ale niezmierzone: wariant „zawis przy 3 m/s" nie
  poleciał.

## Artefakty

- `tools/wk2_k.py` (bilans sił, CI, k w przedziałach v, przechył)
- `tools/wk2_gen_world.py` (generator z zadaną skalą)
- `tools/wk2_calib_boot.sh`: kopia `wk_boot.sh`, ~81 linii diffu. Zmiany K1 nauczyciel/feed B,
  K2 świat + sha jako argument, K3 katalog, K4 blok `wk2` zamiast bloków sieci; percep + sonda
  bez zmian.
- `tools/wk2_rtf.py`
- `k_walidacja.json`, `k_walidacja_W.json`, `k_kal1.json`, `k_kal2.json`, `k_punkty.json`,
  `k_krzywa.json`, `r4_rtf.json`
- `booty/kal1_s046/`, `booty/kal2_s063/` (bez `boot.ulg` — gitignore) + logi driverów.
  Uwaga: `manifest.json` bootów kalibracyjnych zawiera pola, które `bench_finalize` wypełnia
  automatycznie (m.in. `n_success_D6`). Zgodnie z zasadą nadrzędną ich nie odczytywałem ani nie
  raportowałem.
- `worlds/world_wk2_k055_s0.sdf` (s = 0.46), `worlds/world_wk2_s063_s0.sdf` (s = 0.63)
