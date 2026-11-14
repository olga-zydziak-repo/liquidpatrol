#!/usr/bin/env python3
"""harness/nad3_degrad.py — degradacja poprawki ramy B+ (PRE_NAD3 §4–§5.1, PROMPT_NAD3_S1 §1.1). Nowy plik.

Na bazie results/NAD3_RECON/tools/nad3_degrad.py (recon NADIR-III). Wołany w harness/nadir_obs.py MIĘDZY wyliczeniem poprawki
(harness/nadir_fix.Rama.obserwacja — nietknięty) a wysyłką datagramu do gniazd konsumentów (driver i percep_proc dostają ten
sam stan). Producent (Δ wewnętrzne, bramka reszty, r_h, T1) liczy na poprawce czystej.
Przełącznik env NAD3_DEGRAD (JSON); nieustawiony albo pusty ⇒ `przetworz(fx)` zwraca TEN SAM obiekt (datagram i wiersz rejestru
bajtowo jak w NAD2).

Model lotów tej nogi (PRE_NAD3 §4): bias radialny E = s·E_max·p̂_fix, p̂_fix = kierunek od środka strefy przez poprawkę czystą
(p_fix_ne w ramie lokalnej), s = +1 „na_zewnatrz” / −1 „do_srodka”, stały w locie; częstość 1 Hz na sztywnej siatce slotów, K = 0.
Launcher nogi wystawia wyłącznie ten model (results/NAD3/tools/nad3_launch.sh); „bialy” i „wolny” zostają w module dla replayu.
Siatka slotów: t_0 = t_frame pierwszej poprawki ok, slot n = [t_0 + n/f, t_0 + (n+1)/f); poprawka dostarczana ⇔ jej slot
n = ⌊(t_frame − t_0 + TOL_SLOT)·f⌋ jest późniejszy niż slot ostatniej dostarczonej (najwyżej jedna na slot; przy brakującej
klatce na początku slotu pierwsza późniejsza w tym samym slocie). Gubienie K kolejnych dostarczonych slotów (wzór „okresowy”
z fazą z ziarna albo „losowy”) — tylko replay; w lotach K = 0.
Datagram zdegradowany: d_ne i p_fix_ne przesunięte o E, pole "nad3" = {E, slot, model, znak}; datagramy nieprzyjęte, zdecymowane
i zgubione wychodzą ze stanem ostatnio DOSTARCZONYM (d_ne, t_fix), ok = False, powód „nad3_decymacja”/„nad3_zgubiona”.
Poza kontraktem (nazwane, niemodelowane): skok poza E_max (fałszywe dopasowanie).
"""
import copy
import json
import math
import os

import numpy as np

ENV = "NAD3_DEGRAD"
TOL_SLOT = 1e-3                                         # stempel klatki 5 Hz z zaokrągleniem do 1e-4
MODELE = ("zero", "bias_rad", "bialy", "wolny")
KIERUNKI = ("na_zewnatrz", "do_srodka")


def z_env():
    s = os.environ.get(ENV, "")
    return Degradacja(json.loads(s)) if s.strip() else Degradacja(None)


class Degradacja:
    def __init__(self, cfg):
        self.cfg = cfg
        if cfg is None:
            return
        self.model = cfg.get("model", "zero")
        assert self.model in MODELE, self.model
        self.kierunek = cfg.get("kierunek", "do_srodka")
        assert self.kierunek in KIERUNKI, self.kierunek
        self.E = float(cfg.get("E_max", 0.0))
        self.znak = -1.0 if self.kierunek == "do_srodka" else 1.0
        self.Tc = float(cfg.get("T_c", 2.0))
        self.f = cfg.get("f")                            # None ⇒ pełna częstość
        self.K = int(cfg.get("K", 0))
        self.wzor = cfg.get("wzor", "okresowy")
        self.p_paczka = float(cfg.get("p_paczka", 0.2))
        self.rng = np.random.default_rng(int(cfg.get("ziarno", 0)))
        self.t0 = None                                   # początek siatki slotów
        self.slot_ost = None                             # slot ostatniej dostarczonej
        self.slot = None                                 # slot bieżącej poprawki (do rejestru)
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
        s = self.E / 2.0                                 # „wolny”: 2D Ornstein–Uhlenbeck, obcięty do koła E_max
        t = float(fx["t_frame"])
        if self.ou is None:
            self.ou = self.rng.normal(0, s, 2)
        else:
            a = math.exp(-max(t - self.t_ou, 0.0) / self.Tc)
            self.ou = a * self.ou + math.sqrt(1 - a * a) * self.rng.normal(0, s, 2)
        self.t_ou = t
        n = np.linalg.norm(self.ou)
        return self.ou * (self.E / n) if n > self.E else self.ou.copy()

    def _dostarcz(self, fx):
        """Czy poprawka ok przechodzi decymację i wzór gubienia (zwraca powód odrzucenia albo None)."""
        t = float(fx["t_frame"])
        self.slot = None
        if self.f is not None:
            if self.t0 is None:
                self.t0 = t
            n = int(math.floor((t - self.t0 + TOL_SLOT) * float(self.f)))
            if self.slot_ost is not None and n <= self.slot_ost:
                return "nad3_decymacja"
            self.slot_ost = self.slot = n
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
                           nad3={"E": [round(float(E[0]), 6), round(float(E[1]), 6)], "slot": self.slot, "model": self.model,
                                 "znak": int(self.znak)})
                return out
            out["ok"] = False
            out["powod"] = powod
        if self.stan is None:
            out.update(d_ne=[0.0, 0.0], t_fix=None)
        else:
            out.update(d_ne=[round(self.stan["d_ne"][0], 6), round(self.stan["d_ne"][1], 6)], t_fix=self.stan["t_fix"])
        return out

    def echo(self):
        """Konfiguracja do meta rejestru (None przy wyłączonej degradacji)."""
        return None if self.cfg is None else dict(self.cfg)
