"""r03/nadir_shield.py — nakładka NADIR nad nakładką KONT (PROMPT_NADIR_S3 §1, PRE_NADIR §2.4–§2.5, ANEKS_NADIR-2 §2).

Nakładka = PODKLASA r03/kont_shield.KontShield (import, nie kopia; kont_shield.py i r01/shield.py nietknięte). Aktywna
wyłącznie przy NADIR_MODE=1 (env albo argument `nadir_mode`; echo: `nadir_echo()`). Przy NADIR_MODE=0 `step` i
`_kont_barrier` wołają WYŁĄCZNIE metody KontShield — zachowanie bajtowo identyczne z nakładką KONT (przy KONT_MODE=0
dalej z kanonem PatrolShield, T0 KONT).

Reżim NADIR (nadir_mode=True ⇒ maszyneria KONT włączona: monitor utraty GNSS, zatrzask REFUSE(POS), R-G-NOM bez zmian)
zastępuje barierę R-KONT/T* barierą piły (PRE_NADIR §2.4):
  - zegar τ = now − t_fix, t_fix = czas ostatniej obserwacji przyjętej literą (ID z manifestu v2 ∧ bok ≥ 18 px ∧
    reszta < s/2 ∧ r_h < 8 m — ANEKS_NADIR-2 §2; liczy producent harness/nadir_fix.Rama, nakładka dostaje gotowe
    t_fix i koszyk j). Brak poprawki ⇒ τ od wejścia w utratę (kont_t0, jak t_KONT), koszyk najgorszy (J_WORST);
  - bariera: w utracie ALLOW ⇔ τ < τ*(j) − 2·dt ∧ r_est ≤ R(⌊τ⌋, j) = R_E − d_stop − u(τ, j),
    u(τ, j) = ε_fix_freeze(j) + ε_b(⌊τ⌋) + Δ_D5; pierwsze niespełnienie ⇒ REFUSE(POS_DEGRADED) zatrzaśnięty do powrotu
    NOMINAL (reguła R-KONT, przyczyna „τ*” albo „bariera”) — porządek reguł i akcja (D5 + trzymanie yaw) jak KONT;
  - τ obcięte z dołu do 0 (stempel klatki t_fix może wyprzedzić zegar pętli `now`);
  - τ*(j) z reguły PRE §3 (jak T* KONT): największe τ* takie, że ε_fix_freeze(j) + ε_b(k) + Δ_D5 ≤ m_p50 dla k < τ*
    (asercja w proverze r01/proofs/p9_nadir_verify.py): 22, 22, 22, 21 s.
Priorytet bez zmian: latch > R-POS > R-KONT(piła) > R-G > abort > hold > return > R-G-NOM > {OBSERVE|R-AUTH} > patrol.
TCB minimalny: nakładka dostaje cs_gnss_pos, r_est, zegar pętli `now`, t_fix i koszyk; zero percepcji.
"""
from __future__ import annotations
import math
import os

from r03.kont_shield import (KontShield, EPS_B, DELTA_D5, D_STOP, T_MARGIN_TICKS, CAUSE_BARRIER, K_NOMINAL, K_KONT,
                             K_REFUSE)

# --- zamrożenie (ANEKS_NADIR-2 §2, sha256 aneksu potwierdzone przez Olgę 9.11.2026) ---
ANEKS_PATH = "ANEKS_NADIR-2.md"
ANEKS_SHA256 = "6587ad678d542adfb7cc8ce331921323fcf62fd075fdd686c2d63c59e8904989"
EPS_FIX_FREEZE = (0.305, 0.293, 0.227, 0.582)       # koszyki r_h 0–2 / 2–4 / 4–6 / 6–8 m
R_H_MAX = 8.0                                        # litera przyjęcia: r_h < 8 m
KOSZ_M = 2.0                                         # szerokość koszyka r_h
J_WORST = 3                                          # koszyk przy braku poprawki (największe ε_fix_freeze)
TAU_STAR_S = (22, 22, 22, 21)                        # reguła PRE §3 per koszyk (asercja w proverze)
NADIR_MODE_ENV = "NADIR_MODE"
CAUSE_TAUSTAR = "τ*"


