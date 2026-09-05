# FREEZE_NET — zamrożenie wag ramion lecących (ANEKS_NET-1 §4)

LiquidPatrol · noga sieci · sesja 2 · pierwszy commit S2. Od tej chwili wymienione wagi NIETYKALNE aż do lotów pozycji 4 (N6: `weights_sha` w manifeście, zero uczenia w locie).

## tiny-MLP — ZAMROŻONE (PASS bramki N3(i) = 21/24 rolloutów, reguła ANEKS_NET-1 §2)

- Plik wag: `results/NET/mlp/model.npz`
- **weights_sha (sha256, pełny):** `1d1900235724e938...` (pełny hash w repo; skrót do manifestu lotów)
- Architektura: tiny-MLP, okno k=5 (40 wejść), 2×32 ukryte, głowa tanh×V_MAX + clip_v; **2467 parametrów**.
- Config treningu (ZAMROŻONY N-B1, `net/train_config.json` sekcja `mlp`): hidden=32, k=5, lr=0.001, batch=512, epochs=80, seed=1, grad_clip=5.0, Adam(0.9,0.999). Selekcja checkpointu: VAL (ziarno 2), najlepsza epoka 78/80.
- Preprocessing wejścia (adapter, features.py nietknięte): clip_age(≤1.0) + standaryzacja statystykami TRAIN (mean/std zapisane w `model.npz`).
- Wynik S1: val_mse 0.0308, TEST RMS med 0.179; bramka 21/24 (per rollout) = PASS.

## NCP-20 — ZAMROŻONE (PASS bramki N3(i) = 24/24 rolloutów po retrainie N-B3, ANEKS_NET-1 §3)

- Plik wag: `results/NET/ncp/model.npz`
- **weights_sha (sha256, pełny):** `0337d5eae1471bb99ef329d939be195a9ea846017045b8ddac22f3d97bc2ae36`
- Architektura: NCP-20 (CfC closed-form, ~20 neuronów), głowa tanh×V_MAX + clip_v; **1903 parametry**.
- Config N-B3 (ZAMROŻONY, `net/train_config.json` sekcja `ncp`): hidden=20, bb=20, lr=0.003, epochs=1000, lr_schedule milestones[500,800] gamma 0.5, seed=1, grad_clip=5.0, Adam. Selekcja: VAL (ziarno 2), najlepsza epoka 984/1000. DAgger NIE użyty (VAL-proxy seed 2 = 12/12 ⇒ skip).
- Preprocessing: clip_age(≤1.0)+standaryzacja TRAIN (w model.npz).
- Wynik S2: val_mse 0.0485 (S1 0.141 underfit → naprawa capu epok), TEST RMS med 0.215; bramka 24/24 = PASS. TEST dotknięty 2× (S1+S2, ostatni).

## Pełne hashe (weryfikowalne)

```
ncp/model.npz : 0337d5eae1471bb99ef329d939be195a9ea846017045b8ddac22f3d97bc2ae36
mlp/model.npz : 1d1900235724e938557cf9c614e39935483d51edd75f174cce7c8fb3d72f2270
```
