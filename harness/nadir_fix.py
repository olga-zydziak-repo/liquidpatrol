#!/usr/bin/env python3
"""harness/nadir_fix.py — poprawka z kamery nadir i rama B+ (PROMPT_NADIR_S2 §1.1–§1.2, PRE_NADIR §2.3/§2.5). Nowy plik.

Używany WYŁĄCZNIE w gałęzi NADIR_MODE=1: producent (harness/nadir_obs.py) liczy obserwacje i poprawkę, konsumenci
(proces percepcji harness/percep_proc.py, driver results/NADIR/tools/nadir_s2_flight.py) dostają stan ramy datagramem UDS.

Obserwacja przyjęta ⇔ ID z manifestu v2 ∧ środek w stożku centralnym (edge ≥ 0.10, PRE §2.2) ∧ bok ≥ 18 px ∧ reszta do
pozycji manifestu < s/2 (reszta = |punkt gruntu z promienia przy bieżącej pozie ramy − pozycja manifestu tego ID|).
Tryb 12 (PRE §2.3): ≥ 2 przyjęte ⇒ para (kurs i skala z pary, pozycja = średnia z obu), inaczej jeden znacznik (najbliższy
w poziomie od bieżącej pozy ramy). Geometria 1:1 z results/NADIR/tools/nadir_s1v2_analyze.py (ray_world, fix1, fix_para,
ekf_R, montaż v2 (0, 0, −0.215)); postawa (q FRD→NED) i wysokość z EKF — bez GT.
Rama B+: poprawka poziomo (N, E); wysokość zostaje z EKF (2d sądzi poziomo, baro nie dryfuje z GNSS). Stan ramy = przesunięcie
Δ = p_fix − p_EKF(t_fix), stałe między poprawkami:
  p_corr(t) = p_fix + (p_EKF(t) − p_EKF(t_fix)) = p_EKF(t) + Δ;   sp_EKF = sp_net + (p_EKF − p_corr) = sp_net − Δ.
Bez obserwacji rama nie czeka: przed pierwszą poprawką Δ = 0 (czysty EKF), potem Δ trzymane (propagacja przyrostami EKF);
τ = t − t_fix liczone jawnie (None przed pierwszą poprawką).
ANEKS_NADIR-2 §2 (PROMPT_NADIR_S3 §1.1): litera przyjęcia + r_h < R_H_MAX = 8 m (r_h = pozioma odległość kamery w bieżącej
pozie ramy od pozycji manifestu; dalsza obserwacja odrzucana z powodem „rh”); datagram niesie koszyk poprawki
kosz = ⌊r_h(najbliższy) / 2⌋ ∈ {0…3} — wejście bariery piły r03/nadir_shield.py.
Para odrzucana na rzecz trybu 1 (powód w logu), gdy |skala − 1| > PARA_SKALA_MAX albo |δψ| > PARA_DPSI_MAX_DEG — strażnik
spójności pary (S1: skala p50 ≈ 1, δψ p50 −4°), nie strojenie.
PRE_NAD2 §3.1–3.2 (PROMPT_NAD2_S1 §1.1) — litera wybierana JAWNIE przełącznikiem `litera` (argument Rama; domyślnie z env
NADIR_LITERA, brak ⇒ „NADIR1” = stara litera bez zmiany zachowania). Litera „NAD2”: bok ≥ 16 px, najbliższy znacznik r_h < 10 m,
partner pary bez limitu r_h (największa baza), koszyk ⌊r_h/2⌋ ∈ {0…4}; T1 — poprawka jednym znacznikiem obraca wektor poziomy
kamera→znacznik o δψ ostatniej PRZYJĘTEJ pary, jeśli para ma ≤ T1_WIEK_S (2 s); skala bez korekty; bramka przyjęcia (reszta)
bez korekty. Datagram niesie tryb poprawki (pole „tryb”) i literę (pole „litera”, tylko przy NAD2 — przy NADIR1 datagram
bajtowo jak dotąd).
"""
from __future__ import annotations

