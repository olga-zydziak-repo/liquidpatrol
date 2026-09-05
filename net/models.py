#!/usr/bin/env python3
"""net/models.py — architektury nogi sieci (PRE_NET N1). Czysty numpy (brak torch/jax w środowisku).

(a) NCP-20 — komórka CfC (closed-form continuous-time), ~20 neuronów, wejście 8 cech/tick, stan ukryty
    ciągły w epizodzie, reset na starcie epizodu. Głowa: tanh × V_MAX.
(b) tiny-MLP — 8 cech w oknie k=5 (40 wejść, zero-padding startu), 2×32 ukryte, tanh. Głowa: tanh × V_MAX.

Głowa tanh×V_MAX = saturacja architektoniczna ⇒ |v|≤V_MAX ZAWSZE (kontrakt 10⁴, N1/N3(iii)); `clip_v`
kontrolera to druga szelka. Cel = cmd_v_ned (3D), strata MSE (N2).

CfC (forma zamknięta, per krok dt=1): bb=tanh(Wb·[x,h]+bb0); g=tanh(Wg·bb+bg); hh=tanh(Wh·bb+bh);
gate=σ(−(Wt·bb+bt)); h'=gate⊙g+(1−gate)⊙hh; y=tanh(Wo·h'+bo)·V_MAX. Bramka czasu gate interpoluje
między dwiema głowami (g,hh) — struktura CfC; dt zwinięte w wagach. Backprop ręczny (BPTT wsadowy).
"""
import numpy as np


def _tanh(z):
    return np.tanh(z)


def _dtanh(a):            # pochodna tanh wyrażona przez wyjście a=tanh(z)
    return 1.0 - a * a


def _sig(z):
    return 1.0 / (1.0 + np.exp(-z))


# ---------------------------------------------------------------- tiny-MLP
class TinyMLP:
    ARM = "mlp"
    K = 5                          # okno ticków
    IN = 8

    def __init__(self, vmax, hidden=32, seed=0):
        self.vmax = float(vmax)
        self.h = hidden
        self.input_mean = np.zeros(self.IN)      # metadane preprocessingu (do rolloutu/lotu); forward oczekuje już-znorm.
        self.input_std = np.ones(self.IN)
        rng = np.random.RandomState(seed)
        din = self.K * self.IN     # 40
        def he(a, b):
            return (rng.randn(a, b) * np.sqrt(2.0 / a)).astype(np.float64)
        self.W1 = he(din, hidden); self.b1 = np.zeros(hidden)
        self.W2 = he(hidden, hidden); self.b2 = np.zeros(hidden)
        self.W3 = (rng.randn(hidden, 3) * np.sqrt(1.0 / hidden)); self.b3 = np.zeros(3)

    def param_count(self):
        return sum(p.size for p in (self.W1, self.b1, self.W2, self.b2, self.W3, self.b3))

    def forward(self, X, cache=False):
        """X:(N,40) → y:(N,3). cache=True zwraca (y, cache) do backprop."""
        z1 = X @ self.W1 + self.b1; a1 = _tanh(z1)
        z2 = a1 @ self.W2 + self.b2; a2 = _tanh(z2)
        z3 = a2 @ self.W3 + self.b3; a3 = _tanh(z3)
        y = a3 * self.vmax
        if cache:
            return y, (X, a1, a2, a3)
        return y

    def grads(self, cache, dY):
        """dY:(N,3) gradient straty po y. Zwraca dict grad + skala 1/N już wliczona przez wywołującego."""
        X, a1, a2, a3 = cache
        da3 = dY * self.vmax
        dz3 = da3 * _dtanh(a3)
        gW3 = a2.T @ dz3; gb3 = dz3.sum(0)
        da2 = dz3 @ self.W3.T; dz2 = da2 * _dtanh(a2)
        gW2 = a1.T @ dz2; gb2 = dz2.sum(0)
        da1 = dz2 @ self.W2.T; dz1 = da1 * _dtanh(a1)
        gW1 = X.T @ dz1; gb1 = dz1.sum(0)
        return {"W1": gW1, "b1": gb1, "W2": gW2, "b2": gb2, "W3": gW3, "b3": gb3}

    def params(self):
        return {"W1": self.W1, "b1": self.b1, "W2": self.W2, "b2": self.b2, "W3": self.W3, "b3": self.b3}

    def set_params(self, d):
        for k, v in d.items():
            getattr(self, k)[...] = v

    def save(self, path):
        np.savez(path, arm="mlp", vmax=self.vmax, h=self.h,
                 input_mean=self.input_mean, input_std=self.input_std, **self.params())

    @staticmethod
    def load(path):
        d = np.load(path, allow_pickle=True)
        m = TinyMLP(float(d["vmax"]), hidden=int(d["h"]))
        m.set_params({k: d[k] for k in ("W1", "b1", "W2", "b2", "W3", "b3")})
        m.input_mean = d["input_mean"]; m.input_std = d["input_std"]
        return m


