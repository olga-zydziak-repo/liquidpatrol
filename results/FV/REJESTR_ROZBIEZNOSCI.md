# REJESTR ROZBIEŻNOŚCI — różnicówka lustro↔produkcja (noga FV)

Wpisy per rozbieżność wykryta różnicówką `r01/proofs/tests_fv_diff.py` (PRE_FV §4). Zasada: każda
rozbieżność ⇒ poprawka WYŁĄCZNIE lustra (`fv_mirror.py`) + wpis (co, gdzie, która semantyka źle
odwzorowana). Kod produkcyjny (`r01/shield.py`, `r03/**`) nietykany. Rozbieżność potwierdzona NA
PRODUKCJI przy wejściu osiągalnym ⇒ TRIPWIRE (PRE_FV §5), nie wpis tutaj.

## Sesja S1 (11.09.2026, commit C1 729a44c → sweep)

Bieg różnicówki `python3 -m r01.proofs.tests_fv_diff sweep` na siatce zamrożonej w C1:
- siatka deterministyczna: 24 (braking_dist) + 15 (geofence) + 10 (pos_monitor) + 5 (safe_descend) = 54 wpisy
- fuzz ziarna {0,1,2,3,4}: 100000 przypadków / funkcję (braking/geofence/pos_monitor/safe_descend)
- fikstura D5: 11 plików, 4221 ticków (1791 descending) z results/K1/S/**

**ROZBIEŻNOŚCI: 0.** Lustro `fv_mirror.py` odtworzyło wszystkie cztery elementy 1:1 za pierwszym biegiem;
ŻADNA poprawka lustra nie była potrzebna. `fv_mirror.py` niezmieniony po commicie C1.

Stat surowy: `results/FV/diff_stats.json`.

(Brak wpisów — brak rozbieżności. P-FV-2 rozliczane dopiero przy RAPORT_FV, nie tutaj.)
