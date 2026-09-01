# RECON_BENCH — recon ławki (Verified Patrol Bench), read-only

LiquidPatrol · pozycja 2 planu · CC 31.08.2026 · wykonawca Claude Code · READ-ONLY (SR-2). Baza `35c5446`.
Recon niczego nie rozstrzyga — mierzy i wypisuje. Każdy fakt: plik:linia / topik z ŻYWEGO echa / pomiar z bootu.
Booty recon (≤2, `FLIGHT=empty WORLD=world_demo_A3 INTRUDER=1` przez `harness/run_boot.sh`): **boot1** i **boot2**
oba VALID (arm_ok, habitat VALID, model_in_state=1). Env-block przed boot1 (dreamforge @100% CPU) — NIE liczony
(bramka §3 zadziałała, `gate_fired_evidence.txt`).

## D0 — inwentarz plików (intruz / percepcja / orbita / demonstracje)

| obszar | plik | rola |
|---|---|---|
| intruz model | `r02/intruder_model.sdf` | wizual-only, STATYCZNY; poza sterowana z zewnątrz (set_pose) |
| intruz actor | `r02/intruder_actor.sdf`, `r02/intruder_phys.sdf` | warianty: aktor z trajektorią / fizyczny |
| ruch intruza | `r02/intruder_driver.py` | `set_pose()` (subprocess), `GzPoseClient` (trwały gz.transport13), `scripted_pose(sim_t)` (deterministyczna trajektoria) |
| ruch (sweep) | `r02/signal_sweep.py`, `r02/run_gate_r02.sh` | historia set_pose: name-mismatch, `SKIP_CREATE`/`SKIP_SETPOSE`, weryfikacja pozy |
| próbnik pozy | `r02/sample_intruder_pose.py` | czyta `dynamic_pose/info`, wyciąga (sim_time, intruder.y) — dla ACTORA |
| percepcja | `r02/detector_node.py`, `r02/mti.py` | YOLO+MTI runtime (osobny proces, torch/ROS); `MTITracker`, `struktura∧MTI` |
| geometria wzgl. | `r02/observe_guidance.py` | `estimate_intruder_ned(pos,yaw,cx,cy)` — estymacja NED intruza z bearingu kamery |
| ramki | `common/frames.py` | ned2enu/enu2ned/drv2ned/ned2drv (NED[N,E,D], ENU[E,N,U], DRV intruz[E,N,-U]) |
| sędzia DEMO-B | `tools/act_judge.py` | wejście = trace+manifest+spec; `_range3d(pos,intr)` — intr z SPEC, nie z żywego strumienia |
| kontroler | `r03/controllers/{base,route_follower}.py` | `SetpointSource.step(tick,pos,vel,now,descending)` — BEZ stanu intruza |
| spawn intruza | `harness/run_boot.sh:7` (krok 7) | `gz service create` `r02/intruder_model.sdf`, `model_in_state` z `gz model --list` |

---

## R1 — Scena i intruz

**Światy** (`worlds/`, `ls -la`): `world_demo_A1/A2/A3` (~42–60 KB), `world_demo_v1/v2/v3/v3_1`.
`world_demo_A3` (60 KB): ground_plane 500×500, scenografia `tex_0..tex_83`, `tree_*`, `bldg_*`, `rock_*`
(przeszkody boxy ~2–3 m; z żywego `pose/info` boot2), **kamera filmowa `film_cam`** (`worlds/world_demo_A3.sdf:1279`,
sensor `film` type camera) — do ławki NIEPOTRZEBNA (ławka nie sądzi z obrazu; koszt = 1 sensor kamery + bridge, opcjonalny `FILM=0`).
Koszt bootu A3 (zmierzone B2/recon): arm+settle+hover ~3.6 min; boot komplet + finalize OK.

