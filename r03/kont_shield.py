"""r03/kont_shield.py — nakładka KONT nad osłoną r01/shield.py (PROMPT_KONT_S3 §1, ANEKS_KONT-3 §2, ANEKS_KONT-3b §1).

Nakładka = PODKLASA PatrolShield (import, nie kopia; r01/shield.py FROZEN, nietknięty). Aktywna wyłącznie przy
KONT_MODE=1 (env albo argument `kont_mode`; echo do manifestu: `kont_echo()`). Przy KONT_MODE=0 `step` i `_decide`
wołają WYŁĄCZNIE metody bazowe — zachowanie bajtowo identyczne ze starą osłoną (test T0).

Reżim KONT (kont_mode=True) dodaje do gramatyki:
  - monitor utraty GNSS: wejście `cs_gnss_pos` (estimator_status_flags, dds_topics.yaml:23), flaga utraty =
    ¬cs_gnss_pos; debounce i histereza = TE SAME stałe co `_pos_monitor` (self.pos_debounce_ticks /
    self.pos_hyst_ticks, r01/shield.py:72-74 — czytane z instancji, nie przepisane liczbą);
  - zegar t_KONT liczony od PIERWSZEGO ticka biegu flagi, który dał wejście (cofnięcie o debounce,
    ANEKS_KONT-3b §1.3); koszyk ε_b = ⌊t_KONT⌋;
  - R-KONT: w KONT ALLOW ⇔ t_KONT < T* ∧ r_est ≤ R_E − d_stop − ε_b(⌊t_KONT⌋) − Δ_D5; pierwsze niespełnienie ⇒
    REFUSE(POS_DEGRADED) zatrzaśnięty do powrotu NOMINAL (odwracalny jak POS_DEGRADED: flaga zdrowa ≥ M);
    akcja = D5 + trzymanie yaw (warstwa komend: r03/kont_gate.py);
  - R-G-NOM: r_est > R_nom ∧ cel na zewnątrz ⇒ REFUSE(GEOFENCE, rule R-G-NOM) BEZ zatrzasku, stan bez zmian,
    applied = cel bez składowej radialnej na zewnątrz (ANEKS_KONT-3b §1.2);
  - stary monitor POS (pos_flag = dead_reckoning) zostaje uzbrojony (ANEKS_KONT-3b §1.4).
Priorytet: latch > R-POS > R-KONT > R-G > R-G-NOM > abort > hold > return > {OBSERVE|R-AUTH} > patrol
(latch > R-POS > R-G frozen, shield.py:153-166; R-KONT to istniejące REFUSE(POS) PRE_KONT §2.6, więc w klasie
R-POS, ponad R-G z tego samego powodu co shield.py:154; R-G-NOM poniżej R-G, ponad abort — ANEKS_KONT-3b §1.2).

TCB minimalny: nakładka dostaje gotowe cs_gnss_pos, r_est i zegar pętli `now`; zero percepcji.
"""
from __future__ import annotations
import hashlib
import math
import os

from r01.config import DELTA_MARGIN
from r01.shield import PatrolShield, REFUSE, POS_DEGRADED, GEOFENCE, POSDEG, M_PATROL

# --- zamrożenie (ANEKS_KONT-3 §2 + ANEKS_KONT-3b §1.7); nośnik: s2_freeze_bf.json, wartości wkompilowane ---
FREEZE_PATH = "results/KONT/s2/s2_freeze_bf.json"
FREEZE_SHA256 = "ae19f66c6807de6c824bf0fd723965258b15b77963eb866afb78d3dd3740ae4a"
EPS_B = (0.323, 0.462, 0.789, 1.392, 1.866, 2.362, 2.598, 2.833, 2.969, 3.105, 3.478,
         3.478, 3.478, 3.478, 3.478, 3.478, 3.478, 3.478, 3.478, 3.478, 3.478, 3.738)   # eps_b_obwiednia[0:22]
DELTA_D5 = 1.524                 # 1.5 × 1.016 (zejścia Y)
T_STAR_S = 22                    # KONT trwa, dopóki t_KONT < T*
R_NOM = 27.30                    # ANEKS_KONT-3b §1.7 (27.51 → 27.30, bariera koszyka 0 = 27.303)
D_STOP = DELTA_MARGIN            # 2.85 (r01/config.py:27)

