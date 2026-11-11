#!/usr/bin/env python3
"""results/NAD2_RECON/tools/nad2_r3.py — PROMPT_NAD2_S0 R3: błąd poprawki (składnik F) i litera przyjęcia; replay offline ramy
na zapisanych detekcjach i migawkach EKF (wiersze nf nadir_obs.jsonl), sekwencyjnie — rama ma stan (Δ wpływa na pozę bramki).

Geometria wyłącznie z harness/nadir_fix.py (import READ-ONLY: ray_world, fix1, fix_para, ekf_R, MOUNT, stałe). Wariant
(T, Z, C) = klasa RamaV; wariant (T0, Z0, C0) = bieżąca litera — WIERNOŚĆ: musi odtworzyć zapisane fx (ok, tryb, ids, kosz,
p_fix_ne z |Δ| ≤ 1e-4 m, d_ne) w 100% klatek 16 bootów, inaczej STOP bez wniosków.
  T0 bieżący kurs; T1: poprawka jednym znacznikiem z wektorem kamera→znacznik obróconym o δψ ostatniej przyjętej pary
     (wiek pary ≤ T1_WIEK s, dom. 2; brak / starsza ⇒ jak T0; skala bez korekty; bramka przyjęcia bez zmian);
  Z0 r_h < 8 m; Z1 partner pary bez limitu r_h, znacznik najbliższy < 8 m; Z2 bok ≥ 16 px ∧ r_h < 10 m (koszyk 4 = 8–10 m),
     partner bez limitu; w Z1/Z2 obserwacje dopuszczone poza bieżącą literą sprawdzane wobec GT (błędne ID: punkt gruntu
     z promienia przy pozie GT dalej niż s/2 od pozycji manifestu tego ID);
  C0 migawka EKF przy przybyciu klatki (zapisana); C1 pozycja i postawa EKF w t_frame z wyciągu ULG (pozycja interpolowana
     po timestamp_sample, postawa najbliższa próbka).
Miary: geometryczna g = |p_fix − GT(t_fix)|, zakotwiczenia a = |p_fix − GT(t_a)|, t_a = czas sim próbki EKF, względem której
liczono Δ (C0: próbka VLP dopasowana po wartości do migawki — R1(b); C1: t_frame). Poziomo (N, E) — p_fix jest poziome.
Klasy: bez_GNSS / z_GNSS (przed flagą, cięcia) / nominal; klatka „misji” ⇔ najbliższy tick rama (|Δt| ≤ 0.1 s) w fazie misji
przed zejściem. Wyjście: results/NAD2_RECON/r3_poprawka.json (+ r3_wiernosc.json).
Użycie: nad2_r3.py [wiernosc|wszystko]
"""
import bisect
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/olga/projects/liquidpatrol")
import nad2_dane as D
from harness import nadir_fix as NF                                   # READ-ONLY

WARIANTY = [(t, z, c) for c in ("C0", "C1") for t in ("T0", "T1") for z in ("Z0", "Z1", "Z2")]


