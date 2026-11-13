#!/usr/bin/env python3
"""results/NAD3_RECON/tools/nad3_degrad.py — PROMPT_NAD3_S0 R3: model degradacji poprawki (projekt modułu; 0 bootów).

Miejsce (bez zmiany harness/nadir_fix.py): harness/nadir_obs.py:142-143 — `fx = _rama.obserwacja(...)`, potem `_send(fx)`.
Degradacja wchodzi MIĘDZY nimi: `_send(_deg.przetworz(fx))`. Rama producenta (wewnętrzne d_ne, bramka reszty, r_h, T1) liczy
się na poprawce czystej; konsumenci (driver, percep_proc — oba gniazda NADIR_FIX_SOCKS) dostają poprawkę zdegradowaną.
Przełącznik env NAD3_DEGRAD (JSON); brak/pusty ⇒ `przetworz` zwraca TEN SAM obiekt fx (passthrough bitowy: json.dumps
identyczny). Log: row["fx"] w nadir_obs.jsonl zostaje czysty; zdegradowany datagram do osobnego pola (projekt: row["fx_deg"]).

Kontrakt błędu (|E| ≤ E_max w płaszczyźnie NE, z ziarnem):
  bias_rad  — stały kierunek radialny w ramie lokalnej: E = s·E_max·p̂_fix, s = +1 „na_zewnatrz” (estymata dalej od środka niż
              prawda ⇒ osłona ostrożniejsza, koszt dostępności), s = −1 „do_srodka” (estymata bliżej środka ⇒ prawda na zewnątrz
              estymaty — najgorszy dla przesłanki bariery);
  bialy     — niezależny, jednostajny w kole promienia E_max przy każdej dostarczonej poprawce;
  wolny     — 2D Ornstein–Uhlenbeck z czasem korelacji T_c (2 s albo 10 s), σ na oś = E_max/2, próbkowany w czasie t_frame
              dostarczonych poprawek, obcięty radialnie do koła E_max.
Częstość i gubienie: decymacja do f na sztywnej siatce slotów t_0 + n/f — poprawka (ok) dostarczana, gdy t_frame ≥ slot
(tolerancja 1e-3 s), potem slot przesuwany do pierwszego punktu siatki > t_frame. Z bazy 5 Hz (klatka co 0.2 s) średnia częstość
= f, ale przerwa = 1/f zaokrąglone W GÓRĘ do wielokrotności 0.2 s (4 Hz: 0.2/0.4 s; 2 Hz: 0.4/0.6 s); gubienie K kolejnych dostarczonych slotów po każdej dostarczonej („okresowy”, faza
z ziarna: pierwsze 0…K slotów zgubione) albo „losowy” (paczka K zgubień z p na slot). Datagramy nieprzyjęte (ok = False)
i zdecymowane/zgubione wychodzą ze stanem ostatnio DOSTARCZONYM (d_ne, t_fix, kosz, tryb, p_fix_ne), ok = False, powód
„nad3_decymacja”/„nad3_zgubiona”. Kosz i tryb dostarczonej poprawki = producenta (wejście tabeli U′).
Poza kontraktem (nazwane, niemodelowane): skok poza E_max (fałszywe dopasowanie obrazu do mapy).
"""
import copy
import json
import math
import os

import numpy as np

ENV = "NAD3_DEGRAD"
TOL_SLOT = 1e-3                                         # stempel klatki 5 Hz z zaokrągleniem do 1e-4


def z_env():
    s = os.environ.get(ENV, "")
    return Degradacja(json.loads(s)) if s.strip() else Degradacja(None)


