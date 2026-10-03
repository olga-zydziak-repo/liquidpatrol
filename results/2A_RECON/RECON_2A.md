# RECON_2A — recon nogi 2A: percepcja w pętli (kamera → detektor → tracker → feed) → STOP-2AR

LiquidPatrol · CC · 03.10.2026 · PROMPT_2A_S0 · sesja wyłącznie rozpoznawcza: **zero bootów,
zero SITL, zero treningu, zero zmian w plikach istniejących**; nowe pliki wyłącznie
`results/2A_RECON/**` (ten raport + tools + 2 JSON-y pomiarów biurkowych). Po STOP: PRE_2A (CC),
ratyfikacja Olgi; loty dopiero po ratyfikacji.

## §0. Bramka wejścia (wykonaniem)

1. `git fetch` ✓ · origin/master = `d771a0a` (CO-LIQ) ✓ · `origin/master..HEAD` puste ✓ ·
   porcelain pełny pusty (REPO-1) ✓, zero obcych M.
2. FROZEN: piny 5/5 (`check_shield_frozen=True`: shield.py, config.py, gate_run_r03.py,
   base.py, safe_descend.py — sha want=got komplet) · certy 9/9 (`certs_selfcheck` PASS) ·
   sha 5/5: bench_judge `8ec0fcfb` ✓, features `9adc1505` ✓, ncp `0337d5ea` ✓,
   gru `5ec02755` ✓, mlp20 `74b5ae7d` ✓.
3. **Kolizja nazwy „2A": BRAK.** Zero `results/2A*`, zero `ANEKS_2A*/PRE_2A*` w drzewie
   i w logu; jedyne wystąpienie „2a" = kierunek w `KIERUNKI_PO_PLANIE.md:40` („2a PERCEPCJA
   W PĘTLI…"), czyli dokładnie ta noga. Trafienia `git log | grep -i 2a` to podciągi sha
   commitów, nie łańcuch. **Nazwa 2A wolna — rekomendacja: zostaje** (R8).

## §R1. Kontrakt feedu (serce nogi)

**Konsument (kontrakt, jeden dla wszystkich kontrolerów):** `set_feed(sample)` przyjmuje dict
o polach (producent: `harness/track_feed.py:75-78`, `_out()`):
- `trk_pos_ned` [m, NED, lista 3] — pozycja tracku intruza;
- `trk_vel_ned` [m/s, NED] — prędkość tracku (regresja liniowa 1 s sim); **logowana, NIE jest
  cechą lotu** (`bench/demo_logger.py:6`); sieć jej nie konsumuje (`net_controller.py:84-86`:
  features biorą trk_pos_ned + track_age_s + track_valid);
- `track_age_s` [s, SIM] — wiek ostatniej świeżej próbki;
- `track_valid` [bool] — semantyka: utrata tracka ⇒ kontroler przechodzi w hover-hold, gdy
  `fd is None ∨ not track_valid ∨ track_age_s > TRACK_LOSS_S=1.0`
  (`net_controller.py:35,108-111`; identycznie egzekutor `orbit_executor.py:58-60`);
- `feed_sha` — sha parametrów producenta, wymagane niepuste w każdym wierszu demo
  (`demo_logger.py:12-14` REQUIRED + assert :58-59).

Częstotliwość: pętla lotu tyka ~20 Hz i woła `feed.sample(now_sim)` co tick
(`bench/bench_flight.py:348-350`); kadencja ŚWIEŻYCH próbek = wewnętrzna sprawa producenta
(FeedB: 10 Hz, między próbkami hold-last, `track_feed.py:80-86`). Wszystkie okna w SIM-time
(`track_feed.py:7`).

