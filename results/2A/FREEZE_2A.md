# FREEZE_2A — zamrożenie przyrządu nogi 2A (S1 build, przed STOP-2A1)

CC · 03.10.2026 · PROMPT_2A_S1 §5 / PRE_2A §2-D6. Zmiana któregokolwiek sha/stałej poniżej
po tym commicie = nowa decyzja do ratyfikacji, nie poprawka.

## sha256 narzędzi

| plik | sha256 |
|---|---|
| detektor `.b0deps/weights/yolov8s-worldv2.pt` | `9b2c17ab6124a913e9b3a5c170617920d91b0f01111a8479da69f00e2cf27792` |
| `harness/feed_vision.py` | `0ce7569c2cbd012a17db98be69fb5c759a4e706f695046c93c3daeeff891e7cf` |
| `harness/feed_registry.py` | `2629bc40ff0e3ae798fde56b6a126efdc242f30e8996e5e01c31bcb45fa5b840` |
| `results/2A/tools/percep_judge.py` (sędzia percepcji) | `363c37b79abb7479fb71ce5815712f5e83d05615ecefe591cae4559908cc155e` |
| `bench/bench_flight.py` PRZED edycjami (baza, PRE D6) | `3a52e19f2979b40c858d7c0b28996dec81244bbb315a7c91ebcae99b7884a049` |
| `bench/bench_flight.py` PO dwóch edycjach | `2972a48a081e42bb4cd4de1690c47c678287df6f6a739d01dc8b862c20b15b00` |
| `bench/bench_flight.py` PO N1 (ANEKS_2A-1 §3: rad→deg na granicy MAVSDK — TRZECIA edycja, jawne rozszerzenie D6) | `05137098abc1c31e6d3f70ca80e6b721487330131fa8a39181355b659f523a43` |
| `harness/feed_vision.py` PO N2 (ANEKS_2A-1 §3: REFRESH bramkowany + sufit θ_age feedu) | `0a97512106d8ca708c77329fd2bff50e8fe9b5fc0b06da5fa6b7eb5992a2f5de` |
| `harness/feed_vision.py` PO N3-C (ANEKS_2A-3 §3: dedykowany SingleThreadedExecutor węzła feedu — naprawa kolizji egzekutora globalnego z bootu C1; rdzeń YOLO/MTI/admisja/pinhole NIETKNIĘTY) | `acc81df76acf4570af6629edefb77f9ee0051a0eadcdeaf9da9cf270ba74dcce` |

`feed_sha` FEED-V (sha256 JSON parametrów, analog FeedB):
`ffccf86b59d5055f2efe50f716a82a1fce777bf87e7010a8a9d14260c964ad7b` (S1, PRZED N2)
`d6a3367b210f47e79b2ea9b33151235d3a2a0ac21c4ad2b93dfa93092673a895` (PO N2 — params
+ refresh_gate/refresh_gate_m)
PO N3-C feed_sha **BEZ ZMIAN** (= d6a3367b…): naprawa dotyczy wyłącznie transportu
(egzekutor/wątek spin), nie dotyka słownika `params` — zweryfikowane wykonaniem 06.10.

## Stałe geometrii i parametry FEED-V (echo z kodu, harness/feed_vision.py)

- **f_px = 270.0** — kanon przyrządu MTI (`r02/mti.py:17`, PRE_MTI R1); dokładna wartość
  z SDF kamery: (640/2)/tan(1.74/2) = **269.976 px** (rozjazd 0.009% — przyjęty kanon 270.0,
  jedna ogniskowa w całym programie).
- **W_real = 2.5 m** — rozpiętość ramion intruza; źródło: `r02/intruder_model.sdf:15,18`
  (`<size>0.16 2.5 0.14</size>`, dwa ramiona krzyżowe); to ten sam SDF, który spawnuje
  ławka (`harness/run_boot.sh:123`). Jawny prior klasy celu (PRE D1).
- **Kamera STOCK (D3):** hFOV 1.74 rad = 99.7° · 640×480 · 15 Hz · `always_on=1`
  (`PX4-Autopilot/.../mono_cam/model.sdf:50-66`); montaż FIXED przód, offset w FRD
  **(0.12, −0.03, −0.242) m** (`x500_mono_cam/model.sdf` pose `.12 .03 .242` gz→FRD).
- **Admisja (D2):** struktura∧MTI — `ChannelConfig(entry_require_mti=True)`: k=3,
  edge_margin 0.10, move_thr 0.15, θ_age 3.0 s, L_deliver 0.10 s (wartości z
  `r02/config_r02.py`, READ-ONLY); koincydencja MTI center_thr 0.12; MTIParams domyślne
  (`r02/mti.py:28-41`).
- **REFRESH bramkowany (ANEKS_2A-1 N2):** odświeżenie tracku wyłącznie boxem, który
  (a) spełnia koniunkcję admisyjną NA KLATCE (central z `last_conj` kanału ∧ mti_ok) ALBO
  (b) leży ≤ **REFRESH_GATE_M = 3.0 m** od predykcji tracku (last_pos + trk_vel·Δt).
  Kalibracja promienia z danych S2: FeedB p95 1.26 m + ruch celu w oknie ZOH + jitter
  zasięgu pinhole ~1 m, a FP tła ≥5 m (768/810) — separacja klas z marginesem.
  Sufit wieku tracku FEEDU = θ_age 3.0 s (kanał frozen odświeża swój wiek każdym boxem
  przy locku, więc wygaśnięcie orzeka FEED: reset kanału ⇒ pełna re-admisja ENTRY k=3).
- **Kontrakt (D4):** pozycja pinhole RAW (bez EMA, jak FeedB), trk_vel = linreg **1.0 s** sim,
  świeże próbki = kadencja klatek (nominal 15 Hz, cel ≥ ~10 Hz po stracie klatek/detekcji),
  track_valid = lock kanału ∧ istnieje pozycja; hold-last, age w sim-time.
- **Detektor (D4):** YOLO-World yolov8s-worldv2, `set_classes(["drone"])`, imgsz 640,
  conf=0.001 telemetrycznie (A1: top-1 bez bramkowania conf); guard SR-2 w konstruktorze
  (`sha ≠ FREEZE ⇒ RuntimeError ODMOWA`).

## Wersje środowiska

- `.b0deps` (tor wizji): torch **2.11.0+cu128** · ultralytics **8.4.115** · numpy **2.4.4**;
  GPU RTX 5070 Ti Laptop 12 GB.
- python systemowy (tor ławki/sędziów): numpy **1.26.4** (zgodny z FREEZE_LIQ).

## Konwencje ramek (dziedziczone z zamrożonego przyrządu r02/mti.py — nie definiowane na nowo)

Kwaternion pokładowy `VehicleAttitude.q=[w,x,y,z]` FRD→NED (Hamilton); kamera forward=+X FRD;
ramka optyczna x=prawo(+Y_frd), y=dół(+Z_frd), z=przód(+X_frd) (`r02/mti.py:9-24`).
Orientacja w trace gt (edycja D5): kwaternion POZY GZ (świat gz-ENU→body gz), pola
`qw,qx,qy,qz` — konwersję do FRD/NED robi konsument offline (atrybucja etapu A/B).
