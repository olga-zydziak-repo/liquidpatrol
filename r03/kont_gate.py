"""r03/kont_gate.py — warstwa komend trybu KONT (PROMPT_KONT_S3 §1, ANEKS_KONT-3 §2, ANEKS_KONT-3b §1.2).

Tłumaczy decyzję nakładki (r03/kont_shield.py) na krotkę VelocityNedYaw (vn, ve, vd, yaw_deg), jaką tor
wykonawczy wysyła do PX4. `safe_descend_step` (r03/controllers/safe_descend.py, FROZEN) bez zmian — liczy vdesc;
yaw podaje wyłącznie ta warstwa.

  - REFUSE(POS_DEGRADED) (R-POS albo R-KONT) w KONT_MODE=1 ⇒ D5 + trzymanie yaw: heading z chwili decyzji
    (pierwszy tick REFUSE(POS) epizodu) trzymany do przyziemienia;
  - KONT_MODE=0 ⇒ zejście z yaw = 0 jak dotąd (r03/gate_run_r03.py:284, bench/bench_flight.py:389);
  - R-G-NOM ⇒ v_ned bez dodatniej składowej radialnej (tor wykonawczy wysyła prędkość, bench_flight.py:397);
  - pozostałe decyzje ⇒ komenda kontrolera bez zmian.
"""
from __future__ import annotations

from r01.shield import REFUSE, POS_DEGRADED
from r03.kont_shield import R_G_NOM, strip_outward


def is_pos_refuse(d) -> bool:
    return d["decision"] == REFUSE and d.get("reason") == POS_DEGRADED


class KontCommand:
    def __init__(self, kont_mode: bool):
        self.kont_mode = bool(kont_mode)
        self.yaw_hold_deg = None        # heading z chwili decyzji (stopnie, konwencja VelocityNedYaw)

    def release(self):
        """Wołający po wyjściu z REFUSE(POS) (re-ALLOW) — następny epizod łapie nowy heading."""
        self.yaw_hold_deg = None

    def descend(self, vdesc: float, heading_deg: float):
        """Komenda zejścia D5 dla jednego ticka REFUSE(POS); vdesc z safe_descend_step."""
        if not self.kont_mode:
            return (0.0, 0.0, float(vdesc), 0.0)
        if self.yaw_hold_deg is None:
            self.yaw_hold_deg = float(heading_deg)
        return (0.0, 0.0, float(vdesc), self.yaw_hold_deg)

    def patrol(self, d, v_ned, yaw_deg: float, pos):
        """Komenda dla decyzji innej niż REFUSE(POS): R-G-NOM rzutuje v_ned (tylko KONT_MODE=1)."""
        vn, ve, vd = float(v_ned[0]), float(v_ned[1]), float(v_ned[2])
        if self.kont_mode and d.get("rule") == R_G_NOM:
            vn, ve = strip_outward((vn, ve), pos)
        return (vn, ve, vd, float(yaw_deg))
