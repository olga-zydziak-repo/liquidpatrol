# RECON_WK4 — recon nogi WK-IV „turbulencja i sufit wiatru" — STOP-WK4R

Wykonawca · 30.10.2026 · PROMPT_WK4_S0. **Sieć NIE leciała, zero miar misji sieci, zero treningu, zero
edycji istniejących plików.** Nowe pliki: `results/WK4_RECON/**` + `worlds/world_wk4.sdf`.
Booty uzbrojone: **2/≤2, oba nauczyciel** (orbit, feed emulowany, reżim OPS). Do tego **2 próby
nieuzbrojone** (dron nie wystartował, świat nie latał) z dwoma błędami mojego publikatora, oba
nazwane w R4.

## Raport płaski

- **Droga A DZIAŁA.** Publikator przebiegu z pliku, sterowany czasem symulacji, na topiku
  `/world/<W>/wind` (gz.msgs.Wind):
  - zastępuje wektor bazowy, a składowa z działa;
  - przy `time_for_rise` = 0.01 w blokach horizontal i vertical odpowiedź skokowa to ≤ 0.03 s;
  - jest deterministyczny: dwa starty różnią się o max |Δw| 0.0016 m/s, a publikacje padają
    w identycznych chwilach t_sim;
  - odtworzenie D2 / D6 daje σ 0.974–1.000 i opóźnienie 0.02 s przy 20 Hz.
- **Serie D2…D6** (Dryden, ziarno 20261030, 20 Hz, 420 s):
  - σ_w mieści się w ±4%;
  - **σ_v realizacji wynosi 0.87–0.89 celu w 5/5 profili, a σ_u przy D2 0.87, czyli FAIL ±10%**;
  - generator jest poprawny: σ stacjonarna = cel co do 4 miejsc. Diagnostyczny Monte Carlo pokazuje,
    że ±10% na 420 s trafia tylko w 37–73% realizacji, bo L_u/Ū = 11–34 s. **Kryterium ±10% przy tej
    długości jest nieosiągalne pewnie, decyzja należy do PRE.**
  - Czas autokorelacji 1/e mieści się w ±25% teorii przy D4–D6 we wszystkich składowych, a przy D2–D3
    nie wszędzie.
- **D2 a P2:** D2 jest **3× łagodniejsze w σ poziomym** (σ_x 0.33 wobec 1.06 m/s) i **wolniejsze,
  nie szersze w paśmie** (90% mocy poniżej 0.04–0.06 Hz wobec 0.25–0.34 Hz w P2). Nowe są pion
  (σ_z 0.21, pasmo do 0.28 Hz) i brak periodyczności.
- **D6 nauczyciela ze świadkiem: D4 4/4, D6 4/4.** Breach 0, REFUSE 0, V2′ 8/8, k z pliku
  0.496 / 0.4975 (+0.4 / +0.7%). Przechył w epizodach p95 19–21° / 24–27°, max 35.3° / 37.5°.
  Cel poza kadrem ≤ 1.9%.
- **Przewidywany sufit Ū_c = 6 m/s** (pierwsza średnia z D6 sieci ≤ 4/8; pewność 0.55).
  Mechanizm: percepcja/track pod przechyłem i drganiami attitude (zaczyna się transjentne wypadanie
  celu dołem przy r ≤ 8 m), w drugiej kolejności zawracanie orbity. Nie nasycenie: PX4 i sieć mają
  zapas do Ū ≈ 11 m/s. Nauczyciel przechodzi D6 4/4, więc ewentualna porażka sieci przy Ū = 6
  będzie sufitem sterownika lub percepcji, nie płatowca.
- **Ryzyko na S1 (nowe, nazwane):** w świecie WK4 dsim/dwall wynosi **0.915–0.945** wobec 0.9986
  w WK3 przy tej samej roli nauczyciela. Margines do progu V2′ to 1.5–4.5%.

## §0. Bramka — PASS

origin/master == HEAD == `2eb118e9` (CO-WABIK3R), `origin/master..HEAD` puste, porcelain czysty poza
nazwanymi `??` DEMO_C. FROZEN (sha8) zgodne wykonaniem: `wk3_boot.sh` 039e368c, `world_wk3_p1` fe96b096,
`world_wk3_p2` e47ef380, `wk3_gen_world.py` 1b5895c3, `wk3_windprobe.py` abc4a665, `wk3_wind_rekon.py`
6ae9027a, `wk3_gust.py` 12ea2f2f, `wk2_k.py` 09e4b440, x500_base (wind) 13c9174d, mono_cam 3354ae1e,
profil a68a450b, sonda 8df528bb, bench_judge 8ec0fcfb, ncp 0337d5ea, net_controller e8c1b658.

