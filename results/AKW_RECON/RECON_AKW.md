# RECON_AKW — recon nogi AKW (akwizycja): skan yaw przed-ENTRY, brama pod rotacją, plan kampanii

CC · 08.10.2026 · wykonanie PROMPT_AKW_S0. **Zero bootów, zero SITL, zero edycji
istniejących plików**; nowe pliki wyłącznie `results/AKW_RECON/**` (narzędzie:
`tools/akw_rot_strat.py`; inferencja det_v2 offline na ISTNIEJĄCYCH klatkach,
env = `.b0deps` PYTHONPATH jak lot). Czeka PRE_AKW (numerowany).

## §0. Bramka wejścia — PASS

`git fetch` → origin/master zawiera **b8d23db (CO-DET)** ✓ · `origin/master..HEAD`
puste ✓ · porcelain pełny pusty ✓. FROZEN wykonaniem: **piny 5/5** (k1_shield_pins:
SHIELD FROZEN True; shield 1c584964 · config 4c440e42 · gate_run 5647ae20 · base
7fc45cf2 · safe_descend e3c1040b) · **certy 9/9** (certs_selfcheck PASS). Sha
przeliczone i ZGODNE z FREEZE_DET: bench_flight `05137098` · bench_judge `8ec0fcfb` ·
feed_vision `acc81df7` · det_v2.pt `775ead15` · ncp `0337d5ea` · det_v2.py `e801f7d5` ·
percep_proc `38a3a765` · feed_vision_proc `79633489` · feed_registry `ee1481f9`.
**Kolizja nazwy „AKW": BRAK** — grep repo trafia wyłącznie słowo „akwizycja/akwizycyjny"
w dokumentach DET (grep-odróżnialne); żaden katalog, łańcuch, env ani skrót nie używa
„AKW". Rekomendacja: prefiks env **`AKW_`**, katalog wyników `results/AKW/`.

## §R1. Kto dziś komenduje yaw przed-ENTRY — pełny tor i punkty wpięcia

**Emisja (kontroler):** `r03/controllers/net_controller.py:115` — przy ważnym tracku
`yaw = math.atan2(rely, relx)` [rad] („twarz ku intruzowi", kosmetyka jak egzekutor;
egzekutor analogicznie `orbit_executor.py:75`). **Gałąź hover-hold:**
`net_controller.py:107-111` — gdy `fd is None ∨ ¬track_valid ∨ track_age_s >
TRACK_LOSS_S (=1.0, :35)` zwraca `_cmd([0,0,0], tgt=own, …, yaw=0.0, "hold")` —
**yaw jest STAŁĄ 0.0 rad**, nie „ostatnim yaw". Nos jest więc czynnie komenderowany
na azymut 0 (północ) przez cały ślepy zawis — to jest mechanizm 29 ślepych epizodów
DET (stożek = 0° ± 49.85°).

**Granica jednostek (bench):** `bench/bench_flight.py:398-403` — gałąź ALLOW wysyła
`VelocityNedYaw(v[0], v[1], v[2], math.degrees(cmd.get("yaw", 0.0)))` (konwersja N1
wyłącznie na granicy MAVSDK). Gałęzie REFUSE (:395) i D5 (:389) wysyłają yaw=0.
**Komenda jest KĄTEM yaw (deg na API), nie yawspeed** — po stronie PX4 trafia
w `TrajectorySetpoint.yaw` (euler, rad, −π..π; `yawspeed` to osobne, nieużywane pole —
`PX4-Autopilot/msg/versioned/TrajectorySetpoint.msg`).

**Osłona yaw NIE konsumuje:** `r01/shield.py:121` `step(k, pos, vel, target, mode,
pos_flag, auth_ok)` — yaw nie jest argumentem; bariera geofence = `radial(target)` ∨
`radial(pos)+braking(vel)` ∨ `|z|` (`r01/shield.py:101-113`).

**Cykl:** kontroler instancjonowany PER EPIZOD (`bench_flight.py:310-312`,
`make_controller(CONTROLLER, …)` + `ctrl.reset()`); pętla komend 20 Hz
(`r01/config.py:40-41` TICK_HZ=20/DT=0.05; `bench_flight.py:416` sleep(DT));
`controller_sha` = sha pliku modułu klasy → manifest (`r03/controllers/__init__.py:
controller_sha`).

