"""p2/learned.py — ramiona UCZONE (§5 PRE_P2). Interfejs jak analityczne: run(ep)->est+pred.

Rdzenie (parytet ~30k ±2%): GRU+Δt, CfC (continuous-time cell), Mamba-S6 (czysto-PyTorch, A4:
jeden wspólny rdzeń dla time-blind i +Δt — różnica tylko w podaniu age). latent-ODE opcjonalny.
Wejście X[T,5]=(cx,cy,w,h,age). Wyjście per klatka: estymata 4 + predykcje 4×|H|.
UWAGA: trening w train.py DOPIERO po commicie zamrażającym (A2). Tu tylko definicje + parytet.
"""
from __future__ import annotations
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".p2deps"))
import torch, torch.nn as nn, torch.nn.functional as F
import numpy as np

HORIZONS = [13, 25, 50]
OUT = 4 * (1 + len(HORIZONS))     # estymata + predykcje/horyzont


# ------------------------------ rdzenie -------------------------------------
class GRUCore(nn.Module):
    def __init__(self, h=94):
        super().__init__(); self.rnn = nn.GRU(5, h, batch_first=True); self.hdim = h
    def forward(self, x): y, _ = self.rnn(x); return y


class CfCCore(nn.Module):
    """Kompaktowy CfC (closed-form continuous-time): brama a(t) sterowana czasem (age).
    h = (1-a)⊙h + a⊙g, a = σ(Wa[x,h] - softplus(τ)·Δt), g = tanh(Wg[x,h]). Δt z age (kol. 5)."""
    def __init__(self, h=80):
        super().__init__(); self.hdim = h
        self.g = nn.Linear(5 + h, h); self.a = nn.Linear(5 + h, h)
        self.tau = nn.Parameter(torch.zeros(h))
    def forward(self, x):
        B, T, _ = x.shape; h = x.new_zeros(B, self.hdim); ys = []
        for t in range(T):
            xt = x[:, t]; dt = xt[:, 4:5].clamp(0, 100) / 25.0        # age→sekundy
            z = torch.cat([xt, h], -1)
            g = torch.tanh(self.g(z))
            a = torch.sigmoid(self.a(z) - F.softplus(self.tau) * dt)
            h = (1 - a) * h + a * g; ys.append(h)
        return torch.stack(ys, 1)


class MambaS6Core(nn.Module):
    """Selektywny SSM (S6) — referencja czysto-PyTorch (A4). time_aware: age moduluje Δ.
    Jeden rdzeń dla time-blind (time_aware=False) i +Δt (True)."""
    def __init__(self, d_model=48, d_state=8, time_aware=True):
        super().__init__(); self.hdim = d_model; self.N = d_state; self.time_aware = time_aware
        self.in_proj = nn.Linear(5, d_model)
        self.dt_proj = nn.Linear(d_model, d_model)
        self.x_proj = nn.Linear(d_model, 2 * d_state)      # B,C zależne od wejścia
        self.A_log = nn.Parameter(torch.log(torch.arange(1, d_state + 1).float().repeat(d_model, 1)))
        self.D = nn.Parameter(torch.ones(d_model))
    def forward(self, x):
        B, T, _ = x.shape
        age = x[:, :, 4:5]
        u = self.in_proj(x)                                # (B,T,d)
        A = -torch.exp(self.A_log)                         # (d,N)
        dt = F.softplus(self.dt_proj(u))                   # (B,T,d)
        if self.time_aware:
            dt = dt * (1.0 + age.clamp(0, 100) / 25.0)     # +Δt: skala czasem obserwacji
        BC = self.x_proj(u); Bm, Cm = BC[..., :self.N], BC[..., self.N:]   # (B,T,N)
        h = x.new_zeros(B, self.hdim, self.N); ys = []
        for t in range(T):
            dA = torch.exp(dt[:, t].unsqueeze(-1) * A)                     # (B,d,N)
            dB = dt[:, t].unsqueeze(-1) * Bm[:, t].unsqueeze(1)           # (B,d,N)
            h = dA * h + dB * u[:, t].unsqueeze(-1)
            y = (h * Cm[:, t].unsqueeze(1)).sum(-1) + self.D * u[:, t]     # (B,d)
            ys.append(y)
        return torch.stack(ys, 1)


class LatentODECore(nn.Module):
    """Mały latent-ODE: z całkowany Eulerem o Δt (age) przez ode-func, aktualizowany obserwacją."""
    def __init__(self, d=68, h_ode=210):
        super().__init__(); self.hdim = d
        self.enc = nn.Linear(5, d)
        self.ode = nn.Sequential(nn.Linear(d, h_ode), nn.Tanh(), nn.Linear(h_ode, d))
    def forward(self, x):
        B, T, _ = x.shape; z = x.new_zeros(B, self.hdim); ys = []
        for t in range(T):
            dt = (x[:, t, 4:5].clamp(0, 100) / 25.0)
            z = z + dt * self.ode(z)                 # Euler o Δt (age)
            z = z + torch.tanh(self.enc(x[:, t]))     # aktualizacja obserwacją (last_obs+age)
            ys.append(z)
        return torch.stack(ys, 1)


class LearnedArm(nn.Module):
    def __init__(self, core, name):
        super().__init__(); self.core = core; self.name = name
        self.head = nn.Linear(core.hdim, OUT)
    def forward(self, x): return self.head(self.core(x))

    @torch.no_grad()
    def run(self, ep):
        x = torch.tensor(np.nan_to_num(ep["X"], nan=0.0)[None], dtype=torch.float32)
        out = self(x)[0].numpy()                    # [T, OUT]
        est = out[:, :4]
        pred = out[:, 4:].reshape(-1, len(HORIZONS), 4)
        return {"est": est, "pred": pred}


def build(name):
    if name == "GRU+dt":       return LearnedArm(GRUCore(94), name)
    if name == "CfC":          return LearnedArm(CfCCore(116), name)
    if name == "Mamba-notime": return LearnedArm(MambaS6Core(150, 8, time_aware=False), name)
    if name == "Mamba+dt":     return LearnedArm(MambaS6Core(150, 8, time_aware=True), name)
    if name == "latent-ODE":   return LearnedArm(LatentODECore(68, 210), name)
    raise ValueError(name)


LEARNED = ["GRU+dt", "CfC", "Mamba-notime", "Mamba+dt", "latent-ODE"]


def nparams(m): return sum(p.numel() for p in m.parameters())


if __name__ == "__main__":
    budget = 30000; lo, hi = int(budget * 0.98), int(budget * 1.02)
    x = torch.randn(2, 60, 5)
    print(f"[learned] parytet ±2%: {lo}..{hi}")
    for nm in LEARNED:
        m = build(nm); n = nparams(m); y = m(x)
        ok = lo <= n <= hi
        print(f"  {nm:13s} params={n:6d} {'OK' if ok else 'POZA PARYTETEM'}  out={tuple(y.shape)}")