## R1. Litera wejścia w czasie rzeczywistym (sonda w gołym gz, 0 bootów; `probe/*.json`)

Narzędzie `tools/wk4_windprobe.py` (wzór wk3_windprobe; nowe: publikator sterowany czasem
symulacji, rekonstrukcja 3D w = v + a/f, f = 0.397).

- **(a) Topik:** `/world/<W>/wind`, typ `gz.msgs.Wind`. Litera z `gz topic -i` na gołym serwerze:
  jedyny subskrybent to WindEffects. Pola wiadomości: `header`, `linear_velocity`, `enable_wind`.
  `linear_velocity` działa w trzech osiach.
  `enable_wind=false` **wyłącza wiatr całkowicie** (sonda leci ze stałą prędkością, a = 0) i ten
  stan trwa po ustaniu publikacji (`step_seed2.json` [36–55 s]). W świecie WK4 publikator zawsze
  wysyła `true`.
- **(b) Publikacja ZASTĘPUJE wektor bazowy:** baza 2 m/s, wysłane 4 → zrekonstruowane 3.917–4.000
  (nie 6). Odpowiedź skokowa przy domyślnym `time_for_rise` jest wykładnicza ze stałą ok. 1 s
  (t63 1.01 s, t90 2.31 s), także na zmianę w locie.
  Przy `time_for_rise` 0.01: poziomo t63 0.028 s, gdzie sama rekonstrukcja wnosi 0.02 s
  (syntetyk z idealnym skokiem).
  **Pion ma osobny blok:** z samym `horizontal` wz nadal ma τ ≈ 1 s, z `<vertical><time_for_rise>
  0.01</time_for_rise></vertical>` t63 0.03 s (`step_rise001.json`, `step_wk4.json`).
  ⇒ W świecie WK4 0.01 w obu blokach.
- **(c) Blok `<sin>` moduluje wokół wartości Z TOPIKU:** P2 przy topiku 4 m/s → średnia 3.997,
  amplituda 3.191 (= 0.8·4) i kierunek ±30.0° (`sin_topic.json`). ⇒ W świecie WK4 bez `<sin>`.
  Ich brak niczego nie psuje (`step_wk4.json`: wartości stałe co do 0.001).
- **(d) Składowa z wywiera siłę:** wysłane +2 → wz 2.000, −1 → −1.000.
- **(e) Po ustaniu publikacji wiatr TRZYMA OSTATNIĄ wartość**, nie wraca do bazowej:
  `step_rise001.json` [36–49 s] = (0, 3, 0).
- **(f) Determinizm:** D2, dwa starty świata przy 20 Hz.
  - max |Δw| rekonstrukcji **0.0016 m/s** (p99 0.0, próg 0.02 ✓);
  - publikacje 3001/3001 w identycznych chwilach t_sim (`r3_odtworzenie.json`).
- **(g) Częstotliwość publikacji:**

  | | opóźnienie | RMSE x/y/z [m/s] |
  |---|---|---|
  | 20 Hz | 0.02 s | 0.011 / 0.014 / 0.019 |
  | 10 Hz | 0.05 s (pół próbki) | 0.017 / 0.021 / 0.029 |

  Obie częstotliwości nadążają. Wybór: **20 Hz**.

**Werdykt R1: droga A działa.**

## R2. Generator Drydena (`tools/wk4_dryden.py`, 0 bootów; `series/D*.json` + `.sha256`, `walidacja_serii.json`)

**Źródło wzorów (nazwane):** wzory z PROMPT_WK4_S0 §R2, czyli MIL-F-8785C w formie niskiej wysokości.
Litera normy jest niedostępna offline (brak pliku normy na hoście), więc wzory przyjąłem jak podano.

**Parametry:**
- h = 10 m: L_w = 10.0 m, L_u = L_v = 67.3 m, σ_u = σ_v = 1.889·σ_w, σ_w = 0.1·Ū.
- **V = Ū** (adwekcja, hipoteza Taylora), **W20 = Ū** (przybliżenie, nazwane).

