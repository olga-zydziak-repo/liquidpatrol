"""r01/shield.py — osłona patrolu jako CZYSTY WRAPPER (maszyna stanów per misja).

Port z liquidsight/s3c1/shield.py: STRUKTURA/LOGIKA przeniesiona, LICZBY nowe (config.py, A2).
Osłona jest JEDYNĄ ścieżką do publikacji setpointów (kontrakt §2 PRE_R01). Na każdy tick
konsumuje pozycję/prędkość drona + proponowany setpoint planera + tryb (z admitowanych komend)
i zwraca decyzję ALLOW / HOLD / REFUSE(reason) deterministycznie (reguła + wartość + próg).

Reguły (priorytet = kontrakt):
  R-T  terminal latch → REFUSE (zatrzaśnięty).
  R-G  GEOFENCE (najwyższy, każdy tryb): bariera P2-analog — cel poza R_E LUB
       pozycja + dystans_hamowania(v) > R_E → REFUSE(GEOFENCE) + akcja bezpieczna.
  R-A  ABORT: operator kończy misję → REFUSE(ABORT) (bezpieczne zatrzymanie).
  R-H  HOLD: tryb HOLD → podmiana na hold-setpoint (pozycja bieżąca, v=0).
  R-R  RETURN: tryb RETURN → hold do przejęcia przez RTL (MAVSDK).
  R-O  OBSERVE (R0.2, 7. liść): tryb OBSERVE → ALLOW, przepuść setpoint obserwacji (pierścień
       D_safe, bearing-only z kanału). PONIŻEJ R-G: setpoint OBSERVE za płot jest przecięty przez
       R-G tak jak waypoint patrolu (geofence nadrzędny z PRIORYTETU, nie nowej reguły — PRE §2.4).
       OBSERVE nie zmienia v_max/clampów/obwiedni (R02-A3).
  R-P  PATROL: ALLOW → przepuść setpoint planera.
HOLD/REFUSE NIE urywają strumienia (A1/§4): applied = hold-setpoint, strumień żyje < COM_OF_LOSS_T.

outcome() — księgowość trójwynikowa SUKCES/ODMOWA/PORAZKA z asercją rozłączności (port D4).
"""
from __future__ import annotations
import math
from r01.config import ShieldConfig

ALLOW, HOLD, REFUSE = "ALLOW", "HOLD", "REFUSE"
# stany
PATROL, HOLDING, RETURNING, DONE = "PATROL", "HOLDING", "RETURNING", "DONE"
# powody
GEOFENCE, COMMAND_INVALID, STALE_CMD, ABORT = \
    "GEOFENCE", "COMMAND_INVALID", "STALE_CMD", "ABORT"
POS_DEGRADED = "POS_DEGRADED"      # R0.3a: 5. reason (D3) — zdegradowane zdrowie pozycji (GPS-denied)
# tryby (z admitowanych komend)
M_PATROL, M_HOLD, M_RETURN, M_ABORT = "PATROL", "HOLD", "RETURN", "ABORT"
M_OBSERVE = "OBSERVE"           # R0.2: tryb OBSERVE (auto-wyzwalany kanałem, autoryzowany gramatyką P4)
# stan OBSERVE (klasa ALLOW, jak PATROL)
OBSERVING = "OBSERVING"


def _radial(x, y) -> float:
    return math.hypot(float(x), float(y))


