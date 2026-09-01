# D0 — build ławki (PROMPT_BENCH_BUILD I0.4)

Baza `6b32b07` · I0.1 origin/master..HEAD puste ✓ · READ przed budową.

## (a) sha256 pinów i sędziów = zgodne z `k1_shield_pins.py`

| plik | sha256 | zgodne |
|---|---|---|
| `r01/shield.py` | `1c584964ddc85192c1381f5041e8ed3b7b81b984c92b8f33d5c685acd2cba2c2` | ✓ |
| `r03/config.py` | `4c440e4265574b68c2a3341105d5cb0ace07ed683cd0bca43228af356629752a` | ✓ |
| `r03/gate_run_r03.py` | `c3ccabe04b9cae8ea57cfa899b8e363451fe9a6b4dbaffc8b1b0910ad192b729` | ✓ |
| `r03/controllers/base.py` | `7fc45cf2216d4a9eae86fa9ee714d70354fafbc64721f76bff7c0575bb9fb8f9` | ✓ |
| `k1/k1_judge.py` | `4e0dc0af…` | ✓ |
| `tools/act_judge.py` | `79b1e936…` | ✓ |

## (b) FAKT: gdzie egzekwowana jest saturacja |v| ≤ V_MAX (P4 / P-BB1)

**Wyłącznie w kontrolerze.** `r03/controllers/route_follower.py:42`: `vn,ve = (vmax·dx/dist, vmax·dy/dist)` —
norma pozioma = vmax Z KONSTRUKCJI (wektor jednostkowy × vmax). 
- Gate (`gate_run_r03.py`) **NIE obcina**: wysyła `cmd["v_ned"]` bez sprawdzenia (`:298 vn,ve = cmd["v_ned"][0],[1]`).
- `k1_finalize.py:577 vmax_check` = **pomiar post-hoc** (`v_gt_max_cruise` vs `V_ENV`), nie egzekucja.
- `r01/shield.py` decyduje ALLOW/REFUSE — nie obcina prędkości.
- PX4: MPC ma własne limity, ale to nie jest gwarancja na poziomie setpointu offboard.

**Wniosek (P-BB1 potwierdzone):** ani gate, ani finalize nie saturują; dziś robi to tylko kontroler. →
`orbit_executor` MUSI saturować własne wyjście (`common.clip_v`), a test kontraktu sprawdza, że żaden
kontroler nie wypuszcza |v| > V_MAX (ANEKS P4).

## (c) FAKT: jak gate/feed dostaje czas SIM (dla filtrów w czasie sim, ANEKS P2)

- `gate_run_r03.py:82` gt_cb: `sim = msg.header.stamp.sec + msg.header.stamp.nsec/1e9` — **sim-time z nagłówka
  `dynamic_pose/info`** (Pose_V header.stamp = sim-time).
- `pose/info` (źródło feedu, R2) niesie ten sam typ nagłówka → `track_feed` czyta sim-time z `header.stamp`
  każdej próbki `pose/info` (49.8 Hz).
- Alternatywa: `/world/W/clock` (gz.msgs Clock) — subskrybowany dziś przez `GzPoseClient` (`intruder_driver.py:47`).
- `ekf` `m.timestamp/1e6` (`:97`) = czas PX4 (µs), NIE gz-sim — **nie używać do filtrów feedu** (rozjazd z sim).

**Decyzja build:** `track_feed` i `intruder_motion` liczą sim-time z `header.stamp` próbek `pose/info`
(+ `/world/W/clock` jako zegar fazy). Wszystkie okna/opóźnienia w czasie sim (P2).

## (d) FAKT: jak wrapper przekazuje env do modułu lotu

`harness/run_boot.sh` krok 8 `case "$FLIGHT"`: gałęzie `gate_r03|arm_n|empty` z INLINE env
(`SCEN`, `K1_POINT`, `CONTROLLER`, `GATE_OUT`, `PX4_GZ_WORLD`, `HEADLESS`, `B1_MODEL`, `PYTHONPATH`).
Env zewnętrzny (eksportowany przy wywołaniu wrappera) jest DZIEDZICZONY przez subproces pythona (inline env
DODAJE, nie czyści). Brak gałęzi `bench` → default `*)` `exit 2`.

**Delta (G/I):** JEDNA linia — nowa gałąź `bench)` wołająca `python3 -m bench.bench_flight`. `bench_flight`
czyta `BENCH_MANIFEST`/`BENCH_EPISODES`/`FEED_PROFILE`/`CONTROLLER`/`INTRUDER_MOTION` z `os.environ`
(dziedziczone), więc gałąź = jedna linia fizyczna. `intruder_motion.py` uruchamia `bench_flight` wewnętrznie
(INTRUDER_MOTION=1) → BEZ drugiej linii wrappera. `gate_run_r03.py` NIETKNIĘTY. Diff verbatim: RAPORT §1.
