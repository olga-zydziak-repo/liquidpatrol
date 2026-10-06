# RAPORT_2A_S3 — C-sonda bezpieczeństwa: STOP po boocie C1 (bloker frozen integracji FEED=V live)

CC · 06.10.2026 · wykonanie ANEKS_2A-2 §5 · commity sesji: f8a0f9c (ARCH-1) + ten.

## §0. TL;DR

**STOP po 1 z 2 bootów.** Bramka §5.1 PASS i ARCH-1 wykonane. Boot C1 (c11_s01, FEED=V,
NCP) poleciał i jest VALID V2′ (dsw 0.9637, longest_stall 0.0), S-BEZP formalnie czyste
(0 REFUSE, 0 breach) — ale **sonda jest NIEWYKONANA merytorycznie: feed percepcyjny był
MARTWY od pierwszej klatki** (feed_v.jsonl = 0 bajtów, track_valid 0/791 ticków, dron
przestał epizod w hold na home, r_est_max 0.2 m). Przyczyna rozłożona na dwa blokery,
oba zmierzone i odtworzone offline:
- **(2a, błąd MÓJ, drivera):** globalny `export PYTHONPATH=$B0SP` ubił `ros2` CLI
  ⇒ bridge kamery nie wstał. Naprawione w driverze (narzędzie, nie frozen).
- **(2b, defekt FROZEN z budowy S1, bloker właściwy):** `feed_vision.py:299` spinuje
  węzeł feedu na **globalnym** egzekutorze rclpy, który już spinuje wątek EKF
  bench_flighta (`bench_flight.py:248-251`) ⇒ `RuntimeError: Executor is already
  spinning`, wątek `_spin` FeedVisionLive ginie na PIERWSZYM wywołaniu ⇒ zero callbacków
  (pos/att/obraz), nawet gdyby bridge działał.