class PatrolShield:
    def __init__(self, cfg: ShieldConfig | None = None):
        self.cfg = cfg or ShieldConfig()

    def reset(self):
        self.state = PATROL
        self.terminal = None            # (reason, rule) po REFUSE
        self.n_hold_enter = 0
        self.n_hold_release = 0
        self._was_hold = False
        self.trace = []                 # log decyzji per tick
        # R0.3a — monitor zdrowia pozycji (D12): event-based, debounce + histereza.
        # POS_DEGRADED to REFUSE ODWRACALNY (nie terminal latch) — re-ALLOW po M s zdrowia (D6).
        self._pos_bad = 0               # kolejne ticki zwalidowanej flagi (debounce)
        self._pos_healthy = 0           # kolejne ticki zdrowia w stanie POS_DEGRADED (histereza)
        self._pos_refuse = False        # czy aktywny REFUSE(POS_DEGRADED)
        self.n_pos_enter = 0            # księgowość wejść w POS_DEGRADED
        self.pos_debounce_ticks = getattr(self, "pos_debounce_ticks", 2)   # D12: 2 ticki
        self.pos_hyst_ticks = getattr(self, "pos_hyst_ticks",
                                      int(round(5.0 / self.cfg.dt)))        # D6: M=5 s

    def _pos_monitor(self, pos_flag):
        """Aktualizuje stan POS_DEGRADED z debounce (wejście) i histerezą (wyjście).
        pos_flag = zwalidowana flaga utraty aidingu (dead_reckoning, def. R1). None ⇒ monitor nieaktywny
        (kompatybilność wstecz: r01/r02 bez GPS-denied → zachowanie bez zmian)."""
        if pos_flag is None:
            return
        if pos_flag:
            self._pos_bad += 1
            self._pos_healthy = 0
            if self._pos_bad >= self.pos_debounce_ticks and not self._pos_refuse:
                self._pos_refuse = True
                self.n_pos_enter += 1
        else:
            self._pos_bad = 0
            if self._pos_refuse:
                self._pos_healthy += 1
                if self._pos_healthy >= self.pos_hyst_ticks:   # M s ciągłego zdrowia → re-ALLOW
                    self._pos_refuse = False
                    self._pos_healthy = 0

    # -- dystans hamowania (bariera P2-analog) ------------------------------
    def _braking_dist(self, vel) -> float:
        vh = min(math.hypot(float(vel[0]), float(vel[1])), self.cfg.v_max)
        return (vh * vh) / (2.0 * self.cfg.a_brake)

    def _geofence_violation(self, pos, vel, target):
        """Zwraca (bool, detail). Bariera: cel poza R_E LUB pozycja+hamowanie>R_E (poziom),
        oraz pion |z|>V_E."""
        tr = _radial(target[0], target[1])
        if tr > self.cfg.r_e:
            return True, f"cel poza R_E ({tr:.1f}>{self.cfg.r_e:.0f})"
        pr = _radial(pos[0], pos[1])
        if pr + self._braking_dist(vel) > self.cfg.r_e:
            return True, f"pozycja+hamowanie poza R_E ({pr:.1f}+brake>{self.cfg.r_e:.0f})"
        if abs(float(target[2])) > self.cfg.v_e or abs(float(pos[2])) > self.cfg.v_e:
            return True, f"pion poza V_E (>{self.cfg.v_e:.0f})"
        return False, None

    # -- latch REFUSE z warstwy admisji (COMMAND_INVALID / STALE_CMD) --------
    def latch_refuse(self, reason, rule):
        if self.terminal is None:
            self.terminal = (reason, rule)
            self.state = DONE

    # -- pojedynczy tick ----------------------------------------------------
    def step(self, k, pos, vel, target, mode=M_PATROL, pos_flag=None):
        self._pos_monitor(pos_flag)
        d = self._decide(k, pos, vel, target, mode)
        d["t"] = round(k * self.cfg.dt, 4)
        d["values"] = {
            "pos": [round(float(pos[0]), 3), round(float(pos[1]), 3), round(float(pos[2]), 3)],
            "target": [round(float(target[0]), 3), round(float(target[1]), 3), round(float(target[2]), 3)],
            "r_pos": round(_radial(pos[0], pos[1]), 3),
            "r_target": round(_radial(target[0], target[1]), 3),
            "mode": mode,
        }
        # księgowość HOLD (wejścia/wyjścia)
        is_hold = d["decision"] == HOLD
        if is_hold and not self._was_hold:
            self.n_hold_enter += 1
        if (not is_hold) and self._was_hold:
            self.n_hold_release += 1
        self._was_hold = is_hold
        self.trace.append(d)
        return d

    def _hold_setpoint(self, pos):
        return [float(pos[0]), float(pos[1]), float(pos[2])]

    def _decide(self, k, pos, vel, target, mode):
        # R-T terminal
        if self.terminal is not None:
            r, rule = self.terminal
            return {"k": k, "state": DONE, "decision": REFUSE, "reason": r, "rule": rule,
                    "applied": self._hold_setpoint(pos)}

        # R-POS (R0.3a, D3/D12): zdegradowane zdrowie pozycji → REFUSE(POS_DEGRADED).
        # PONIŻEJ latch, NA/PONAD R-G (prekondycja geofence: bariera p+v²/2a≤R_E na NIEPEWNYM p
        # niewiarygodna — nie wolno ufać barierze na dryfującym p). ODWRACALNY (nie terminal): re-ALLOW
        # po histerezie M. Akcja bezpieczna = velocity-descent dwufazowy (D5 zrew.; AUTO.LAND wykluczony).
        if self._pos_refuse:
            return {"k": k, "state": self.state, "decision": REFUSE, "reason": POS_DEGRADED,
                    "rule": "R-POS", "action": "VELOCITY_DESCENT", "applied": self._hold_setpoint(pos)}

        # R-G geofence (najwyższy priorytet, każdy tryb)
        viol, detail = self._geofence_violation(pos, vel, target)
        if viol:
            self.terminal = (GEOFENCE, "R-G"); self.state = DONE
            return {"k": k, "state": DONE, "decision": REFUSE, "reason": GEOFENCE,
                    "rule": "R-G", "detail": detail, "applied": self._hold_setpoint(pos)}

        # R-A abort (operator)
        if mode == M_ABORT:
            self.terminal = (ABORT, "R-A"); self.state = DONE
            return {"k": k, "state": DONE, "decision": REFUSE, "reason": ABORT,
                    "rule": "R-A", "detail": "operator abort", "applied": self._hold_setpoint(pos)}

        # R-H hold
        if mode == M_HOLD:
            self.state = HOLDING
            return {"k": k, "state": HOLDING, "decision": HOLD, "reason": None,
                    "rule": "R-H", "applied": self._hold_setpoint(pos)}

        # R-R return (egzekutor przełącza RTL przez MAVSDK; osłona utrzymuje hold do przejęcia)
        if mode == M_RETURN:
            self.state = RETURNING
            return {"k": k, "state": RETURNING, "decision": HOLD, "reason": None,
                    "rule": "R-R", "detail": "return→RTL(MAVSDK)", "applied": self._hold_setpoint(pos)}

        # R-O observe (R0.2, 7. liść) → ALLOW; setpoint obserwacji przepuszczony (target = pierścień
        # D_safe z kanału, wyliczony w egzekutorze). PONIŻEJ R-G: gdy setpoint OBSERVE za płotem,
        # R-G (wyżej) już zwrócił REFUSE(GEOFENCE) — tu docieramy tylko gdy geofence-bezpiecznie.
        if mode == M_OBSERVE:
            self.state = OBSERVING
            return {"k": k, "state": OBSERVING, "decision": ALLOW, "reason": None, "rule": "R-O",
                    "applied": [float(target[0]), float(target[1]), float(target[2])]}

        # R-P patrol → ALLOW
        self.state = PATROL
        return {"k": k, "state": PATROL, "decision": ALLOW, "reason": None, "rule": "R-P",
                "applied": [float(target[0]), float(target[1]), float(target[2])]}

    # -- podsumowanie misji (D4 — port 1:1) ---------------------------------
    def outcome(self, env_success, wrong_action=False):
        refused = self.terminal is not None
        if refused:
            res = "ODMOWA"
        elif wrong_action:
            res = "PORAZKA"           # wrong-action = porażka I klasy (setpoint za płot przepuszczony)
        elif env_success:
            res = "SUKCES"
        else:
            res = "PORAZKA"           # nieosiągnięcie/dryf/pad bez odmowy
        assert res in ("SUKCES", "ODMOWA", "PORAZKA")
        assert (res == "ODMOWA") == refused, \
            "odmowa <=> osłona zatrzymała misję (bez podwójnego liczenia)"
        return {"wynik": res,
                "refuse_reason": (self.terminal[0] if refused else None),
                "refuse_rule": (self.terminal[1] if refused else None),
                "n_hold_enter": self.n_hold_enter, "n_hold_release": self.n_hold_release}
