"""r02/target_channel.py — KANAŁ CELU 5-dim ZOH-age (R3, PRE_R02 §2.3 + 0ter/A1).

Format kanału (DECYZJA, ZAMROŻONE): `(cx, cy, w, h, age_s)` znormalizowany do rozdzielczości
obrazu. **BEZ `conf` (R02-A1/D1)** — detektor publikuje top-1 box bez bramkowania conf; conf żyje
wyłącznie w telemetrii/logach detektora, NIGDY w kanale ani w decyzjach osłony.

Semantyka (§2.3):
  - **detekcja** → nadpisz `(cx,cy,w,h)`, `age_s := L_deliver` (świeże).
  - **brak detekcji** (gdy zamknięty lock) → **ZOH** ostatniej detekcji, `age_s += Δt` (starzeje się).
  - **ENTRY** (R1-B, strukturalny, NIE conf) = spójna detekcja przez **k=3** kolejne klatki @1 Hz
    (top-1 box w spójnej lokalizacji: ruch środka ≤ move_thr między klatkami). age liczony od
    pierwszej z serii k (anchor `t_entry`); w chwili ENTRY `age_s = L_deliver`.
  - **sufit θ_age**: `age_s > θ_age` ⇒ cel „wygasły" ⇒ EXPIRE ⇒ wyjście z locka (powrót do SEARCHING).

Maszyna stanów kanału (rozłączna z automatem OSŁONY — kanał NIE decyduje o ruchu, tylko zasila):
  SEARCHING → (box) CANDIDATE(streak) → (streak==k) LOCKED[ENTRY] → (age>θ_age) SEARCHING[EXPIRE].
Determinizm: wszystkie przejścia = czysta funkcja (sekwencja klatek, sim-time). Bez zegara ściennego.

Kanał jest aktualizowany na kadencji DETEKTORA (`on_frame` @1 Hz); `sample(t)` (dowolna chwila, np.
osłona @20 Hz) ekstrapoluje age_s = (t - t_ostatniej_detekcji) + L_deliver między klatkami (ZOH).
"""
from __future__ import annotations
from dataclasses import dataclass
import math

from r02.config_r02 import ChannelConfig

# stany kanału
SEARCHING, CANDIDATE, LOCKED = "SEARCHING", "CANDIDATE", "LOCKED"
# zdarzenia (do trace/logu osłony)
EV_ENTRY, EV_EXPIRE, EV_REFRESH, EV_NONE = "ENTRY", "EXPIRE", "REFRESH", None


@dataclass(frozen=True)
class Box:
    """Top-1 box detektora, znormalizowany [0,1]. conf CELOWO poza kanałem (A1) —
    opcjonalne pole `conf` dozwolone WYŁĄCZNIE do logu/telemetrii, nie wchodzi do wartości kanału."""
    cx: float
    cy: float
    w: float
    h: float
    conf: float | None = None        # tylko log/telemetria (A1) — NIE część kanału

    def center(self):
        return (self.cx, self.cy)

    def edge_dist(self):
        """Odległość środka boxa od najbliższej krawędzi kadru (0=krawędź, 0.5=środek)."""
        return min(self.cx, 1.0 - self.cx, self.cy, 1.0 - self.cy)


@dataclass(frozen=True)
class ChannelValue:
    """Wartość kanału 5-dim (BEZ conf). age_s = staleness detekcji (podłoga L_deliver)."""
    cx: float
    cy: float
    w: float
    h: float
    age_s: float

    def as_tuple(self):
        return (self.cx, self.cy, self.w, self.h, self.age_s)


def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