**Ruch intruza — mechanizmy (żywy test boot1/boot2):**
- **`set_pose` (gz service `/world/W/set_pose`, gz.msgs.Pose)** — DZIŚ dostępny i działa. `GzPoseClient`
  (`r02/intruder_driver.py:44`, trwały klient, worker async): **zmierzone applied_hz = 19.63 (boot1) / 19.92 (boot2)**
  przy targecie 20 Hz, **ok_rate = 0.876 / 0.874** (frakcja request→ok). Historia R02C: name-mismatch (spójna nazwa
  „intruder" przez create/set_pose/query, `run_gate_r02.sh:54`), `SKIP_CREATE`/`SKIP_SETPOSE` (para repro).
- **plugin trajektorii w SDF (actor)** — `intruder_actor.sdf` (odczyt D0); actor animowany pojawia się w `dynamic_pose/info`.
- **max sensowna częstotliwość aktualizacji:** ~20 Hz aplikowane (GzPoseClient worker); wyżej ogranicza request set_pose
  (~108 ms sync historycznie, ANEKS_D7 §7a → async worker; teraz ~20 Hz stabilnie).
- **Determinizm:** `scripted_pose(sim_t)` (`intruder_driver.py:18`) = CZYSTA funkcja sim-time (bez fizyki/losu) →
  ta sama sekwencja sim_t ⇒ ta sama trajektoria (z konstrukcji; ocena jakościowa PASS — boot1 y_cmd 6.588→−12.9 wg skryptu).
- **Ziarno:** `scripted_pose` przyjmuje parametry (x,z,ymin,ymax,v); „seed=ID scenariusza podmienia parametry"
  (`intruder_driver.py:9`) — powtarzalność osadzić w skrypcie harnessa movera (seed→parametry trajektorii).

---

## R2 — Skąd kontroler może znać stan intruza (pytanie rozstrzygające)

**Żywe topiki (boot1, `gz topic -l` → `recon_gz_topics.txt`, 43 topiki; `ros2 topic list` → `recon_ros2_topics.txt`, 53):**
- **`/world/world_demo_A3/pose/info`** — poza WSZYSTKICH modeli, w tym `name: "intruder"` (boot2
  `recon2_poseinfo_names.txt`: intruder + cała scenografia). **Częstotliwość: ~49.8 Hz** (398 nagłówków/8 s,
  `recon2_poseinfo_rate.txt`). Intruz statyczny/teleportowany JEST TU (x=12, y=10.824, z=10 = `scripted_pose`).
- **`/world/world_demo_A3/dynamic_pose/info`** — poza tylko encji FIZYCZNIE-DYNAMICZNYCH: `base_link`,
  `rotor_0..3`, `x500_mono_cam_0` (boot2 `recon2_dynpose_names.txt`) = **DRON**. **~49.8 Hz** (398/8 s).
  **Intruz statyczny (`intruder_model.sdf` + set_pose) NIE pojawia się tutaj** (boot1+boot2 parallel_sub
  filtr name=="intruder" → n_msgs=0). Actor (trajektoria) by się pojawił.
- **ROS:** ŻADEN z 53 topików ros2 nie niesie pozy intruza (tylko `/fmu/out/*` = PX4 uXRCE). Intruz = wyłącznie gz-side.

**Kluczowy fakt R2:** poza intruza dostępna z gz na **~50 Hz bez ROS** (P-B1 potwierdzone). Dla intruza
STATYCZNEGO+set_pose źródłem jest **`pose/info`** (nie `dynamic_pose/info`); dla ACTORA — `dynamic_pose/info`.

**Runtime percepcja/MTI zdatna na 20 Hz:** `r02/detector_node.py`+`r02/mti.py` ISTNIEJĄ (YOLO+MTI, osobny proces,
`.b0deps/weights/yolov8s-worldv2.pt`, wymaga torch/ROS). W stacku recon (empty flight) **NIE uruchomiony** —
zero topików detektora w echu. Historia (REGATE/§8): percepcja live limitowała ENTRY (mti_ok centralnie),
nie 20 Hz-czysta. → **P-B3 kierunkowo potwierdzone: brak GOTOWEGO runtime toru percepcji w tym stacku; track-feed
trzeba emulować harnessem** (decyzja w PRE).

**Fakt architektoniczny (żywy test, boot1/boot2):** równoległa subskrypcja gz.transport13 (`parallel_sub.py`)
+ zapis jsonl RÓWNOLEGLE do stacku **NIE dławi mostu**: **RTF 1.0 → 1.0** (boot1 `recon_rtf_impact.json`,
boot2 `recon2_rtf_impact.json`), przy jednoczesnym moverze 20 Hz. → **P-B2 potwierdzone.** Kontroler
(niepinowany) MOŻE mieć własną subskrypcję gz + własny zapis demonstracji bez wiedzy pętli gate.

---

## R3 — Co może widzieć sędzia orbity

**Dzisiejszy trace (`r03/gate_run_r03.py`, odczyt):**
- wiersz `gt` (`:83`): `{t, mono, sim, x, y, z}` gdzie `p.name == MODEL` (`:81`, MODEL=`x500_mono_cam_0`) =
  **poza DRONA, NIE intruza**. Intruza w trace NIE MA.
- wiersz `tick` (`:263`): `{tick, mono, r_est, margin_R_E, decision, reason, state, pos, dr, descending}` —
  brak pozy intruza, brak `v_ned`/`tgt`.
- `act_judge.py` (DEMO-B): `_range3d(pos, intr)` (`:38`) — `intr` z SPEC (poza intruza zadeklarowana), nie z żywego strumienia.

**Legalna droga GT intruza dla sędziego (GT = wyłącznie sędzia):** osobny plik GT pisany przez harness.
Co `harness/run_boot.sh` UMIE dziś: spawn intruza + `model_in_state` (obecność), `world_hash`, `ulog_sha`.
Czego BRAKUJE (LISTA, nie kod):
1. zapis GT pozy intruza w czasie (jsonl sim_t→xyz) — mover ZNA `scripted_pose(sim_t)`, więc może pisać wprost;
2. albo równoległa subskrypcja `pose/info` filtr „intruder" → GT jsonl (~50 Hz, dowiedzione R2);
3. spięcie GT z trace drona po sim-time (wspólna ramka: `frames.drv2ned` intruz → NED drona).

**`common/frames.py` sygnatury:** `ned2enu(v)`, `enu2ned(v)`, `drv2enu(v)`, `enu2drv(v)`, `drv2gz(v)`,
`drv2ned(v)` („intruz DRV[E,N,-U]→NED[N,E,D], zamiana E/N"), `ned2drv(v)`. Konwencje: NED=[N,E,D], ENU=[E,N,U], DRV(intruz)=[E,N,-U].

---

## R4 — Kanał demonstracji

**Wejścia `SetpointSource.step` DZIŚ (`r03/controllers/base.py`, verbatim):**
`step(tick, pos_ned, vel_ned, now_s, descending)`. Zwraca `tgt_ned/v_ned/yaw/seg_i/dist/wps/extra`.
**Brakuje orbicie:** stan WZGLĘDNY intruza (pozycja/prędkość intruza w ramce drona) — dziś step go NIE dostaje.
Do dołożenia (LISTA): pozycja intruza (NED, z track-feed/GT), ew. prędkość intruza, znacznik „intruz widoczny/track-age".

**Logowanie `v_ned` per tick:** wiersz `tick` NIE loguje `v_ned` ani `tgt` (tylko `decision`/`pos`/`r_est`).
→ komenda kontrolera NIE jest dziś logowana per tick. **Logowanie po stronie modułu kontrolera (R2: własny jsonl)
domyka lukę** — kontroler pisze własny rekord demonstracji (tick, pos, v_ned, stan wzgl. intruza) bez dotykania pinów.

**Rozmiar logu (szacunek z wiersza pozy ~113 B, `parallel_sub` schemat):** @20 Hz ≈ **2.26 KB/s = 8.1 MB/h**;
@50 Hz ≈ 5.65 KB/s. Rząd wielkości: demonstracja ~1–2 min → ~0.3 MB. Zaniedbywalne (RTF bez wpływu, R2).

---

## R5 — Arytmetyka koperty (z config, plik:linia)

| stała | wartość | źródło |
|---|---|---|
| V_MAX | 3.0 m/s | `r01/config.py:24` |
| R_E (koperta) | 32.0 m | `r01/config.py:30` |
| EPS_CAP | 9.25 m | `r03/config.py:20` |
| HALF_P (pół boku) | 14.07 m | `r03/config.py:26` |
| R_ROUTE_P | 19.90 m | `r03/config.py:25` |
| DELTA_MARGIN | 2.85 m | `r01/config.py:27` |
| A_BRAKE | 2.0 m/s² (zmierz. 2.65) | `r01/config.py:26` |
| DEBOUNCE_TICKS | 2 (0.10 s) | `r03/config.py:30` |
| DT / TICK_HZ | 0.05 s / 20 Hz | `r01/config.py:41,40` |
| T_REACT_S | 0.20 s | `r01/config.py:25` |

**Geometria orbity (sama arytmetyka):**
- Poza spawnu intruza (wrapper default `harness/run_boot.sh` INTRUDER_POSE): `x:7, y:0, z:11.5` (gz world).
- a_dośrodkowe = v²/r_orb. Przy v=V_MAX=3.0: r_orb ≥ v²/A_BRAKE = 9/2.0 = **4.5 m** by a ≤ A_BRAKE. Wolniej → ciaśniej
  (v=2 → r_orb ≥ 2.0 m). Pasmo r_orb ~[4.5, ~15] m mieści się z zapasem prędkościowym.
- Odległość orbity od granicy R_E: intruz ~7 m od origin; drone orbituje r_orb wokół intruza → max r_est ≈ 7 + r_orb.
  Dla r_orb=15 m: r_est_max ≈ 22 m. Zapas do R_E=32: 32 − 22 − x_exc(K1 ~2.5–3.5) ≈ **6.5–7.5 m**. r_orb do ~15 m
  bezpieczny; nawet r_orb=20 m (r_est~27) mieści się (~1.5–2.5 m zapasu przy dryfie).

**Czas:**
- Jedno okrążenie: obwód 2π·r_orb / V_MAX. r_orb=8 m → 2π·8/3 ≈ **16.8 s/okrążenie**. N=3 → ~50 s + podejście ~10 s ≈ **~60 s/demonstracja**.
- Booty/h (zmierzone B2, START→START): cykle [536,537,540,540,535] s → mean 538 s → **6.7 boot/h** (z cooldownem 5 min).
  Lot ~3.6 min. Jedna sesja wieczorna ~3 h → ~20 bootów; jeśli 1 demonstracja/boot → ~20 demonstracji; jeśli
  okno lotu mieści kilka demonstracji (hover 60 s → wydłużyć) → więcej. (Mianownik do decyzji w PRE.)

---

## R6 — Kandydackie metryki „udanej orbity" (mierzalne z R3; BEZ wyboru — wybór w PRE)

| metryka | jak zmierzona | z pliku |
|---|---|---|
| frakcja czasu w paśmie [r_lo, r_hi] wokół intruza | per-tick \|pos_drona − pos_intruza\| (GT), frakcja w paśmie | GT-jsonl (R3) + trace `pos` |
| pokrycie kątowe ≥ θ | kąt bearing drona względem intruza po okręgu; suma pokrytych sektorów | GT-jsonl + trace `pos` |
| czas do wejścia w pasmo | pierwszy tick z r ∈ [r_lo,r_hi] − t_start | trace `tick`/mono + GT |
| liczba REFUSE | count `decision==REFUSE` w tick | trace `tick.decision` |
| breach (R_E) | max r_est vs R_E (jak K1 sędzia) | trace `tick.r_est`/`margin_R_E` |
| stabilność odstępu (intruz ruchomy) | sd(\|pos−intr\|) w oknie orbity | GT-jsonl + trace `pos` |

Wszystkie wymagają GT intruza w czasie (R3 luka) + trace drona (istnieje). `margin_R_E`/`r_est` już w trace.

---

## PYTANIA DO PRE (decyzje, które recon zostawia otwarte)

1. **Źródło stanu intruza dla KONTROLERA:** (a) emulowany track-feed z zadeklarowanym opóźnieniem/szumem
   (harness zna `scripted_pose` → podaje pozycję z Δt/σ), vs (b) percepcja live (`detector_node`+MTI, dziś
   nieuruchomiona, percepcja-limitowana). Recon: (a) trywialne i deterministyczne; (b) wymaga toru percepcji. **[P-B3 → (a) prawdopodobne]**
2. **Typ intruza:** static `intruder_model.sdf`+set_pose (poza na `pose/info` @50 Hz) vs actor `intruder_actor.sdf`
   (poza na `dynamic_pose/info`). Wybór wpływa na źródło GT i na to, czy `sample_intruder_pose.py` działa wprost.
3. **Parametry orbity:** r_orb (pasmo 4.5–~15 m bezpieczne), v_orbit (≤ V_MAX=3), N okrążeń, wysokość, kierunek.
4. **Schemat rekordu demonstracji:** pola (tick, sim_t, pos_drona, v_ned, stan_wzgl_intruza, r, bearing);
   gdzie pisany (moduł kontrolera, R2 — bez dotykania pinów); format (jsonl ~113 B/wiersz @20 Hz).
5. **GT dla sędziego:** plik GT intruza (mover pisze wprost z `scripted_pose`, LUB subskrypcja `pose/info`);
   spięcie po sim-time; ramka wspólna (`frames.drv2ned`).
6. **Definicja „sukcesu orbity" i mianownik „≥90 %":** która metryka R6, pasmo [r_lo,r_hi], próg pokrycia θ,
   nad czym liczone 90 % (frakcja ticków? demonstracji? sesji?).
7. **Kryterium śmierci** (kiedy ławka „nie żyje": breach? brak wejścia w pasmo w czasie T? liczba REFUSE?).
8. **Budżety:** ile demonstracji-nauczyciela, ile lotów-kotwicy (ramię porównawcze pod sędzią), sesje.
9. **Świat:** `world_demo_A3` (z kamerą filmową, koszt) vs lżejszy bez film_cam (`FILM=0` już wspiera wrapper).
10. **Kadencja ruchu intruza:** ~20 Hz set_pose (GzPoseClient) — czy wystarcza; determinizm z `scripted_pose(sim_t)` + seed.

---

## Predykcje CC — bilans

- **P-B1 ✓** — poza intruza z gz na ~50 Hz bez ROS (`pose/info` 49.8 Hz).
- **P-B2 ✓** — równoległa subskrypcja + jsonl nie zdławiła mostu (RTF 1.0→1.0, boot1+boot2, mover 20 Hz równolegle).
- **P-B3 ✓ (kierunkowo)** — brak gotowego runtime toru percepcji w stacku (detektor nieuruchomiony, percepcja-limitowany historycznie); track-feed do emulacji harnessem — decyzja w PRE (pyt. 1).

## Bonus (nieplanowane znalezisko)
Bramka procesowa §3 (`harness/proc_gate.py`, INFRA-3 B1) **zadziałała w boju**: przed boot1 recon odmówiła startu,
gdy pojawił się `dreamforge-arc/attempts_2_10.py` @100% CPU (env-block, `boot1` manifest kind=env-block →
`gate_fired_evidence.txt`). Boot NIE policzony do budżetu. Live-walidacja mechanizmu B1.
