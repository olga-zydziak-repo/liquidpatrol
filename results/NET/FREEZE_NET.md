# FREEZE_NET — zamrożenie wag ramion lecących (ANEKS_NET-1 §4)

LiquidPatrol · noga sieci · sesja 2 · pierwszy commit S2. Od tej chwili wymienione wagi NIETYKALNE aż do lotów pozycji 4 (N6: `weights_sha` w manifeście, zero uczenia w locie).

## tiny-MLP — ZAMROŻONE (PASS bramki N3(i) = 21/24 rolloutów, reguła ANEKS_NET-1 §2)

- Plik wag: `results/NET/mlp/model.npz`
- **weights_sha (sha256, pełny):** `1d1900235724e938...` (pełny hash w repo; skrót do manifestu lotów)
- Architektura: tiny-MLP, okno k=5 (40 wejść), 2×32 ukryte, głowa tanh×V_MAX + clip_v; **2467 parametrów**.
- Config treningu (ZAMROŻONY N-B1, `net/train_config.json` sekcja `mlp`): hidden=32, k=5, lr=0.001, batch=512, epochs=80, seed=1, grad_clip=5.0, Adam(0.9,0.999). Selekcja checkpointu: VAL (ziarno 2), najlepsza epoka 78/80.
- Preprocessing wejścia (adapter, features.py nietknięte): clip_age(≤1.0) + standaryzacja statystykami TRAIN (mean/std zapisane w `model.npz`).
- Wynik S1: val_mse 0.0308, TEST RMS med 0.179; bramka 21/24 (per rollout) = PASS.

## NCP-20 — NIE zamrożone (ścieżka sesji 2 wg ANEKS_NET-1 §3)

NCP FAIL bramki w S1 (underfit). Sesja 2: N-B3 (retrain cap×5 + lr sched) → [DAgger] → TEST (2. i ostatni). Zamrożenie NCP nastąpi w RAPORT_NET_S2/STOP-N2 tylko jeśli przejdzie bramkę §2. Jeśli FAIL — NCP odpada (§3.4), leci sam MLP.

## Pełne hashe (weryfikowalne)

```
mlp/model.npz : 1d1900235724e938557cf9c614e39935483d51edd75f174cce7c8fb3d72f2270
```