import json
import math
import os
import socket

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "results/NADIR/s1/n1/manifest_znaczniki_v2.json")
F = 320.0 / math.tan(0.87)                 # 269.47 px — nadir 640×480, hfov 1.74
IW, IH = 640, 480
EDGE, BOK_MIN = 0.10, 18.0
MOUNT = np.array([0.0, 0.0, -0.215])       # montaż v2 pod płozami (ANEKS_NADIR-1), rama body FLU
PARA_SKALA_MAX, PARA_DPSI_MAX_DEG = 0.20, 20.0
R_H_MAX, KOSZ_M = 8.0, 2.0                 # ANEKS_NADIR-2 §2 (= r03/nadir_shield.R_H_MAX, KOSZ_M; asercja w proverze)
LITERY = ("NADIR1", "NAD2")
LITERA_ENV = "NADIR_LITERA"
BOK_MIN_NAD2, R_H_NEAR_NAD2, T1_WIEK_S = 16.0, 10.0, 2.0   # PRE_NAD2 §3.1–3.2 (litera Z2 + korekta kursu T1)


def rotm(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def ekf_R(q_ned):
    """q FRD→NED (PX4) → macierz FLU→ENU."""
    T = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]])        # NED↔ENU
    B = np.diag([1, -1, -1])                                  # FRD↔FLU
    return T @ rotm(q_ned) @ B


def ray_world(R, u, v):
    return R @ np.array([-(v - IH / 2) / F, -(u - IW / 2) / F, -1.0])


def fix1(R, z_cam, u, v, zn):
    """Pozycja (E, N) kamery z jednego znacznika: postawa R (FLU→ENU), wysokość kamery z_cam nad z = 0."""
    r = ray_world(R, u, v)
    t = (zn["z"] - z_cam) / r[2]
    return np.array([zn["E"], zn["N"]]) - t * r[:2]


def fix_para(R, z_cam, obs):
    """Para: wektory poziome znacznik−kamera z promieni obrócone o δψ i przeskalowane do bazy z mapy."""
    (ua, va, za), (ub, vb, zb) = obs
    ga = ray_world(R, ua, va); gb = ray_world(R, ub, vb)
    ga = ga[:2] * ((za["z"] - z_cam) / ga[2]); gb = gb[:2] * ((zb["z"] - z_cam) / gb[2])
    Ma, Mb = np.array([za["E"], za["N"]]), np.array([zb["E"], zb["N"]])
    dg, dM = gb - ga, Mb - Ma
    dpsi = math.atan2(dM[1], dM[0]) - math.atan2(dg[1], dg[0])
    sk = np.linalg.norm(dM) / max(np.linalg.norm(dg), 1e-6)
    c, s = math.cos(dpsi), math.sin(dpsi)
    Rz = np.array([[c, -s], [s, c]])
    p = ((Ma - sk * Rz @ ga) + (Mb - sk * Rz @ gb)) / 2
    return p, math.degrees((dpsi + math.pi) % (2 * math.pi) - math.pi), sk


