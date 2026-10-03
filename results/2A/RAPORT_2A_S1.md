# RAPORT_2A_S1 — build: FEED-V, rejestr feedów, sędzia percepcji (zero lotów) → STOP-2A1

LiquidPatrol · CC · 03.10.2026 · PROMPT_2A_S1 · PRE_2A ratyfikowany (ARCH-1 commit tej sesji,
sha256 kopii `480a60d7…` byte-identyczna z dostarczoną). Zero bootów, zero SITL, zero
treningu — budżet lotny nogi (≤31) nietknięty.

## §0. Bramka wejścia (wykonaniem)

origin/master = `e4bd980` ✓ · `origin/master..HEAD` puste ✓ · porcelain pełny pusty ✓,
zero obcych M. FROZEN: piny 5/5 (`check_shield_frozen=True`) · certy 9/9 (`certs_selfcheck`
PASS) · sha: bench_judge `8ec0fcfb` ✓ · features `9adc1505` ✓ · ncp `0337d5ea` ✓ · yolo
`9b2c17ab` ✓ · **bench_flight baza `3a52e19f` potwierdzona PRZED edycją** ✓ (pełne sha
w FREEZE_2A). Pliki dotykane: dokładnie lista zamknięta PRE §6 (PRE_2A.md; NOWE:
harness/feed_vision.py, harness/feed_registry.py, results/2A/**; EDYCJA: bench_flight.py
2 hunki; r02/* nietknięte — wyłącznie importy READ-ONLY).

## §1. FEED-V (`harness/feed_vision.py`, sha `0ce7569c…`)

**Reguła nadrzędna dotrzymana konstrukcyjnie:** plik nie zawiera żadnego źródła GT —
wejścia to klatki (stempel sim-time) + stan własny POKŁADOWY. **Źródła stanu własnego
(wprost, PROMPT §1):** pozycja/prędkość własna = EKF `/fmu/out/vehicle_local_position`
(ten sam topic co pętla ławki, bench_flight.py:99); orientacja = `/fmu/out/vehicle_attitude`
(kwaternion [w,x,y,z] FRD→NED — konwencja zamrożonego przyrządu r02/mti.py:9); klatki =
zbridżowany topic kamery pokładowej `…imager/image` (BEST_EFFORT, lekcja R0.1). GT nie
występuje w torze FEED-V w żadnej postaci; jedyne miejsce toru 2A dotykające GT = sędzia
offline (§3).

- **Tryby:** LIVE (`FeedVisionLive`: własny węzeł ROS2 + spin-thread daemon — zero dodatkowych
  edycji pętli bench_flight) i REPLAY/SYNTETYCZNY (`push_frame`/`ingest_box` z zewnątrz —
  smoke S1, sędzia etapu B).
- **Detekcja (D4):** `YoloDetector` 1:1 z B0 (YOLO-World, classes=["drone"], imgsz 640,
  conf=0.001 telemetrycznie, top-1 bez bramkowania conf — A1); **guard SR-2**: sha wag ≠
  `9b2c17ab…` ⇒ RuntimeError ODMOWA (test negatywny w §4b-nocie).
- **Admisja (D2):** struktura∧MTI przez `TargetChannel(ChannelConfig(entry_require_mti=True))`
  — ENTRY k=3, edge_margin 0.10, θ_age 3.0 s; koincydencja box↔komponent MTI
  (`box_matches_component`, thr 0.12); MTI z derotacją attitude (`MTITracker`). Detekcje
  przed admisją NIE dotykają tracku (test §4c). Nota semantyczna (dziedziczona z zamrożonej
  logiki r02, target_channel.py:124-127): REFRESH locka nie stosuje bram admisyjnych —
  admisja bramkuje WEJŚCIE do locka, nie jego podtrzymanie.
- **box→NED (D1):** Z = f_px·W_real/w_px; f_px = **270.0** (kanon r02/mti.py:17; dokładnie
  269.976 z hFOV 1.74/640 — rozjazd 0.009%); W_real = **2.5 m** z `r02/intruder_model.sdf:15,18`
  (ten sam SDF spawnuje ławka, run_boot.sh:123); kierunek z (cx,cy) + quat pokładowy
  (quat_to_R importowany z r02/mti — jedna konwencja ramek w programie); offset kamery
  w FRD (0.12, −0.03, −0.242) uwzględniony.
- **Kontrakt R1 co do pola i typu:** `sample(sim_now)` zwraca ten sam dict co `FeedB._out`
  (trk_pos_ned/trk_vel_ned/track_age_s/track_valid/feed_sha; zaokrąglenia identyczne);
  trk_vel = linreg 1.0 s sim (import `_slope` z track_feed — ta sama arytmetyka co FeedB);
  utrata = hold-last z rosnącym age (hover-hold pozostaje u KONSUMENTA). `feed_sha` FEED-V:
  `ffccf86b…` (sha parametrów, echo w FREEZE_2A).
- Shadow-log (etap A/B): opcjonalny jsonl per klatka (t_frame, wall, box, conf, mti_ok, ev,
  locked, fresh, own_pos/own_q, trk_pos_ned) — surowiec sędziego §3.

## §2. Rejestr feedów + DWIE edycje bench_flight (diffy VERBATIM)

**Rejestr `harness/feed_registry.py`** (sha `2629bc40…`, wzór SR-9/make_controller):
`make_feed(name, *, seed, world)` → `(feed, holder)`; `"B"` → konstrukcja DZISIEJSZA 1:1
(`FeedB(seed, f=10.0)` + `TrackFeedGz(world, feed)`), `"V"` → `FeedVisionLive` (topic z env
`FEED_V_TOPIC`/`LIVE_DETECTOR_TOPIC`, shadow-log z `FEED_V_LOG`; seed przyjmowany
i ignorowany — percepcja deterministyczna względem klatek, nota). Test 1:1: params i feed_sha
instancji z rejestru == FeedB wprost; holder.feed is feed (§4).

**Edycja 1 — wybór producenta (bench_flight.py:309-310 → FEED=env, default "B" zachowuje
dawne dwie linie VERBATIM w gałęzi default):**
```diff
@@ -306,8 +310,15 @@ async def main():
         ctrl = make_controller(CONTROLLER, params=exec_params, orbit_dir=ep["orbit_dir"],
                                vmax=V_MAX, home_ned=(0.0, 0.0, -C.ALT_M))
         ctrl.reset()
-        feed = FeedB(ep["seed"], f=10.0)
-        tf = TrackFeedGz(WORLD, feed)          # subskrybuje pose/info → feed
+        # 2A D6 (PRE_2A §2): wybór producenta feedu z rejestru po FEED=env; default "B"
+        # zachowuje dzisiejsze zachowanie CO DO LINII (gałąź poniżej = dawne dwie linie verbatim).
+        _feed_name = os.environ.get("FEED", "B")
+        if _feed_name == "B":
+            feed = FeedB(ep["seed"], f=10.0)
+            tf = TrackFeedGz(WORLD, feed)          # subskrybuje pose/info → feed
+        else:
+            from harness.feed_registry import make_feed
+            feed, tf = make_feed(_feed_name, seed=ep["seed"], world=WORLD)
         # bramka startu: dron na home, intruz w pozie startowej
         in_gate = await _fly_to_home_hover(RESET_MAX)
         m = ekf.m
```

**Edycja 2 — orientacja w strumieniu gt (D5, pole ADDYTYWNE):**
```diff
@@ -118,7 +118,11 @@ def _dronegt_cb(msg):
         if p.name == MODEL:
             sim = msg.header.stamp.sec + msg.header.stamp.nsec / 1e9
             _w({"t": "gt", "mono": round(now, 4), "sim": round(sim, 4),
-                "x": round(p.position.x, 5), "y": round(p.position.y, 5), "z": round(p.position.z, 5)})
+                "x": round(p.position.x, 5), "y": round(p.position.y, 5), "z": round(p.position.z, 5),
+                # 2A D5 (PRE_2A §2): orientacja drona — pole ADDYTYWNE; kwaternion gz pose
+                # (świat gz-ENU → body gz: x przód, y lewo, z góra), kolejność [w,x,y,z].
+                "qw": round(p.orientation.w, 6), "qx": round(p.orientation.x, 6),
+                "qy": round(p.orientation.y, 6), "qz": round(p.orientation.z, 6)})
             _drone_gt_last[0] = now
             return
```

`git diff` całego pliku = DOKŁADNIE te 2 hunki (zliczenie `grep -c ^@@` = 2). Format D5:
kwaternion pozy gz (świat gz-ENU → body gz), pola `qw,qx,qy,qz` po 6 miejsc; konwersja do
FRD/NED u konsumenta offline. sha po edycjach `2972a48a…` (FREEZE_2A). Decyzja wykonawcza
(w duchu „dokładnie dwa miejsca"): odczyt env + leniwy import rejestru umieszczone WEWNĄTRZ
hunku 1 — zero trzeciego miejsca w pliku (koszt: getenv raz na epizod, pomijalny).

## §3. Sędzia percepcji offline (`results/2A/tools/percep_judge.py`, sha `363c37b7…`)

Tryby: `--demo <bootdir>` (FeedB z demo.jsonl + gt_intruder) · `--shadow <log> --gt <gt>`
(FEED-V). Metryki: błąd NED mean/p50/p95/max na tickach track_valid; **dekompozycja
kierunek-vs-zasięg** (kąt między LOS own→trk i own→gt [deg]; |Δd| + bias ze znakiem) —
obowiązkowa przy cytowaniu C (PRE §4); kadencja świeżych próbek (p50 Hz z odstępów);
latencja capture→update p50/p95 (gdy log niesie stemple; dla FeedB = 0.2 s z konstrukcji,
nie mierzona — pole null).

**SANITY PRZYRZĄDU WYKONANIEM (obowiązkowa, PROMPT §3): baseline RECON R4 ODTWORZONY
CO DO LICZBY** na `results/LIQ/camp/r1_ncp`:
mean **0.741** / p50 **0.673** / p95 **1.258** / max 21.416, n=5689 — identycznie z RECON_2A
§R4 (artefakt: `results/2A/sanity_feedb_r1_ncp.json`). Bonus kalibracyjny (punkt odniesienia
dekompozycji dla etapu B): FeedB kąt p50 3.11° / p95 6.96°, zasięg |Δd| p50 0.333 /
p95 0.975 m, bias +0.028 m, kadencja świeżych 9.62 Hz (spójna z f=10 Hz · p_drop 0.05).

## §4. Smoke offline (zero SITL) — wyniki

**(a) pinhole:** projekcja w przód liczona NIEZALEŻNYM wzorem w teście → `box_to_ned`
odwraca ją z błędem < 1e-9 m (tożsamość i yaw 35°/pitch −7°); box zdegenerowany (<1 px)
→ None. 3 testy PASS. (Nota uczciwa: roundtrip dowodzi poprawności numeryki pinhole
i spójności ramki wewnętrznej; poprawność KONWENCJI quat względem PX4 dziedziczymy
z zamrożonego r02/mti.py — zmierzona w locie dopiero w etapie A.)

**(b) detekcja na istniejących klatkach repo** (`smoke_detect.py` → `smoke_detect.json`,
GPU, guard sha przeszedł): czasy 7.2–9.9 ms/klatkę — zgodne z det_bench.json (p50 6.5/p95
13.1). Boxy: `static.png` → box (0.495, 0.372, w 0.041) conf **0.154** = cel (zgodny
z historycznym separatorem r02 ~0.156); `base.png`/`flight.png` → brak boxów;
`intruder.png` → top-1 pełnokadrowy conf 0.0013 (śmieciowy FP semantyki A1 — top-1 BEZ
bramki conf). Wniosek wprost: **struktura sama jest FP-podatna, dokładnie dlatego admisja
D2 (struktura∧MTI) stoi przed trackiem** — na statycznych klatkach MTI nie ma, więc FP
z (b) NIE przeszedłby admisji.

**(c) feed_vision REPLAY/syntetycznie — pełny cykl życia tracku** (`test_smoke_s1.py`):
przed czymkolwiek sample invalid → 2 klatki z boxem (mti_ok=True) NIE admitują → 3. klatka
= **ENTRY** (k=3), sample valid, age=0, pozycja = pinhole co do 1e-3 (Z=270·2.5/32≈21.09 m
dla boxa 32 px) → świeże klatki odświeżają (age→0, n_fresh rośnie) → utrata boxów: ZOH,
age rośnie (0.6 s przy valid=True — cięcie na 1.0 s należy do konsumenta) → **EXPIRE** po
suficie θ_age=3.0 s → valid=False. Negatywy: mti_ok=False ×6 → zero ENTRY, zero fresh;
box przy krawędzi (edge_dist<0.10) ×6 → zero ENTRY. trk_vel: box malejący → vel x > 1 m/s
(regresja działa). **6 testów PASS.**

**Rejestr:** nieznana nazwa → ValueError; `make_feed("B")` ≡ FeedB 1:1 (params, feed_sha,
holder=TrackFeedGz z tym samym feed). **2 testy PASS.** Razem nowe testy S1: **9/9 PASS** (w tym guard
SR-2 wag wykonany pozytywnie w (b) — konstrukcja z poprawnym sha; ścieżka ODMOWY
to literalnie wzór liq_controller SR-2).

## §5. Regresja istniejących testów (po edycjach bench_flight)

- katalogi `bench net r01 r02 r03 tools k1 harness acts results/2A/tools`:
  **96 passed** (w tym 9 nowych S1);
- pliki `bench/tests_*.py net/tests_*.py harness/tests_*.py` (konwencja nazw spoza
  domyślnej kolekcji pytest — tak samo wołane w poprzednich sesjach): **85 passed**
  (w tym tests_track_feed, tests_demo_features, tests_campaign_* — konsumenci i sędziowie
  nietknięci);
- łącznie **181 unikalnych PASS, 0 FAIL**. Poza biegiem: `r01/brake_test.py`
  i `r02/test_deadman.py` (import rclpy na poziomie modułu — wymagają env ROS lotnego;
  stan niezmieniony od poprzednich sesji, pliki nietknięte).

## §6. FREEZE_2A, odchylenia, commity

FREEZE_2A (`results/2A/FREEZE_2A.md`): sha yolo/feed_vision/rejestru/sędziego +
bench_flight PRZED (`3a52e19f…`) i PO (`2972a48a…`); stałe f_px 270.0 (vs dokładne 269.976,
rozjazd 0.009% — kanon mti.py), W_real 2.5 m + ścieżka SDF, kamera 99.7°/640×480/15 Hz,
parametry FEED-V (k=3, θ_age 3.0, center_thr 0.12, okno regresji 1.0 s, kadencja nominal
15 Hz), wersje: torch 2.11.0+cu128 / ultralytics 8.4.115 / numpy 2.4.4 (.b0deps) · numpy
1.26.4 (python systemowy toru ławki).

**Odchylenia: brak.** Lista zamknięta dotrzymana (jedyna edycja istniejącego pliku =
bench_flight 2 hunki; r02 wyłącznie importy). Wątpliwości wymagających STOP nie było.
Nota porządkowa: PRE_2A.md w korzeniu ma tryb 755 (kopia z /mnt/c — identycznie jak
PRE_LIQ.md, precedens).

**Commity sesji:** (1) `7882b9f` ARCH-1 PRE_2A verbatim (sha kopii `480a60d7…` = dostarczona);
(2) build S1: feed_vision + feed_registry + bench_flight (2 hunki) + results/2A/**
(sędzia, smoke, FREEZE_2A, ten raport). Porcelain po commicie 2: PUSTY (zweryfikowane
wykonaniem przy STOP). Push = Olga; „wypchnięte" wystarczy.

**Dalej:** PROMPT_2A_S2 (etap A shadow 2 booty + etap B) przyjdzie NUMEROWANY — po wysyłce
warstwy 0 (PRE §5, bramka w rękach CC). Do tego czasu: zero bootów. STOP-2A1.
