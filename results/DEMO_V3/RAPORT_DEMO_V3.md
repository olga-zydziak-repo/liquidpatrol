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


---

# SESJA 2 (po ANEKS_DEMO3-1) — akty + montaż → STOP-D3

## §7. Bramka wejścia S2 + ARCH-1
origin/master zawierał e526612+4550af8+1c7cc22 (push Olgi) ⇒ dalej. ARCH-1: `ANEKS_DEMO3-1.md`
pierwszym commitem sesji 2. Bramka świata per ANEKS_DEMO3-1 §2: **V2′ ∧ kadr-check = PASS
retroaktywnie** (control_1/2: 0.9383/0.9366 ≥0.90, tj 0, kadr OK); reguła DEMO-1 przyjęta.

## §8. Booty aktów (ziarna JAWNE, uzasadnienia 1-zdaniowe; wszystkie: net, W_ARM_ALWAYS=1, FILM=1)
| akt | boot | świat (sha) | epizod | V2′ (dsw) | REFUSE | z_max | max przerwa sim klatek |
|-----|------|-------------|--------|-----------|--------|-------|------------------------|
| 1 | act1/take_1 | v3_s0 (98a9aa92) | c10_s02 (ep22) | VALID (0.9213) | 0 | 13.8 | **0.26 s** |
| 2 | act2/take_1 | v3_s1p5 (aa625ff1) | c11_s01 (ep11) | VALID (0.9296) | 0 | 13.6 | **0.43 s** |
| 3 | act3/take_1 | v3_s3 (b23ce93e) | c11_s02 (ep23) | VALID (0.9396) | 0 (brak repro) | 15.1 | 1.12 s (nie-materiał) |
| 3 | act3/take_2 | v3_s3 (b23ce93e) | c11_s02 (ep23) | VALID (0.9238) | **1 GEOFENCE** | 19.4 | **0.82 s** |

Uzasadnienia ziaren: c10_s02 = wzór D1a DEMO_V2 (pełne podejście + orbita RUCHOMEGO intruza);
c11_s01 = ziarno, pod którego zmierzoną kopertę xy ustawiona jest kamera świata s1p5 (poziom 1.5
wybrany dla czytelności: ciaśniejszy kadr niż s0, przechył ~2× względem L0); c11_s02 = DOKŁADNIE
konfiguracja kryterialna sejwu (ANEKS_DEMO3-1/§4 promptu). Poziom aktu 2 = 1.5 (nie 3.0), bo akt 3
i tak niesie 3.0 — film pokazuje drabinę 0 → 1.5 → 3.0.

## §9. Akt 3 — REPRODUKCJA SEJWU (podejście 2/2)
take_1: refuse 0, z_max 15.08 (emergent nie zaszedł — boot zachowany, zaraportowany).
take_2: **REFUSE(GEOFENCE) @ sim 181.68 (t_rel epizodu 68.0 — kryterialny: 68.5), r_est 19.94,
z_max GT 19.42, breach false** — sejw zreprodukowany na żywo; panel podpisuje akt jako
„demo re-flight", liczby roszczeniowe w captions cytowane z epizodu KRYTERIALNEGO (RAPORT_W §2).
Fallback trace-driven NIEPOTRZEBNY.

## §10. Warunek płynności (ANEKS_DEMO3-1 §2)
Oś czasu montażu budowana ze STEMPLI SIM-TIME klatek (frames_index.jsonl), nie z fps.
Maksymalna przerwa sim między kolejnymi klatkami w materiale aktów: 0.26 / 0.43 / 0.82 s —
**wszystkie <1 s, zero widocznych freeze'ów ⇒ PASS, zero powtórek z tego tytułu**.

## §11. Sanity panelu (3 klatki kontrolne, wzór U1R; `results/DEMO_V3/sanity/`)
| akt | sim_t | MODE (panel=trace) | z_gt | tilt | wiatr cfg |
|-----|-------|--------------------|------|------|-----------|
| 1 | 150.0 | OBSERVE (phase=orbit) | 11.985 | 8.84 | 0,0,0 |
| 2 | 160.0 | OBSERVE (phase=orbit) | 13.756 | 17.16 | 1.5,0,0 |
| 3 | 182.2 | REFUSE (reason GEOFENCE) | 19.016 | 17.66 | 3.0,0,0 |
Wartości panelu = wartości źródłowe z konstrukcji (renderer czyta wyłącznie trace/demo/ulog/
manifest); PNG + sanity.json w repo. Minimapa (ANEKS_DEMO3-1 §4): pozycje = own/trk z demo.jsonl.

## §12. Artefakt finalny
`results/DEMO_V3/DEMO_V3.mp4` — **362.6 s (6:03)**, 1920×1080 @ 10 fps, mp4v (cv2, bez ffmpeg),
37 478 472 B, sha256 `eac816983fcea2fb03e28ac8ad7d2a4bf9dcb0c64c808f0177480be5d0c10e81`.
Kompozycja: intro 8 s → akt1 114.2 s → akt2 115.4 s → akt3 110.0 s → outro 15 s; **4 cięcia,
wyłącznie na granicach aktów**; materiał aktów = czas symulacji 1:1. Segmenty pośrednie usunięte
(odtwarzalne lokalnie z klatek + act.json). Klatki źródłowe ~11 GB lokalnie (gitignore).
Nota: akt kończy się na końcu trace'u (opadanie ~5 m AGL) — panel pozostaje uczciwy do ostatniej
klatki; touchdown zachodzi po zamknięciu trace'u (teardown), poza materiałem.

## §13. Odchylenia/noty sesji 2
1. Budżet bootów: **6/8** (2 bramka + 4 akty; limit dotrzymany). Sesje: 2/2.
2. take_1 aktu 3 miał max przerwę 1.12 s — nie jest materiałem; warunek płynności dotyczy
   materiału aktów (wszystkie <1 s).
3. CAPTIONS_VERBATIM.txt: czasy sfinalizowane po bootach (+8 s pre-roll dla długości celowej);
   pełna treść w repo — do werdyktu kanoniczności ANEKS_DEMO3-2 (EN renderingi zdań WOLNO).
4. „sha wideo" w outro = samoreferencja — prowieniencja w outro bez sha; sha w §12 (precedens
   DEMO_V2 §1).
