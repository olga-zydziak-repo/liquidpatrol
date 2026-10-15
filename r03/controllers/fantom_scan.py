#!/usr/bin/env python3
"""r03/controllers/fantom_scan.py — kwarantanna tracków sprzed startu epizodu
(noga FANTOM, PRE_FANTOM §1/§2, SR-9).

`FantomScan(SetpointSource)`, name="net_fantom": buduje wewnętrzny `AkwScan(**kw)`
(profil skanu II FROZEN b94cdeae NIETKNIĘTY — delegacja wzorem AkwScan→NetController)
i deleguje `step()`. Jedyna zmiana w systemie: po `reset()` (marker startu epizodu,
bench_flight.py:312) feed jest NIEWIDOCZNY dla delegata — delegat dostaje fd
nieodróżnialny od „brak tracku" wg istniejącego kontraktu (NOWY dict; zero mutacji
obiektu współdzielonego) ⇒ hold → dwell → profil II od ψ_last=0. Wyjście z kwarantanny
JEDNORAZOWE per epizod; po wyjściu pass-through VERBATIM (delegat dostaje ten sam
obiekt fd i jego cmd wraca bez kopii — tożsamość bit-w-bit, test T1).

PREDYKAT WYJŚCIA — K1 (PRE_FANTOM §2, WYBRANY regułą desku T2 — K2 „fresh-po-starcie"
padł na kryterium (ii): lock-real c05_s04 nie jest odświeżany w epizodzie przez
pierwsze 3 s (age rośnie 0.14→3.18, pomiar t2_desk) i K2 wychodziłby tam dopiero C@3.0,
podobnie outlier czysty c04_s03 — szczegóły RAPORT_FANTOM_S1 §T2). K1 = pierwsze z:
  (A) przejście invalid→valid fd (świeża admisja po utracie/expire — czyste ENTRY),
  (B) przeskok trk_pos o > D_JUMP = 5.0 m względem migawki z t_ref (przechwyt
      realnego celu bramą mti kanału — obserwowany w danych kampanii),
  (C) upływ T_q = 3.0 s (= θ_age; po T_q każdy track sprzed startu albo wygasł,
      albo jest odświeżany czymś realnym w FOV).
t_ref = now_s PIERWSZEGO step() po reset(). Koszt nazwany (PRE §2): na śladach
B/lock-real bez skoku i bez utraty wyjście dopiero przez (C) — pomiar T2: 12/48
epizodów B, +3 s kwarantanny każde. ε (K2, 0.5 s) pozostaje zadeklarowane jako
parametr kandydacki — NIEUŻYWANY przy K1 (zapis dla FREEZE_FANTOM).

GRANICA UCZCIWOŚCI (PRE §1): wrapper decyduje wyłącznie, co SAM konsumuje;
percepcja/admisja/telemetria percepcji/choreografia/profil II — nietknięte;
fantom zostaje w logach percepcji. Telemetria kwarantanny: klucze q_* w cmd["extra"]
WYŁĄCZNIE na tickach kwarantanny i na ticku wyjścia (poza nimi cmd delegata wraca
bez zmian — stąd T1 dosłowny); dziennik diagnostyczny env `FANTOM_QLOG` (ścieżka
jsonl; wyłącznie diagnostyka per PRE §7 — brak env = brak logu, zero zmian zachowania).
"""
import json
import math
import os

from r03.controllers.base import SetpointSource
from r03.controllers.akw_scan import AkwScan

FANTOM_EPS_S_FROZEN = 0.5      # ε (K2) [s] — kandydacki, NIEUŻYWANY przy K1 (FREEZE)
FANTOM_TQ_S_FROZEN = 3.0       # (C) fallback twardy T_q [s] (= θ_age) — FROZEN §2
FANTOM_DJUMP_M_FROZEN = 5.0    # (B) próg przeskoku [m] — FROZEN §2 (wybór T2: K1)


def _blank_fd(fd):
    """fd „brak tracku" wg istniejącego kontraktu (kształt jak klient V2 bez wiadomości,
    feed_vision_proc.py:63-65); NOWY dict — zero mutacji współdzielonego obiektu."""
    return {"trk_pos_ned": [0.0, 0.0, 0.0], "trk_vel_ned": [0.0, 0.0, 0.0],
            "track_age_s": 1e9, "track_valid": False,
            "feed_sha": (fd or {}).get("feed_sha")}