**Producent emulowany (FEED-B):** `harness/track_feed.py:28-105`, parametry VERBATIM w kodzie
(`:29`): `f=10.0 Hz, L=0.20 s, sigma_xy=0.5, sigma_z=0.3, p_drop=0.05 (hold-last, age rośnie),
pos RAW, trk_vel = linreg 1.0 s sim`; RNG z ziarna epizodu (`:33`). GT bierze z gz:
`TrackFeedGz` (`track_feed.py:108-128`) subskrybuje `/world/W/pose/info`, wyciąga pozę
APPLIED modelu `intruder`, ENU→NED (`:121-127`), karmi `FeedB.push_gt`; sim-time
z header.stamp. Wpięcie w lot: `bench_flight.py:309-310` (konstrukcja per epizod,
seed=ziarno epizodu) + `:348-350` (sample→set_feed→step).

**Co podmienić, żeby wpiąć INNEGO producenta (lista dokładna):**
1. `bench/bench_flight.py:309-310` — jedyne lotne miejsce konstrukcji (FeedB + TrackFeedGz);
   `:348` konsumuje przez `feed.sample(now_sim)`. **Nic więcej po stronie lotu.**
2. Konsumenci (orbit/net/gru/mlp20) — **NIETKNIĘCI**: kontrakt to dict z `set_feed`
   (`orbit_executor.py:9`: „Wejścia WYŁĄCZNIE argumenty step + set_feed; bez GT, bez gz").
3. Sędziowie — **NIEZALEŻNI od feedu**: `campaign_analyze.judge_boot` czyta wyłącznie
   trace + gt_intruder + rtf_stream (`bench/campaign_analyze.py:51-58`); bench_judge
   deklaruje wejście GT-only (`bench_judge.py:4-10`). Podmiana producenta nie dotyka toru
   sędziowania ani V2′.
4. Offline: drugi konstruktor FeedB w `net/rollout_eval.py:92` (model punktowy, feed_mode="B")
   — nie dotyczy lotu, zostaje.

**Rejestr producentów: NIE ISTNIEJE.** `FEED_PROFILE` występuje TYLKO w docstringu
(`bench_flight.py:10`); blok env `:49-76` go nie czyta — wybór producenta jest dziś zaszyty
na sztywno. Wzór SR-9 (rejestr kontrolerów `r03/controllers/__init__.py`, `make_controller`)
jest gotowym szablonem; analogiczny rejestr feedów = dopisanie addytywne, **do ratyfikacji
w PRE_2A**. Status mrożenia: `bench_flight.py` NIE jest pinem (piny 5/5 to osłona;
`results/BENCH/FREEZE_CAMPAIGN.md:19`: „bench_flight/intruder_motion to harness, poza listą
§7 PRE") — ale jego sha w FREEZE_CAMPAIGN (`:16`, v1.3 `b8eb68ca`) jest już historyczny:
dzisiejszy sha `3a52e19f` po ratyfikowanych edycjach K2/W (commity `a5b15d3`, `683fcdf`,
`2529c5a` — `git log -- bench/bench_flight.py`). Precedens: edycja harnessu = ratyfikowany
diff w aneksie, nowe echo sha do manifestów. PRE_2A musi zamrozić wersję bazową.

**LUKA KRYTYCZNA KONTRAKTU (to, co dziś UNIEMOŻLIWIA podmianę 1:1):** kontrakt wymaga
`trk_pos_ned` **3D w metrach NED**, a istniejący tor percepcji kończy się na kanale
**PIKSELOWYM 5-dim** `(cx,cy,w,h,age)` (`r02/detector_node.py:6-13`,
pub `/liquidpatrol/target_channel`). **Ogniwo box→pozycja NED nie istnieje w repo** (R2).
Bez niego „podmiana producenta bez dotykania konsumentów" jest zdaniem o KONTRAKCIE
(prawdziwym), ale nie o GOTOWOŚCI toru: trzeba zbudować estymator pozycji (opcje do PRE:
pinhole + znany rozmiar intruza z SDF; bearing-only + znana wysokość intruza; sensor
głębi x500_depth z drzewa PX4). To jest główny przedmiot decyzji PRE_2A, nie szczegół.

## §R2. Inwentarz toru C (detekcja)

**Pliki i model:**
- `r02/detector_node.py` — węzeł ROS2: sub sensor_msgs/Image BEST_EFFORT, YOLO-World top-1
  bez bramkowania conf (conf tylko telemetria), zasila `TargetChannel`, pub
  `/liquidpatrol/target_channel` Float32MultiArray 5-dim (cx,cy,w,h,age) (`:1-17`);
  brama LIVE `DEMO_MTI=1` = struktura∧MTI (`:29-34`).
- `r02/target_channel.py` — kanał ZOH-age, ENTRY k=3, sufit θ_age; `r02/mti.py` — człon MTI
  (derotacja); testy `r02/test_mti.py`.
- Wagi: `.b0deps/weights/yolov8s-worldv2.pt`, **sha256
  `9b2c17ab6124a913e9b3a5c170617920d91b0f01111a8479da69f00e2cf27792`**
  (`results/R02/RAPORT_B0.md:24`), 24.7 MB, `set_classes(["drone"])`, imgsz=640, conf=0.001
  (`RAPORT_B0.md:37`). **Trenowany: pretrained open-vocabulary (ultralytics assets v8.4.0)
  — ZERO treningu na naszym symie** (`RAPORT_B0.md:23`).
- Kadencja decyzji LIVE: **2.0 Hz ratyfikowana**; bieg z det_hz≠2.0 = INVALID z definicji
  (`r02/gate_run_r02.py:37-39,1138-1140`); `DET_HZ=1.0` w `config_r02.py:22` pozostaje
  historią charakteryzacji.
- Orkiestracja live wzorcowa: `acts/run_act_live.sh` (bridge mono PO settle EKF — lekcja
  4×env-fail `:46-56`; env LIVE_DETECTOR_TOPIC/YOLO_WEIGHTS/DEMO_MTI `:53-56`).

**Werdykty — co WOLNO mówić (verbatim z plików):**
- REGATE: „**Re-bramka ENTRY-once: (+) PASS · (−) PASS** (×3 świeże booty, world_demo_v1.1,
  ANEKS-H)" (`results/R02/mti/REGATE/RAPORT_MTI_REGATE.md:144`); (+) coverage_entry_once
  mediana 1.0 @5/7/9 m, admisja 3/3 (`:43-44`); (−) 0 fałszywych ENTRY ×3 booty × 2 sceny,
  z dekompozycją koniunktów (`:54-56`).
- PUŁAPKA AM2.0 (obowiązuje przy każdym cytowaniu B5): „B5 (+) FAIL był artefaktem metryki
  `coverage_gate`" (`RAPORT_MTI_REGATE.md:147`) — **NIE WOLNO** mówić „MTI oblało bramkę
  zasięgu"; rdzeń SR-R4 nietknięty, admission-only mti_ok był w kodzie od początku.
- R02C (o renderze, nie percepcji): „Dźwignie 0/2/R2-alt (gimbal/MTI/detektor) pozostają
  bezprzedmiotowe — celowały w nie-problem (percepcja), gdy przyczyną jest render. θ_conf
  i kryterium dwustronne bez zmian." (`results/R02/RAPORT_R02C.md:136-137`). ENGINE-RECON:
  „powietrzny sensor nie renderuje intruza" OBALONE — render headless z 9 m działa,
  przyczyną była kontencja GUI (memoria programu; guard headless w bootach —
  `headless_proof.txt` w każdym OUTDIR).

**Czas inferencji detektora OFFLINE na RTX (pomiar tej sesji, zero SITL):** narzędzie
`results/2A_RECON/tools/det_bench.py`, wynik `results/2A_RECON/det_bench.json` —
tor 1:1 z B0 (YOLO-World, ["drone"], imgsz 640, conf 0.001), 4 ISTNIEJĄCE klatki kamery
640×480 z repo (r1_frames/gate_live), warmup 10, N=200, GPU RTX 5070 Ti Laptop 12 GB,
torch 2.11.0+cu128: **p50 6.52 ms · p95 13.06 ms · max 25.15 ms · mean 7.24 ms.**
Zgodne z B0 (p95 13–22 ms). Przy kadencji FeedB 10 Hz budżet 100 ms/próbkę — detektor
offline ma ~8× zapas na p95; ryzykiem nie jest inferencja, lecz KONTENCJA stacka (R6).

## §R3. Kamera pokładowa w gz

**Stock PX4 ma gotowy wariant z kamerą i ławka JUŻ NA NIM LATA:**
- Drzewo modeli `PX4-Autopilot/Tools/simulation/gz/models/` zawiera (ls, nie z pamięci):
  `x500, x500_base, x500_mono_cam, x500_mono_cam_down, x500_depth, x500_gimbal,
  x500_flow, x500_lidar_*…`.
- **Każdy boot ławki spawnuje `x500_mono_cam`**: `harness/run_boot.sh:102`
  `MODEL=gz_x500_mono_cam` (stack) + `:136-147` `B1_MODEL=x500_mono_cam_0` (gate/bench);
  bench czyta `B1_MODEL` z env (`bench_flight.py:50`).
- Model: `x500_mono_cam/model.sdf:4-16` = x500 + `mono_cam` przez joint **FIXED**, pose
  `.12 .03 .242 0 0 0` — **montaż sztywny, przód, bez rotacji** (to jest dzisiejszy stan;
  yaw-follow robi SAM DRON, bo komenda yaw = atan2 ku trackowi co tick,
  `net_controller.py:115` → `bench_flight.py:387` VelocityNedYaw).
- Sensor: `mono_cam/model.sdf:50-66`: `imager`, **hFOV 1.74 rad = 99.7°**, **640×480**,
  **update_rate 15 Hz**, `always_on=1`, `visualize=false`, clip 0.1–3000 m.
  (vFOV z aspektu 4:3 ≈ 83.3°.) `always_on=1` ⇒ sensor tyka w każdym boocie ławki — czy
  gz faktycznie renderuje bez subskrybenta (koszt w baseline), potwierdzi 1 pomiar etapu A.

**Droga klatek do Pythona (ISTNIEJĄCA, używana w live r02/D):** topic gz
`/world/<W>/model/x500_mono_cam_0/link/camera_link/sensor/imager/image` (dowód z przeszłych
bootów: `results/demo/A1/*/topics.txt`, wiersz `MONO=…imager/image`) → `ros_gz_bridge
parameter_bridge` (`acts/run_act_live.sh:40` + analogi w `acts/run_stability*.sh`,
`r02/run_signal_sweep.sh:21`) → `sensor_msgs/Image` BEST_EFFORT → `detector_node`.

**FILM=1 to INNA kamera:** kamera ŚWIATA `film_cam` (topic `film.*image`,
`harness/run_boot.sh:115-119`; `results/demo/A1_v3/proba_1/topics.txt`:
`FILM=/world/…/model/film_cam/link/l/sensor/film/image`); `film_recorder`
(`results/DEMO_V3/tools/film_recorder.py:1-13`) czyta kamerę FILMOWĄ, nie pokładową.
Proxy kosztowe z FILM dotyczy więc renderu DODATKOWEJ kamery świata — R6.

**Parametry do decyzji PRE:** (a) FOV/rozdzielczość/fps — rekomendacja recon: STOCK
(99.7°/640×480/15 Hz) bez dotykania drzewa PX4; desk R5 pokazuje, że 99.7° wystarcza
z zapasem; ewentualna zmiana SDF = NOWY model w `worlds/` wzorem `worlds/wind_models`
(precedens nogi W), nigdy edycja drzewa PX4. (b) Montaż — sztywny przód (stan stock);
dane R5 mówią, że przy yaw-komendzie ku trackowi to wystarcza; `x500_gimbal` istnieje
jako plan B. (c) fps vs det_hz: sensor 15 Hz, decyzje 2 Hz (ratyfikowane w D) — do spięcia
w PRE z kadencją feedu 10 Hz (fizycznie: świeża detekcja ≤15 Hz, track w międzyczasie ZOH).

## §R4. Ground truth do sędziowania percepcji

- **GT intruza:** `gt_intruder.jsonl` per boot, ~50 Hz sim-time, kolumna `ned` = poza
  **APPLIED** (nie komenda; „GT sędziego = APPLIED — chybienia set_pose w danych",
  `harness/intruder_motion.py:6-9`; zapis `:150-153`). Już w NED (drv2ned w intruder_motion).
- **GT własnej pozycji:** trace `t:"gt"` z `/world/W/dynamic_pose/info`, 50 Hz, pozycja
  modelu drona (`bench_flight.py:113-123,217`); konwersję ENU→NED robi sędzia
  (`bench_judge.py:4-10`). **UWAGA: orientacja NIELOGOWANA** (tylko x,y,z) — yaw/pitch drona
  nie ma w żadnym artefakcie ławki (lekcja r02: att() logował tylko yaw). Dla sędziego
  percepcji etapu B wystarcza pozycja (błąd tracku); dla atrybucji kadrowania (pitch) —
  dopisać logowanie orientacji w etapie A (addytywne, do PRE).
- **Błąd percepcji vs GT (przepis sędziego B, policzalny z dzisiejszych artefaktów):**
  e(t) = |trk_pos_ned(demo.jsonl @t) − intr_ned(gt_intruder interp @t_sim)|, na tickach
  track_valid. **Sanity wykonaniem (r1_ncp, n=5689 ticków):** mean **0.741 m** ·
  p50 **0.673** · p95 **1.258** · max 21.4 m (max = znany tranzient teleportu granicznego,
  `intruder_motion.py:28`). To jest BASELINE FeedB (σ_xy=0.5 + latencja 0.2 s w ruchu),
  z którym feed percepcyjny będzie parowany w etapie C.

## §R5. Geometria kadru — DESK (wejście do bramki A)

Narzędzie: `results/2A_RECON/tools/geom_fov.py` (NOWY, zero bootów), pełne per-scenariusz
JSON: `results/2A_RECON/geom_fov.json`. Dane: 24 booty kampanii LIQ (12 NCP + 12 GRU,
48 epizodów/ramię), demo.jsonl (own, trk, phase) + gt_intruder.jsonl (GT APPLIED, interp).
Definicje: az_err = az(GT) − yaw_cmd, gdzie yaw_cmd = atan2(trk−own) — DOKŁADNIE wzór
yaw komendy (`net_controller.py:115`); montaż PRZOD = kamera sztywno w przód przy tej
komendzie (bez dynamiki yaw — optymistycznie); FOLLOW = idealny yaw-follow (az_err≡0,
górna granica). vFOV = 2·atan(tan(hFOV/2)·0.75): 60°→46.8°, 90°→73.7°, 110°→93.9°.
**Założenie: kamera pozioma (pitch=0) — pitch NIELOGOWANY; r02 §3f dowiódł, że przechył
kadruje. Desk NIE zastępuje bramki A — wyznacza jej hipotezę.**

**Agregaty (frakcja ticków z intruzem w kadrze):**

| ramię/faza | n | f60 przod/follow | f90 przod/follow | f110 przod/follow |
|---|---|---|---|---|
| NCP approach | 3 060 | 0.983 / 1.000 | 0.983 / 1.000 | 0.984 / 1.000 |
| **NCP orbit** | 64 472 | 0.997 / 0.997 | **1.000 / 1.000** | 1.000 / 1.000 |
| GRU approach | 3 805 | 0.947 / 0.964 | 0.985 / 1.000 | 0.986 / 1.000 |
| GRU orbit | 63 753 | 0.770 / 0.770 | 0.984 / 0.984 | 1.000 / 1.000 |

Per scenariusz (48×2 fazy×2 ramiona, kolumny f60/f90/f110×2 montaże + średnie |az_err|,
|el|, d): pełna tabela w `geom_fov.json`; skrajności NCP: najgorsze f60 orbit =
c08_s03 **0.923** (dalej c05_s03 0.958); najgorsze f90 orbit = c11_s02 **0.998**;
średnia |elewacja| orbit 13.4–17.2° przy d̄ ≈ 8.6–8.8 m (połowa vFOV stock 41.6° — zapas >2×).
GRU f60 orbit spada do 0.41–0.47 (c05_s04/c01_s04/c10_s03) — spójne z mechanizmem c_sweep
z RAPORT_LIQ (szersza/pełzająca orbita), opisowo.

**Wniosek desk (hipoteza bramki A):** przy kamerze STOCK (hFOV 99.7° — między 90 a 110)
i obecnym zachowaniu yaw-ku-trackowi intruz jest w kadrze ~100% ticków orbity NCP
(f90 przod = 1.000; nawet f60 ≥ 0.92 na najgorszym scenariuszu). Geometria NIE jest
blokerem; ryzyko przesuwa się na (a) pitch w locie (niemodelowany), (b) percepcję
(detekcja/конwersja do NED), (c) kontencję (R6).

## §R6. Headroom wydajności (proxy, nie pomiar)

- **Render DODATKOWEJ kamery świata + rejestrator 8 fps: koszt NIEMIERZALNY** na tym hoście:
  biegi kontrolne DEMO_V3 (FILM=1, scena v3) dsw **0.9383/0.9366** vs mediana 16 bootów
  kampanii W BEZ filmu **0.938** — „dodanie sceny v3 + kamery + rejestratora nie kosztuje
  nic mierzalnego" (`results/DEMO_V3/RAPORT_DEMO_V3.md:41-57`).
- Kamera POKŁADOWA (imager, always_on=1) siedzi na modelu w KAŻDYM boocie ławki — jeśli gz
  renderuje ją bez subskrybenta, jej koszt już jest w baseline kampanii (dsw LIQ 0.9544–1.0);
  jeśli nie renderuje leniwie, dojdzie z chwilą bridge'a. Rozstrzygnięcie = 1 pomiar etapu A.
- **Czego proxy NIE mówi:** kosztu mostu Image 15 Hz (ros_gz_bridge), YOLO per klatka
  WSPÓŁBIEŻNIE z gz (obie rzeczy na jednym GPU: ogre2 render + CUDA inferencja — kontencja
  GPU niezmierzona; D §5c mierzył kontencję CPU/churn), producenta feedu w Pythonie.
  Znane liczby z nogi D (tor aktów, nie ławka): pełny stack LIVE z churnem subprocess
  RTF 0.69; po trwałym kliencie in-process 0% głębokich dipów, jednostajne **0.919**
  (`ANEKS_D7.md:51`); ławka już używa trwałego GzPoseClient (`bench_flight.py:253,261`)
  — lekcja churnu skonsumowana. **Pomiar właściwy = etap A, nie recon.**

## §R7. Kosztorys (szkic do PRE_2A)

| etap | booty | treść |
|---|---|---|
| **A — potwierdzenie geometrii i kosztu** | **1–2** | boot ławki (NCP, scenariusz c08_s03 = najgorszy desk f60 + 1 nominalny) z bridge mono + zrzutem klatek (decymacja 2 Hz, jpg) + logiem orientacji (addytywnym); mierzy: pokrycie kadru RZECZYWISTE (vs desk R5), dsw z aktywnym renderem+YOLO (vs baseline), czy always_on renderuje w baseline; zero zmian w kontrolerach |
| **B — sędzia percepcji offline** | **0** | klatki+GT z A; detekcja→(konwersja NED wg decyzji PRE)→błąd vs GT przepisem R4; progi bramki B zamraża PRE (punkt odniesienia: FeedB mean 0.741/p95 1.258 m); rozstrzyga, czy feed percepcyjny w ogóle wchodzi do C |
| **C — kampania parowana** | **~24+smoke+zapas ≤ 29–30** | 2 ramiona feedu (FEED-B emulowany vs percepcyjny) × 12 bootów × 4 epizody, TEN SAM kontroler NCP 0337d5ea, parowanie i rytm 1:1 z LIQ (V2′, kolejki, cooldowny); sędziowie nietknięci (feed-niezależni, R1) |

**Niewiadome, które PRE musi znać/rozstrzygnąć:** (1) ogniwo box→NED — NIE ISTNIEJE (R1,
luka krytyczna; wybór metody determinuje etap B); (2) czas bootu z kamerą+YOLO i kontencja
GPU render↔CUDA (etap A); (3) dysk na klatki: raw npy 640×480 RGB ≈ 0.9 MB/klatkę ⇒ 15 Hz
×~7 min ≈ 5.8 GB/boot — decymacja do 2 Hz + jpg ≈ 40–50 MB/boot, zapis klatek TYLKO w A
(C liczy feed on-line, demo.jsonl standardowo); (4) semantyka track_valid/age po stronie
percepcji (mapowanie TargetChannel lock/age → kontrakt R1); (5) wersja bazowa bench_flight
do zamrożenia + kształt rejestru producentów (addytywny, wzór SR-9); (6) logowanie
orientacji drona (addytywne) — bez niego atrybucja kadrowania w locie niewykonalna (R4).

## §R8. Higiena i ryzyka

- **Dysk:** 756 G wolne (results = 43 G) — klatki etapu A (≤0.1 G/boot po decymacji) bez ryzyka.
- **Procesy:** zero osieroconych procesów stacka w chwili recon (pgrep gz/px4/XRCE/mavsdk czysty).
- **WSL2/render headless:** render kamery headless DZIAŁA (ENGINE-RECON: D0.5 PASS, intruz
  renderowany z 9 m; hipoteza cullingu obalona); konfundatorem była kontencja GUI — zakaz
  `gz sim -g` w bootach pomiarowych obowiązuje (guard `headless_proof.txt` już w torze,
  `acts/run_act_live.sh:36`). Pułapki serwera EGL/OGRE znane z toru FILM i nogi W
  (server.config) — orkiestracja etapu A przez istniejące launchery, nie nowe ścieżki.
- **Kolizja nazwy:** brak (§0.3) — łańcuch zostaje „2A" (PROMPT_2A_*, ANEKS_2A-n, PRE_2A,
  results/2A_RECON/** już w tej konwencji).
- **Ryzyko metodologiczne nr 1 (do PRE wprost):** detektor YOLO-World jest pretrained
  i STRZELA NA TŁO (REGATE: n_box 406–439 na ~443–456 ticków scen (−); fałszywe ENTRY
  gasi dopiero koniunkcja z MTI). Feed percepcyjny odziedziczy FP tła — projekt konwersji
  box→NED i semantyki track_valid musi to przewidzieć (np. brama struktura∧MTI przed
  admisją do tracku, jak w D), inaczej etap C pomiesza „percepcję" z „filtrem".

## STOP-2AR

Wykonanie: bramka §0 (3/3), R1–R8 z dowodami plik:linia, 2 narzędzia biurkowe + 2 JSON-y
pomiarów (`tools/geom_fov.py`→`geom_fov.json`, `tools/det_bench.py`→`det_bench.json`),
zero bootów, zero SITL, zero treningu, zero edycji plików istniejących (pliki dotykane =
wyłącznie `results/2A_RECON/**`). Dalej: **PRE_2A** (CC; bramki etapów A/B/C + śmierć
kierunku + decyzja box→NED + rejestr producentów + wersja bazowa bench_flight), ratyfikacja
Olgi; sygnały bez numeru odrzucam. Push = Olga. STOP.
