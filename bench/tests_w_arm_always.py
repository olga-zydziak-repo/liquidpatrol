#!/usr/bin/env python3
"""tests_w_arm_always.py — W (noga wiatru) B2: test dwustronny flagi W_ARM_ALWAYS w bench_flight.

Dep-free: NIE importuje bench_flight (ciągnąłby px4_msgs/mavsdk/gz). Zamiast tego:
 1) asercja, że rzeczywista linia `arm = ...` w źródle jest DOKŁADNIE tą oczekiwaną (łapie drift),
 2) tablica prawdy tej samej formuły w obu trybach flagi:
    - default (W_ARM_ALWAYS=False): arm zależy WYŁĄCZNIE od (denial_done, t_entry) — bit-zgodne z linią
      bazową `arm = denial_done or (K2_ARM_MONITOR and t_entry is not None)`,
    - flaga ON (W_ARM_ALWAYS=True): przy K2_ARM_MONITOR=True i t_entry=None → arm=True (pos_flag=dr od OFFBOARD).
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "bench", "bench_flight.py")

EXPECTED_ARM_LINE = "arm = (denial_done or (K2_ARM_MONITOR and (W_ARM_ALWAYS or t_entry is not None)))"
EXPECTED_ENV_DECL = 'W_ARM_ALWAYS = os.environ.get("W_ARM_ALWAYS") == "1"'


def _arm(denial_done, k2_arm_monitor, w_arm_always, t_entry):
    """Formuła 1:1 z bench_flight.py:arm (mirror testowany asercją źródła)."""
    return (denial_done or (k2_arm_monitor and (w_arm_always or t_entry is not None)))


def _baseline_arm(denial_done, k2_arm_monitor, t_entry):
    """Linia bazowa sprzed nogi W (bit-zgodność default)."""
    return (denial_done or (k2_arm_monitor and t_entry is not None))


def test_source_lines_present():
    src = open(SRC).read()
    assert EXPECTED_ENV_DECL in src, "brak deklaracji env W_ARM_ALWAYS"
    assert EXPECTED_ARM_LINE in src, "linia arm= nie zgadza się z oczekiwaną (drift?)"


def test_default_off_bit_identical():
    # default OFF: dla wszystkich kombinacji arm == baseline (niezależnie od t_entry/denial/monitor)
    for denial in (False, True):
        for mon in (False, True):
            for te in (None, 0.0, 12.3):
                assert _arm(denial, mon, False, te) == _baseline_arm(denial, mon, te), \
                    f"OFF nie bit-zgodne: denial={denial} mon={mon} t_entry={te}"


def test_flag_on_arms_from_offboard():
    # flaga ON + monitor ON + BRAK wejścia w pasmo (t_entry=None) + brak denialu → arm=True
    assert _arm(False, True, True, None) is True
    # baseline w tej sytuacji dałby False (monitor martwy bez t_entry) — to jest różnica, o którą chodzi
    assert _baseline_arm(False, True, None) is False


def test_flag_on_respects_legacy_unarmed():
    # K2_ARM_MONITOR=False (K2_LEGACY_UNARMED) → arm zależy tylko od denial_done, flaga bez wpływu
    assert _arm(False, False, True, None) is False
    assert _arm(True, False, True, None) is True


if __name__ == "__main__":
    test_source_lines_present()
    test_default_off_bit_identical()
    test_flag_on_arms_from_offboard()
    test_flag_on_respects_legacy_unarmed()
    print("tests_w_arm_always: 4 passed")