def kosz_v(rh):
    return int(rh // NF.KOSZ_M)


class RamaV:
    def __init__(self, T="T0", Z="Z0", C="C0", t1_wiek=2.0):
        man = json.load(open(NF.MANIFEST))
        self.zn = {z["id"]: z for z in man["znaczniki"]}
        self.s = man["s_m"]
        self.T, self.Z, self.C, self.t1_wiek = T, Z, C, t1_wiek
        self.d_ne = [0.0, 0.0]
        self.t_fix = None
        self.para_dpsi = None                       # (t_frame, δψ rad) ostatniej przyjętej pary

    def p_corr(self, p):
        return [p[0] + self.d_ne[0], p[1] + self.d_ne[1], p[2]]

    def obserwacja(self, t_frame, det, ekf_q, ekf_pos):
        rec = {"t_frame": float(t_frame), "ok": False, "tryb": None, "ids": [], "kosz": None, "nowe": []}
        if ekf_q is None or ekf_pos is None:
            rec["powod"] = "brak_ekf"
            return rec
        bok_min = 16.0 if self.Z == "Z2" else NF.BOK_MIN
        rh_near = 10.0 if self.Z == "Z2" else NF.R_H_MAX
        Re = NF.ekf_R(ekf_q)
        off = Re @ NF.MOUNT
        z_cam = -ekf_pos[2] + off[2]
        pc = self.p_corr(ekf_pos)
        cam_en = np.array([pc[1], pc[0]]) + off[:2]
        acc, far = [], []
        for m in det:
            zn = self.zn.get(m["id"])
            if zn is None:
                continue
            u, v = m["uv"]
            if min(u / NF.IW, 1 - u / NF.IW, v / NF.IH, 1 - v / NF.IH) < NF.EDGE:
                continue
            if m["bok"] < bok_min:
                continue
            r = NF.ray_world(Re, u, v)
            if r[2] >= -1e-6:
                continue
            g = cam_en + ((zn["z"] - z_cam) / r[2]) * r[:2]
            reszta = float(np.hypot(g[0] - zn["E"], g[1] - zn["N"]))
            if reszta >= self.s / 2:
                continue
            rh = float(np.hypot(zn["E"] - cam_en[0], zn["N"] - cam_en[1]))
            nowa = m["bok"] < NF.BOK_MIN
            if rh >= NF.R_H_MAX:
                nowa = True
            if self.Z == "Z0":
                if rh >= NF.R_H_MAX:
                    continue
                acc.append((m, zn, rh, reszta, nowa))
            else:
                (acc if rh < rh_near else far).append((m, zn, rh, reszta, nowa))
        if not acc:
            rec["powod"] = "brak_przyjetych"
            return rec
        acc.sort(key=lambda a: a[2])
        near = acc[0]
        u0, v0 = near[0]["uv"]
        r0 = NF.ray_world(Re, u0, v0)
        hv = ((near[1]["z"] - z_cam) / r0[2]) * r0[:2]             # wektor poziomy kamera → znacznik (E, N)
        if self.T == "T1" and self.para_dpsi is not None and t_frame - self.para_dpsi[0] <= self.t1_wiek:
            c, s = math.cos(self.para_dpsi[1]), math.sin(self.para_dpsi[1])
            hv = np.array([[c, -s], [s, c]]) @ hv
            rec["t1"] = True
        cam1 = np.array([near[1]["E"], near[1]["N"]]) - hv
        p_en, tryb = cam1 - off[:2], "jeden"
        partnerzy = acc[1:] + far
        uzyte = [near]
        if partnerzy:
            part = max(partnerzy, key=lambda a: math.hypot(a[1]["E"] - near[1]["E"], a[1]["N"] - near[1]["N"]))
            obs = [(u0, v0, near[1]), (part[0]["uv"][0], part[0]["uv"][1], part[1])]
            pp, dpsi, sk = NF.fix_para(Re, z_cam, obs)
            if not (abs(sk - 1) > NF.PARA_SKALA_MAX or abs(dpsi) > NF.PARA_DPSI_MAX_DEG):
                p_en, tryb = pp - off[:2], "para"
                self.para_dpsi = (float(t_frame), math.radians(dpsi))
                uzyte.append(part)
        p_fix_ne = [float(p_en[1]), float(p_en[0])]
        self.d_ne = [p_fix_ne[0] - ekf_pos[0], p_fix_ne[1] - ekf_pos[1]]
        self.t_fix = float(t_frame)
        rec.update(ok=True, tryb=tryb, ids=[a[0]["id"] for a in acc], kosz=kosz_v(near[2]), p_fix_ne=p_fix_ne, rh=near[2],
                   p_anchor=[float(x) for x in ekf_pos], nowe=[(a[0], a[1]) for a in uzyte if a[4]])
        return rec


def gt_q(b, t):
    """Postawa GT (gz: FLU→ENU) z trace, najbliższa próbka."""
    if not hasattr(b, "_gtq"):
        tr = sorted([r for r in D.jl(os.path.join(b.d, "trace.jsonl"), "gt")], key=lambda r: r["sim"])
        b._gtq_t = np.array([r["sim"] for r in tr])
        b._gtq = np.array([[r["qw"], r["qx"], r["qy"], r["qz"]] for r in tr])
    i = int(np.clip(np.searchsorted(b._gtq_t, t), 0, len(b._gtq_t) - 1))
    return b._gtq[i]


def bledne_id(b, t, m, zn, s):
    """Punkt gruntu promienia znacznika przy pozie GT; > s/2 od manifestu ⇒ błędne ID."""
    R = NF.rotm(gt_q(b, t))
    g = b.gt(t)[0]                                                  # NED
    cam = np.array([g[1], g[0], -g[2]]) + R @ NF.MOUNT              # ENU
    r = NF.ray_world(R, m["uv"][0], m["uv"][1])
    if r[2] >= -1e-6:
        return True
    p = cam[:2] + ((zn["z"] - cam[2]) / r[2]) * r[:2]
    return float(np.hypot(p[0] - zn["E"], p[1] - zn["N"])) >= s / 2


def misja_fn(b):
    ts = np.array([r["sim"] for r in b.rama])
    mi = np.array([b.misja(r) for r in b.rama])

    def f(t):
        i = int(np.clip(np.searchsorted(ts, t), 0, len(ts) - 1))
        if i > 0 and abs(ts[i - 1] - t) < abs(ts[i] - t):
            i -= 1
        return bool(mi[i]) and abs(ts[i] - t) <= 0.1
    return f


def replay(b, T, Z, C, t1_wiek=2.0, gt_id=True):
    """Sekwencyjny replay ramy wariantu na klatkach nf bootu. Zwraca listę rekordów klatek z miarami."""
    rv = RamaV(T, Z, C, t1_wiek)
    mis = misja_fn(b)
    out = []
    for r in b.nf:
        tf = r["sim"]
        if C == "C0":
            q, p = r.get("ekf_q"), r.get("ekf_pos")
            t_a = None
            if p is not None:
                i, d = b.dopasuj(p, tf, okno=(-0.3, 0.3))
                t_a = float(b.vts[i]) if i is not None else tf
        else:
            if r.get("ekf_pos") is None:
                q, p, t_a = None, None, None
            else:
                p = [float(x) for x in b.ekf_w(tf)]
                q, _ = b.q_w(tf)
                t_a = tf
        fx = rv.obserwacja(tf, r["det"], q, p)
        x = {"t_frame": tf, "mono": r["mono"], "ms": r.get("ms", 0.0), "ok": fx["ok"], "tryb": fx["tryb"], "kosz": fx["kosz"], "misja": mis(tf), "klasa": b.klasa(tf),
             "t_a": t_a, "d_ne": list(rv.d_ne)}
        if fx["ok"]:
            pf = np.array(fx["p_fix_ne"])
            x["p_fix"] = fx["p_fix_ne"]; x["p_anchor"] = fx["p_anchor"]; x["rh"] = fx["rh"]
            x["g"] = float(np.linalg.norm(pf - b.gt(tf)[0][:2]))
            x["a"] = float(np.linalg.norm(pf - b.gt(t_a)[0][:2]))
            x["t1"] = bool(fx.get("t1"))
            if gt_id and fx["nowe"]:
                x["nowe_n"] = len(fx["nowe"])
                x["bledne_id"] = sum(bledne_id(b, tf, m, zn, rv.s) for m, zn in fx["nowe"])
        out.append(x)
    return out


def wiernosc(boots):
    """T0 Z0 C0 ≡ zapisane fx (oryginalna klasa NF.Rama i RamaV) na wszystkich klatkach."""
    wyn = {}
    for n in boots:
        b = D.Boot(n)
        rv = RamaV()
        n_kl, n_zgod, dmax, zle = 0, 0, 0.0, []
        for r in b.nf:
            fx0 = r["fx"]
            fx = rv.obserwacja(r["sim"], r["det"], r.get("ekf_q"), r.get("ekf_pos"))
            n_kl += 1
            ok = fx["ok"] == fx0["ok"]
            if ok and fx["ok"]:
                ok = fx["tryb"] == fx0["tryb"] and fx["kosz"] == fx0["kosz"] and sorted(fx["ids"]) == sorted(fx0["ids"])
                dd = max(abs(fx["p_fix_ne"][k] - fx0["p_fix_ne"][k]) for k in range(2))
                dmax = max(dmax, dd)
                ok = ok and dd <= 1e-4
            ok = ok and max(abs(rv.d_ne[k] - fx0["d_ne"][k]) for k in range(2)) <= 1e-4
            n_zgod += int(ok)
            if not ok and len(zle) < 5:
                zle.append({"sim": r["sim"], "zapis": {k: fx0.get(k) for k in ("ok", "tryb", "kosz", "ids", "p_fix_ne", "powod")},
                            "replay": {k: fx.get(k) for k in ("ok", "tryb", "kosz", "ids", "p_fix_ne", "powod")}})
        wyn[n] = {"klatki": n_kl, "zgodne": n_zgod, "max_dp_fix_m": round(dmax, 7), "przyklady_niezgodnosci": zle}
        print(n, n_kl, n_zgod, round(dmax, 7), flush=True)
    wyn["_wierny"] = all(v["klatki"] == v["zgodne"] for k, v in wyn.items() if not k.startswith("_"))
    json.dump(wyn, open(os.path.join(D.OUT, "r3_wiernosc.json"), "w"), ensure_ascii=False, indent=1)
    return wyn["_wierny"]


def statystyki(rek_boot):
    """rek_boot: {boot: [rekordy klatek]} ⇒ tabele per klasa × tryb × koszyk, udziały, okna bez poprawki."""
    tab, udz, okna = {}, {}, {}
    for n, rek in rek_boot.items():
        prev = None
        okb = []
        for x in rek:
            if not x["misja"]:
                prev = None
                continue
            kl = x["klasa"]
            u = udz.setdefault(kl, {"para": 0, "jeden": 0, "brak": 0})
            u[x["tryb"] or "brak"] += 1
            if x["ok"]:
                c = tab.setdefault(kl, {}).setdefault(x["tryb"], {}).setdefault(str(x["kosz"]), {"g": [], "a": []})
                c["g"].append(x["g"]); c["a"].append(x["a"])
                if prev is not None:
                    okb.append(x["t_frame"] - prev)
                prev = x["t_frame"]
        okb = np.array(okb)
        okna[n] = {"max_s": round(float(okb.max()), 3) if okb.size else None, "n_ge_0.4": int((okb >= 0.399).sum()),
                   "n_ge_0.6": int((okb >= 0.599).sum()), "n_ge_1.0": int((okb >= 0.999).sum())}
    t2 = {kl: {tr: {ko: {"geom": D.rozklad(v["g"]), "zakotw": D.rozklad(v["a"])} for ko, v in sorted(d2.items())}
               for tr, d2 in d1.items()} for kl, d1 in tab.items()}
    return t2, udz, okna


def main():
    tryb = sys.argv[1] if len(sys.argv) > 1 else "wszystko"
    boots = D.CIECIA_S4 + D.NOM_S4
    if not wiernosc(boots):
        print("STOP: replay bieżącej litery NIE odtwarza zapisanych fx — R3 bez wniosków (PROMPT_NAD2_S0 R3)")
        sys.exit(3)
    if tryb == "wiernosc":
        return
    out = {"warianty": {}, "czulosc_T1_wiek": {}}
    B = {n: D.Boot(n) for n in boots}
    for T, Z, C in WARIANTY:
        rek = {n: replay(B[n], T, Z, C) for n in boots}
        t2, udz, okna = statystyki(rek)
        bl = sum(x.get("bledne_id", 0) for v in rek.values() for x in v)
        nn = sum(x.get("nowe_n", 0) for v in rek.values() for x in v)
        n_t1 = sum(1 for v in rek.values() for x in v if x.get("t1") and x["misja"])
        out["warianty"][f"{T}{Z}{C}"] = {"tabela": t2, "udzialy_klatek_misji": udz, "okna_bez_poprawki": okna,
                                         "obserwacje_spoza_litery_uzyte": nn, "bledne_id": bl, "klatki_T1_skorygowane": n_t1}
        j = t2.get("bez_GNSS", {}).get("jeden", {})
        print(f"{T}{Z}{C}", "bez_GNSS jeden max a", {k: v["zakotw"]["max"] for k, v in j.items()},
              "para", {k: v["zakotw"]["max"] for k, v in t2.get("bez_GNSS", {}).get("para", {}).items()}, "udz", udz.get("bez_GNSS"),
              "bledne", bl, "/", nn, flush=True)
    for wiek in (1.0, 5.0):
        rek = {n: replay(B[n], "T1", "Z0", "C0", t1_wiek=wiek, gt_id=False) for n in boots}
        t2, udz, _ = statystyki(rek)
        out["czulosc_T1_wiek"][str(wiek)] = {kl: {ko: v["zakotw"] for ko, v in t2.get(kl, {}).get("jeden", {}).items()} for kl in t2}
    json.dump(out, open(os.path.join(D.OUT, "r3_poprawka.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