**Dyskretyzacja (nie Euler):**
- dokładna: e^{A·dt} + kowariancja Van Loana, stan początkowy ze stacjonarnej Lapunowa;
- wejście to biały szum o jednostronnej gęstości 1 w ω, intensywność q = π, bo widmo całkuje się
  do σ²;
- **ziarno 20261030 (jedno dla nogi)**, ta sama realizacja szumu dla każdego profilu, profile
  różnią się tylko Ū;
- 20 Hz, 420 s, Ū wzdłuż +x ENU.

**Kontrola teorii:** σ stacjonarna z Lapunowa = cel co do 4 miejsc dla każdego profilu i składowej.

| profil | sha256/8 | σ real/cel u · v · w | t1e u (L/V) | t1e v (teoria) | t1e w (teoria) | \|w_h\| min–max | σθ (oczek.) | odwr. |
|---|---|---|---|---|---|---|---|---|
| D2 | 6e09f653 | **0.865** · **0.866** · 1.037 | 18.9 (33.7) | 15.9 (21.1) | 5.0 (3.1) | 1.30–3.03 | 9.1° (10.7°) | 0 |
| D3 | df2369db | 0.928 · **0.865** · 1.001 | 17.3 (22.5) | 10.4 (14.0) | 2.4 (2.1) | 1.68–4.73 | 9.4° | 0 |
| D4 | a4c085f9 | 0.955 · **0.873** · 0.988 | 15.8 (16.8) | 8.3 (10.5) | 1.65 (1.56) | 2.01–6.53 | 9.5° | 0 |
| D5 | caa10794 | 0.966 · **0.882** · 0.985 | 14.8 (13.5) | 6.7 (8.4) | 1.25 (1.25) | 2.33–8.39 | 9.6° | 0 |
| D6 | 673e09e1 | 0.971 · **0.889** · 0.985 | 13.8 (11.2) | 5.9 (7.0) | 1.05 (1.04) | 2.67–10.29 | 9.7° | 0 |

**Walidacja:**
- **σ w ±10%: FAIL** dla v w 5/5 profili i dla u przy D2. Pozostałe składowe PASS.
- **Odchylenie nazwane (kryterium czasu 1/e):**
  - ±25% od L/V to kryterium właściwe tylko dla u (filtr 1. rzędu).
  - Dla v i w (Dryden 2. rzędu, autokorelacja (1 − x/2)e^{−x}) czas 1/e wynosi teoretycznie
    **0.627·L/V**. Liczę oba warianty (JSON).
  - Wobec teorii ±25%: D4–D6 3/3 PASS, D3 v FAIL, D2 u i w FAIL.
- **Diagnostyka bez selekcji** (`walidacja_serii.json:diagnostyka_mc_200_ziaren`; zamrożone ziarno
  nie zmienione). Rozkład σ_real/cel na 420 s z ziaren 1–200:

  | | u | v | w |
  |---|---|---|---|
  | D2: frakcja w ±10% / p5–p95 | 37% / 0.66–1.24 | 42% / 0.74–1.19 | 92% |
  | D6: frakcja w ±10% | 57% | 73% | 100% |

  ⇒ ±10% na 420 s to próba losowa z L/V rzędu 10–30 s, nie własność generatora.
- **Propozycja do PRE:** albo miara „σ zrealizowane w pliku" zamiast celu normy (plik jest literą),
  albo przebieg ≥ 1800 s.

**Ta sama miara na P2 WK-III:** σ_x 1.06, σ_y 0.82, σ_z 0, |w| 0.40–3.60, σθ 21.2°, f90 x/y 0.25 / 0.34 Hz.
- **D2 a P2:** σ poziome 3× mniejsze (0.33 / 0.33 wobec 1.06 / 0.82) i pasmo NIŻSZE (f90 x 0.04 Hz,
  y 0.06 Hz wobec 0.25 / 0.34). **Zdanie promptu „D2 szersze w paśmie" nie zachodzi poziomo.**
  Nowe w D2 są pion (σ_z 0.21, f90 0.28 Hz) i brak periodyczności.
- **D6** dorównuje P2 w σ_x (1.10) przy średniej 3× wyższej, a pasmo poziome nadal ma niższe
  (0.095 Hz).
- Odwrócenie wiatru (wx < 0): 0 we wszystkich profilach.