class FantomScan(SetpointSource):
    name = "net_fantom"

    def __init__(self, **kw):
        self._akw = AkwScan(**kw)
        self.eps_s = FANTOM_EPS_S_FROZEN
        self.t_q_s = FANTOM_TQ_S_FROZEN
        self.d_jump_m = FANTOM_DJUMP_M_FROZEN
        self._qlog_path = os.environ.get("FANTOM_QLOG")   # diagnostyka (PRE §7)
        self.reset()

    # -- delegacja atrybutów spoza kontraktu (arm, weights_sha, scan_mode, phase …)
    def __getattr__(self, item):
        return getattr(self._akw, item)

    def reset(self):
        self._akw.reset()
        self.q_active = True          # kwarantanna ON od startu epizodu (marker=reset())
        self._t_ref = None            # now_s pierwszego step() po reset
        self._fd = None               # ostatni PRAWDZIWY fd (set_feed)
        self._snapshot_pos = None     # migawka trk_pos z t_ref (K1-B)
        self._prev_valid = None       # ważność fd na poprzednim ticku (K1-A)
        self.q_exit_reason = None     # A / B / C / None (nigdy nie wyszła)
        self.q_exit_t = None

    def set_feed(self, sample):
        """Wrapper przechwytuje fd; decyzja co konsumuje delegat zapada w step()
        (predykat potrzebuje now_s). Poza kwarantanną delegat dostaje TEN SAM obiekt."""
        self._fd = sample

    def _qlog(self, obj):
        if self._qlog_path:
            try:
                with open(self._qlog_path, "a") as f:
                    f.write(json.dumps(obj) + "\n")
            except OSError:
                pass

    def step(self, tick, pos_ned, vel_ned, now_s, descending):
        fd = self._fd
        if not self.q_active:
            self._akw.set_feed(fd)
            return self._akw.step(tick, pos_ned, vel_ned, now_s, descending)
        if self._t_ref is None:
            self._t_ref = now_s
            self._snapshot_pos = (list(fd["trk_pos_ned"])
                                  if (fd and fd.get("track_valid")) else None)
            self._prev_valid = bool(fd and fd.get("track_valid"))
            self._qlog({"ev": "q_enter", "t": round(now_s, 4),
                        "fd_valid_at_ref": bool(fd and fd.get("track_valid"))})
        dt = now_s - self._t_ref
        valid = bool(fd and fd.get("track_valid"))
        reason = None
        if valid and self._prev_valid is False:
            reason = "A"                          # invalid→valid: świeża admisja w epizodzie
        elif (valid and self._snapshot_pos is not None
                and math.dist(fd["trk_pos_ned"][:2], self._snapshot_pos[:2]) > self.d_jump_m):
            reason = "B"                          # przeskok > D_JUMP vs migawka z t_ref
        elif dt >= self.t_q_s:
            reason = "C"                          # fallback twardy T_q
        self._prev_valid = valid
        if reason is not None:
            self.q_active = False
            self.q_exit_reason = reason
            self.q_exit_t = now_s
            self._qlog({"ev": "q_exit", "reason": reason, "t": round(now_s, 4),
                        "dt": round(dt, 4)})
            self._akw.set_feed(fd)
            cmd = self._akw.step(tick, pos_ned, vel_ned, now_s, descending)
            out = dict(cmd)
            out["extra"] = dict(cmd["extra"])
            out["extra"].update({"q_active": False, "q_exit_reason": reason,
                                 "q_exit_t": round(now_s, 4)})
            return out
        # w kwarantannie: delegat widzi „brak tracku". Podmiana na blank WYŁĄCZNIE dla
        # fd WAŻNEGO (fantom); fd już nieważny idzie surowy — dla sterowania jest
        # nieodróżnialny od blank (net_controller.py:108), a echo telemetrii w extra
        # (track_age_s) zostaje prawdziwe. Przeciek niemożliwy: podmiana zależy od
        # BIEŻĄCEGO ticku — odświeżony fantom (valid, age małe) jest podmieniany.
        self._akw.set_feed(_blank_fd(fd) if (fd is not None and fd.get("track_valid"))
                           else fd)
        cmd = self._akw.step(tick, pos_ned, vel_ned, now_s, descending)
        out = dict(cmd)
        out["extra"] = dict(cmd["extra"])
        out["extra"].update({"q_active": True, "q_exit_reason": None, "q_exit_t": None})
        return out
