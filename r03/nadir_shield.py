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

PRE_NAD2 §3.4 + ANEKS_NAD2-1 §2 (PROMPT_NAD2_S1 §1.2) — reżim NAD2 wybierany JAWNIE przełącznikiem `nad2` (argument;
domyślnie env NADIR_LITERA == "NAD2"; brak ⇒ stary reżim NADIR-I bez zmiany zachowania). Tylko przy nadir_mode=True:
  - tabela U(przedział τ, koszyk 0–4, tryb para|jeden) = 1.5·(F(koszyk, tryb) + G(przedział)) zamiast ε_fix_freeze + ε_b(⌊τ⌋);
    bariera R = R_E − d_stop − (U + Δ_D5); przedział z τ + TAU_EPS_NAD2 (0.012 s); REFUSE(τ*) przy τ ≥ τ* − 2·dt = 0.95 s;
    brak poprawki od wejścia w utratę ⇒ pole (jeden, koszyk 4), τ od zera zegara utraty;
  - RAMA: step dostaje pozycję i cel w ramie EKF (pos, target) ORAZ w ramie poprawionej (pos_corr, target_corr); po
    aktualizacji monitora GNSS w tym samym ticku osłona wybiera ramę — w utracie (KONT, KONT_REFUSE) poprawioną, w NOMINAL
    EKF; r_est = |pozycja w ramie wybranej|; cała gramatyka (R-KONT, R-G, R-G-NOM, applied) liczy w ramie wybranej; wyjście
    applied przeliczane do ramy EKF (applied − Δ w N, E) i to jest „applied” decyzji; oryginał w d["nad2"]["applied_rama"].
