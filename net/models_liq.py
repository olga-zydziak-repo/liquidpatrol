#!/usr/bin/env python3
"""net/models_liq.py — kontrole nogi LIQ (PRE_LIQ §1/§2): GRU21 i MLPk20. NOWY plik; net/models.py NIETKNIĘTY.

GRU21 — kontrola rekurencji, budżet 1956 parametrów (RECON R2.4: p(h)=3h^2+30h+3, h=21):
  z = sig([x,h]Wz+bz) · r = sig([x,h]Wr+br) · n = tanh([x, r*h]Wn+bn) · h' = (1-z)*n + z*h
  (wariant combined-input, 1 bias/bramkę — konwencja zliczania jak w RECON; r aplikowane do h
  PRZED konkatenacją). Wyjście y = tanh(h'Wo+bo)*vmax — ta sama głowa co NCP20/TinyMLP.
  Init stanu = zera, reset per epizod (wyjątek architektoniczny §2 PRE, lista zamknięta).
  API lustrzane z NCP20 (step_np / forward_seq / grads_seq) — tor sekwencyjny train_ncp 1:1.

MLPk20 — kontrola okna, budżet 1939 parametrów (k=20, din=160, h=11, 2x hidden jak TinyMLP):
  dziedziczy TinyMLP (forward/grads/params bez zmian), nadpisuje K i save/load (arm=mlp20).
  Zero-padding okna na starcie epizodu (wyjątek §2 PRE) — identycznie jak tor okienny k=5.

Gradient-check (numeryczny) w _gradcheck_gru() — dowód poprawności BPTT do raportu S1.
"""
import numpy as np

from net.models import TinyMLP, _tanh, _dtanh, _sig


class GRU21:
    ARM = "gru"
    IN = 8

    def __init__(self, vmax, hidden=21, seed=0):
        self.vmax = float(vmax)
        self.H = hidden
        self.input_mean = np.zeros(self.IN)
        self.input_std = np.ones(self.IN)
        rng = np.random.RandomState(seed)
        cin = self.IN + hidden
        def w(a, b, g=1.0):
            return (rng.randn(a, b) * np.sqrt(g / a)).astype(np.float64)
        self.Wz = w(cin, hidden); self.bz = np.zeros(hidden)
        self.Wr = w(cin, hidden); self.br = np.zeros(hidden)
        self.Wn = w(cin, hidden); self.bn = np.zeros(hidden)
        self.Wo = w(hidden, 3);   self.bo = np.zeros(3)

    def param_count(self):
        return sum(p.size for p in self.params().values())

    def params(self):
        return {"Wz": self.Wz, "bz": self.bz, "Wr": self.Wr, "br": self.br,
                "Wn": self.Wn, "bn": self.bn, "Wo": self.Wo, "bo": self.bo}

    def set_params(self, d):
        for k, v in d.items():
            getattr(self, k)[...] = v

    def step_np(self, x, h):
        """x:(B,8), h:(B,H) → (y:(B,3), h':(B,H), cache)."""
        cz = np.concatenate([x, h], axis=1)
        z = _sig(cz @ self.Wz + self.bz)
        r = _sig(cz @ self.Wr + self.br)
        cn = np.concatenate([x, r * h], axis=1)
        n = _tanh(cn @ self.Wn + self.bn)
        h2 = (1.0 - z) * n + z * h
        a_o = _tanh(h2 @ self.Wo + self.bo)
        y = a_o * self.vmax
        cache = (cz, cn, z, r, n, h2, a_o, h)
        return y, h2, cache

    def forward_seq(self, X, mask):
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
        """BPTT wsadowy, konwencja maskowania jak NCP20.grads_seq (maska na dh2 w kroku t)."""
        T = len(caches)
        g = {k: np.zeros_like(v) for k, v in self.params().items()}
        B = dY.shape[1]
        dh_next = np.zeros((B, self.H))
        for t in range(T - 1, -1, -1):
            cz, cn, z, r, n, h2, a_o, h_prev = caches[t]
            m = mask[t][:, None]
            da_o = dY[t] * self.vmax
            dzo = da_o * _dtanh(a_o)
            g["Wo"] += h2.T @ dzo
            g["bo"] += dzo.sum(0)
            dh2 = dzo @ self.Wo.T + dh_next
            dh2 = dh2 * m
            # h2 = (1-z)*n + z*h_prev
            dz = dh2 * (h_prev - n)
            dn = dh2 * (1.0 - z)
            dh_prev = dh2 * z
            # n = tanh(cn Wn + bn), cn = [x, r*h_prev]
            dzn = dn * _dtanh(n)
            g["Wn"] += cn.T @ dzn; g["bn"] += dzn.sum(0)
            dcn = dzn @ self.Wn.T
            drh = dcn[:, self.IN:]
            dr = drh * h_prev
            dh_prev = dh_prev + drh * r
            # bramki sigmoidowe na cz = [x, h_prev]
            dzz = dz * z * (1.0 - z)
            g["Wz"] += cz.T @ dzz; g["bz"] += dzz.sum(0)
            dh_prev = dh_prev + (dzz @ self.Wz.T)[:, self.IN:]
            dzr = dr * r * (1.0 - r)
            g["Wr"] += cz.T @ dzr; g["br"] += dzr.sum(0)
            dh_prev = dh_prev + (dzr @ self.Wr.T)[:, self.IN:]
            dh_next = dh_prev
        return g

    def save(self, path):
        np.savez(path, arm="gru", vmax=self.vmax, H=self.H,
                 input_mean=self.input_mean, input_std=self.input_std, **self.params())

    @staticmethod
    def load(path):
        d = np.load(path, allow_pickle=True)
        m = GRU21(float(d["vmax"]), hidden=int(d["H"]))
        m.set_params({k: d[k] for k in ("Wz", "bz", "Wr", "br", "Wn", "bn", "Wo", "bo")})
        m.input_mean = d["input_mean"]; m.input_std = d["input_std"]
        return m


