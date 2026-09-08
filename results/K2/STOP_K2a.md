# STOP-K2a — ceremonia ekstrakcji D5 (PROMPT_K2_BUILD, po B2)

LiquidPatrol · K2 build · branch `k2-build` (B2-B6 przygotowane, NIECOMMITOWANE DO MASTER — twardy punkt ceremonii).
Master = K2-B0(docs) + mapa I0.3 + B1 baseline (commit c8c2e3f). Zero bootów.

## §1. Ekstrakcja D5 (B2) — chirurgia pinu wzorem INFRA-3 A1
- `r03/controllers/safe_descend.py` (NOWY) — `safe_descend_step(st, now, cfg)`: literalny ekstrakt bloku is_pos `gate_run_r03.py:275-289` (@ c3ccabe0). Jedyna zmiana: `time.monotonic()` (2× w bloku) → argument `now` (funkcja czysta). `vdesc` schodkowe ⇒ wyjście bit-w-bit gdy wołający podaje now=monotonic().
- gate woła funkcję zamiast bloku inline: **diff = 2 huki (import + wywołanie z marshallingiem stanu), nic więcej** (SR-2).

## §2. Diff verbatim gate (master → branch)
```
diff --git a/r03/gate_run_r03.py b/r03/gate_run_r03.py
index 26fec23..48b9741 100644
--- a/r03/gate_run_r03.py
+++ b/r03/gate_run_r03.py
@@ -27,6 +27,7 @@ from mavsdk.action import ActionError
 from r01.shield import PatrolShield, REFUSE, POS_DEGRADED, M_PATROL
 from r03 import config as C
 from r03.controllers import make_controller, controller_sha   # INFRA-3 A1: źródło setpointów wypięte z pętli
+from r03.controllers.safe_descend import safe_descend_step    # K2 B2: D5 wypięte z pętli (współdzielone z ławką)
 
 SCEN = os.environ.get("SCEN", "S2")
 OUT = os.environ.get("GATE_OUT", f"/tmp/r03gate/{SCEN}.jsonl")
@@ -273,18 +274,15 @@ async def main():
             "pos": [round(v, 3) for v in pos], "dr": bool(dr), "descending": bool(descending)})
 
         if is_pos:
-            if not descending:
-                descending = True; desc_t0 = time.monotonic(); ev("refuse_pos_land")
-            el = time.monotonic() - desc_t0
-            if el < desc_fast_dur:
-                vdesc = C.V_DESC_FAST
-            else:
-                if not h_switched:
-                    ev("h_switch"); h_switched = True
-                vdesc = C.V_DESC_LAND
+            _sd = {"descending": descending, "desc_t0": desc_t0, "h_switched": h_switched, "td": td}
+            _sd_cfg = {"v_desc_fast": C.V_DESC_FAST, "v_desc_land": C.V_DESC_LAND,
+                       "desc_fast_dur": desc_fast_dur, "desc_total": desc_total}
+            vdesc, _sd_evs, _sd_td, _sd = safe_descend_step(_sd, time.monotonic(), _sd_cfg)
+            descending, desc_t0, h_switched, td = _sd["descending"], _sd["desc_t0"], _sd["h_switched"], _sd["td"]
+            for _e in _sd_evs:
+                ev(_e)
             await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, vdesc, 0))
-            if el >= desc_total and not td:
-                ev("touchdown"); td = True
+            if _sd_td:
                 break                                   # S2/S4 (i S3 bez re-ALLOW przed touchdown)
         else:
             # ALLOW (patrol LUB re-ALLOW po histerezie w S3)
```

## §3. Test bit-w-bit (wzór INFRA-3 A1.3)
- `bench/tests_safe_descend.py`: referencja = literalna transkrypcja bloku is_pos (monotonic→now); ekstrakt = `safe_descend_step`.
- Fikstura = **4221 wierszy tick** z `results/K1/S/**` (11 plików), **1791 z descending=True** (faza D5) — identyczna jak A1.3.
- Asercja: **identyczne (vdesc, events, touchdown, stan) dla wszystkich 1791 ticków descending** — bez tolerancji (SR-4). PASS.
- + test przejść faz (V_DESC_FAST→h_switch→V_DESC_LAND→touchdown) PASS.

## §4. SHA (do re-baseline pinu w ANEKS_K2-2)
| plik | sha256 |
|---|---|
| gate STARY (master, pin **c3ccabe0**) | `c3ccabe04b9cae8e...` |
| gate NOWY (branch) | `5647ae20565426f7...` |
| `safe_descend.py` (5. pin) | `e3c1040b83edc490...` |
| `k2_judge.py` (glue, frozen przed lotami) | `b4ef92ce15c5c554...` |

## §5. Status brancha B3-B6 (przygotowane, niecommitowane do master)
- **B3** `bench_flight.py`: `pos_flag` z `dead_reckoning` (wzór gate:267) zamiast None; ścieżka REFUSE(POS) → `safe_descend_step` (ta sama funkcja co gate) do touchdown → `denial_boot_end` (denial kończy boot). GEOFENCE/inny REFUSE = hover+koniec epizodu (jak dotąd). Nominał bez K2_INJECT_T = IDENTYCZNY jak dotąd (pos_flag=None).
- **B4** hook: `K2_INJECT_T` (s po t_entry; brak = zero denialu); `param set EKF2_GPS_CTRL 0` w T_inj; `denial`+t_inj_sim w trace/meta; test timingu (±DT ⊂ ±0.2 s).
- **B5** `certs_selfcheck` dla FLIGHT=bench (subprocess w bench_flight, bez dotykania run_boot.sh NIETYKALNEGO); rc w meta + `certs_selfcheck.log`.
- **B6** `bench/k2_judge.py` (glue, zero zmian w zamrożonych): ważność do T_inj = bench_judge V2′; metryki po T_inj = k1_judge.gt_metrics (x_exc/t_td/breach); t_refuse pasmo [0.05,0.15]; verdict (+) + drabina 12/12·1·≥2. Testy syntetyczne + unit `pos_flag=True` na sucho — PASS.
- **Pełny pytest: 79 passed** (bez regresji), gate diff 2 huki.

## §6. Do CC (ANEKS_K2-2)
Ratyfikacja ekstrakcji (diff §2, bit-w-bit §3, sha §4) → wykonawca: aktualizuje `k1_shield_pins.py` (gate nowy sha `5647ae20` + `safe_descend.py` `e3c1040b` jako 5. pin), commituje B2→B6 do master, STOP. Olga: push. Potem shakeout diag (osobny sygnał „K2-diag go"). Weto K4b Olgi otwarte do końca sesji build.