class Rama:
    """Producent: obserwacje → poprawka → Δ. Jeden obiekt na proces nadir_obs."""

    def __init__(self, manifest=MANIFEST, litera=None):
        self.litera = os.environ.get(LITERA_ENV, "NADIR1") if litera is None else litera
        assert self.litera in LITERY, self.litera
        self.para_dpsi = None                  # NAD2/T1: (t_frame, δψ [rad]) ostatniej przyjętej pary
        man = json.load(open(manifest))
        self.zn = {z["id"]: z for z in man["znaczniki"]}
        self.s = man["s_m"]
        self.reszta_max = self.s / 2
        self.d_ne = [0.0, 0.0]
        self.t_fix = None
        self.p_fix_ne = None
        self.seq = 0
        self.n_fix = {"para": 0, "jeden": 0}

    def p_corr(self, p_ekf_ned):
        return [p_ekf_ned[0] + self.d_ne[0], p_ekf_ned[1] + self.d_ne[1], p_ekf_ned[2]]

    def obserwacja(self, t_frame, det, ekf_q, ekf_pos):
        """det = lista {id, uv, bok, ...} z jednej klatki; ekf_q (FRD→NED), ekf_pos (NED) = migawka EKF przy klatce.
        Zwraca rekord (datagram) ze stanem ramy po tej klatce; Δ zmienia się tylko przy przyjętej poprawce."""
        self.seq += 1
        rec = {"t": "fx", "seq": self.seq, "t_frame": round(float(t_frame), 4), "n_det": len(det), "ok": False, "tryb": None,
               "ids": [], "odrz": []}
        if ekf_q is None or ekf_pos is None:
            rec["powod"] = "brak_ekf"
            return self._stan(rec)
        nad2 = self.litera == "NAD2"
        if nad2:
            rec["litera"] = "NAD2"
        bok_min = BOK_MIN_NAD2 if nad2 else BOK_MIN
        Re = ekf_R(ekf_q)
        off = Re @ MOUNT
        z_cam = -ekf_pos[2] + off[2]
        pc = self.p_corr(ekf_pos)
        cam_en = np.array([pc[1], pc[0]]) + off[:2]                  # bieżąca poza ramy: kamera w ENU (E, N)
        acc, far = [], []
        for m in det:
            zn = self.zn.get(m["id"])
            if zn is None:
                rec["odrz"].append({"id": m["id"], "powod": "id_poza_manifestem"}); continue
            u, v = m["uv"]
            if min(u / IW, 1 - u / IW, v / IH, 1 - v / IH) < EDGE:
                rec["odrz"].append({"id": m["id"], "powod": "krawedz"}); continue
            if m["bok"] < bok_min:
                rec["odrz"].append({"id": m["id"], "powod": "bok", "bok": m["bok"]}); continue
            r = ray_world(Re, u, v)
            if r[2] >= -1e-6:
                rec["odrz"].append({"id": m["id"], "powod": "promien"}); continue
            g = cam_en + ((zn["z"] - z_cam) / r[2]) * r[:2]
            reszta = float(np.hypot(g[0] - zn["E"], g[1] - zn["N"]))
            if reszta >= self.reszta_max:
                rec["odrz"].append({"id": m["id"], "powod": "reszta", "reszta": round(reszta, 3)}); continue
            rh = float(np.hypot(zn["E"] - cam_en[0], zn["N"] - cam_en[1]))
            if nad2:                                                  # PRE_NAD2 §3.1: najbliższy < 10 m, partner bez limitu
                (acc if rh < R_H_NEAR_NAD2 else far).append((m, zn, rh, reszta))
                continue
            if rh >= R_H_MAX:                                         # ANEKS_NADIR-2 §2
                rec["odrz"].append({"id": m["id"], "powod": "rh", "rh": round(rh, 3)}); continue
            acc.append((m, zn, rh, reszta))
        if not acc:
            for a in far:
                rec["odrz"].append({"id": a[0]["id"], "powod": "rh_bez_bliskiego", "rh": round(a[2], 3)})
            rec["powod"] = "brak_przyjetych"
            return self._stan(rec)
        acc.sort(key=lambda a: a[2])
        near = acc[0]
        if nad2:                                                      # PRE_NAD2 §3.2: T1 (obrót wektora poziomego o δψ pary)
            u0, v0 = near[0]["uv"]
            r0 = ray_world(Re, u0, v0)
            hv = ((near[1]["z"] - z_cam) / r0[2]) * r0[:2]
            if self.para_dpsi is not None and float(t_frame) - self.para_dpsi[0] <= T1_WIEK_S:
                c_, s_ = math.cos(self.para_dpsi[1]), math.sin(self.para_dpsi[1])
                hv = np.array([[c_, -s_], [s_, c_]]) @ hv
                rec["t1"] = {"dpsi_deg": round(math.degrees(self.para_dpsi[1]), 3),
                             "wiek_s": round(float(t_frame) - self.para_dpsi[0], 3)}
            cam1 = np.array([near[1]["E"], near[1]["N"]]) - hv
        else:
            cam1 = fix1(Re, z_cam, near[0]["uv"][0], near[0]["uv"][1], near[1])
        rec["jeden"] = {"id": near[0]["id"], "rh_est": round(near[2], 3), "reszta": round(near[3], 3),
                        "p_ne": [round(float(cam1[1] - off[1]), 4), round(float(cam1[0] - off[0]), 4)]}
        p_en, tryb = cam1 - off[:2], "jeden"
        partnerzy = acc[1:] + far
        if partnerzy:
            part = max(partnerzy, key=lambda a: math.hypot(a[1]["E"] - near[1]["E"], a[1]["N"] - near[1]["N"]))
            obs = [(near[0]["uv"][0], near[0]["uv"][1], near[1]), (part[0]["uv"][0], part[0]["uv"][1], part[1])]
            pp, dpsi, sk = fix_para(Re, z_cam, obs)
            rec["para"] = {"ids": [near[0]["id"], part[0]["id"]], "dpsi_deg": round(dpsi, 3), "skala": round(float(sk), 4),
                           "p_ne": [round(float(pp[1] - off[1]), 4), round(float(pp[0] - off[0]), 4)]}
            if abs(sk - 1) > PARA_SKALA_MAX or abs(dpsi) > PARA_DPSI_MAX_DEG:
                rec["para"]["odrzucona"] = "spojnosc"
            else:
                p_en, tryb = pp - off[:2], "para"
                if nad2:
                    self.para_dpsi = (float(t_frame), math.radians(dpsi))
        p_fix_ne = [float(p_en[1]), float(p_en[0])]
        self.d_ne = [p_fix_ne[0] - ekf_pos[0], p_fix_ne[1] - ekf_pos[1]]
        self.t_fix = float(t_frame)
        self.p_fix_ne = p_fix_ne
        self.n_fix[tryb] += 1
        rec.update(ok=True, tryb=tryb, ids=[a[0]["id"] for a in acc], kosz=int(near[2] // KOSZ_M), p_fix_ne=[round(x, 4) for x in p_fix_ne],
                   p_ekf_fix=[round(float(x), 4) for x in ekf_pos])
        return self._stan(rec)

    def _stan(self, rec):
        rec["d_ne"] = [round(self.d_ne[0], 6), round(self.d_ne[1], 6)]
        rec["t_fix"] = None if self.t_fix is None else round(self.t_fix, 4)
        return rec


class RamaKlient:
    """Konsument (percepcja, driver): odbiór datagramów producenta przez UDS (SOCK_DGRAM, nieblokujący, wzór
    harness/feed_vision_proc.FeedVisionProc). Stan = najnowszy datagram (po seq). Brak datagramów ⇒ Δ = 0 (czysty EKF)."""

    def __init__(self, sock_path):
        self.sock_path = sock_path
        if os.path.exists(sock_path):
            os.unlink(sock_path)
        self._sk = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self._sk.bind(sock_path)
        self._sk.setblocking(False)
        self.d_ne = [0.0, 0.0]
        self.t_fix = None
        self.seq = 0
        self.last = None
        self.p_fix = None                    # p_fix (N, E) ostatniej przyjętej poprawki
        self.kosz = None                     # koszyk r_h ostatniej przyjętej poprawki (wejście bariery piły)
        self.tryb = None                     # PRE_NAD2 §3.2: tryb ostatniej przyjętej poprawki (para | jeden) — wejście tabeli U
        self.nowe = []                       # datagramy od ostatniego odbierz_nowe() — do logu ramy

    def drain(self):
        while True:
            try:
                data, _ = self._sk.recvfrom(65536)
            except (BlockingIOError, InterruptedError, OSError):
                break
            try:
                m = json.loads(data.decode())
            except ValueError:
                continue
            if m.get("t") != "fx":
                continue
            self.nowe.append(m)
            if m["seq"] > self.seq:
                self.seq = m["seq"]
                self.d_ne = list(m["d_ne"])
                self.t_fix = m["t_fix"]
                self.last = m
                if m.get("ok"):
                    self.p_fix = m["p_fix_ne"]
                    self.kosz = m.get("kosz")
                    self.tryb = m.get("tryb")

    def odbierz_nowe(self):
        n, self.nowe = self.nowe, []
        return n

    def p_corr(self, p_ekf_ned):
        return [p_ekf_ned[0] + self.d_ne[0], p_ekf_ned[1] + self.d_ne[1], p_ekf_ned[2]]

    def tau(self, t):
        return None if self.t_fix is None else t - self.t_fix

    def close(self):
        try:
            self._sk.close()
        finally:
            if os.path.exists(self.sock_path):
                os.unlink(self.sock_path)


def sp_ekf(sp_net, p_ekf, p_corr):
    """Setpoint pozycyjny z ramy sieci do ramy EKF: sp_EKF = sp_net + (p_EKF − p_corr) (PRE §2.5)."""
    return [sp_net[k] + (p_ekf[k] - p_corr[k]) for k in range(3)]


def nadawca(paths):
    """Wysyłka datagramu do listy gniazd konsumentów; brak słuchacza nie jest błędem (wzór percep_proc.send)."""
    sk = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sk.setblocking(False)

    def send(obj):
        b = json.dumps(obj).encode()
        for p in paths:
            try:
                sk.sendto(b, p)
            except OSError:
                pass
    return send
