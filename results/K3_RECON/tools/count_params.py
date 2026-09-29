#!/usr/bin/env python3
"""results/K3_RECON/tools/count_params.py — R2.4 (PROMPT_K3_S0): budżet parametrów kontrolerów.

Zlicza parametry z npz (net/frozen) + wzory kandydatów kontrol:
  GRU (1 bias/gate, jak konwencja numpy repo): p(h) = 3*(8h + h^2 + h) + (3h + 3) = 3h^2 + 30h + 3
  MLP okno k=20 (din=160, 2 warstwy ukryte jak TinyMLP): p(h) = (160h+h) + (h^2+h) + (3h+3) = h^2 + 165h + 3
Kryterium promptu: |params - params_NCP| <= 5%. Offline, zero SITL, zero treningu.
"""
import numpy as np, os
ROOT = "/home/olga/projects/liquidpatrol"
META = {"input_mean", "input_std", "vmax", "arm", "H", "BB", "h", "K", "k"}  # metadane npz, nie wagi

def npz_params(path):
    d = np.load(path)
    tot = int(sum(d[k].size for k in d.files if k not in META))
    return tot, {k: list(d[k].shape) for k in d.files if k not in META}

ncp, ncp_sh = npz_params(os.path.join(ROOT, "net/frozen/ncp.npz"))
mlp, mlp_sh = npz_params(os.path.join(ROOT, "net/frozen/mlp.npz"))
print(f"ncp.npz: {ncp} parametrów  {ncp_sh}")
print(f"mlp.npz: {mlp} parametrów  {mlp_sh}")
lo, hi = 0.95 * ncp, 1.05 * ncp
print(f"\nbudżet 5% wokół NCP: [{lo:.0f}, {hi:.0f}]")
print("\nGRU p(h)=3h^2+30h+3:")
for h in range(18, 24):
    p = 3*h*h + 30*h + 3
    print(f"  h={h}: {p}  ({(p-ncp)/ncp:+.1%})  {'OK' if lo<=p<=hi else '--'}")
print("\nMLP k=20 p(h)=h^2+165h+3 (din=160):")
for h in range(9, 15):
    p = h*h + 165*h + 3
    print(f"  h={h}: {p}  ({(p-ncp)/ncp:+.1%})  {'OK' if lo<=p<=hi else '--'}"
          + (f"  [vs mlp.npz {(p-mlp)/mlp:+.1%}]" if h in (13,14) else ""))