KONT_MODE_ENV = "KONT_MODE"
K_NOMINAL, K_KONT, K_REFUSE = "NOMINAL", "KONT", "KONT_REFUSE"
R_KONT, R_G_NOM = "R-KONT", "R-G-NOM"
CAUSE_TSTAR, CAUSE_BARRIER = "T*", "bariera"


def kont_mode_from_env() -> bool:
    return os.environ.get(KONT_MODE_ENV, "0") == "1"


def r_kont(k: int, r_e: float) -> float:
    """Bariera w KONT dla koszyka k (0 ≤ k < T*): R_E − d_stop − ε_b(k) − Δ_D5."""
    return r_e - D_STOP - EPS_B[k] - DELTA_D5


def outward(pos, target) -> float:
    """Składowa radialna (cel − pozycja) wzdłuż r̂ = pos_xy/|pos_xy| [m]; > 0 ⇔ ruch na zewnątrz."""
    px, py = float(pos[0]), float(pos[1])
    r = math.hypot(px, py)
    if r == 0.0:
        return 0.0
    return ((float(target[0]) - px) * px + (float(target[1]) - py) * py) / r


def strip_outward(vec_xy, pos):
    """Wektor poziomy bez dodatniej składowej wzdłuż r̂ (składowa do środka i styczna bez zmian)."""
    px, py = float(pos[0]), float(pos[1])
    r = math.hypot(px, py)
    vx, vy = float(vec_xy[0]), float(vec_xy[1])
    if r == 0.0:
        return vx, vy
    ux, uy = px / r, py / r
    vr = vx * ux + vy * uy
    if vr <= 0.0:
        return vx, vy
    return vx - vr * ux, vy - vr * uy


def freeze_check(root="."):
    """T3: sha nośnika i zgodność tablicy wkompilowanej z JSON. Zwraca dict z wynikami (nie rzuca)."""
    import json
    p = os.path.join(root, FREEZE_PATH)
    raw = open(p, "rb").read()
    F = json.loads(raw)
    return {
        "sha_ok": hashlib.sha256(raw).hexdigest() == FREEZE_SHA256,
        "eps_ok": tuple(F["eps_b_obwiednia"][:T_STAR_S]) == EPS_B,
        "delta_ok": F["delta_D5"] == DELTA_D5,
        "tstar_ok": F["T_star_s"] == T_STAR_S and F["k_ostatni_koszyk"] == T_STAR_S - 1,
        "r_nom_json": F["R_nom"],
        "r_nom_code": R_NOM,
    }


def kont_echo(shield) -> dict:
    """Echo do manifestu (PROMPT_KONT_S3 §1)."""
    return {"KONT_MODE": int(bool(shield.kont_mode)), "T_star_s": T_STAR_S, "R_nom": R_NOM,
            "delta_D5": DELTA_D5, "d_stop": D_STOP, "freeze_sha256": FREEZE_SHA256,
            "debounce_ticks": shield.pos_debounce_ticks, "hyst_ticks": shield.pos_hyst_ticks}