def nadir_mode_from_env() -> bool:
    return os.environ.get(NADIR_MODE_ENV, "0") == "1"


def kosz(r_h: float):
    """Koszyk r_h obserwacji przyjętej (0…3); r_h ≥ 8 m ⇒ None (obserwacja nieprzyjęta literą)."""
    if not (0.0 <= r_h < R_H_MAX):
        return None
    return int(r_h // KOSZ_M)


def u_pila(k: int, j: int) -> float:
    """u(τ, j) dla kubełka k = ⌊τ⌋ i koszyka j."""
    return EPS_FIX_FREEZE[j] + EPS_B[k] + DELTA_D5


def r_pila(k: int, j: int, r_e: float) -> float:
    """Bariera piły: R(k, j) = R_E − d_stop − u(k, j)."""
    return r_e - D_STOP - u_pila(k, j)


def nadir_echo(shield) -> dict:
    return {"NADIR_MODE": int(bool(shield.nadir_mode)), "eps_fix_freeze": list(EPS_FIX_FREEZE), "r_h_max": R_H_MAX,
            "tau_star_s": list(TAU_STAR_S), "j_worst": J_WORST, "aneks_sha256": ANEKS_SHA256,
            "delta_D5": DELTA_D5, "d_stop": D_STOP, "T_margin_ticks": T_MARGIN_TICKS}


class NadirShield(KontShield):
    def __init__(self, cfg=None, kont_mode=None, nadir_mode=None):
        nm = nadir_mode_from_env() if nadir_mode is None else bool(nadir_mode)
        super().__init__(cfg, kont_mode=(True if nm else kont_mode))
        self.nadir_mode = nm

    def reset(self):
        super().reset()
        self._t_fix = None              # czas ostatniej przyjętej poprawki (wejście)
        self._j = None                  # jej koszyk
        self._tau = None
        self._j_eff = None

    def _kont_barrier(self, now, r_est):
        if not self.nadir_mode:
            return super()._kont_barrier(now, r_est)
        self._t_kont = None
        self._tau = None
        self._j_eff = None
        if not self._kont:
            return
        self._t_kont = now - self._kont_t0
        if self._t_fix is None:
            t0, j = self._kont_t0, J_WORST
        else:
            t0, j = self._t_fix, self._j
        tau = max(0.0, now - t0)        # stempel klatki może wyprzedzić zegar pętli o ułamek ticku — τ ≥ 0
        self._tau, self._j_eff = tau, j
        if self._kont_refuse:
            return
        if tau >= TAU_STAR_S[j] - T_MARGIN_TICKS * self.cfg.dt:
            self._kont_refuse, self.kont_cause = True, CAUSE_TAUSTAR
        elif r_est > r_pila(int(math.floor(tau)), j, self.cfg.r_e):
            self._kont_refuse, self.kont_cause = True, CAUSE_BARRIER

    def step(self, k, pos, vel, target, mode="PATROL", pos_flag=None, auth_ok=True,
             cs_gnss_pos=None, now=None, r_est=None, dr=None, t_fix=None, kosz_j=None):
        if not self.nadir_mode:
            return super().step(k, pos, vel, target, mode=mode, pos_flag=pos_flag, auth_ok=auth_ok,
                                cs_gnss_pos=cs_gnss_pos, now=now, r_est=r_est, dr=dr)
        if t_fix is not None and kosz_j is not None:
            self._t_fix, self._j = float(t_fix), int(kosz_j)
        d = super().step(k, pos, vel, target, mode=mode, pos_flag=pos_flag, auth_ok=auth_ok,
                         cs_gnss_pos=cs_gnss_pos, now=now, r_est=r_est, dr=dr)
        kb = int(math.floor(self._tau)) if self._tau is not None else None
        d["kont"]["R_k"] = (round(r_pila(kb, self._j_eff, self.cfg.r_e), 3)
                            if kb is not None and kb < TAU_STAR_S[self._j_eff] else None)
        d["nadir"] = {"tau": (round(self._tau, 4) if self._tau is not None else None), "k": kb, "j": self._j_eff,
                      "t_fix": self._t_fix, "u": (round(u_pila(kb, self._j_eff), 4)
                                                  if kb is not None and kb < TAU_STAR_S[self._j_eff] else None)}
        return d