Bloker 2b jest deterministyczny — **bootu C2 nie paliłem** (powtórka = identyczny wynik).
Naprawa wymaga edycji pliku FROZEN (FREEZE_2A: „zmiana sha = nowa decyzja do ratyfikacji,
nie poprawka"), a ANEKS_2A-2 §3 mówi „zero edycji kodu" ⇒ STOP, decyzja Olgi/aneks.

## §1. Bramka §5.1 + ARCH-1 (wykonane)

- origin/master zawierał ed5d084 (Olga wypchnęła), ahead 0, porcelain pusty na starcie.
- FROZEN wykonaniem (sha256 zgodne z FREEZE_2A): bench_flight `05137098…`, feed_vision
  `0a975121…`, feed_registry `2629bc40…`, percep_judge `363c37b7…`, wagi YOLO `9b2c17ab…`.
- ARCH-1: `ANEKS_2A-2.md` verbatim w korzeniu, commit f8a0f9c.
- Sanity zerolotny środowiska sondy (bez budżetu): w konfiguracji B0SP+ROS importy
  rclpy/px4_msgs/bench_flight OK pod numpy 2.4.4, YoloDetector ładuje się 7.4 s na CUDA
  (sha-guard SR-2 zgodny), inferencja smoke OK, rejestr ma wpis „V".

## §2. Boot C1 — przebieg i atrybucja

Driver `results/2A/tools/probeC_boot.sh` (wzór stageA_boot.sh: REPO-2, pgrep wyłączności,
cooldown, GZ_IP=127.0.0.1 habitat; bridge po `armed`): boot `results/2A/probeC/C1_c11_s01`,
ep 11 (c11_s01, seed 1, CCW), CONTROLLER=net NET_ARM=ncp (weights_sha 0337d5ea…), FEED=V.
Oś czasu (sim): armed 99.24 → takeoff → offboard 110.85 → make_feed (YOLO in-process,
~4.8 s wall, strumień offboard podtrzymany przez mavsdk_server — mechanizm potwierdzony:
offboard NIE padł) → episode 115.12–155.13 (koniec regułą „nie weszło" t_rel>40) →
reset, land, finalize rc=0. Manifest: kind=2a, n_valid_V2p=1, dsw 0.9637, longest_stall
0.0, **feed_sha d6a3367b… = FEED-V po N2** (dowód: rejestr zadziałał, FeedVisionLive
SKONSTRUOWANY, YOLO załadowany; FeedB w S2b miał da9ef2f4…).

### §2a. Bloker drivera (błąd MÓJ): bridge 0 klatek

`probeC_boot.sh` (wersja lotu C1) robił globalne `export PYTHONPATH=$B0SP` — potrzebne
procesowi bench_flight (torch in-process), ale dziedziczone też przez `ros2 run
ros_gz_bridge …` i `ros2 topic list`. B0SP maskuje metadata dystrybucji ros2cli ⇒
`importlib.metadata.PackageNotFoundError: ros2cli` ⇒ bridge umarł na starcie
(`C1_c11_s01/bridge_feedv.log` traceback; `topics.txt` sekcja ros2 pusta). Repro offline:
`PYTHONPATH=.b0deps/... ros2 topic list` → ten sam błąd. **Naprawa wykonana** (driver to
narzędzie): B0SP+FEED idą wyłącznie w env inwokacji `run_boot.sh`; bridge startuje z
czystym PYTHONPATH. Klasa błędu: lustro lekcji REPO/K1 o zasięgu env — wpis do odchyleń.

### §2b. Bloker FROZEN (budowa S1): kolizja egzekutora globalnego rclpy

`C1_c11_s01/act.log:8-22`:
```
Exception in thread Thread-4 (_spin):
  File ".../harness/feed_vision.py", line 299, in _spin
    rclpy.spin_once(self._node, timeout_sec=0.05)
  File ".../rclpy/executors.py", line 222, in _enter_spin
    raise RuntimeError('Executor is already spinning')
```
Mechanizm: `rclpy.spin_once(node)` używa egzekutora **GLOBALNEGO**. bench_flight spinuje
nim swój węzeł EKF w wątku (`bench_flight.py:248-251`, pętla `rclpy.spin_once(ekf, 0.02)`).
Wątek `_spin` FeedVisionLive (`feed_vision.py:296-299`) woła to samo na swoim węźle ⇒
RuntimeError przy pierwszym wywołaniu ⇒ wątek ginie (jednorazowy wyjątek w threading) ⇒
FeedVisionLive nie dostaje ŻADNEGO callbacku: `_own=None` na zawsze, obrazy nieodbierane.
Skutek niezależny od bridge'a — **2a i 2b blokują rozłącznie, każdy w pełni**.
Dlaczego nie wykryte wcześniej: S1 = zero bootów (smoke offline na FeedVision-rdzeniu,
bez LIVE-in-process); S2/S2b karmiły shadow w OSOBNYM procesie (`shadow_feed_live.py`,
własny rclpy.init — kolizji być nie mogło). Docstring FeedVisionLive („własny węzeł +
spin-thread — zero dotykania pętli bench_flight") opisuje intencję, której implementacja
nie dowiozła: węzeł własny, egzekutor WSPÓLNY.

Repro i dowód naprawy-kandydata (offline, zero lotów, `results/2A/tools/
probeC_repro_executor.py`): część `collision` odtwarza RuntimeError 1:1 (wzór
bench:250 vs feed_vision:299); część `fix` — węzeł feedu na DEDYKOWANYM
`SingleThreadedExecutor` (add_node + pętla `ex.spin_once(0.05)`) współistnieje ze spinem
globalnym i odbiera 5/5 wiadomości. Szkic naprawy **N3-C** (do ratyfikacji, ~3 linie w
`FeedVisionLive.__init__`/`_spin`, rdzeń percepcji YOLO/MTI/admisja NIETKNIĘTY):
```python
# __init__:  self._ex = SingleThreadedExecutor(); self._ex.add_node(self._node)
# _spin:     while self._running and rclpy.ok(): self._ex.spin_once(timeout_sec=0.05)
```
Alternatywa bez zmiany sha: override `FeedVisionLive._spin` w launcherze drivera
(runtime-patch, wzór „proxy loga" S2) — NIE rekomenduję: to edycja zachowania toru
percepcji w locie bez zmiany bajtów, gorsza jawnościowo niż uczciwa edycja z nowym sha
w FREEZE_2A.

## §3. Wyniki C1 (to, co pomiar uczciwie dał)

**S-BEZP (kryterialne):** breach 0, REFUSE 0 (żadnej gałęzi), REFUSE(POS) brak. UWAGA:
to wynik ZDEGENEROWANY — nie „system bezpieczny przy złej percepcji", tylko „system z
MARTWYM feedem nie robi nic": track_valid nigdy, NCP w fazie hold 791/791 ticków,
|cmd|<0.1 przez 100 % epizodu, r_est_max 0.2 m (margines do R_E 31.8 m). Pytania sondy
(sterowanie ku fantomom) NIE dotknięto — fantomów nie było, bo nie było percepcji.
**S-MISJA (opisowe):** orbit-entry NIE (t_entry null, koniec regułą 40 s); z w paśmie
−8.32…−8.60 m; intruz GT (c11_s01 przechodzi nad home) zbliżył się do ślepego,
wiszącego drona na **1.64 m** (t_sim 130.0) — zero reakcji systemu; d_min_m manifestu
1.662 spójne. Rozbiór: `C1_c11_s01/probeC_summary.json` (narzędzie `probeC_analyze.py`,
smoke na boocie S2b A1b dał sensowne wartości: track err p50 0.70 m vs GT = kalibracja
FeedB spójna).

**Prowieniencja:** manifest C1 + sekcja feed_v (topic, sha pustego loga e3b0c442… =
dowód 0 bajtów); nota: numpy w procesie ławki 2.4.4 (B0SP, wymóg torch in-process;
precedens: finalize w run_boot.sh:173 od zawsze z B0SP). GZ_IP=127.0.0.1 zastosowane
(host po reboocie — habitat 05.10); env czysty (proc_gate PASS, load 0.14 na starcie).

## §4. Budżet i status

Boot C1: **lotny, VALID V2′ technicznie, sonda-niewykonana merytorycznie** — klasyfikację
budżetową zostawiam do ANEKS (uczciwie: poleciał ⇒ 5 lotnych VALID z ≤31; jeśli liczony
jak diag/env — 4+1 do osobnej rubryki). Boot C2 NIE poleciał (bloker deterministyczny,
palenie budżetu bez szansy pomiaru). Porcelain przy STOP: tylko artefakty tej sesji
(probeC/, tools sondy, raport) — commit poniżej.

## §5. Do decyzji (ANEKS kolejny)

1. **N3-C:** ratyfikacja edycji `harness/feed_vision.py` `_spin`→dedykowany executor
   (szkic §2b, dowód offline PASS) + nowy sha w FREEZE_2A + test jednostkowy kolizji
   (wzór test_aneks1) → powtórka sondy 2 bootów wg §3 aneksu bez zmian progów/pomiarów.
2. Albo: sankcja dla override'u w driverze (nie rekomenduję, §2b).
3. Klasyfikacja budżetowa C1 (§4).
STOP.