## R3. Odtworzenie w świecie sondy (`r3_odtworzenie.json`, świat `probe_worlds/probe_wk4.sdf`)

| przebieg | RMSE x / y / z [m/s] | σ_rek/σ_plik x / y / z | opóźnienie | próg PRE (σ ±10%, ≤0.1 s) |
|---|---|---|---|---|
| D2 20 Hz (start a) | 0.011 / 0.014 / 0.019 | 0.997 / 1.000 / 0.991 | 0.02 s | ✓ |
| D2 20 Hz (start b) | identyczne | identyczne | 0.02 s | ✓ |
| D2 10 Hz | 0.017 / 0.021 / 0.029 | 0.997 / 1.000 / 0.991 | 0.05 s | ✓ |
| D6 20 Hz | 0.058 / 0.072 / 0.099 | 0.996 / 0.997 / 0.974 | 0.02 s | ✓ |

## R4. Nauczyciel jako ramię odniesienia (`booty/n_D4c`, `booty/n_D6`; `view_*.json`, `judge_*.json`, `kadr_*.json`)

**Świat `world_wk4` (sha256 `7acf407f…d1b1`, `tools/wk4_gen_world.py`):**
- baza A3 + `plugins_block(0.63)` z wk2_gen_world, czyli import, habitat bez zmian;
- `time_for_rise` 0.01 w horizontal i vertical, bez `<sin>` i `<noise>`, `<wind>` 0 0 0;
- diff wobec `world_wk3_p2` wyłącznie w bloku wiatru i komentarzu.

**Publikator `tools/wk4_publisher.py`:**
- seria przypięta sha, sterowany zegarem, 20 Hz;
- t_off 40 s: przed nim trzyma próbkę 0, po końcu serii ostatnią;
- pierwsza publikacja przy t_sim 0.03–0.04 s; okna epizodów 109.7–429.5 s mieszczą się w serii
  (koniec 460 s).

Epizody: c00_s01, c04_s01, c06_s01, c04_s02 (id 0, 4, 6, 16).

| boot | profil | V2′ (dsim/dwall) | D6 pełny / świadek | sweep [°] | d_min [m] | przechył p50 / p95 / max w oknach epizodów [°] | poza kadrem (dół) | k z pliku | breach / REFUSE |
|---|---|---|---|---|---|---|---|---|---|
| n_D4c | D4 | 4/4 (0.916–0.945) | **4/4 / 4/4** | 770–864 | 7.66–8.28 | 12.6–14.5 / 19.2–21.3 / 25.7–35.3 | 0–1.5% (0) | 0.4962 (+0.4%) ✓ | 0 / 0 |
| n_D6 | D6 | 4/4 (0.915–0.943) | **4/4 / 4/4** | 792–861 | 7.45–8.01 | 18.0–19.5 / 24.3–26.9 / 28.7–37.5 | 0–1.9% (≤ 0.36%) | 0.4975 (+0.7%) ✓ | 0 / 0 |

- Residuum wiatru odtworzonego przez drona wobec pliku (p50 / p95): 0.20 / 0.46 i 0.33 / 0.68 m/s.
- **Ramię odniesienia: nauczyciel trzyma D6 4/4 przy Ū = 6 m/s.** Porażka sieci na tych szczeblach
  nic nie mówi o płatowcu.
- Kwalifikator: nauczyciel ma feed emulowany, więc NIE certyfikuje percepcji. Kadr mierzony jest
  geometrią GT (definicja wk3_kadr).

**Przebieg bootów (odchylenia nazwane, wszystko w `booty/` i logach drivera):**
1. **`n_D4`: ENV-BLOCK w `run_boot` (proc_gate §3) przed stackiem.** Mój publikator czekał na
   zegar w pętli co 1 ms (2.6% CPU).
   Poprawka: uśpienie 0.2 s przed światem, 2 ms w locie. Driver czeka, aż %CPU publikatora
   z `ps` (średnia od startu) spadnie, maksymalnie 90 s.
2. **`n_D4b`: PX4 „Timed out waiting for Gazebo world”.** `px4-rc.gzsim:33` uznaje świat za
   działający, gdy `gz topic -l` pokazuje `/world/.*/clock`, a mój publikator subskrybował zegar
   przed startem serwera. PX4 nie uruchomił więc gz. Dron się nie uzbroił.
   Poprawka: publikator czeka na serwis `/world/<W>/scene/info`. Sprawdzone w izolowanej partycji
   (przed serwerem 0 topików zegara).
   Po tej próbie zostały procesy-sieroty (`bench_flight`, `rtf_sampler`, `ekf_watchdog`), które
   zablokowały pierwsze wywołanie `n_D4c` (ENV-BLOCK drivera przed `mkdir`). Zabite ręcznie,
   host czysty, potem `n_D4c` przeszedł.