# ---------------------------------------------------------------- NCP-20 (CfC)
class NCP20:
    ARM = "ncp"
    IN = 8

    def __init__(self, vmax, hidden=20, bb=20, seed=0):
        self.vmax = float(vmax)
        self.H = hidden
        self.BB = bb
        self.input_mean = np.zeros(self.IN)      # metadane preprocessingu (rollout/lot); forward oczekuje już-znorm.
        self.input_std = np.ones(self.IN)
        rng = np.random.RandomState(seed)
        cin = self.IN + hidden
        def w(a, b, g=1.0):
            return (rng.randn(a, b) * np.sqrt(g / a)).astype(np.float64)
        self.Wb = w(cin, bb); self.bb0 = np.zeros(bb)
        self.Wg = w(bb, hidden); self.bg = np.zeros(hidden)
        self.Wh = w(bb, hidden); self.bh = np.zeros(hidden)
        self.Wt = w(bb, hidden); self.bt = np.zeros(hidden)
        self.Wo = w(hidden, 3, g=1.0); self.bo = np.zeros(3)

    def param_count(self):
        return sum(p.size for p in self.params().values())

    def params(self):
        return {"Wb": self.Wb, "bb0": self.bb0, "Wg": self.Wg, "bg": self.bg,
                "Wh": self.Wh, "bh": self.bh, "Wt": self.Wt, "bt": self.bt,
                "Wo": self.Wo, "bo": self.bo}

    def set_params(self, d):
        for k, v in d.items():
            getattr(self, k)[...] = v

    def step_np(self, x, h):
        """Jeden krok: x:(B,8), h:(B,H) → (y:(B,3), h':(B,H), cache). Używane też w rolloucie (B=1)."""
        concat = np.concatenate([x, h], axis=1)
        zb = concat @ self.Wb + self.bb0; bb = _tanh(zb)
        g = _tanh(bb @ self.Wg + self.bg)
        hh = _tanh(bb @ self.Wh + self.bh)
        zt = bb @ self.Wt + self.bt; gate = _sig(zt)
        h2 = gate * g + (1.0 - gate) * hh
        zo = h2 @ self.Wo + self.bo; a_o = _tanh(zo)
        y = a_o * self.vmax
        cache = (concat, bb, g, hh, gate, h2, a_o, h)
        return y, h2, cache

    def forward_seq(self, X, mask):
        """X:(T,B,8), mask:(T,B) → Y:(T,B,3), lista cache per t. Stan h zerowany na start (reset epizodu)."""
        T, B, _ = X.shape
        h = np.zeros((B, self.H))
        Y = np.zeros((T, B, 3))
        caches = []
        for t in range(T):
            y, h, c = self.step_np(X[t], h)
            Y[t] = y
            caches.append(c)
        return Y, caches

    def grads_seq(self, caches, dY, mask):
        """BPTT wsadowy. dY:(T,B,3) (już zważone/zmaskowane), mask:(T,B). Zwraca dict grad."""
        T = len(caches)
        g = {k: np.zeros_like(v) for k, v in self.params().items()}
        B = dY.shape[1]
        dh_next = np.zeros((B, self.H))
        for t in range(T - 1, -1, -1):
            concat, bb, gg, hh, gate, h2, a_o, h_prev = caches[t]
            m = mask[t][:, None]
            # wyjście
            da_o = (dY[t] * self.vmax)
            dzo = da_o * _dtanh(a_o)
            g["Wo"] += h2.T @ dzo
            g["bo"] += dzo.sum(0)
            dh2 = dzo @ self.Wo.T + dh_next          # gradient do h' (z wyjścia + z następnego kroku)
            dh2 = dh2 * m                             # maska paddingu
            # h2 = gate*g + (1-gate)*hh
            dgate = dh2 * (gg - hh)
            dgg = dh2 * gate
            dhh = dh2 * (1.0 - gate)
            dzt = dgate * gate * (1.0 - gate)         # sigmoid'
            dzg = dgg * _dtanh(gg)
            dzh = dhh * _dtanh(hh)
            g["Wg"] += bb.T @ dzg; g["bg"] += dzg.sum(0)
            g["Wh"] += bb.T @ dzh; g["bh"] += dzh.sum(0)
            g["Wt"] += bb.T @ dzt; g["bt"] += dzt.sum(0)
            dbb = dzg @ self.Wg.T + dzh @ self.Wh.T + dzt @ self.Wt.T
            dzb = dbb * _dtanh(bb)
            g["Wb"] += concat.T @ dzb; g["bb0"] += dzb.sum(0)
            dconcat = dzb @ self.Wb.T
            dh_prev = dconcat[:, self.IN:]            # część gradientu wracająca do h poprzedniego kroku
            dh_next = dh_prev
        return g

    def save(self, path):
        np.savez(path, arm="ncp", vmax=self.vmax, H=self.H, BB=self.BB,
                 input_mean=self.input_mean, input_std=self.input_std, **self.params())

    @staticmethod
    def load(path):
        d = np.load(path, allow_pickle=True)
        m = NCP20(float(d["vmax"]), hidden=int(d["H"]), bb=int(d["BB"]))
        m.set_params({k: d[k] for k in ("Wb", "bb0", "Wg", "bg", "Wh", "bh", "Wt", "bt", "Wo", "bo")})
        m.input_mean = d["input_mean"]; m.input_std = d["input_std"]
        return m