Stałe tabeli wkompilowane z sumą sha tabeli (results/NAD2/s1/freeze_U.json, sha256_tabeli) i sha PRE/ANEKS (wzór ANEKS_SHA256).
"""
from __future__ import annotations
import math
import os

from r03.kont_shield import (KontShield, EPS_B, DELTA_D5, D_STOP, T_MARGIN_TICKS, CAUSE_BARRIER, K_NOMINAL, K_KONT,
                             K_REFUSE)
from r01.shield import PatrolShield

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


# --- NAD2 (PRE_NAD2 §4 + ANEKS_NAD2-1 §2; ratyfikacje Olgi 11.11.2026) ---
NAD2_PRE_PATH, NAD2_PRE_SHA256 = "PRE_NAD2.md", "eea6fcc82b1a14b9dfacd710ec4c6c0f426bbbea34b549ab4c1511de9567e634"
NAD2_ANEKS_PATH, NAD2_ANEKS_SHA256 = "ANEKS_NAD2-1.md", "92d4dfcbbd55cccae9cc6df1058bb229c47cddc7e61f0a01bac9ea88c6b5f33b"
NAD2_TABELA_PATH = "results/NAD2/s1/freeze_U.json"
NAD2_TABELA_SHA256 = "6a118fd404491b04556a26cbeb5d8a6b296597c7499e12e7a8c553af44641073"
KRAW_NAD2 = (0.25, 0.45, 0.65, 0.85, 1.05)                  # górne krawędzie przedziałów τ [s]
G_NAD2 = (0.6251, 1.0722, 1.4583, 1.7894, 2.0638)           # przyrost EKF (okno przesuwne, poziomo)
F_NAD2 = {"para": (0.1968, 0.2372, 0.2372, 0.2372, 0.2577),
          "jeden": (0.2562, 0.3376, 0.4445, 0.4527, 0.4527)}  # błąd zakotwiczenia, koszyki r_h 0–2 … 8–10 m
ZAPAS_NAD2 = 1.5
TAU_STAR_NAD2 = 1.05
TAU_EPS_NAD2 = 0.012                                        # ANEKS_NAD2-1 §2.3
KOSZ_N_NAD2, TRYBY_NAD2 = 5, ("para", "jeden")
POLE_BRAK_NAD2 = ("jeden", 4)                               # brak poprawki od wejścia w utratę
LITERA_ENV = "NADIR_LITERA"


def nad2_from_env() -> bool:
    return os.environ.get(LITERA_ENV, "NADIR1") == "NAD2"


def przedzial_nad2(tau: float) -> int:
    """Indeks przedziału dla τ osłony: krawędź wybrana dla τ + TAU_EPS_NAD2; None ⇔ poza tabelą."""
    t = tau + TAU_EPS_NAD2
    for i, kr in enumerate(KRAW_NAD2):
        if t <= kr:
            return i
    return None


def u_nad2(i: int, k: int, tryb: str) -> float:
    """u′ = U + Δ_D5, U = 1.5·(F(k, tryb) + G(i))."""
    return ZAPAS_NAD2 * (F_NAD2[tryb][k] + G_NAD2[i]) + DELTA_D5


def r_nad2(i: int, k: int, tryb: str, r_e: float) -> float:
    return r_e - D_STOP - u_nad2(i, k, tryb)


def nad2_tabela_check(root="."):
    """Zgodność stałych wkompilowanych z freeze_U.json (sha tabeli) — test/asercja proverów."""
    import json, hashlib
    F = json.load(open(os.path.join(root, NAD2_TABELA_PATH)))
    t = F["tabela"]
    can = json.dumps(t, sort_keys=True, separators=(",", ":"))
    return {"sha_ok": hashlib.sha256(can.encode()).hexdigest() == NAD2_TABELA_SHA256 == F["sha256_tabeli"],
            "kraw_ok": tuple(t["krawedzie_tau_s"]) == KRAW_NAD2, "G_ok": tuple(t["G"]) == G_NAD2,
            "F_ok": all(tuple(t["F"][tr]) == F_NAD2[tr] for tr in TRYBY_NAD2), "zapas_ok": t["zapas"] == ZAPAS_NAD2,
            "tau_star_ok": t["tau_star_s"] == TAU_STAR_NAD2, "delta_ok": t["delta_D5"] == DELTA_D5,
            "pre_ok": F["pre_sha256"] == NAD2_PRE_SHA256, "aneks_ok": F["aneks_sha256"] == NAD2_ANEKS_SHA256}


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
    def __init__(self, cfg=None, kont_mode=None, nadir_mode=None, nad2=None):
        nm = nadir_mode_from_env() if nadir_mode is None else bool(nadir_mode)
        super().__init__(cfg, kont_mode=(True if nm else kont_mode))
        self.nadir_mode = nm
        self.nad2 = (nad2_from_env() if nad2 is None else bool(nad2)) and nm      # NAD2 tylko w reżimie NADIR

    def reset(self):
        super().reset()
        self._t_fix = None              # czas ostatniej przyjętej poprawki (wejście)
        self._j = None                  # jej koszyk
        self._tau = None
        self._j_eff = None
        self._tryb = None               # NAD2: tryb ostatniej poprawki
        self._tryb_eff = None
        self._przedzial = None
        self._rama = None               # NAD2: „corr” | „ekf” — rama wejść osłony w tym ticku

    def _kont_barrier(self, now, r_est):
        if not self.nadir_mode:
            return super()._kont_barrier(now, r_est)
        if self.nad2:
            return self._nad2_barrier(now, r_est)
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

    def _nad2_barrier(self, now, r_est):
        """PRE_NAD2 §3.4, ANEKS_NAD2-1 §2.3/§2.5: bariera tabeli U; REFUSE(τ*) przy τ ≥ τ* − 2·dt."""
        self._t_kont = None
        self._tau = self._j_eff = self._tryb_eff = self._przedzial = None
        if not self._kont:
            return
        self._t_kont = now - self._kont_t0
        if self._t_fix is None:
            t0, (tr, j) = self._kont_t0, POLE_BRAK_NAD2
        else:
            t0, tr, j = self._t_fix, self._tryb, self._j
        tau = max(0.0, now - t0)
        i = przedzial_nad2(tau)
        self._tau, self._j_eff, self._tryb_eff, self._przedzial = tau, j, tr, i
        if self._kont_refuse:
            return
        if tau >= TAU_STAR_NAD2 - T_MARGIN_TICKS * self.cfg.dt or i is None:
            self._kont_refuse, self.kont_cause = True, CAUSE_TAUSTAR
        elif r_est > r_nad2(i, j, tr, self.cfg.r_e):
            self._kont_refuse, self.kont_cause = True, CAUSE_BARRIER

    def _step_nad2(self, k, pos, vel, target, mode, pos_flag, auth_ok, cs_gnss_pos, now, dr, t_fix, kosz_j, tryb,
                   pos_corr, target_corr):
        """Kształt 1:1 z KontShield.step (monitor → bariera → PatrolShield.step → d["kont"]), z wyborem ramy po monitorze."""
        if t_fix is not None and kosz_j is not None:
            self._t_fix, self._j = float(t_fix), int(kosz_j)
            self._tryb = tryb if tryb in TRYBY_NAD2 else "jeden"
        now = k * self.cfg.dt if now is None else float(now)
        self._gnss_monitor(None if cs_gnss_pos is None else (not cs_gnss_pos), now)
        corr = self._kont and pos_corr is not None and target_corr is not None
        self._rama = "corr" if corr else "ekf"
        pu, tu = (pos_corr, target_corr) if corr else (pos, target)
        dn, de = ((float(pos_corr[0]) - float(pos[0]), float(pos_corr[1]) - float(pos[1])) if corr else (0.0, 0.0))
        self._r_est = math.hypot(float(pu[0]), float(pu[1]))
        self._kont_barrier(now, self._r_est)
        d = PatrolShield.step(self, k, pu, vel, tu, mode=mode, pos_flag=pos_flag, auth_ok=auth_ok)
        a = d.get("applied")
        app_r = list(a) if a is not None else None
        if a is not None and corr:
            d["applied"] = [float(a[0]) - dn, float(a[1]) - de, float(a[2])]
        kb = self._przedzial
        d["kont"] = {"phase": self.kont_phase(), "now": round(now, 4),
                     "t_kont": (round(self._t_kont, 4) if self._t_kont is not None else None),
                     "k": kb, "R_k": (round(r_nad2(kb, self._j_eff, self._tryb_eff, self.cfg.r_e), 3) if kb is not None else None),
                     "r_est": round(self._r_est, 3), "cause": self.kont_cause, "n_enter": self.n_kont_enter,
                     "cs_gnss_pos": cs_gnss_pos, "dr": dr}
        d["nadir"] = {"tau": (round(self._tau, 4) if self._tau is not None else None), "k": kb, "j": self._j_eff,
                      "t_fix": self._t_fix, "u": (round(u_nad2(kb, self._j_eff, self._tryb_eff), 4) if kb is not None else None)}
        d["nad2"] = {"rama": self._rama, "d_ne": [round(dn, 6), round(de, 6)], "przedzial": kb, "tryb": self._tryb_eff,
                     "r_est": self._r_est, "applied_rama": app_r}
        return d

    def step(self, k, pos, vel, target, mode="PATROL", pos_flag=None, auth_ok=True,
             cs_gnss_pos=None, now=None, r_est=None, dr=None, t_fix=None, kosz_j=None, tryb=None,
             pos_corr=None, target_corr=None):
        if self.nadir_mode and self.nad2:                    # PRE_NAD2 §3.4 (r_est wyłącznie z ramy wybranej)
            return self._step_nad2(k, pos, vel, target, mode, pos_flag, auth_ok, cs_gnss_pos, now, dr, t_fix, kosz_j, tryb,
                                   pos_corr, target_corr)
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