3. **`n_D4c` i `n_D6`: oba uzbrojone, ważne, sonda kadencji PASS.**

**Booty uzbrojone: 2/≤2. Próby nieuzbrojone: 2** (świat lub stack nie wstał, zero lotu). Rozliczenie
budżetu zostawiam CC.

**Ryzyko V2′ na S1:** dsim/dwall 0.915–0.945 we wszystkich 8 epizodach WK4. W WK3 (kalibracja
nauczyciela `kal1/2`, kampania `p2_b2`) było 0.9986–1.0. Przyczyny NIE rozstrzygam. Kandydaci:
publikacja 20 Hz przez transport gz, `time_for_rise` 0.01 (krok filtra wiatru w trzech osiach) albo
pion. Przy sieci z percepcją, czyli tym samym rytuale percep co tu, margines do 0.90 to 1.5–4.5%.

## R5. Rachunek sufitu przed lotami sieci (`tools/wk4_r5.py` → `r5_sufit.json`)

**(a) Przechył statyczny z oporu, θ = atan(k·v_rel/g), k = 0.494:**

| Ū [m/s] | 2 | 4 | 6 | 8 | 10 |
|---|---|---|---|---|---|
| zawis | 5.8° | 11.4° | 16.8° | 21.9° | 26.7° |
| zawis + 3σ_u | 9.0° | 17.5° | 25.3° | 32.3° | 38.3° |
| orbita pod wiatr + 3σ_u | 14.0° | 22.1° | 29.4° | 35.8° | 41.3° |

Pomiar nauczyciela: p50 przy D4 / D6 = 12.6–14.5 / 18.0–19.5°, model 11.4 / 16.8°. Max 35–37°
przekracza model statyczny o ≤ 8° (dynamika manewru).

**(b) Kadr (litera mono_cam):**
- fy = 270 px, pół-pole pionowe 41.6° (40.4° po marginesie MTI), poziome 49.9°;
- montaż poziomy, orbita 12 m nad celem na 10 m, więc cel leży 11.3 / 14.0 / 18.4° pod osią
  przy r = 10 / 8 / 6 m.

**Mechanizm wypadania dołem:** dron po NAWIETRZNEJ stronie celu patrzy z wiatrem i przechyla się
nosem w górę. Cel wypada dołem przy pitch > 29.1 / 26.4 / 22.0°, czyli statycznie przy Ū
11.1 / 9.9 / 8.0 m/s. **Szczytem +3σ_u próg zostaje osiągnięty już przy Ū 7.1 / 6.3 / 5.1 m/s.**
Górą: pitch nosem w dół > 51.7° przy limicie przechyłu 45°, czyli **niemożliwe**.
Pomiar nauczyciela przy D6: dół ≤ 0.36% ticków, co zgadza się z progiem zjawiska.

**(c) Limity PX4 (litera parametrów, airframe 4010 → 4001 bez nadpisań MPC):**
- MPC_TILTMAX_AIR 45° (`multicopter_position_control_limits_params.c:96`) wiąże dopiero przy
  v_rel 19.9 m/s, czyli Ū ≈ 11.5 m/s ze szczytem orbity.
- MPC_THR_MAX 1.0 (:140) przy THR_HOVER 0.60 (`4001_gz_x500:50`) pozwala utrzymać wysokość
  do 53°, więc nie wiąże przed 45°.
- MPC_XY_VEL_MAX 12 m/s (:47) i V_MAX sieci 3.0 (`net_controller.py:50`) to prędkości GRUNTOWE.
  Wiatr nie zwiększa prędkości gruntowej wymaganej na orbicie (1.8 + 0.5 m/s), tylko przechył.
  **Nasycenie przed Ū ≈ 11 m/s nie zachodzi.**
- MPC_ACC_HOR 3 (`multicopter_autonomous_params.c:88`) dotyczy trybów autonomicznych. W trybie
  offboard prędkościowym nie weryfikowałem.

