#!/usr/bin/env python3
"""results/ORTO_RECON/tools/orto_r2.py — PROMPT_ORTO_S0 R2: klatki kamery w dół jako rzut płaskiego gruntu z ortofotomapy (0 bootów).

Kamera z przypiętego modelu results/NADIR/s1/zrodla/x500_nadir2_flow/model.sdf (READ-ONLY): link „nadir_link” (poza względem base_link),
czujnik „nadir” (poza względem linku, horizontal_fov, width, height, update_rate) — wartości i numery linii czytane parserem z pliku.
Łańcuch include x500_nadir2_flow → x500_mono_cam → x500 → x500_base: jedyna poza po drodze to <pose> modelu x500_base (0 0 .24),
więc base_link = rama modelu (GT) + 0.24 m w górę (PX4-Autopilot/Tools/simulation/gz/models/x500_base/model.sdf, linia z parsera).
Konwencja gz: oś optyczna = +X czujnika, obraz u w prawo = −Y czujnika, v w dół = −Z czujnika; F = (W/2) / tan(hfov/2).
Poza drona: GT z trace.jsonl (x = E, y = N, z = góra; q = FLU→ENU), interpolowana do czasu klatki (sim wiersza nf); środek kamery
C = p + R·t_link, R_kam = R·R_czujnika.
Rzut: promień piksela przecięty z płaszczyzną z = 0 (grunt), punkt (E, N) → piksel okna ortofotomapy (środek strefy = środek łaty,
N do góry, okno 100 × 100 m z R1); próbkowanie dwuliniowe; poza oknem czarne (licznik).
Sprawdzian przyrządu: reprojekcja środków znaczników z manifestu v2 (E, N, z) przy pozie GT wobec zapisanego uv detektora
(nadir_obs.jsonl lotów NAD2: 12 cięć S3 + lot długi; loader results/NAD3_RECON/tools/nad3_dane.py) — p50 / p95 / max [px];
dodatkowo przesunięcie czasu klatki dt ∈ [−0.2, 0.2] s minimalizujące p50 (opisowo, nie poprawka).
Klatki: każda klatka 5 Hz (wiersz nf) od cięcia (t_inj_sim zdarzenia „denial”) do zejścia planowego epizodu cięcia — 12 cięć S3
NAD3 (results/NAD3/s3/p*_c05_*/p*_c10_*) i lot długi NAD2 (results/NAD2/s4/L_c10_s01). Zapis: poza GT, migawka EKF z klatki (q, pozycja,
wiek) — wejścia kandydatów R3 bez GNSS — oraz p_corr NAD3 z datagramu (porównanie opisowe).
Wyjście: results/ORTO_RECON/r2_kamera.json, r2_sprawdzian.json, r2_klatki.json.gz.
"""
import glob
import gzip
import json
import math
import os
import re
import sys

import cv2
import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [os.path.join(ROOT, "results/NAD3_RECON/tools")]
import nad3_dane as N3

OUT = os.path.join(ROOT, "results/ORTO_RECON")
MODEL = os.path.join(ROOT, "results/NADIR/s1/zrodla/x500_nadir2_flow/model.sdf")
MANIFEST = os.path.join(ROOT, "results/NADIR/s1/n1/manifest_znaczniki_v2.json")
BAZA = os.path.join(ROOT, "PX4-Autopilot/Tools/simulation/gz/models/x500_base/model.sdf")   # łańcuch include: nadir2_flow → mono_cam → x500 → x500_base
S3_NAD3 = os.path.join(ROOT, "results/NAD3/s3")
POL_OKNA = 50.0


