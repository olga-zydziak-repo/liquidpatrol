"""p2/arms.py — ramiona estymatora (§5 PRE_P2). Analityczne (bez treningu) + skeleton uczonych.

Interfejs ramienia: run(episode) -> dict{est[T,4], pred[T,H,4]}.
  est[t]   = estymata stanu w chwili t (filtracja).
  pred[t,j]= predykcja z chwili t na horyzont HORIZONS[j] (do ADE/FDE w dziury).
Analityczne dostają PRAWDZIWE σ szumu (A3): R = (σ·rozmiar)².  Uczone: interfejs identyczny (train.py).
"""
from __future__ import annotations
import numpy as np

HORIZONS = [13, 25, 50]           # {0.5,1,2}s @25fps


# ----------------------------- ZOH-age (kotwica) ----------------------------
class ZOHAge:
    name = "ZOH-age"
    def run(self, ep):
        X, obs = ep["X"], ep["observed"]
        T = X.shape[0]
        est = X[:, :4].copy()                     # trzyma ostatnią obserwację
        pred = np.repeat(est[:, None, :], len(HORIZONS), axis=1)  # bez ruchu
        return {"est": est, "pred": pred}


# ----------------------------- Kalman CV ------------------------------------
class KalmanCV:
    """cx,cy: constant-velocity; w,h: random-walk. Δt-aware. R=(σ·rozmiar)² (A3)."""
    name = "Kalman-CV"
    def __init__(self, sigma, q_pos=1e-4, q_vel=1e-3, q_wh=1e-4):
        self.sigma = sigma; self.q_pos = q_pos; self.q_vel = q_vel; self.q_wh = q_wh

    def _cv_step(self, x, P, dt, meas, R, q_pos, q_vel):
        # stan [p, v]; F=[[1,dt],[0,1]]
        F = np.array([[1, dt], [0, 1.0]])
        Q = np.array([[q_pos, 0], [0, q_vel]]) * max(dt, 1)
        x = F @ x; P = F @ P @ F.T + Q
        if meas is not None:
            H = np.array([[1.0, 0]])
            y = meas - (H @ x)[0]
            S = (H @ P @ H.T)[0, 0] + R
            K = (P @ H.T)[:, 0] / S
            x = x + K * y; P = P - np.outer(K, H @ P)
        return x, P

    def _rw_step(self, x, P, dt, meas, R, q):
        P = P + q * max(dt, 1)
        if meas is not None:
            S = P + R; K = P / S
            x = x + K * (meas - x); P = (1 - K) * P
        return x, P

    def run(self, ep):
        X, obs, noisy = ep["X"], ep["observed"], ep["noisy"]
        T = X.shape[0]
        est = np.full((T, 4), np.nan); pred = np.full((T, len(HORIZONS), 4), np.nan)
        # init z pierwszej obserwacji
        xcx = np.zeros(2); xcy = np.zeros(2); xw = 0.0; xh = 0.0
        Pcx = np.eye(2); Pcy = np.eye(2); Pw = 1.0; Ph = 1.0
        started = False; last_t = None
        for t in range(T):
            dt = 1.0 if last_t is None else (t - last_t)
            m = noisy[t] if (obs[t] and not np.isnan(noisy[t, 0])) else None
            if m is not None and not started:
                xcx = np.array([m[0], 0.0]); xcy = np.array([m[1], 0.0]); xw = m[2]; xh = m[3]
                started = True; last_t = t
                est[t] = [xcx[0], xcy[0], xw, xh]
            elif started:
                Rw = (self.sigma * max(xw, 1e-3)) ** 2; Rh = (self.sigma * max(xh, 1e-3)) ** 2
                mcx = m[0] if m is not None else None; mcy = m[1] if m is not None else None
                mw = m[2] if m is not None else None; mh = m[3] if m is not None else None
                step_dt = 1.0
                xcx, Pcx = self._cv_step(xcx, Pcx, step_dt, mcx, Rw, self.q_pos, self.q_vel)
                xcy, Pcy = self._cv_step(xcy, Pcy, step_dt, mcy, Rh, self.q_pos, self.q_vel)
                xw, Pw = self._rw_step(xw, Pw, step_dt, mw, Rw, self.q_wh)
                xh, Ph = self._rw_step(xh, Ph, step_dt, mh, Rh, self.q_wh)
                est[t] = [xcx[0], xcy[0], xw, xh]
                if m is not None: last_t = t
            if started:
                for j, H in enumerate(HORIZONS):
                    pred[t, j] = [xcx[0] + xcx[1] * H, xcy[0] + xcy[1] * H, xw, xh]
        return {"est": est, "pred": pred}