**(d) Mechanizmy porażki sieci w oczekiwanej kolejności:**
1. **Percepcja/track:** akwizycja na 15 m (3/3 porażek WK-II/III) pod przechyłem 17–25° i drganiami
   attitude. Obraz jest obrócony względem lotów, na których uczono det_v2, a przy Ū ≥ 5 dochodzą
   transjentne wypadnięcia dołem przy r ≤ 8 m.
2. **Zawracanie orbity** (take1 demo c04@P2).
3. **Nasycenie:** nie w drabince D2–D6.

**JEDNA LICZBA (przed S1): Ū_c = 6 m/s**, czyli D6 sieci ≤ 4/8 (pewność 0.55), z mechanizmem (1).
Obok: D2 sieci ≥ 7/8 (pewność 0.75), bo D2 jest łagodniejsze od P2, na którym sieć miała 7/8.
Jeśli D6 ≥ 5/8, sufit leży powyżej drabinki.

## R6. Projekt i wycena dla PRE (propozycje; rozstrzyga PRE)

- **Siatka:** c00–c07 × s01 na szczebel (8 epizodów = 2 booty). Kolejność D2 → D6 → bisekcja (D4,
  potem D3 lub D5) do 1 m/s. **Budżet S1 ≤ 10 bootów** + ≤ 2 booty nauczyciela na szczeblu sufitu,
  jeśli to nie D4 / D6 (te R4 pokrył dla 4 komórek).
- **Kryteria:**
  - (i) D2 < 6/8 ⇒ roszczenie „turbulencja” pada;
  - (ii) sufit = pierwsze Ū z D6 ≤ 4/8, każda porażka z mechanizmem;
  - (iii) nauczyciel pada na szczeblu ⇒ sufit płatowca lub kamery (przy D4 / D6 nie pada);
  - (iv) breach / REFUSE(POS) ⇒ STOP.
- **Do decyzji PRE:**
  - (1) walidacja σ serii: realizacja zamiast celu normy albo dłuższy przebieg (R2);
  - (2) kryterium czasu 1/e dla v / w względem teorii 0.627·L/V;
  - (3) zdanie o D2 względem P2 poprawione: łagodniejsze i wolniejsze, nowe pion i brak
    periodyczności;
  - (4) ryzyko V2′: najpierw pomiar przyczyny 0.92–0.94 w gołym świecie, bez sieci;
  - (5) t_off 40 s i okno serii 420 s pokrywają 4 epizody na boot (koniec 429.5 s < 460 s).
- **Driver S1 `wk4_boot.sh`** (do zbudowania przy PRE) = kopia `wk3_boot.sh` 039e368c z hunkami
  H3 / H4 / H5 / H6 drivera reconu niżej:
  - świat `world_wk4` z pełnym sha;
  - seria przypięta sha per profil;
  - publikator przed `run_boot` z oczekiwaniem na %CPU i na serwis scene/info;
  - kill publikatora po locie;
  - blok `wk4` w manifeście;
  - dodatkowo sprzątanie dzieci `run_boot` po kill przed uzbrojeniem (lekcja `n_D4b`).

### Pełny diff drivera reconu: `tools/wk4_calib_boot.sh` (a4d2175f) vs `wk3_calib_boot.sh` (eb095bda, nietknięty)

Hunki:
- **H1** nagłówek/użycie: `1a2,12`, `33,34c44,45`;
- **H2** katalog i log: `37,39c48,50`, `51c71`;
- **H3** świat + seria z sha: `41,43c52,60`;
- **H4** publikator: `111a132,144`, `161a195`;
- **H5** KIND i samowykluczenie: `66c86`, `114c147`;
- **H6** blok `wk4` w manifeście: `169c203`, `172a207`, `184c219,222`;
- `44a62,64` to tekst nagłówka kopii przeniesiony z H1.

