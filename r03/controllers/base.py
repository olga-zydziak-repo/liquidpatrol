#!/usr/bin/env python3
"""r03/controllers/base.py — interfejs źródła setpointów (INFRA-3 A1).

Rozcięcie kontroler/osłona: pętla `gate_run_r03` pyta `SetpointSource.step(...)` o cel/prędkość,
osłona (`r01.shield.PatrolShield`) decyduje niezależnie co tick. Ławka egzekutora i sieć wpinają
nowy kontroler tu, bez dotykania osłony ani pętli (SR-9: gniazdo, nie wtyczka).

Kontrakt (nazwy pól OBOWIĄZUJĄCE — pętla i triggery K1/S4 czytają dokładnie te klucze):

    step(tick, pos_ned, vel_ned, now_s, descending) -> dict {
        "tgt_ned": (x, y, z),      # setpoint pozycji NED [m] (z = -ALT)
        "v_ned":   (vn, ve, vd),   # setpoint prędkości NED [m/s] (gałąź ALLOW wysyła vn, ve)
        "yaw":     float,          # [rad]
        "seg_i":   int,            # indeks segmentu trasy PO ewentualnym inkremencie (trigger K1/S4)
        "dist":    float,          # odległość pozioma do bieżącego celu [m] (trigger S4)
        "wps":     list | None,    # lista waypointów NED lub None (trigger K1)
        "extra":   dict,           # dane diagnostyczne kontrolera (poza kontraktem osłony)
    }

`step` NIE dotyka osłony, denialu, zejścia ani trace — zwraca wyłącznie propozycję setpointu.
"""


class SetpointSource:
    """Interfejs bazowy. name = etykieta kanału ("route" | "orbit" | "net" | ...)."""

    name = "base"

    def reset(self) -> None:
        """Zeruje stan wewnętrzny (indeks segmentu itp.) przed lotem."""
        raise NotImplementedError

    def step(self, tick, pos_ned, vel_ned, now_s, descending) -> dict:
        """Zwraca dict wg kontraktu w docstringu modułu."""
        raise NotImplementedError