class TargetChannel:
    """Kanał celu ZOH-age. Konsument: (1) `on_frame(box|None, t)` na kadencji detektora (1 Hz);
    (2) `sample(t)` w dowolnej chwili → ChannelValue|None (None gdy brak locka)."""

    def __init__(self, cfg: ChannelConfig | None = None):
        self.cfg = cfg or ChannelConfig()
        assert self.cfg.sane(), "ChannelConfig niespójny (k/podłoga/sufit/próg)"
        self.reset()

    def reset(self):
        self.state = SEARCHING
        self.streak = 0                 # licznik spójnych klatek (kandydat na ENTRY)
        self.anchor = None              # środek pierwszej klatki serii k (t_entry anchor)
        self.t_first = None             # sim-time pierwszej klatki serii k
        self.last_box = None            # ostatni box (ZOH)
        self.t_last_det = None          # sim-time ostatniej klatki Z BOXEM przy locku
        self.locked = False
        self.n_entry = 0
        self.n_expire = 0
        self.n_false_entry = 0          # ENTRY policzone gdy scena PUSTA (ustalane z ground-truth w bramce)
        self.events = []                # [(t, event, detail)]

    # -- klatka detektora (kadencja 1 Hz) -----------------------------------
    def on_frame(self, box, t, gt_present: bool | None = None, mti_ok: bool | None = None):
        """Jedna klatka detektora. box: Box|None (top-1, BEZ bramkowania conf — A1). t: sim-time [s].
        gt_present: opcjonalny ground-truth (czy intruz realnie w FOV) — TYLKO do liczenia ε_FP w bramce,
        NIE wpływa na logikę kanału. mti_ok: czy box koincyduje z komponentem MTI (STRUKTURA ∧ MTI, B3) —
        używane WYŁĄCZNIE gdy cfg.entry_require_mti. Zwraca zdarzenie (EV_ENTRY/EXPIRE/REFRESH/None)."""
        ev = EV_NONE
        if self.locked:
            ev = self._on_frame_locked(box, t, gt_present)
        else:
            ev = self._on_frame_unlocked(box, t, gt_present, mti_ok)
        if ev is not None:
            self.events.append((round(t, 4), ev, self._detail()))
        return ev

    def _on_frame_unlocked(self, box, t, gt_present, mti_ok=None):
        # ENTRY-admisja (KOMBINACJA, upstream locka): box musi być CENTRALNY (edge-margin, geometryczny,
        # A1-preserving). Druga brama zależy od trybu:
        #   - cfg.entry_require_mti=True (DEMO/MTI, B3): box musi koincydować z KOMPONENTEM MTI (mti_ok).
        #     conf ZDEGRADOWANE DO TELEMETRII PASYWNEJ — logowane w Box.conf, NIGDY w admisji (symetria z
        #     eph z R0.3a). θ_conf pozostaje zdefiniowane, przestaje być bramą (ratyfikowana zmiana znaczenia).
        #   - cfg.entry_require_mti=False (R0.2/GT-fed/frozen): conf-floor θ_conf (R02-A6) jak dotąd.
        # conf/MTI UŻYTE WYŁĄCZNIE tu (admisja ENTRY) — NIGDY w wartości kanału (5-dim), osłonie, P1/P5.
        # Refresh locka (poniżej) NIE stosuje ani edge-margin, ani conf/MTI.
        if box is not None and box.edge_dist() < self.cfg.entry_edge_margin:
            box = None
        if self.cfg.entry_require_mti:
            if box is not None and not mti_ok:
                box = None                  # B3: STRUKTURA ∧ MTI — brak koincydencji ruchu ⇒ brak ENTRY
        elif box is not None and box.conf is not None and box.conf < self.cfg.entry_theta_conf:
            box = None                      # R02-A6 conf-floor (legacy) — conf nie wchodzi do kanału
        if box is None:
            # brak boxa → seria się zrywa
            self.state = SEARCHING; self.streak = 0; self.anchor = None; self.t_first = None
            return EV_NONE
        c = box.center()
        if self.streak == 0:
            # start nowej serii
            self.streak = 1; self.anchor = c; self.t_first = t
            self.state = CANDIDATE
        else:
            # spójna lokalizacja? ruch środka względem POPRZEDNIEJ klatki serii ≤ próg
            if _dist(c, self.anchor) <= self.cfg.entry_move_thr:
                self.streak += 1
            else:
                # skok → re-anchor, seria od nowa (streak=1)
                self.streak = 1; self.t_first = t
            self.anchor = c
        self.last_box = box
        if self.streak >= self.cfg.entry_k:
            # ENTRY: lock, age spada z „∞/sufit" do L_deliver; anchor age = pierwsza z serii k
            self.locked = True; self.state = LOCKED
            self.t_last_det = t
            self.n_entry += 1
            if gt_present is False:
                self.n_false_entry += 1        # fałszywy lock na pustej scenie (ε_FP)
            return EV_ENTRY
        return EV_NONE

    def _on_frame_locked(self, box, t, gt_present):
        # najpierw sprawdź wygaśnięcie po wieku (ZOH nie mostkuje dłużej niż θ_age)
        if self.t_last_det is not None:
            age = (t - self.t_last_det) + self.cfg.l_deliver_s
            if age > self.cfg.theta_age_s:
                self._expire(t)
                # ta klatka może od razu zacząć nową serię, jeśli ma box
                return self._on_frame_unlocked(box, t, gt_present) or EV_EXPIRE
        if box is not None:
            # świeża detekcja → nadpisz box, age:=L_deliver (top-1, bez conf gate)
            self.last_box = box; self.t_last_det = t
            return EV_REFRESH
        # brak boxa, lock wciąż w wieku → ZOH (nic nie nadpisujemy; age rośnie w sample())
        return EV_NONE

    def _expire(self, t):
        self.locked = False; self.state = SEARCHING; self.streak = 0
        self.anchor = None; self.t_first = None; self.t_last_det = None
        self.n_expire += 1
        self.events.append((round(t, 4), EV_EXPIRE, self._detail()))

    # -- odczyt wartości kanału (dowolna chwila; osłona @20 Hz) --------------
    def sample(self, t) -> ChannelValue | None:
        """Wartość 5-dim w chwili t (sim-time). None gdy brak locka (SEARCHING/CANDIDATE).
        age_s = (t - t_ostatniej_detekcji) + L_deliver (ZOH między detekcjami)."""
        if not self.locked or self.last_box is None or self.t_last_det is None:
            return None
        age = (t - self.t_last_det) + self.cfg.l_deliver_s
        b = self.last_box
        return ChannelValue(b.cx, b.cy, b.w, b.h, round(age, 4))

    def is_expired(self, t) -> bool:
        """Czy age przekroczył sufit (osłona: warunek wyjścia z OBSERVE)."""
        if not self.locked or self.t_last_det is None:
            return False
        return (t - self.t_last_det) + self.cfg.l_deliver_s > self.cfg.theta_age_s

    def tick_time(self, t):
        """Wywoływane na kadencji OSŁONY (20 Hz) MIĘDZY klatkami detektora: egzekwuje sufit
        wieku bez czekania na następną klatkę (age rośnie w czasie, nie tylko na klatce)."""
        if self.locked and self.is_expired(t):
            self._expire(t)
            return EV_EXPIRE
        return EV_NONE

    def _detail(self):
        return {"state": self.state, "streak": self.streak, "locked": self.locked,
                "box": None if self.last_box is None else
                       [round(self.last_box.cx, 4), round(self.last_box.cy, 4),
                        round(self.last_box.w, 4), round(self.last_box.h, 4)]}

    def summary(self):
        return {"n_entry": self.n_entry, "n_expire": self.n_expire,
                "n_false_entry": self.n_false_entry, "state": self.state, "locked": self.locked}