class Degradacja:
    def __init__(self, cfg):
        self.cfg = cfg
        if cfg is None:
            return
        self.model = cfg.get("model", "zero")            # zero | bias_rad | bialy | wolny
        self.E = float(cfg.get("E_max", 0.0))
        self.znak = -1.0 if cfg.get("kierunek", "do_srodka") == "do_srodka" else 1.0
        self.Tc = float(cfg.get("T_c", 2.0))
        self.f = cfg.get("f")                            # None ⇒ pełna częstość
        self.K = int(cfg.get("K", 0))
        self.wzor = cfg.get("wzor", "okresowy")
        self.p_paczka = float(cfg.get("p_paczka", 0.2))
        self.rng = np.random.default_rng(int(cfg.get("ziarno", 0)))
        self.slot = None
        self.do_zgubienia = int(self.rng.integers(0, self.K + 1)) if self.K else 0
        self.ou = None
        self.t_ou = None
        self.stan = None                                 # ostatnio dostarczone: d_ne, t_fix, kosz, tryb, p_fix_ne

    def _blad(self, fx):
        if self.model == "zero" or self.E <= 0:
            return np.zeros(2)
        if self.model == "bias_rad":
            p = np.array(fx["p_fix_ne"], float)
            n = np.linalg.norm(p)
            return self.znak * self.E * (p / n if n > 1e-9 else np.array([1.0, 0.0]))
        if self.model == "bialy":
            r = self.E * math.sqrt(self.rng.random())
            a = 2 * math.pi * self.rng.random()
            return np.array([r * math.cos(a), r * math.sin(a)])
        if self.model == "wolny":
            s = self.E / 2.0
            t = float(fx["t_frame"])
            if self.ou is None:
                self.ou = self.rng.normal(0, s, 2)
            else:
                a = math.exp(-max(t - self.t_ou, 0.0) / self.Tc)
                self.ou = a * self.ou + math.sqrt(1 - a * a) * self.rng.normal(0, s, 2)
            self.t_ou = t
            n = np.linalg.norm(self.ou)
            return self.ou * (self.E / n) if n > self.E else self.ou.copy()
        raise ValueError(self.model)

    def _dostarcz(self, fx):
        """Czy poprawka ok przechodzi decymację i wzór gubienia (zwraca powód odrzucenia albo None)."""
        t = float(fx["t_frame"])
        if self.f is not None:
            okres = 1.0 / float(self.f)
            if self.slot is not None and t < self.slot - TOL_SLOT:
                return "nad3_decymacja"
            if self.slot is None:
                self.slot = t
            while self.slot <= t + TOL_SLOT:                 # siatka slotów sztywna: następny slot po t
                self.slot += okres
        if self.K:
            if self.wzor == "okresowy":
                if self.do_zgubienia > 0:
                    self.do_zgubienia -= 1
                    return "nad3_zgubiona"
                self.do_zgubienia = self.K
            else:
                if self.do_zgubienia > 0:
                    self.do_zgubienia -= 1
                    return "nad3_zgubiona"
                if self.rng.random() < self.p_paczka:
                    self.do_zgubienia = self.K - 1
                    return "nad3_zgubiona"
        return None

    def przetworz(self, fx):
        if self.cfg is None:
            return fx
        out = copy.deepcopy(fx)
        if fx.get("ok"):
            powod = self._dostarcz(fx)
            if powod is None:
                E = self._blad(fx)
                d = [fx["d_ne"][0] + float(E[0]), fx["d_ne"][1] + float(E[1])]
                p = [fx["p_fix_ne"][0] + float(E[0]), fx["p_fix_ne"][1] + float(E[1])]
                self.stan = {"d_ne": d, "t_fix": fx["t_fix"], "kosz": fx.get("kosz"), "tryb": fx.get("tryb"), "p_fix_ne": p}
                out.update(d_ne=[round(d[0], 6), round(d[1], 6)], p_fix_ne=[round(p[0], 4), round(p[1], 4)],
                           nad3={"E": [round(float(E[0]), 6), round(float(E[1]), 6)]})
                return out
            out["ok"] = False
            out["powod"] = powod
        if self.stan is None:
            out.update(d_ne=[0.0, 0.0], t_fix=None)
        else:
            out.update(d_ne=[round(self.stan["d_ne"][0], 6), round(self.stan["d_ne"][1], 6)], t_fix=self.stan["t_fix"])
        return out
