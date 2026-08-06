"""p2/protocol.py — protokół WYROCZNI (§2 PRE_P2), deterministyczny z seedów.

Gęste GT (box per-klatka) = detekcje wyroczni. Nakładamy:
  (a) szum obserwacyjny σ jako frakcja rozmiaru boxa (per-oś);
  (b) maski nieregularności: Bernoulli p (frakcja miss) + burst L (długość dziury) — model
      Gilbert-Elliott 2-stanowy (stacjonarny miss-frac = p, średnia długość dziury = L);
  (c) naturalne dziury exist=0 zawsze = miss („duch G2");
  (d) strumień wejścia 5-dim: (cx,cy,w,h, age) = ostatnia obserwacja + wiek [klatki] (kanał LiquidSight).
Wszystko odtwarzalne: RandomState(seed ⊕ hash(nazwa_sekwencji)).
"""
from __future__ import annotations
import numpy as np


def _seq_rng(seed, name):
    h = (hash(name) ^ (seed * 2654435761)) & 0x7FFFFFFF
    return np.random.RandomState(h)


def gilbert_elliott_observed(exist, p, L, rng):
    """Zwraca observed[T] bool. 2-stany: OBS/MISS. a=P(obs→miss)=(1/L)·p/(1−p), b=P(miss→obs)=1/L.
    Stacjonarnie: miss-frac=p, średnia dziura=L. Naturalne exist=0 wymuszają MISS."""
    T = len(exist)
    b = 1.0 / max(L, 1)
    a = b * (p / (1.0 - p)) if p < 1.0 else 1.0
    obs = np.ones(T, dtype=bool)
    state_miss = False
    for t in range(T):
        if state_miss:
            state_miss = not (rng.rand() < b)      # zostań w miss z prawd. 1-b
        else:
            state_miss = (rng.rand() < a)          # wejdź w miss z prawd. a
        obs[t] = not state_miss
    obs &= exist                                   # naturalne dziury: brak detekcji
    return obs


def add_noise(boxes, sigma, rng):
    """Szum σ·rozmiar per-oś: cx±N(0,σw), cy±N(0,σh), w±N(0,σw), h±N(0,σh). NaN→NaN."""
    out = boxes.copy()
    T = boxes.shape[0]
    valid = ~np.isnan(boxes[:, 0])
    for t in range(T):
        if not valid[t]:
            continue
        cx, cy, w, h = boxes[t]
        out[t, 0] = cx + rng.randn() * sigma * w
        out[t, 1] = cy + rng.randn() * sigma * h
        out[t, 2] = max(1e-4, w + rng.randn() * sigma * w)
        out[t, 3] = max(1e-4, h + rng.randn() * sigma * h)
    return out


def build_input_stream(noisy, observed):
    """Strumień 5-dim: [cx,cy,w,h,age]. Trzyma ostatnią OBSERWOWANĄ detekcję; age = klatki od niej.
    Przed pierwszą obserwacją: valid_from wskazuje start. Zwraca X[T,5], valid_from(int)."""
    T = noisy.shape[0]
    X = np.zeros((T, 5), dtype=np.float64)
    last = None; last_t = None; valid_from = None
    for t in range(T):
        if observed[t] and not np.isnan(noisy[t, 0]):
            last = noisy[t, :4].copy(); last_t = t
            if valid_from is None:
                valid_from = t
        if last is not None:
            X[t, :4] = last
            X[t, 4] = float(t - last_t)            # age w klatkach
        else:
            X[t, 4] = np.nan
    return X, (valid_from if valid_from is not None else T)


def make_episode(seq, sigma, p, L, seed):
    """seq: dict z io_labels (boxes[T,4], exist[T], name). Zwraca protokół dla jednej realizacji."""
    rng = _seq_rng(seed, seq["name"])
    boxes, exist = seq["boxes"], seq["exist"]
    observed = gilbert_elliott_observed(exist, p, L, rng)
    noisy = add_noise(boxes, sigma, rng)
    X, valid_from = build_input_stream(noisy, observed)
    return {"name": seq["name"], "gt": boxes, "exist": exist, "observed": observed,
            "noisy": noisy, "X": X, "valid_from": valid_from,
            "params": {"sigma": sigma, "p": p, "L": L, "seed": seed}}


def hole_segments(observed, valid_from=0):
    """Segmenty dziur (kolejne nie-obserwowane) po valid_from — do ewaluacji predykcji."""
    T = len(observed); segs = []; s = None
    for t in range(valid_from, T):
        if not observed[t]:
            if s is None: s = t
        else:
            if s is not None: segs.append((s, t)); s = None
    if s is not None: segs.append((s, T))
    return segs


if __name__ == "__main__":
    # samo-test na syntetycznej trajektorii CV (bez etykiet)
    T = 300
    t = np.arange(T)
    cx = 0.3 + 0.001 * t; cy = 0.5 + 0.0005 * t
    boxes = np.stack([cx, cy, np.full(T, 0.05), np.full(T, 0.04)], axis=1)
    exist = np.ones(T, bool); exist[100:120] = False        # naturalna dziura
    seq = {"name": "synth_cv", "boxes": boxes, "exist": exist}
    ep = make_episode(seq, sigma=0.05, p=0.5, L=25, seed=0)
    obs_frac = ep["observed"].mean()
    segs = hole_segments(ep["observed"], ep["valid_from"])
    mean_hole = np.mean([e - s for s, e in segs]) if segs else 0
    print(f"[protocol] samo-test CV: obs_frac={obs_frac:.3f} (~1-p oczek. 0.5), "
          f"dziur={len(segs)}, śr.dł={mean_hole:.1f} (L=25), valid_from={ep['valid_from']}")
    print(f"[protocol] X[130]={np.round(ep['X'][130],3)} (age rośnie w dziurze), "
          f"NaN_before_first={np.isnan(ep['X'][0,4])}")
    print("[protocol] OK")
