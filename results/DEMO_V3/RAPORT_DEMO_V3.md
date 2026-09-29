# RAPORT_DEMO_V3 — sesja 1: build + bramka świata FAIL 2/2 → STOP (fallback niewykonalny)

LiquidPatrol · pozycja demo · CC 29.09.2026 · PROMPT_DEMO_V3. **DEMO ≠ POMIAR** — żadna liczba
stąd nie wchodzi do ksiąg. Sesja 1 z ≤2; budżet bootów: **2/8 zużyte** (2 biegi kontrolne bramki).
AKTY NIE POLECIAŁY — bramka §2 blokuje; zero REFUSE, zero zdarzeń lotnych do raportowania.

## §0. Bramka wejścia
`origin/master` w chwili startu NIE zawierał e526612 (CO-W) ani commita ANEKS_W-2a. Per §0.1
(„prośba o push/wykonanie, potem dalej"): commit **ANEKS_W-2a wykonany w sesji** —
`4550af8` (gitignore glob `results/**/.last_boot_end`, treść w pełni określona w §0.1) —
i wysłana jedna prośba o push {e526612, 4550af8}; sesja kontynuowała build (zero bootów przed
bramką świata). FROZEN nietknięte (piny, sędziowie, wagi 0337d5ea, run_boot, w_launcher, FREEZE_W,
światy world_wind_s*).

## §1. Zbudowane (gotowe do aktów po ratyfikacji)
- **Światy (NOWE)**: `worlds/gen_world_wind_v3.py` + `world_wind_v3_s0/s1p5/s3.sdf` — baza
  world_demo_v3_1 (uplift U2R, cast_shadows=false) + pełny stack 13 systemów + WindEffects
  (pułapka R1.8) + wektor per poziom + **kamera filmowa per świat** pod zmierzone koperty
  epizodów (c10_s02 / c11_s01 / c11_s02 z trace'ów DEMO_V2 i kampanii W). sha:
  s0 `98a9aa92…` · s1p5 `aa625ff1…` · s3 `b23ce93e…`. Poprawka znaku pitch względem helpera
  `gen_world_demo_v1._cam_pose` (dowód: suchy preview; komentarz w generatorze). Kadry
  zweryfikowane suchymi preview (wzór U2R-2 §2, poza budżetem bootów).
- **Narzędzia** (`results/DEMO_V3/tools/`): `film_recorder.py` (jeden proces, klatki ze
  stemplami sim-time z headera — zero churnu subprocess, lekcja D §5c), `run_demo_v3_boot.sh`
  (booty WYŁĄCZNIE przez zamrożony w_launcher/run_boot; OUTDIR pod DEMO_V3 przez względny
  OUTREL `../DEMO_V3/...` — launcher nietknięty, guardy działają), `panel_montage.py`
  (canvas 1920×1080: lot 720p po lewej, panel 600 px: MODE/wiatr/przechył/pasek wysokości
  z linią V_E=20/dystanse/minimapa[dodatek ponad listę §5 — do werdyktu]/captions; montaż
  real-time 1:1 sim; podkomenda `sanity` = 3 klatki kontrolne wzór U1R).
- **CAPTIONS_VERBATIM.txt** (szkic): footer w brzmieniu DYKTOWANYM §6; captions = zdania
  opisowe + wierne EN renderingi zdań WOLNO (W §5 / NET §11 / K2 §7; precedens EN = DEMO_V2 §6);
  czasy do finalizacji po aktach. Nota: „sha wideo" w outro jest samoreferencyjne — w outro
  prowieniencja bez sha wideo, sha w raporcie (jak DEMO_V2 §1).
- `.gitignore`: + `results/DEMO_V3/**/frames/` (wymóg §0.3, wzór linii DEMO_V2).

## §2. BRAMKA ŚWIATA — FAIL 2/2 (progi byte-identyczne z U2 [3]/U2R [4])
Bieg kontrolny = pełna konfiguracja filmowa: FLIGHT=bench, c10_s02 (ep 22), CONTROLLER=net,
W_ARM_ALWAYS=1, FILM=1 + film_recorder (8 fps), world_wind_v3_s0, przez w_launcher (lock,
pgrep, cooldown ≥300 s). Okno pomiaru = okno epizodu.

| bieg | Δsim/Δwall (≥0.95) | frac<0.5 (=0) | min_rtf | timejump | kadr-check | klatki |
|------|--------------------:|---------------:|--------:|----------|------------|-------:|
| control_1 | **0.9383** | 0.0034 | 0.017 | 0 | OK (dron+intruz+akcja) | 1218 |
| control_2 | **0.9366** | 0.0034 | 0.010 | 0 | OK | 927 |

(Oba biegi: longest_stall 0.0, n_deep_stall 3, refuse 0, breach false, valid_V2p=True,
world_hash `98a9aa92…` w manifestach, weights 0337d5ea guard OK, stemple sim-time klatek
poprawne — span pokrywa lot.)

## §3. Diagnoza (liczby, nie opinia): próg 0.95 mierzy tu POPULACJĘ PĘTLI, nie świat
1. **Estetyka v3 i pipeline filmowy NIE są przyczyną**: kampania W (16 bootów, światy surowe
   world_wind_s*, BEZ filmu, ta sama pętla ławki) miała dsim_dwall 0.908–0.960, mediana
   **0.938** — biegi kontrolne (0.9383/0.9366, Z filmem i sceną v3) siedzą DOKŁADNIE na tej
   medianie. Dodanie sceny v3 + kamery + rejestratora nie kosztuje nic mierzalnego.
2. **Progi U2 były kalibrowane na innej populacji**: U2R control_1 (0.9997) to lot AKTOWY
   (gate_r03-kształtny) na world_demo_v3. Pętla ławki (bench_flight: ciągły teleport intruza
   + feed + osłona per tick) ma na tym hoście systematycznie Δsim/Δwall ~0.94 — w 19 bootach
   ławkowych od 28.09 (17 kampanii W + 2 kontrolne) próg ≥0.95 osiągnęły 2/19.
3. Wniosek: przy scenariuszu demo = epizody ŁAWKI, próg 0.95 jest nieosiągalny niezależnie od
   świata — bramka w tym brzmieniu odrzuca każdy możliwy materiał, także taki, którego habitat
   jest bit-klasy z ważnymi bootami kanonicznej kampanii W (V2′: dsw≥0.90 ∧ longest≤1.5 ∧ tj=0).

## §4. Fallback §2 jest technicznie NIEWYKONALNY — stąd STOP zamiast fallbacku
„2. FAIL ⇒ finał na światach surowych world_wind_s*": zamrożone światy s* NIE zawierają
kamery filmowej (`grep -c camera world_wind_s3.sdf` = 0) — FILM=1 nie znajduje topiku, zero
klatek, film fizycznie niemożliwy. Dodanie kamery do kopii świata surowego = nowy świat
(sprzeczne z „fallback zamrożony"), więc bez ratyfikacji NIE wykonano. Zero dalszych bootów
(akty zablokowane bramką). To odpowiednik precedensu W-S2/route: przyrząd odmówił, wykonawca
nie improwizuje.

## §5. Pytania do ratyfikacji (ANEKS_DEMO3-1 albo sub-numer)
Q1 [rekomendacja CC]: bramka świata dla DEMO_V3 przechodzi na reżim ważności KAMPANII
    (V2′: Δsim/Δwall≥0.90 ∧ longest_stall≤1.5 ∧ timejump=0) ∧ kadr-check — czyli dokładnie
    ten reżim, pod którym osądzono kanoniczne dane W cytowane w filmie. Oba biegi kontrolne
    JUŻ go spełniają ⇒ bramka PASS retroaktywnie, akty lecą na world_wind_v3_* bez nowych
    biegów kontrolnych (budżet zostaje 6/8 na 3 akty + ≤2 podejścia sejwu + zapas).
Q2 [alternatywa]: ratyfikacja wariantu „świat surowy s* + WYŁĄCZNIE model film_cam" jako
    nowych plików (world_wind_s*_cam.sdf) — kosztem estetyki wbrew wizji „ładny domyślnie".
Q3 [alternatywa]: rezygnacja z filmu / zmiana kształtu (np. akty na locie gate_r03-kształtnym,
    który przechodzi 0.95 — ale to NIE jest materiał ławki z sejwem W).
Do decyzji też: minimapa w panelu (dodatek ponad listę §5) — zostaje / wypada.

## §6. Higiena (REPO-1 / D3-6)
Booty: 2 (gate/control_1, control_2), oba z manifestami 1. klasy; klatki lokalnie (gitignore);
zero powtórek, zero REFUSE, zero kolizji wyłączności; host po sesji czysty. Porcelain przed
commitem: nowe worlds/gen_world_wind_v3.py + world_wind_v3_s*.sdf, results/DEMO_V3/**
(tools, captions, gate, raport), zmodyfikowany .gitignore. Po commicie drzewo czyste.
Push = Olga (razem z zaległymi e526612 + 4550af8, jeśli jeszcze nie poszły).
Sygnały bez numeru odrzucam; do ratyfikacji zero bootów.