```diff
1a2,12
> # results/WK4_RECON/tools/wk4_calib_boot.sh — driver bootu NAUCZYCIELA reconu WK4 (PROMPT_WK4_S0 §R4). KOPIA
> # results/WK3_RECON/tools/wk3_calib_boot.sh (eb095bda, nietknięty) ze zmianami WYŁĄCZNIE:
> #   (H1) nagłówek/użycie: 4. argument = PROFIL serii (D2…D6), świat stały world_wk4 z pełnym sha;
> #   (H2) katalog results/WK4_RECON/booty + log wk4_monitor.log;
> #   (H3) świat world_wk4 (wk4_gen_world.py) z zaszytym pełnym sha; seria results/WK4_RECON/series/<P>.json
> #        z zaszytym pełnym sha (inny plik ⇒ ODMOWA; publikator sprawdza sha drugi raz);
> #   (H4) publikator wk4_publisher.py startuje PRZED run_boot (czeka na zegar świata — trzyma oś t_sim),
> #        t_off = 40 s (próbka 0 ↔ t_sim 40 s; przed — trzyma próbkę 0, po 460 s — ostatnią), kill po locie;
> #   (H5) KIND=wk4_kalib; samowykluczenie procesowe obejmuje wk4_publisher;
> #   (H6) blok manifestu "wk4" (seria, sha, t_off, sha publikatora, log publikacji) obok bloków kopii.
> # --- nagłówek kopii (wk3_calib_boot.sh) ---
33,34c44,45
< # Użycie: wk3_calib_boot.sh <BOOT_N> <NAZWA_pod_results/WK3_RECON/booty> <EP_IDS_csv> <WORLD=world_wk3_*> <SHA256_świata>
< #   np.:  wk3_calib_boot.sh 1 kal1_p1 0 world_wk3_p1 fe96b096...
---
> # Użycie: wk4_calib_boot.sh <BOOT_N> <NAZWA_pod_results/WK4_RECON/booty> <EP_IDS_csv> <PROFIL=D2..D6>
> #   np.:  wk4_calib_boot.sh 1 n_D4 0,4,6,8 D4
37,39c48,50
< BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; EPIDS="${3:?EP_IDS}"; WORLD="${4:?WORLD}"; WORLD_SHA_ARG="${5:?SHA256 świata}"
< OUTDIR="$ROOT/results/WK3_RECON/booty/$NAME"
< MONLOG="$ROOT/results/WK3_RECON/booty/wk3_monitor.log"
---
> BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; EPIDS="${3:?EP_IDS}"; PROF="${4:?PROFIL}"
> OUTDIR="$ROOT/results/WK4_RECON/booty/$NAME"
> MONLOG="$ROOT/results/WK4_RECON/booty/wk4_monitor.log"
41,43c52,60
< case "$WORLD" in
<   world_wk3_*) WORLD_SHA_EXPECTED="$WORLD_SHA_ARG";;
<   *) echo "[wk3 $NAME] GUARD: WORLD=$WORLD spoza world_wk3_* — ODMOWA"; exit 5;;
---
> WORLD=world_wk4
> WORLD_SHA_EXPECTED="7acf407ff97e71ef10ce9cad15a12aa591e195703b6360c194d9560f3eedd1b1"
> case "$PROF" in
>   D2) SER_SHA="6e09f653d44d3c40d78e22d0365e903af8c27300ec4b590c26b2cdcbc9544b64";;
>   D3) SER_SHA="df2369dbbd73e84b7c90ed71b1d007c49d55dd5cf05ca87c5ee976559b2d7b29";;
>   D4) SER_SHA="a4c085f96fe158d90e120b479e74fed818e1ef37359e9edf8b50983e8e528624";;
>   D5) SER_SHA="caa1079448fa29b44ae5ec2f21b1f0b474e690a93f8067a2dd4f2d472591da3e";;
>   D6) SER_SHA="673e09e1e07ac4fe66c76fa29d4943ef7cc20b912b88738cd93497c7c232f051";;
>   *) echo "[wk4 $NAME] GUARD: PROFIL=$PROF spoza D2..D6 — ODMOWA"; exit 5;;
44a62,64
> SER="$ROOT/results/WK4_RECON/series/$PROF.json"
> T_OFF=40.0
> [ "$(sha256sum "$SER" | cut -d' ' -f1)" != "$SER_SHA" ] && { echo "[wk4 $NAME] SHA SERII FAIL $SER — ODMOWA"; exit 5; }
51c71
< mkdir -p "$ROOT/results/WK3_RECON/booty"
---
> mkdir -p "$ROOT/results/WK4_RECON/booty"
66c86
< COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent|percep_proc' 2>/dev/null | grep -v -e "$$" -e perc2_s2_boot -e pgrep)"
---
> COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent|percep_proc|wk4_publisher' 2>/dev/null | grep -v -e "$$" -e perc2_s2_boot -e pgrep)"
111a132,144
> # (H4) publikator serii PRZED światem/PX4 — czeka na /world/world_wk4/clock, trzyma oś t_sim
> setsid nohup python3 "$ROOT/results/WK4_RECON/tools/wk4_publisher.py" "$SER" "$SER_SHA" "$WORLD" "$T_OFF" \
>   "$OUTDIR/wind_pub.jsonl" 20 > "$OUTDIR/wind_pub_stdout.log" 2>&1 &
> PUB=$!
> sleep 2
> kill -0 "$PUB" 2>/dev/null || { echo "[wk4 $NAME] publikator nie wstał — STOP"; cat "$OUTDIR/wind_pub_stdout.log"; exit 6; }
> # proc_gate run_boota liczy %CPU z ps (średnia od startu procesu): koszt importów publikatora musi się
> # rozmyć < 1 % zanim run_boot sprawdzi bramkę (pierwsza próba n_D4: ENV-BLOCK przy 2.6 %)
> for i in $(seq 1 90); do
>   PC=$(ps -o pcpu= -p "$PUB" | tr -d ' '); awk -v p="$PC" 'BEGIN{exit !(p<1.0)}' && break; sleep 1
> done
> echo "[wk4 $NAME] publikator %CPU(ps)=$PC po ${i} s" | tee -a "$MONLOG"
> echo "[wk4 $NAME] publikator pid=$PUB seria $PROF sha ${SER_SHA:0:16} t_off=$T_OFF" | tee -a "$MONLOG"
114c147
< env FLIGHT=bench CONTROLLER=orbit INTRUDER=1 WORLD=$WORLD FILM=0 KIND=wk2_kalib \
---
> env FLIGHT=bench CONTROLLER=orbit INTRUDER=1 WORLD=$WORLD FILM=0 KIND=wk4_kalib \
161a195
> kill -TERM "$PUB" 2>/dev/null; sleep 1; kill -9 "$PUB" 2>/dev/null
169c203
< python3 - "$OUTDIR" "$BN" "$SONDA_RC" "$PIN_GOT" "$WORLD" "$WORLD_SHA_GOT" "$WIND_PIN_GOT" <<'PY'
---
> python3 - "$OUTDIR" "$BN" "$SONDA_RC" "$PIN_GOT" "$WORLD" "$WORLD_SHA_GOT" "$WIND_PIN_GOT" "$SER" "$SER_SHA" "$T_OFF" <<'PY'
172a207
> ser, ser_sha, t_off = sys.argv[8], sys.argv[9], float(sys.argv[10])
184c219,222
< m["wk2"] = {"rola": "POMIAR WIATRU/FIZYKI (PROMPT_WK3_S0 §R3) — nauczyciel, feed emulowany; zero miar misji",
---
> m["wk4"] = {"seria": os.path.relpath(ser, ROOT), "seria_sha256": ser_sha, "t_off_s": t_off,
>            "publikator_sha256": fsha(os.path.join(ROOT, "results/WK4_RECON/tools/wk4_publisher.py")),
>            "log_publikacji_sha256": fsha(os.path.join(outdir, "wind_pub.jsonl"))}
> m["wk2"] = {"rola": "RAMIĘ ODNIESIENIA (PROMPT_WK4_S0 §R4) — nauczyciel, feed emulowany; sieć NIE lata",
```

## Pliki (nowe; sha256/8)

| plik | sha | | plik | sha |
|---|---|---|---|---|
| `tools/wk4_dryden.py` | 19b4249d | | `tools/wk4_windprobe.py` | 013467b8 |
| `tools/wk4_r3.py` | 5aa21f19 | | `tools/wk4_gen_world.py` | 84ee0eca |
| `tools/wk4_publisher.py` | 746a958b | | `tools/wk4_calib_boot.sh` | a4d2175f |
| `tools/wk4_view.py` | 40b91117 | | `tools/wk4_r5.py` | cbd15eb7 |
| `worlds/world_wk4.sdf` | 7acf407f | | serie D2–D6 | jak w tabeli R2 |

Diff-stat i porcelain: commit STOP-WK4R. W commicie wyłącznie nowe pliki (`results/WK4_RECON/**`,
`worlds/world_wk4.sdf`), zero edycji istniejących. boot.ulg według `.gitignore`.

**Push = Olga („wypchnięte” — CC czyta z repo i przelicza walidację serii niezależnie). STOP-WK4R.**