# ----------------------------- IMM (CV + stationary) ------------------------
class IMM:
    """Mieszanka: CV (ruch) + stationary (CV z v≈0). Uproszczony IMM na cx,cy; w,h random-walk."""
    name = "IMM"
    def __init__(self, sigma):
        self.sigma = sigma
        self.cv = KalmanCV(sigma, q_vel=1e-2)         # model manewrujący
        self.st = KalmanCV(sigma, q_vel=1e-5)         # model prawie-stacjonarny

    def run(self, ep):
        # uproszczenie: uruchom oba, miksuj po dopasowaniu do ostatniej obserwacji (waga ~ likelihood)
        rcv = self.cv.run(ep); rst = self.st.run(ep)
        obs, noisy = ep["observed"], ep["noisy"]
        T = ep["X"].shape[0]
        est = np.full((T, 4), np.nan); pred = np.full((T, len(HORIZONS), 4), np.nan)
        mu = 0.5
        for t in range(T):
            if np.isnan(rcv["est"][t, 0]):
                continue
            if obs[t] and not np.isnan(noisy[t, 0]):
                e_cv = np.linalg.norm(rcv["est"][t, :2] - noisy[t, :2])
                e_st = np.linalg.norm(rst["est"][t, :2] - noisy[t, :2])
                lcv = np.exp(-e_cv / (self.sigma + 1e-6)); lst = np.exp(-e_st / (self.sigma + 1e-6))
                mu = np.clip((mu * lcv) / (mu * lcv + (1 - mu) * lst + 1e-9), 0.05, 0.95)
            est[t] = mu * rcv["est"][t] + (1 - mu) * rst["est"][t]
            pred[t] = mu * rcv["pred"][t] + (1 - mu) * rst["pred"][t]
        return {"est": est, "pred": pred}


ANALYTIC = {"ZOH-age": ZOHAge, "Kalman-CV": KalmanCV, "IMM": IMM}

# ----------------------------- A3: strojenie baseline na TRAIN ---------------
Q_VEL_GRID = [1e-3, 1e-4, 1e-5, 1e-6, 1e-7, 1e-8, 1e-9]   # strojone WYŁĄCZNIE na train (A3)


def tune_kalman_q(train_eps, sigma, q_grid=Q_VEL_GRID):
    """A3: mocny baseline. R=σ² (prawdziwe σ) + Q strojone na TRAIN (grid q_vel, wybór po ADE predykcji).
    Zwraca best q_vel + tabelę. Test NIE dotykany. Empirycznie: default Q => słomiany; strojony => mocny."""
    from p2.metrics import evaluate
    rows = {}
    for qv in q_grid:
        ades = []
        for ep in train_eps:
            m = evaluate(KalmanCV(sigma, q_pos=1e-6, q_vel=qv), ep)
            if not np.isnan(m["ADE"]):
                ades.append(m["ADE"])
        rows[qv] = float(np.mean(ades)) if ades else np.nan
    best = min((qv for qv in q_grid if not np.isnan(rows[qv])), key=lambda qv: rows[qv])
    return {"best_q_vel": best, "grid_ADE_train": rows}