class KontShield(PatrolShield):
    def __init__(self, cfg=None, kont_mode=None):
        super().__init__(cfg)
        self.kont_mode = kont_mode_from_env() if kont_mode is None else bool(kont_mode)

    def reset(self):
        super().reset()
        self._g_bad = 0                 # kolejne ticki flagi utraty GNSS (debounce)
        self._g_healthy = 0             # kolejne ticki zdrowia w KONT (histereza)
        self._g_run_t0 = None           # `now` pierwszego ticka bieżącego biegu flagi
        self._kont = False              # monitor GNSS w stanie utraty (KONT lub KONT_REFUSE)
        self._kont_t0 = None            # zero zegara t_KONT (= _g_run_t0 biegu, który dał wejście)
        self._kont_refuse = False       # REFUSE(POS) z KONT zatrzaśnięty do powrotu NOMINAL
        self.kont_cause = None
        self.n_kont_enter = 0
        self._r_est = 0.0
        self._t_kont = None

    # -- monitor GNSS: kształt 1:1 z _pos_monitor (shield.py:76-94) + zegar od pierwszego ticka biegu --------
    def _gnss_monitor(self, gnss_lost, now):
        if gnss_lost is None:
            return
        if gnss_lost:
            if self._g_bad == 0:
                self._g_run_t0 = now
            self._g_bad += 1
            self._g_healthy = 0
            if self._g_bad >= self.pos_debounce_ticks and not self._kont:
                self._kont = True
                self._kont_t0 = self._g_run_t0
                self.n_kont_enter += 1
        else:
            self._g_bad = 0
            if self._kont:
                self._g_healthy += 1
                if self._g_healthy >= self.pos_hyst_ticks:     # M s ciągłego zdrowia → NOMINAL
                    self._kont = False
                    self._kont_refuse = False
                    self._g_healthy = 0
                    self._kont_t0 = None
                    self.kont_cause = None

    def _kont_barrier(self, now, r_est):
        self._t_kont = None
        if not self._kont:
            return
        t = now - self._kont_t0
        self._t_kont = t
        if self._kont_refuse:
            return
        if t >= T_STAR_S:
            self._kont_refuse, self.kont_cause = True, CAUSE_TSTAR
        elif r_est > r_kont(int(math.floor(t)), self.cfg.r_e):
            self._kont_refuse, self.kont_cause = True, CAUSE_BARRIER

    def kont_phase(self):
        if self._kont_refuse:
            return K_REFUSE
        return K_KONT if self._kont else K_NOMINAL

    def step(self, k, pos, vel, target, mode=M_PATROL, pos_flag=None, auth_ok=True,
             cs_gnss_pos=None, now=None, r_est=None, dr=None):
        if not self.kont_mode:
            return super().step(k, pos, vel, target, mode=mode, pos_flag=pos_flag, auth_ok=auth_ok)
        now = k * self.cfg.dt if now is None else float(now)
        self._r_est = math.hypot(float(pos[0]), float(pos[1])) if r_est is None else float(r_est)
        self._gnss_monitor(None if cs_gnss_pos is None else (not cs_gnss_pos), now)
        self._kont_barrier(now, self._r_est)
        d = super().step(k, pos, vel, target, mode=mode, pos_flag=pos_flag, auth_ok=auth_ok)
        kb = int(math.floor(self._t_kont)) if self._t_kont is not None else None
        d["kont"] = {"phase": self.kont_phase(), "now": round(now, 4),
                     "t_kont": (round(self._t_kont, 4) if self._t_kont is not None else None),
                     "k": kb,
                     "R_k": (round(r_kont(kb, self.cfg.r_e), 3) if kb is not None and kb < T_STAR_S else None),
                     "r_est": round(self._r_est, 3), "cause": self.kont_cause, "n_enter": self.n_kont_enter,
                     "cs_gnss_pos": cs_gnss_pos, "dr": dr}
        return d

    def _decide(self, k, pos, vel, target, mode, auth_ok=True):
        if not self.kont_mode:
            return super()._decide(k, pos, vel, target, mode, auth_ok)
        # latch i R-POS (frozen)
        if self.terminal is not None or self._pos_refuse:
            return super()._decide(k, pos, vel, target, mode, auth_ok)
        # R-KONT: istniejące REFUSE(POS), akcja D5 + trzymanie yaw
        if self._kont_refuse:
            self.state = POSDEG
            return {"k": k, "state": POSDEG, "decision": REFUSE, "reason": POS_DEGRADED, "rule": R_KONT,
                    "detail": self.kont_cause, "action": "VELOCITY_DESCENT_YAW_HOLD",
                    "applied": self._hold_setpoint(pos)}
        # R-G (frozen, zatrzask)
        if self._geofence_violation(pos, vel, target)[0]:
            return super()._decide(k, pos, vel, target, mode, auth_ok)
        # R-G-NOM: prewencyjny, bez zatrzasku, stan bez zmian
        if self._r_est > R_NOM and outward(pos, target) > 0.0:
            ax, ay = strip_outward((float(target[0]) - float(pos[0]), float(target[1]) - float(pos[1])), pos)
            return {"k": k, "state": self.state, "decision": REFUSE, "reason": GEOFENCE, "rule": R_G_NOM,
                    "detail": f"r_est>R_nom ({self._r_est:.2f}>{R_NOM:.2f}), składowa na zewnątrz odjęta",
                    "applied": [float(pos[0]) + ax, float(pos[1]) + ay, float(target[2])]}
        return super()._decide(k, pos, vel, target, mode, auth_ok)
