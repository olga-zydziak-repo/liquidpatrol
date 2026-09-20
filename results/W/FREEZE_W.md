FREEZE_W — zamrożenie przyrządu nogi W (wiatr) przed pierwszym bootem kryterialnym
=================================================================================
CC · 20.09.2026 · PROMPT_W_S2 §1 · commit C-F (PRZED jakimkolwiek bootem S2).
Od tego commitu przyrząd nogi W jest ZAMROŻONY (PRE_W §6/§10, ANEKS_W-0 §2). Defekt znaleziony
w zamrożonym przyrządzie po freeze ⇒ STOP + pytanie do CC — nigdy cicha poprawka (SR-W-3/S2-A).

Wszystkie sumy = sha256 pełnego pliku (bez skrótów), stan drzewa = HEAD po pushu commitów S1
(2529c5a build [CB] + d766310 [CW-A]), git status --porcelain pusty w chwili freeze.


§1. TABELA plik → sha256 (przyrząd nogi W)
------------------------------------------
| plik                                    | sha256                                                           |
|-----------------------------------------|------------------------------------------------------------------|
| bench/w_judge.py                        | e68040ae27482e582d7bff698b0393534357352c6d76eaa820010d2410463856 |
| bench/tests_w_judge.py                  | 00886e9f2691f17c7313dccff2ea5158717801dcd3b664ff8c664b60bfa0cc38 |
| tools/w_launcher.sh                     | 28df8928b9ef9e2b08ab852e2f351eab9146351a23e68a618e829cb27247a701 |
| tools/w_tilt.py                         | b22be3d056829e8415c921eea8120ba8ea2a894c82e3c1e177f9b254d251c771 |
| bench/tests_w_arm_always.py             | f0b189f5a34102a1e17bf4d7f7fe65c517d6870817620486de215e967fd6c23c |
| bench/bench_flight.py (sha po S1)       | 3a52e19f2979b40c858d7c0b28996dec81244bbb315a7c91ebcae99b7884a049 |
| worlds/world_wind_s0.sdf                | 921bdda7a975321c524a557e8ae0204e457a11011ef17f9b21adf09def046be2 |
| worlds/world_wind_s1p5.sdf              | b8380e8ad9ffa10cdbd1aaeb05fde81e4415af3e4ac11974c8297d1c09f5bb5b |
| worlds/world_wind_s3.sdf                | 73214a2d822c6c7fc8b896209ff0efac57d7658b1c4ccd7ce9916a0059de0bcc |
| worlds/world_wind_s4p5.sdf              | cf9df7b83901b409ee2354212f9369f37a53ba69e8321ee484b5c3a20181efe1 |
| worlds/wind_models/x500_base/model.sdf  | 13c9174d4195b730e594d2c9b1de9041492885aaffdb1895bbbe787476b7e214 |

Zgodność świateł ze sha16 raportu W-A: s0=921bdda7 · s1p5=b8380e8a · s3=73214a2d · s4p5=cf9df7b8 —
identyczne (RAPORT_W_A §1/§6). Model wind_models/x500_base (enable_wind) prependowany przez
w_launcher (GZ_SIM_RESOURCE_PATH, W9/R1.7).


§2. bench_flight.py — jedyna zmiana harnessu nogi W (W_ARM_ALWAYS), diff verbatim
--------------------------------------------------------------------------------
Odsyłacz: commit build S1 2529c5a0b9060653f311f79793d70bb71ed1111d, plik bench/bench_flight.py
(blob 8476415 → d63aa3d). Diff 2 hunki (verbatim):

    @@ -70,6 +70,10 @@ K2_INJECT_T = ...
     K2_LEGACY_UNARMED = os.environ.get("K2_LEGACY_UNARMED") == "1"
     K2_ARM_MONITOR = not K2_LEGACY_UNARMED
    +# W (noga wiatru, PRE_W §2): W_ARM_ALWAYS=1 uzbraja pos_flag od wejścia w OFFBOARD (nie od t_entry),
    +# bo kampania W jest bez denialu i bez potrzeby wejścia w pasmo intruza. default OFF = bit-zgodne
    +# z linią bazową (arm zależy wyłącznie od t_entry gdy flaga wyłączona). Jedyna zmiana harnessu nogi W.
    +W_ARM_ALWAYS = os.environ.get("W_ARM_ALWAYS") == "1"
     _SD_CFG = {...}
    @@ -358,7 +362,7 @@ async def main():
                 ev("denial", ...)
    -            arm = (denial_done or (K2_ARM_MONITOR and t_entry is not None))
    +            arm = (denial_done or (K2_ARM_MONITOR and (W_ARM_ALWAYS or t_entry is not None)))
                 pf = dr if arm else None

default OFF ⇒ bit-zgodne z linią bazową (test dwustronny tests_w_arm_always 4/4, B6 S1). Kampania
W-B lata z W_ARM_ALWAYS=1 ⇒ każdy epizod kryterialny w całości jest próbką ramienia (−) (PRE §2).


§3. Identyfikatory 3 ziaren komórki c11 (CYTAT VERBATIM z scenario_manifest.json)
--------------------------------------------------------------------------------
Źródło: results/BENCH/scenario_manifest.json, sha256
e0527026df01b488e38e79307c258bf447ad68f2da0c7db3fac3810f0a388fd7 (== e0527026, PRE §3/§6/W5).
Komórka c11 = cells[11] = {"cell_index": 11, "v_intr": 1.0, "bearing_deg": 270}.
3 ziarna kryterialne = 3 niebazowe (is_test=false) ziarna bloku 1 (seed 1/2/3); seed 4 (c11_s04)
jest is_test=true (holdout ławki) i NIE wchodzi do siatki W. Cytat pól identyfikujących verbatim:

  c11_s01 : {"scenario_id": "c11_s01", "cell_index": 11, "seed": 1, "block": 1, "is_test": false,
             "orbit_dir": "CCW", "start_pos": [-0.0, -15.0, 10.0], "z": 10.0, "ep_dur_s": 110.0,
             "episode_id": 11}
  c11_s02 : {"scenario_id": "c11_s02", "cell_index": 11, "seed": 2, "block": 1, "is_test": false,
             "orbit_dir": "CW",  "start_pos": [-0.0, -15.0, 10.0], "z": 10.0, "ep_dur_s": 110.0,
             "episode_id": 23}
  c11_s03 : {"scenario_id": "c11_s03", "cell_index": 11, "seed": 3, "block": 1, "is_test": false,
             "orbit_dir": "CCW", "start_pos": [-0.0, -15.0, 10.0], "z": 10.0, "ep_dur_s": 110.0,
             "episode_id": 35}

Mapowanie na selektor bench_flight (BENCH_EPISODE_IDS): s01→11, s02→23, s03→35.
Boot-0 diag (§2 R-NC): „pierwsze ziarno" = c11_s01 = episode_id 11.


§4. FROZEN NIETKNIĘTE (spoza przyrządu W, dziedziczone)
------------------------------------------------------
harness/run_boot.sh · piny 5/5 · sędziowie (bench_judge 8ec0fcfb i pozostali) · wagi net/frozen ·
provery/certy · gate (pinowany — dlatego W_ARM_ALWAYS żyje w bench_flight, nie w gate). w_judge
wyłącznie DOKŁADA pola nad bench_judge (PRE §6); bench_judge orzeka ważność V2′ epizodu bez zmian.
git status --porcelain pusty w chwili C-F; git diff HEAD pusty (drzewo == HEAD po S1).
