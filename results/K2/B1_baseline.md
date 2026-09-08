# B1 — baseline stanu zastanego (PROMPT_K2_BUILD B1)

## Pin gate
`r03/controllers/gate_run_r03.py` sha256 `c3ccabe04b9cae8e…` (pin **c3ccabe0**, `k1/k1_shield_pins.py`).

## Blok D5 (is_pos) do ekstrakcji — zakres @ c3ccabe0
`r03/gate_run_r03.py:275-289` (blok `if is_pos:`):
- `:276-277` — pierwsze wejście: `descending=True; desc_t0=time.monotonic(); ev("refuse_pos_land")`
- `:278` — `el = time.monotonic() - desc_t0`
- `:279-284` — dwufaza: `el<desc_fast_dur → V_DESC_FAST` ; else `ev("h_switch")` (raz) + `V_DESC_LAND`
- `:285` — `set_velocity_ned(0,0,vdesc)`
- `:286-288` — touchdown: `el>=desc_total → ev("touchdown"); td=True; break`
Parametry: `desc_fast_dur=(ALT-C.H_SWITCH_AGL)/C.V_DESC_FAST` (`:222`), `desc_total=desc_fast_dur+C.H_SWITCH_AGL/C.V_DESC_LAND+1.5` (`:223`). Config: `C.V_DESC_FAST`, `C.V_DESC_LAND`, `C.H_SWITCH_AGL`.
Zależność krytyczna: blok czyta `time.monotonic()` DWUKROTNIE (desc_t0 + el) — ekstrakcja przenosi zegar do argumentu `now` (sygnatura `safe_descend_step(state, pos, now, cfg)`), gate podaje `now=time.monotonic()`. `vdesc` jest funkcją SCHODKOWĄ el (V_DESC_FAST/V_DESC_LAND) ⇒ wyjście `v_ned` bit-w-bit mimo mikroróżnicy el (0 na 1. ticku vs ~µs w oryginale).

## Fikstura bit-w-bit (wzór INFRA-3 A1.3)
Strumień z `results/K1/S/**/trace.jsonl` — wiersze `tick` (schemat v2, pola `pos`, `descending`):
**4221 wierszy tick** w 11 plikach S (identycznie jak A1.3), z czego **1791 z `descending=True`** (faza zejścia D5).
Test B2: referencja = LITERALNA kopia bloku is_pos z `git show c3ccabe0:r03/gate_run_r03.py:275-289` (parametryzowana `now`); ekstrakt = `safe_descend_step`; napęd = sekwencje `descending` z 4221 ticków + syntetyczny zegar `now=idx·DT`. Asercja: identyczne `(v_ned, descending, h_switched, td)` dla wszystkich — bez tolerancji (SR-4).