def _rpy(r, p, y):
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return np.array([[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
                     [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
                     [-sp, cp * sr, cp * cr]])


def kamera(model=MODEL, baza=BAZA):
    """Parametry kamery w dół z modelu: wartości + numery linii (1-based). Plus poza modelu x500_base (dołączony merge, więc base_link
    leży o tę pozę od ramy modelu, którą zapisuje GT) — pierwsza <pose> w pliku bazy."""
    L = open(model).read().split("\n")
    i_link = next(i for i, l in enumerate(L) if '<link name="nadir_link">' in l)
    i_sens = next(i for i in range(i_link, len(L)) if '<sensor name="nadir"' in L[i])
    i_end = next(i for i in range(i_sens, len(L)) if "</sensor>" in L[i])

    def znajdz(tag, a, b):
        for i in range(a, b):
            m = re.search(rf"<{tag}[^>]*>([^<]+)</{tag}>", L[i])
            if m:
                return m.group(1).strip(), i + 1
        raise KeyError(tag)

    pl, n_pl = znajdz("pose", i_link, i_sens)
    ps, n_ps = znajdz("pose", i_sens, i_end)
    hf, n_hf = znajdz("horizontal_fov", i_sens, i_end)
    w, n_w = znajdz("width", i_sens, i_end)
    h, n_h = znajdz("height", i_sens, i_end)
    ur, n_ur = znajdz("update_rate", i_sens, i_end)
    B = open(baza).read().split("\n")
    i_b = next(i for i, l in enumerate(B) if "<pose>" in l)
    pb = [float(x) for x in re.search(r"<pose>([^<]+)</pose>", B[i_b]).group(1).split()]
    pl, ps = [float(x) for x in pl.split()], [float(x) for x in ps.split()]
    k = {"plik": os.path.relpath(model, ROOT), "baza_plik": os.path.relpath(baza, ROOT), "baza_poza": pb, "linia_baza_poza": i_b + 1,
         "link_poza": pl, "linia_link_poza": n_pl, "czujnik_poza": ps, "linia_czujnik_poza": n_ps,
         "hfov": float(hf), "linia_hfov": n_hf, "W": int(w), "linia_W": n_w, "H": int(h), "linia_H": n_h,
         "update_rate": float(ur), "linia_update_rate": n_ur}
    k["F"] = (k["W"] / 2) / math.tan(k["hfov"] / 2)
    return k


class Kam:
    def __init__(self, k):
        self.k = k
        self.W, self.H, self.F = k["W"], k["H"], k["F"]
        self.t_link = np.array(k["link_poza"][:3]) + np.array(k["baza_poza"][:3])   # rama modelu (GT) → base_link → nadir_link
        assert not any(k["baza_poza"][3:]), k["baza_poza"]
        self.R_link = _rpy(*k["link_poza"][3:])
        self.R_cz = self.R_link @ _rpy(*k["czujnik_poza"][3:])          # czujnik → body (FLU)
        u, v = np.meshgrid(np.arange(self.W) + 0.5, np.arange(self.H) + 0.5)
        # kierunek w ramie czujnika gz: X = oś optyczna, Y = lewo (−u), Z = góra (−v)
        self.d_cz = np.stack([np.ones_like(u), -(u - self.W / 2) / self.F, -(v - self.H / 2) / self.F], -1)

    def poza(self, p_enu, R_body):
        C = p_enu + R_body @ self.t_link
        return C, R_body @ self.R_cz

    def rzut(self, C, Rk, P):
        """Punkty świata P (n × 3, ENU) → uv (n × 2) w indeksach pikseli (środek piksela i = i, jak uv detektora) i głębokość."""
        q = (np.asarray(P, float) - C) @ Rk                               # współrzędne w ramie czujnika
        d = q[:, 0]
        u = self.W / 2 - self.F * q[:, 1] / d - 0.5
        v = self.H / 2 - self.F * q[:, 2] / d - 0.5
        return np.stack([u, v], 1), d

    def grunt(self, C, Rk):
        """Dla każdego piksela: (E, N) przecięcia promienia z z = 0; NaN, gdy promień nie trafia gruntu."""
        r = self.d_cz @ Rk.T
        t = -C[2] / r[..., 2]
        t[t <= 0] = np.nan
        return C[0] + t * r[..., 0], C[1] + t * r[..., 1]

    def renderuj(self, orto, piksel, C, Rk, pol=POL_OKNA):
        """Klatka W × H (BGR) z okna ortofotomapy (środek okna = (0, 0) świata, N do góry); zwraca też ułamek pikseli poza oknem."""
        E, Nn = self.grunt(C, Rk)
        mx = ((E + pol) / piksel - 0.5).astype(np.float32)
        my = ((pol - Nn) / piksel - 0.5).astype(np.float32)
        poza = ~np.isfinite(mx) | (mx < 0) | (my < 0) | (mx > orto.shape[1] - 1) | (my > orto.shape[0] - 1)
        mx[~np.isfinite(mx)] = -1; my[~np.isfinite(my)] = -1
        im = cv2.remap(orto, mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        return im, float(poza.mean())


def rotm(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


class GT:
    """Poza GT (ENU, q FLU→ENU) z trace.jsonl interpolowana w czasie (pozycja liniowo, q nlerp ze zgodnym znakiem)."""

    def __init__(self, d):
        g = sorted(N3.jl(d, "trace.jsonl", "gt"), key=lambda r: r["sim"])
        self.t = np.array([r["sim"] for r in g])
        self.p = np.array([[r["x"], r["y"], r["z"]] for r in g])
        q = np.array([[r["qw"], r["qx"], r["qy"], r["qz"]] for r in g])
        for i in range(1, len(q)):
            if q[i] @ q[i - 1] < 0:
                q[i] = -q[i]
        self.q = q

    def __call__(self, t):
        i = int(np.clip(np.searchsorted(self.t, t), 1, len(self.t) - 1))
        a = (t - self.t[i - 1]) / max(self.t[i] - self.t[i - 1], 1e-9)
        a = float(np.clip(a, 0, 1))
        p = (1 - a) * self.p[i - 1] + a * self.p[i]
        q = (1 - a) * self.q[i - 1] + a * self.q[i]
        q /= np.linalg.norm(q)
        return p, q, float(min(abs(t - self.t[i - 1]), abs(self.t[i] - t)))


def sprawdzian(kam):
    man = {z["id"]: z for z in json.load(open(MANIFEST))["znaczniki"]}
    wyn, wszystkie = {}, {}
    for nazwa, d, _ in N3.loty():
        g = GT(d)
        rows = [r for r in N3.jl(d, "nadir_obs.jsonl", "nf") if r.get("det")]
        for dt in (-0.2, -0.1, -0.05, 0.0, 0.05, 0.1, 0.2):
            e = []
            for r in rows:
                p, q, _ = g(r["sim"] + dt)
                C, Rk = kam.poza(p, rotm(q))
                for m in r["det"]:
                    z = man.get(m["id"])
                    if z is None:
                        continue
                    uv, dep = kam.rzut(C, Rk, [[z["E"], z["N"], z["z"]]])
                    if dep[0] > 0:
                        e.append(float(np.hypot(*(uv[0] - np.array(m["uv"])))))
            wszystkie.setdefault(dt, []).extend(e)
            if dt == 0.0:
                wyn[nazwa] = dict(N3.rozklad(e), klatek_z_detekcja=len(rows))
        print("sprawdzian", nazwa, wyn[nazwa], flush=True)
    dts = {f"{dt:+.2f}": N3.rozklad(v) for dt, v in sorted(wszystkie.items())}
    return {"per_lot_dt0": wyn, "razem_dt0": N3.rozklad(wszystkie[0.0]), "przesuniecie_czasu": dts,
            "uwaga": "uv detektora = przecięcie przekątnych narożników (harness/nadir_obs.py); znacznik z manifestu (E, N, z = 0.03); poza GT"}


def loty_klatek():
    out = []
    for d in sorted(glob.glob(os.path.join(S3_NAD3, "p*_c05_*")) + glob.glob(os.path.join(S3_NAD3, "p*_c10_*"))):
        if os.path.isdir(d):
            out.append((os.path.basename(d), d))
    ks = [json.loads(l) for l in open(os.path.join(S3_NAD3, "kampania_ksiega.jsonl")) if l.strip()]
    wazne = {w["nazwa"] for w in ks if w.get("status") == "wazny"}
    out = [(n, d) for n, d in out if n in wazne]
    return sorted(out) + [(N3.LOT_DLUGI[0], N3.LOT_DLUGI[1])]


def klatki():
    out = []
    for nazwa, d in loty_klatek():
        g = GT(d)
        ev = N3.jl(d, "trace.jsonl", "event")
        den = next(e for e in ev if e.get("ev") == "denial")
        # koniec misji jak sędzia NAD3 (nad3_s3_lot): ostatni tick epizodu cięcia w fazie misji, bez zejścia, przed zejściem planowym
        zp0 = next((e["sim"] for e in ev if e.get("ev") == "zejscie_planowe" and e.get("episode_id") == den["episode_id"]), 1e18)
        ms = [r["sim"] for r in N3.jl(d, "rama.jsonl") if r.get("ep") == den["episode_id"] and r.get("phase") in N3.MISJA
              and not r.get("desc") and r["sim"] < zp0]
        zp = max(ms)
        koniec = "zejscie_planowe" if zp0 < 1e17 else "odmowa_w_misji"
        scen = next(e["scenario_id"] for e in ev if e.get("ev") == "episode_start" and e.get("episode_id") == den["episode_id"])
        n = 0
        for r in N3.jl(d, "nadir_obs.jsonl", "nf"):
            if not (den["t_inj_sim"] <= r["sim"] <= zp):
                continue
            p, q, dtg = g(r["sim"])
            fx = r.get("fx_deg") or r.get("fx") or {}
            out.append({"lot": nazwa, "scen": scen, "sim": r["sim"], "od_ciecia": round(r["sim"] - den["t_inj_sim"], 3),
                        "gt_p": [round(x, 4) for x in p], "gt_q": [round(x, 6) for x in q], "gt_dt": round(dtg, 4),
                        "ekf_q": r.get("ekf_q"), "ekf_pos": r.get("ekf_pos"), "ekf_pos_age": r.get("ekf_pos_age"),
                        "d_ne_nad3": fx.get("d_ne"), "t_fix_nad3": fx.get("t_fix"), "koniec_misji": koniec})
            n += 1
        print("klatki", nazwa, scen, "cięcie", den["t_inj_sim"], "zejście", zp, "klatek", n, flush=True)
    return out


def main():
    k = kamera()
    kam = Kam(k)
    json.dump(k, open(os.path.join(OUT, "r2_kamera.json"), "w"), ensure_ascii=False, indent=1)
    print("kamera", k, flush=True)
    s = sprawdzian(kam)
    json.dump(s, open(os.path.join(OUT, "r2_sprawdzian.json"), "w"), ensure_ascii=False, indent=1)
    print("razem", s["razem_dt0"], "dt", {a: b.get("p50") for a, b in s["przesuniecie_czasu"].items()}, flush=True)
    kl = klatki()
    with gzip.open(os.path.join(OUT, "r2_klatki.json.gz"), "wt") as f:
        json.dump(kl, f)
    print("klatek razem", len(kl))


if __name__ == "__main__":
    main()
