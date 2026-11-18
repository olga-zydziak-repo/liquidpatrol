#!/usr/bin/env python3
"""results/PETLA_RECON/tools/pl_intruz.py — klasa intruza I i rodziny torów (PROMPT_PETLA_S0 §6; 0 bootów).

Klasa I: koło ρ = 11.0 m wokół home (0, 0), prędkość ≤ v_max (1.0 albo 0.5 m/s), wysokość stała 10 m (z NED = −10), start
w losowym punkcie 6–11 m od home. Ograniczenie koła: składowa prędkości na zewnątrz przy |q| ≥ ρ odjęta (ślizg po krawędzi),
pozycja rzutowana do koła. Rodziny (otwarte = tor nie zależy od stanu drona):
  postoj     (otwarta) — do najbliższego punktu krawędzi z v_max, potem postój;
  wahadlo    (otwarta) — po średnicy o losowym kierunku (start na tej średnicy 6–11 m od home), zawrót na krawędzi;
  odcinki    (otwarta) — odcinki losowe 1–10 s, kierunek losowy, prędkość v_max, zawrót (odbicie radialne) przy krawędzi;
  krazenie   (otwarta) — do krawędzi, potem po krawędzi z v_max, kierunek losowy ±;
  ucieczka   (zamknięta) — od drona z v_max, ślizg po krawędzi;
  podejscie  (zamknięta) — ku dronowi z v_max;
  nagonka    (zamknięta) — ku dronowi, gdy dron dalej od home niż intruz, inaczej radialnie na krawędź;
  tor        (otwarta) — 30 odcinków po 10 s (kierunek, ułamek v_max) z parametrów (szukanie).
"""
import numpy as np

RHO, Z_I, DT = 11.0, -10.0, 0.05
RODZINY = ("postoj", "wahadlo", "odcinki", "krazenie", "ucieczka", "podejscie", "nagonka")
OTWARTE = ("postoj", "wahadlo", "odcinki", "krazenie", "tor")


def _start(rng, B):
    r = rng.uniform(6.0, 11.0, B); a = rng.uniform(-np.pi, np.pi, B)
    return np.stack([r * np.cos(a), r * np.sin(a)], 1)


def _kolo(q, v):
    """Ślizg po krawędzi: odjęcie składowej na zewnątrz przy |q| ≥ ρ; rzut do koła."""
    r = np.linalg.norm(q, axis=1, keepdims=True)
    u = q / np.maximum(r, 1e-9)
    out = (v * u).sum(1, keepdims=True)
    v = np.where((r >= RHO - 1e-9) & (out > 0), v - out * u, v)
    qn = q + v * DT
    rn = np.linalg.norm(qn, axis=1, keepdims=True)
    qn = np.where(rn > RHO, qn * (RHO / rn), qn)
    return qn


class Intruz:
    def __init__(self, rodzina, B, vmax, rng, param=None):
        self.r, self.B, self.vmax, self.rng = rodzina, B, vmax, rng
        self.t = 0.0
        if rodzina == "wahadlo":
            a = rng.uniform(-np.pi, np.pi, B)
            self.u = np.stack([np.cos(a), np.sin(a)], 1)
            s = rng.uniform(6.0, 11.0, B) * rng.choice([-1.0, 1.0], B)
            self.q = self.u * s[:, None]
            self.kier = -np.sign(s)[:, None]
        elif rodzina == "tor":
            P = np.asarray(param)                     # (B, 2 + 60): kąt startu, r startu (6–11), 30 × (kąt, ułamek v)
            a0, r0 = P[:, 0], 6.0 + 5.0 / (1 + np.exp(-P[:, 1]))
            self.q = np.stack([r0 * np.cos(a0), r0 * np.sin(a0)], 1)
            self.seg_a = P[:, 2:32]; self.seg_f = 1 / (1 + np.exp(-P[:, 32:62]))
        else:
            self.q = _start(rng, B)
        if rodzina == "odcinki":
            self._nowy_odc(np.ones(B, bool))
        if rodzina == "krazenie":
            self.zn = rng.choice([-1.0, 1.0], B)

    def _nowy_odc(self, m):
        n = int(m.sum())
        a = self.rng.uniform(-np.pi, np.pi, n)
        if not hasattr(self, "dir"):
            self.dir = np.zeros((self.B, 2)); self.left = np.zeros(self.B)
        self.dir[m] = np.stack([np.cos(a), np.sin(a)], 1)
        self.left[m] = self.rng.uniform(1.0, 10.0, n)

    def pos3(self):
        return np.concatenate([self.q, np.full((self.B, 1), Z_I)], 1)

    def krok(self, p_drona):
        q, B, vm = self.q, self.B, self.vmax
        r = np.linalg.norm(q, axis=1, keepdims=True)
        u = q / np.maximum(r, 1e-9)
        if self.r == "postoj":
            v = np.where(r < RHO - 1e-6, u * vm, 0.0)
        elif self.r == "wahadlo":
            proj = (q * self.u).sum(1, keepdims=True)
            self.kier = np.where(proj * self.kier >= RHO - 1e-6, -self.kier, self.kier)
            v = self.u * self.kier * vm
        elif self.r == "odcinki":
            self.left -= DT
            self._nowy_odc(self.left <= 0)
            out = (self.dir * u).sum(1, keepdims=True)
            odb = (r >= RHO - 1e-6) & (out > 0)
            self.dir = np.where(odb, self.dir - 2 * out * u, self.dir)
            v = self.dir * vm
        elif self.r == "krazenie":
            tan = np.stack([-u[:, 1], u[:, 0]], 1) * self.zn[:, None]
            v = np.where(r < RHO - 1e-6, u * vm, tan * vm)
        elif self.r in ("ucieczka", "podejscie", "nagonka"):
            dd = q - p_drona[:, :2]
            ud = dd / np.maximum(np.linalg.norm(dd, axis=1, keepdims=True), 1e-9)
            if self.r == "ucieczka":
                v = ud * vm
            elif self.r == "podejscie":
                v = -ud * vm
            else:
                rd = np.linalg.norm(p_drona[:, :2], axis=1, keepdims=True)
                v = np.where(rd > r, -ud * vm, u * vm)
        elif self.r == "tor":
            i = min(int(self.t // 10.0), 29)
            a, f = self.seg_a[:, i], self.seg_f[:, i]
            v = np.stack([np.cos(a), np.sin(a)], 1) * (f * vm)[:, None]
        self.q = _kolo(q, v)
        self.t += DT
        return self.pos3()