**Kandydackie punkty wpięcia skanu:**

| wariant | miejsce | diff | ocena |
|---|---|---|---|
| (a) edycja gałęzi hold | `net_controller.py:108-111` | ~3 linie | ODRADZANE: edytuje lecący plik nogi NET (controller_sha we wszystkich manifestach od NET; bajty frozen konwencją programu) |
| **(b) NOWA klasa-wrapper + rejestr additive** | nowy plik `r03/controllers/akw_scan.py` + `__init__.py:18-24` `_REGISTRY` | **1 nowy plik (~40 linii) + 2 linie rejestru (import + wpis)** | **REKOMENDOWANE** — rejestr jest na to projektowany (`__init__.py:8`: „Rejestr rozszerza ławka/sieć DOPISANIEM klasy — bez dotykania osłony/pętli (SR-9)"); precedensy additive: LIQ `gru`/`mlp20` w tym samym rejestrze, DET wpis `V2` w feed_registry |
| (c) nadpis w ALLOW benchu | `bench_flight.py:396-403` | ~4 linie | ODRADZANE: edycja frozen 05137098 (historycznie już 3 ratyfikowane edycje; tu niepotrzebna) |

Szkic (b): klasa `AkwScan(SetpointSource)`, `name="net_akw"`; konstruktor buduje
wewnętrzny `NetController(**kw)` (guard SR-2 sha wag zachowany bez zmian); `step()`
deleguje i TYLKO gdy `extra.phase=="hold"` podmienia pole `yaw` na profil skanu
ψ(t); `reset()` zeruje fazę skanu. Uruchomienie: `CONTROLLER=net_akw` (env, zero
zmian driverów poza wartością zmiennej). Manifest niesie sha nowego pliku;
sha `__init__.py` po wpisie → FREEZE_AKW.

**Czego skanowi NIE WOLNO dotknąć (wszystko FROZEN):** wagi `net/frozen/*` (ncp
0337d5ea, det_v2 775ead15); osłona + piny 5/5 (shield/config/gate_run/base/
safe_descend); percepcja `harness/{feed_vision, det_v2, percep_proc,
feed_vision_proc}` i rejestr feedów ee1481f9; brama admisyjna `r02/*` (ENTRY k=3,
edge-margin 0.10, θ_conf, θ_age 3.0); `bench_flight` 05137098; `bench_judge`
8ec0fcfb. Skan = wyłącznie WARTOŚĆ pola `yaw` w cmd kontrolera w fazie hold —
pole istnieje w kontrakcie od zawsze (`base.py` docstring: `"yaw": float [rad]`).

## §R2. Dynamika skanu — desk-matematyka + limity PX4 (z drzewa, nie z pamięci)

**Limity PX4** (drzewo `PX4-Autopilot/` v1.16.2, commit 54f0455ffc; airframe
`4010_gz_x500_mono_cam` dziedziczy `4001_gz_x500` — ZERO nadpisów MC_YAW*/MPC_YAW*
⇒ obowiązują domyślne):
- `MC_YAWRATE_MAX = 200°/s` (`src/modules/mc_att_control/mc_att_control_params.c:147`),
  nałożone w `mc_att_control_main.cpp:97-98` (`setRateLimit`);
- `MC_YAW_P = 2.8` (:79), `MC_YAW_WEIGHT = 0.4` (:97) z kompensacją gainu
  (`AttitudeControl/AttitudeControl.cpp:49-51`: `P(2) /= yaw_w`) ⇒ **efektywne
  P_yaw ≈ 2.8 1/s**;
- `MPC_YAWRAUTO_MAX = 45°/s` dotyczy goto/auto (`multicopter_autonomous_params.c:148`,
  konsument `_goto_control` `MulticopterPositionControl.cpp:210`) — **NIE offboard**.

**Nadążanie za rampą** ψ(t)=ψ₀+ω·t (setpoint = kąt bezwzględny, slew robi PX4):
opóźnienie ustalone ≈ ω/P_yaw = **5.4° / 10.7° / 21.4°** @ 15/30/60°/s — wszystkie
≪ pół-stożka 49.85°; cap 200°/s nieaktywny przy prędkościach skanu.

**Geometria stożka:** FOV 99.7° (pół-kąt 49.85°, pinhole f_px=270 ⇒ 320/tan=270 ✓).
Efektywny stożek **ENTRY** węższy przez edge-margin 0.10 (`r02/config_r02.py:36`,
cx∈[0.10,0.90] ⇒ atan(0.4·640/270)=43.5°) ⇒ **~86.9°**.

**Rachunek czasu (cel statyczny, skan ciągły 360°; obie kadencje bimodalne):**

| ω | czas w stożku ENTRY 86.9°/ω | klatek @14.71 Hz | @7.58 Hz | worst-case czekanie 273.1°/ω | t_entry (D6 ≤25 s) |
|---|---|---|---|---|---|
| 15°/s | 5.8 s | 85 | 44 | 18.2 s | ~21 s — **na styk** |
| 30°/s | 2.9 s | 43 | 22 | 9.1 s | ~12 s — komfort |
| 60°/s | 1.45 s | 21 | 11 | 4.6 s | ~7.6 s — komfort, ale pasmo R3 25+ cienkie |

(t_entry = czekanie + dolot do pasma 6–10 m z ~15 m @ ≤3 m/s ≈ 2–3 s; sędzia:
`bench_judge.py:122-123` t_entry≤25 ∧ frac_band≥0.85.) ENTRY k=3 kolejnych admisji
(`config_r02.py:27`) osiągalne wszędzie (minimum 11 klatek w stożku @60°/s∧7.58 Hz).
`ENTRY_MOVE_THR=0.15` przekątnej/klatkę (:30) NIE pada: ruch od skanu @30°/s∧14.71 Hz
≈ 2.0°/kl ≈ 13 px ≈ 0.016 przekątnej; worst 60°/s∧7.58 Hz ≈ 51 px ≈ 0.064 < 0.15 ✓.

**Profil:** ciągły jednokierunkowy 360° > wahadłowy (wahadło podwaja worst-case
dla sektora „za plecami"; ciągły daje deterministyczny sufit 273°/ω). Kierunek do
zamrożenia w PRE (scena symetryczna; naturalny CCW jak orbita).

**Po akwizycji:** wrapper przestaje nadpisywać (phase≠hold) — przejmuje
`yaw=atan2` (`net_controller.py:115`); skok setpointu ≤ ~43.5° (cel musi być
w stożku ENTRY), slew P=2.8/cap 200°/s — bez szarpnięcia.

**Po utracie:** hold wyzwala się po `TRACK_LOSS_S=1.0 s` (`net_controller.py:35`),
a kanał/feed wygasa dopiero po `θ_age=3.0 s` (`config_r02.py:52`;
`feed_vision.py:175`); REFRESH-okno 3.0 m wokół predykcji (`feed_vision.py:195-208`,
`REFRESH_GATE_M=3.0`) może odzyskać track — ale tylko jeśli nos jeszcze patrzy na
cel. **Do PRE: dwell przed wznowieniem skanu** (kandydat: θ_age−TRACK_LOSS = 2.0 s
trzymania ostatniego yaw), potem skan OD BIEŻĄCEGO yaw (ciągłość, bez powrotu do 0).

## §R3. Brama pod rotacją — ZMIERZONE na istniejących danych (0 lotów)

Narzędzie `tools/akw_rot_strat.py`: (a) replay frozen `det_replay.py` (de0feb37)
z `--detector det_v2.pt` na 12 bootach dolotu S1 (FEED=B, 15 Hz, 8 036 klatek,
GPU, wall ~15 s/boot) → `replays/`; (b) żywe `percep_feed.jsonl` z 12 bootów V2
kampanii C (det_v2 w pętli zamkniętej, zero inferencji). Yaw z `own_q` (wxyz),
yaw_rate różnicą centralną na unwrapped ψ (pary dt≤0.3 s — odcina teleporty);
etykieta celu: BootGeo 8f7430cd, kryterium on-target IDENTYCZNE jak
`det_replay.py:147-151`. **Walidacja przyrządu:** moje replaye D03/D07 odtwarzają
artefakty S2 CO DO LICZBY (0.579/0.725/0.88 n=575 on 99.7 · 1.234/1.388/1.602
n=686 on 100.0) — ten sam tor bajtów.

**(a) REPLAY dolotu B (det_v2 offline):** mediany |yaw_rate| per bin 2.1/15.2/34.0 °/s

| bin °/s | n | n_fov | on-target% | fp_fov | box_nofov | fresh% | g_mti | g_win | ENTRY | EXPIRE |
|---|---|---|---|---|---|---|---|---|---|---|
| 0–10 | 3423 | 1788 | 99.8 | 4 | 691 | 67.0 | 2123 | 171 | 9 | 8 |
| 10–25 | 4069 | 4004 | **99.9** | 3 | 30 | **98.7** | 3944 | 72 | 1 | 2 |
| 25+ | 447 | 303 | 98.7 | 4 | 57 | 66.9 | 289 | 10 | 5 | 0 |

**(b) ŻYWE V2 kampanii C (pętla zamknięta):** mediany 0.0/14.0/52.1 °/s

| bin °/s | n | n_fov | on-target% | fp_fov | box_nofov | fresh% | g_mti | g_win | ENTRY | EXPIRE |
|---|---|---|---|---|---|---|---|---|---|---|
| 0–10 | 16912 | 2841 | 97.3 | 57 | 617 | 16.7 | 2717 | 111 | 17 | 15 |
| 10–25 | 7759 | 7633 | **99.8** | 12 | 11 | **98.2** | 7593 | 30 | 1 | 2 |
| 25+ | 558 | 339 | 88.2 | 29 | 37 | 48.6 | 233 | 38 | 4 | 0 |

(fresh% liczone po WSZYSTKICH klatkach bina — niskie wartości w 0–10 i 25+ to
głównie klatki BEZ celu w FOV: ślepe zawisy w (b), brzegi epizodów; box_nofov to
w przewadze klatki z flagą F2 = poza oknem GT intruza, nie dowiedzione tło.)

**Odpowiedź na pytanie rozstrzygane danymi:** w paśmie **10–25°/s brama admituje
cel praktycznie w całości i nie wpuszcza tła** — on-target ≥99.8 %, fresh ≥98 %,
gate zdominowany przez mti, w obu źródłach niezależnie (n=4069 replay + 7759 live).
Przy **25+°/s łagodna degradacja** (on-target 98.7 replay / 88.2 live, admisja
warunkowa na FOV nadal wysoka), ale pasmo jest CIENKO próbkowane (n=447/558, mediany
34/52 °/s). **Fałszywe ENTRY na tle pod rotacją: brak potwierdzonych** — z 15 ENTRY
replayu 7 „bez celu" to w 7/7 flaga F2 (okno GT przy spawn/pozycjonowaniu ≈ t 108 s —
dokładnie mechanizm „lock przed epizodem" z ANEKS_DET-4 §3, tu widoczny w danych);
z 23 ENTRY live 1 kandydat tła (r3_V2 @317.1 F3_out_of_fov), reszta analogicznie F2/F1.

**Ograniczenie reprezentatywności (nazwane):** cała rotacja korpusu to rotacja
Z ORBITĄ/nadążaniem — nos ŚLEDZI cel (cel centralny w kadrze, tło przepływa).
Pomiar dowodzi odporności detekcji celu centralnego i odrzucania tła POD rotacją
kadru; **NIE mierzy detekcji celu PRZELATUJĄCEGO przez kadr** (geometria czystego
skanu w zawisie: cel wchodzi od krawędzi i transituje w 86.9°/ω). Wniosek dla
smoke: smoke MUSI zawierać akwizycję ZE SKANU na scenariuszu ślepym DET (bearing
90/180/270°) — replay tej geometrii nie wytworzy z istniejących klatek.

## §R4. Projekt kampanii powtórkowej (do zamrożenia w PRE)

**(i) 12 rund × {B, V2+skan} — REKOMENDOWANE.** Powtórka DET S4 VERBATIM z jedną
zmianą env w ramieniu V2: `CONTROLLER=net_akw` (driver detS4_boot jako wzór; nowy
driver kopiujący, zero edycji starego). Zalety: Δ_new liczona na TYCH SAMYCH 48
parach, tych samych progach zdania zamrożonego PRE_2A §4 i wprost porównywalna
z Δ=34; 29 ślepych epizodów DET = gotowy zbiór odniesienia per para; narzędzia
parowania (detS4_pairs.py) reużywalne co do wzoru. Świeże ramię B kontroluje dryf
habitatu w tej samej sesji. Koszt: **24 booty + zapas 3, 1 sesja lotna** (wzór S4:
24 booty, 09:22–14:54), dysk ~3 GB (wzór `results/DET/camp`).

**(ii) 12 rund × {V2-bez, V2+skan}** — izoluje samo zachowanie, ale: ramię V2-bez
to re-pomiar znanej liczby (13/48) za 12 bootów; progi PRE_2A są zdefiniowane dla
pary wyrocznia-vs-percepcja (Δ(V2,V2+skan) nie ma zamrożonej interpretacji);
izolację daje już porównanie z kampanią DET (identyczna siatka, percepcja
i scenariusze — jedyna zmiana to skan). **Jako pełne ramię NIEREKOMENDOWANE;**
opcjonalnie sonda 2–4 booty (1–2 rundy pary), jeżeli PRE uzna kontrolę świeżości
habitatu V2-bez za potrzebną.

**Smoke przed kampanią (1 boot + naprawcze ≤2):** scenariusz ŚLEPY z DET (komórka
bearing 180° lub 90/270°, np. c01/c02) — zdarzenie bramkowe = **akwizycja ZE SKANU**
(ENTRY po starcie skanu) + bramki runtime jak detS3 (kadencja, E2E) + S-BEZP + V2′;
rekomendacja: smoke w trybie bootu KAMPANIJNEGO (4-epizodowy), domykając klasę
przyrządową „smoke jednoepizodowy niereprezentatywny dla akwizycji" (rejestr,
ANEKS_DET-4 §3/§7).

**Kosztorys łączny nogi:** build 0 bootów (wrapper + testy przedlotowe wzór
test_aneks_det2) · smoke 1 (+2 naprawcze) · kampania 24 (+3 zapas) · sonda (ii)
0–4 ⇒ **sufit ≤ 34 bootów, 2 sesje lotne** (build+smoke; kampania) + ewentualna
trzecia na sondę.

## §R5. Ryzyka i tryby porażki (mechanizmy)

1. **Oscylacja skan↔ENTRY:** histereza naturalna — hold wyzwala się dopiero po
   1.0 s braku świeżych (TRACK_LOSS_S); seria ENTRY k=3 nie pada na move_thr
   (rachunek §R2). Ryzyko właściwe: utrata tuż po akwizycji (cel przy krawędzi) →
   po 1 s skan odkręca nos i udaremnia odzysk REFRESH-oknem (żyje do θ_age 3.0 s).
   Mitygacja do PRE: **dwell 2.0 s** przed wznowieniem skanu + skan od bieżącego yaw.
2. **Re-akwizycja po FEED_EXPIRE:** po expire kanał zresetowany ⇒ pełne ENTRY k=3;
   skan czyni ją zależną od ω zamiast od przypadku (w DET FEED_EXPIRE 8/48 —
   marginalne).
3. **Fałszywe ENTRY na tle pod rotacją:** zmierzone §R3 — 0 potwierdzonych
   w replayu (7/7 „bez celu" = artefakt okna GT), 1 kandydat/23 w live; fp_fov
   niskie; pasmo 25+°/s cienko próbkowane ⇒ pokrycie smokiem przy ω=30°/s.
4. **dsw/stall (V2′):** skan nie dodaje obliczeń (zmienia WARTOŚĆ istniejącego pola
   yaw) — ryzyko pomijalne; standardowa ważność V2′+żywość per boot jak DET S4.
5. **Interakcja z lekcją choreografii:** skan uniezależnia akwizycję od pozycji
   epizodu w boocie ⇒ „lock przed epizodem" przestaje być nośny dla wyniku; artefakt
   falsy-zero t_entry w trace POZOSTAJE (właściwość logowania bench frozen) — nota
   interpretacyjna, zero zmian kodu. Źródło locków widoczne w danych §R3 (ENTRY@F2
   przy spawn ~108 s).
6. **REFUSE pod skanem:** yaw nie jest wejściem osłony (`r01/shield.py:121`);
   bariera = radial(target) ∨ radial(pos)+hamowanie ∨ |z| (:101-113); w hold
   target=own i v=0 ⇒ geofence nieaktywny Z KONSTRUKCJI (potwierdzone z definicji,
   jak żądał prompt); REFUSE(POS) od pos_flag — od yaw niezależny. Oczekiwanie
   0 fałszywych REFUSE (predykcja do PRE z regułą kalibracyjną DET-4).
7. **ω=15°/s a budżet t_entry≤25 s:** worst-case ~21 s — na styk (§R2); to argument
   za 30°/s mimo cieńszego pokrycia R3 (stąd smoke z akwizycją ze skanu jako bramka).
8. **Intruz ruchomy (v≥0.5):** spotkanie skanu z celem ruchomym zmienia rachunek
   statyczny w obie strony — desk nie rozstrzyga; mierzy kampania (48 par pokrywa
   v∈{0,0.5,1.0} jak DET).

## §R6. Higiena i kosztorys

- **Nazwa:** AKW wolna (§0); env prefiks `AKW_` (`AKW_SCAN_DPS`, `AKW_DWELL_S`;
  wybór kontrolera standardowo `CONTROLLER=net_akw`); wyniki `results/AKW/`.
- **Dysk:** kampania ~3 GB (wzór DET/camp; bez zrzutu klatek), recon 2.5 MB
  (replays + strat.json — commitowane).
- **Sufit bootów nogi:** ≤34 (smoke 1+2 · kampania 24+3 · sonda warunkowa 0–4);
  **sesje: 2 lotne** (+1 warunkowa na sondę (ii)); build i analiza 0 bootów.
- **FREEZE_AKW:** sha `r03/controllers/akw_scan.py` (nowy), sha
  `r03/controllers/__init__.py` PO wpisie additive, parametry profilu FROZEN
  (ω [°/s], dwell [s], kierunek, start od bieżącego yaw), sha drivera kampanii;
  dziedziczone bez zmian: piny 5/5, FREEZE_DET (det_v2, feed_sha_v2, percep/klient,
  rejestr), ncp 0337d5ea, bench 05137098/8ec0fcfb.

## §S. Rekomendacje nazwane (dla PRE_AKW)

1. Punkt wpięcia: **wariant (b)** — wrapper `net_akw` + wpis additive do rejestru
   kontrolerów (1 nowy plik + 2 linie; zero dotykania frozen).
2. Profil: **skan ciągły 360°, jednokierunkowy, ω=30°/s nominalnie** (10–25°/s
   zmierzone czyste; 30 tuż powyżej — bramkuje smoke z akwizycją ze skanu);
   15°/s wariant awaryjny (pełne pokrycie pomiarem, kosztem marginesu t_entry);
   **dwell 2.0 s** po utracie tracku, skan od bieżącego yaw.
3. Kampania: **wariant (i)** 12×{B, V2+skan} verbatim po DET S4; progi Δ VERBATIM
   z PRE_2A §4; dekompozycja per bearing/split/sceno-świeżość jak DET; zbiór
   odniesienia 29 ślepych epizodów.
4. Smoke: boot 4-epizodowy, scenariusz ślepy DET, bramka = akwizycja ze skanu
   + runtime + S-BEZP + V2′.

Artefakty: `results/AKW_RECON/{RECON_AKW.md, akw_R3_strat.json,
tools/akw_rot_strat.py, replays/ (24× json+jsonl+log, 2.5 MB)}`. STOP-AKWR:
commit (RECON + tools). **Push = Olga („wypchnięte")**; potem PRE_AKW numerowany —
sygnały bez numeru odrzucam. STOP.
