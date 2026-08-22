"""common/frames.py — nazwane konwencje ramek (spłata długu Z2 z RAPORT_U2R-2).

W kodzie DEMO-B żyją TRZY konwencje (historyczne, zamrożone w danych trace); wcześniej mieszane
„gołymi" swapami indeksów w konsumentach (bug E/N przeżył U1R/U2R). Ten moduł je NAZYWA — konsumenci
konwertują TYLKO przez te helpery, nigdy lokalnym swapem.

  NED  (dron: mav.pos, trace 'pos')      = [North, East, Down]
  ENU  (świat gz, kamera film/dron)      = [East,  North, Up]
  DRV  (intruz: trace 'intr_ned')        = [East,  North, -Up]   (intruder_driver.set_pose: gz_x=intr_ned[0]=East)

Przykłady liczbowe (dwell):
  dron  N=1.5 E=-0.1 alt=10  → ned=[1.5,-0.1,-10]   → ned2enu = [-0.1, 1.5, 10]
  intruz E=7.86 N=0 alt=11.5 → drv=[7.86,0,-11.5]   → drv2enu = [7.86, 0, 11.5]
  (drv2enu NIE zamienia E/N — to naprawa markera z U2R-2; drv2ned zamienia bo NED ma North pierwszy.)
"""
from __future__ import annotations


def ned2enu(v):
    "Dron NED [N,E,D] -> ENU [E,N,U]."
    return [v[1], v[0], -v[2]]


def enu2ned(v):
    "ENU [E,N,U] -> NED [N,E,D]."
    return [v[1], v[0], -v[2]]


def drv2enu(v):
    "Intruz DRV [E,N,-U] -> ENU [E,N,U] (BEZ zamiany E/N — naprawa markera U2R-2)."
    return [v[0], v[1], -v[2]]


def enu2drv(v):
    "ENU [E,N,U] -> DRV [E,N,-U]."
    return [v[0], v[1], -v[2]]


def drv2gz(v):
    "Intruz DRV [E,N,-U] -> pozycja gz set_pose [x=E, y=N, z=U] (intruder_driver)."
    return [v[0], v[1], -v[2]]


def drv2ned(v):
    "Intruz DRV [E,N,-U] -> NED-standard [N,E,D] (zamiana E/N; do wspólnej ramki z dronem)."
    return [v[1], v[0], v[2]]


def ned2drv(v):
    "NED [N,E,D] -> DRV [E,N,-U]."
    return [v[1], v[0], v[2]]