class MLPk20(TinyMLP):
    ARM = "mlp20"
    K = 20

    def __init__(self, vmax, hidden=11, seed=0):
        # TinyMLP.__init__ używa self.K (nadpisane klasowo na 20) → din=160.
        super().__init__(vmax, hidden=hidden, seed=seed)

    def save(self, path):
        np.savez(path, arm="mlp20", vmax=self.vmax, h=self.h, k=self.K,
                 input_mean=self.input_mean, input_std=self.input_std, **self.params())

    @staticmethod
    def load(path):
        d = np.load(path, allow_pickle=True)
        m = MLPk20(float(d["vmax"]), hidden=int(d["h"]))
        m.set_params({k: d[k] for k in ("W1", "b1", "W2", "b2", "W3", "b3")})
        m.input_mean = d["input_mean"]; m.input_std = d["input_std"]
        return m


def _gradcheck_gru(eps=1e-6, T=7, B=3, seed=0):
    """Numeryczny vs analityczny gradient GRU21 na losowych danych (maska z zerami). Zwraca max błąd wzgl."""
    rng = np.random.RandomState(seed)
    m = GRU21(3.0, seed=seed)
    X = rng.randn(T, B, 8); Y = rng.randn(T, B, 3)
    mask = np.ones((T, B)); mask[-2:, 0] = 0.0
    def loss(params=None):
        if params is not None:
            m.set_params(params)
        Yh, caches = m.forward_seq(X, mask)
        d = (Yh - Y) * mask[:, :, None]
        return float(np.sum(d * d)), caches, d
    L0, caches, d = loss()
    n_eff = 1.0
    g = m.grads_seq(caches, 2.0 * d / n_eff, mask)
    worst = 0.0
    base = {k: v.copy() for k, v in m.params().items()}
    for k in g:
        flat = base[k].ravel()
        for idx in rng.choice(flat.size, size=min(6, flat.size), replace=False):
            p = {kk: vv.copy() for kk, vv in base.items()}
            p[k].ravel()[idx] += eps
            Lp, _, _ = loss(p)
            p[k].ravel()[idx] -= 2 * eps
            Lm, _, _ = loss(p)
            num = (Lp - Lm) / (2 * eps)
            ana = g[k].ravel()[idx]
            rel = abs(num - ana) / max(1e-8, abs(num) + abs(ana))
            worst = max(worst, rel)
    m.set_params(base)
    return worst


if __name__ == "__main__":
    print(f"GRU21 params={GRU21(3.0).param_count()} (oczekiwane 1956)")
    print(f"MLPk20 params={MLPk20(3.0).param_count()} (oczekiwane 1939)")
    print(f"gradcheck GRU max_rel_err={_gradcheck_gru():.2e}")
