#!/usr/bin/env python3
"""r03/controllers/safe_descend.py — zejście bezpieczne D5 (PROMPT_K2_BUILD B2, PRE_K2 K1b).

Ekstrakcja bloku `is_pos` z pinowanego `gate_run_r03.py:275-289` (pin c3ccabe0) do WSPÓŁDZIELONEJ,
CZYSTEJ funkcji — chirurgia wzorem INFRA-3 A1 (rozcięcie + re-baseline pinu + test bit-w-bit).
K2 uzbraja pętlę ławki tą SAMĄ funkcją co gate (jeden tor zejścia dla wszystkich nóg).

RÓŻNICA JEDYNA vs blok inline: zegar `time.monotonic()` (czytany 2× w bloku) przeniesiony do argumentu
`now` — funkcja czysta, testowalna, deterministyczna. `vdesc` jest funkcją SCHODKOWĄ `el` (V_DESC_FAST/
V_DESC_LAND), więc wyjście `v_ned` pozostaje bit-w-bit identyczne, gdy wołający podaje `now=time.monotonic()`.
Zejście dwufazowe: V_DESC_FAST do H_SWITCH_AGL, potem V_DESC_LAND do touchdown; v_xy=0; AUTO.LAND wykluczony.
"""


def new_state():
    """Stan zejścia (per epizod). Wołający trzyma i przekazuje między tickami."""
    return {"descending": False, "desc_t0": None, "h_switched": False, "td": False}


def safe_descend_step(st, now, cfg):
    """Jeden tick zejścia D5. Odtwarza blok is_pos gate:275-289 DOKŁADNIE (monotonic→now).

    st  = dict z `new_state()` (descending/desc_t0/h_switched/td) — mutowany i zwracany.
    now = czas [s] (wołający: `time.monotonic()`).
    cfg = {v_desc_fast, v_desc_land, desc_fast_dur, desc_total}.
    Zwraca (vdesc, events, touchdown, st):
      vdesc     = prędkość pionowa NED [m/s] (Down>0); v_ned = (0, 0, vdesc).
      events    = lista nazw zdarzeń do wyemitowania (['refuse_pos_land'|'h_switch'|'touchdown']).
      touchdown = True gdy osiągnięto touchdown w tym ticku (wołający: break).
    """
    events = []
    if not st["descending"]:
        st["descending"] = True
        st["desc_t0"] = now
        events.append("refuse_pos_land")
    el = now - st["desc_t0"]
    if el < cfg["desc_fast_dur"]:
        vdesc = cfg["v_desc_fast"]
    else:
        if not st["h_switched"]:
            events.append("h_switch")
            st["h_switched"] = True
        vdesc = cfg["v_desc_land"]
    touchdown = False
    if el >= cfg["desc_total"] and not st["td"]:
        events.append("touchdown")
        st["td"] = True
        touchdown = True
    return vdesc, events, touchdown, st
