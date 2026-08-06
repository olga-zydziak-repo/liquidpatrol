"""p2/bench_core.py — R3 benchmark rdzenia ~30k param (parytet §5). CPU = konserwatywny bound.

Buduje mały GRU (wejście 5-dim, wyjście: estymata 4 + predykcje na horyzontach) ≈30k param,
mierzy czas forward+backward na skali treningu (289k timestepów/epokę) → czas/epokę, /run.
"""
from __future__ import annotations
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".p2deps"))
import torch, torch.nn as nn

HORIZONS = [13, 25, 50]           # {0.5,1,2}s @25fps
HIDDEN = 100                      # ~30k param (parytet ±2%)


class Core(nn.Module):
    def __init__(self, hidden=HIDDEN, n_h=len(HORIZONS)):
        super().__init__()
        self.gru = nn.GRU(5, hidden, batch_first=True)
        self.head = nn.Linear(hidden, 4 * (1 + n_h))   # estymata + predykcje/horyzont
    def forward(self, x):
        y, _ = self.gru(x)
        return self.head(y)


def count_params(m):
    return sum(p.numel() for p in m.parameters())


def main():
    torch.manual_seed(0)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    m = Core().to(dev)
    n = count_params(m)
    print(f"[bench] params={n} (cel ~30k, parytet ±2% => {int(30000*0.98)}..{int(30000*1.02)})  dev={dev}")
    opt = torch.optim.AdamW(m.parameters(), lr=1e-3)
    lossf = nn.SmoothL1Loss()
    # skala: 160 seq x ~1808 kl. Batch po sekwencjach, okna 200 kl (BPTT).
    B, Tw = 32, 200
    total_tsteps = 160 * 1808
    steps = total_tsteps // (B * Tw)          # kroków optymalizatora / epokę
    x = torch.randn(B, Tw, 5, device=dev)
    tgt = torch.randn(B, Tw, 4 * (1 + len(HORIZONS)), device=dev)
    # rozgrzewka
    for _ in range(2):
        opt.zero_grad(); loss = lossf(m(x), tgt); loss.backward(); opt.step()
    t0 = time.time()
    for _ in range(steps):
        opt.zero_grad(); loss = lossf(m(x), tgt); loss.backward(); opt.step()
    dt = time.time() - t0
    per_epoch = dt
    print(f"[bench] {steps} krokow/epoke (B={B},Tw={Tw}) = {total_tsteps} timestepow -> "
          f"{per_epoch:.2f}s/epoke")
    for E in (100, 150):
        print(f"[bench]   {E} epok = {per_epoch*E/60:.1f} min/run   "
              f"(25 runow = {per_epoch*E*25/3600:.1f} h)")
    print("[bench] uwaga: CPU = gorny bound; GPU szybszy. Wymiarowanie seedow konserwatywne.")


if __name__ == "__main__":
    main()
