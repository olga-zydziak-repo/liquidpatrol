# FREEZE_K2 — przyrząd K2 zamrożony przed lotami (PRE_K2 K4, ANEKS_K2-2 §C2)

Po ratyfikacji ekstrakcji D5 (ANEKS_K2-2). Piny osłony (`k1/k1_shield_pins.py`) rozszerzone:
- `r03/gate_run_r03.py` : `5647ae20565426f7…` (re-baseline po ekstrakcji, pin c3ccabe0 → 5647ae20)
- `r03/controllers/safe_descend.py` : `e3c1040b83edc490…` (5. pin, zejście D5 współdzielone gate↔ławka)

Sędzia glue K2 (frozen SHA przed lotami — PRE_K2 K4, zero zmian w zamrożonych sędziach):
- `bench/k2_judge.py` : `b4ef92ce15c5c554373ffde0de37ed0515e1a2498aa11bdb3da23968e3f651c9`

Uzbrojenie ławki (harness lotu K2, niepinowane — bench_flight jest harnessem):
- `bench/bench_flight.py` — pos_flag z dead_reckoning + ścieżka REFUSE(POS)→safe_descend_step + hook K2_INJECT_T + certs_selfcheck. Nominał bez K2_INJECT_T = identyczny jak dotąd.

Bit-w-bit ekstrakcji: 4221 tick / 1791 descending (results/K1/S/**) = identyczne cmd (bench/tests_safe_descend.py).
Pełny pytest: bez regresji.
