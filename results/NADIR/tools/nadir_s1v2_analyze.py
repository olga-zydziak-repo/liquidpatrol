#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s1v2_analyze.py — KOPIA nadir_s1_analyze.py (nietknięty), ANEKS_NADIR-1: manifest v2 (n1/), maska v2,
montaż kamery (0, 0, MOUNT_Z) w ramie body: geometria nadir liczona ze środka kamery, poprawka daje pozycję kamery, a drona =
kamera − R·montaż (R z GT albo z EKF — ta sama, z której liczono promień); wyniki do results/NADIR/s1/n1/. Nagłówek oryginału:"""
"""results/NADIR/tools/nadir_s1_analyze.py — analiza bootów epizodowych S1 NADIR (PROMPT_NADIR_S1 §R2–§R6).

Wejścia per boot (results/NADIR/s1/<nazwa>/): nadir_obs.jsonl (harness/nadir_obs.py), trace.jsonl (gt drona ENU + kwaternion,
sim; zdarzenia), demo.jsonl (fazy epizodów), percep_feed.jsonl (det_v2 top-1 kamery misji, zdarzenia ENTRY/REFRESH),
gt_intruder.jsonl, rtf_stream.jsonl (V2′ przez bench/campaign_analyze.judge_boot — READ-ONLY). Manifest znaczników FROZEN.
Maska własnego kadłuba nadir: results/NADIR/s1/b1/maska_kadluba.png (piksele stałe we wszystkich klatkach nadir bootu b1).
GT w chwili klatki: interpolacja liniowa pozycji i nlerp kwaternionu między sąsiednimi próbkami gt (≈31 Hz), po czasie sim.

R2 detekcja: klatka orbity „z ID” ⇔ ≥ 1 znacznik z ID z manifestu, środek w stożku centralnym (edge ≥ 0.10), bok ≥ 18 px
  (= obserwacja przyjęta PRE §2.3 bez warunku reszty; z resztą osobno). Para ⇔ ≥ 2 takie. Bok najbliższego (r_h z GT)
  wykrytego vs przewidywanie reconu (p5/p50 = 19.6/22.2 px).
R3 poprawka vs GT: per obserwacja przyjęta |p_fix − p_GT| (poziomo, p_GT = początek base_link = środek kamery nadir):
  „piksel”  — postawa i wysokość z GT (błąd czysto detekcji/modelu);
  „ekf_att” — postawa z EKF (q FRD→NED), wysokość z GT (wkład postawy, w tym kursu);
  „ekf”     — postawa i wysokość z EKF (realny tryb 1);
  „para”    — dwa znaczniki: kurs i skala z pary (EKF roll/pitch/wysokość jako start), pozycja = średnia z obu.
  Próg: p95 błędu ≤ model ZMIERZ z reconu (results/NADIR_RECON/tools/nadir_r1.eps_fix, wariant ZMIERZ) liczony dla
  geometrii TEJ obserwacji — porównanie p95(błąd) z p50(model) w koszyku r_h (0–2/2–4/4–6/6–8/8–10/10+).
R4 percepcja misji: top-1 det_v2 per klatka kamery misji; „na znaczniku” ⇔ środek boxa wewnątrz rzutu płyty znacznika
  (pinhole imagera z pozy GT, margines 3 px) ∧ dalej niż 25 px od rzutu intruza. ENTRY na znaczniku = fałszywa admisja;
  REFRESH z boxem na znaczniku = przejęcie tracku. Kontrola: ten sam rachunek na boocie KONT bez znaczników (znaczniki
  rzutowane „na niby”) = tło przypadkowych trafień tych pikseli.
R5 tempo: V2′ kanoniczne (judge_boot) per epizod + dsim/dwall z rtf_stream.
R6 okluzja: per (klatka, znacznik) przewidziany geometrią w stożku centralnym — wykryty / niewykryty; niewykryty rozbity:
  „pod bryłą” (kolizja z manifestu), „kadłub” (środek przewidywany w masce kadłuba), „za mały bok” (przewidywany < 18 px),
  „przy bryle” (węzeł ≤ 2 m od rzutu bryły — zasłonięcie w widoku skośnym), „inne” (rozmycie, krawędź nogi, oświetlenie).
Użycie: nadir_s1_analyze.py <boot_dir> [<boot_dir> ...] [--kontrola <boot KONT bez znaczników>]
"""
import bisect
import json
import math
import os
import sys

import cv2
import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results/NADIR_RECON/tools"))
S1 = os.path.join(ROOT, "results/NADIR/s1")
MAN = json.load(open(os.path.join(S1, "n1/manifest_znaczniki_v2.json")))
MOUNT = np.array([0.0, 0.0, -0.215])
OUTD = os.path.join(S1, "n1")
ZN = {z["id"]: z for z in MAN["znaczniki"]}
F = 320.0 / math.tan(0.87)
IW, IH = 640, 480
EDGE, BOK_MIN, S = 0.10, 18.0, MAN["s_m"]
CAM_MISJI = np.array([0.12, 0.03, 0.242])
PLATE = MAN["plyta_m"]
RH_BINS = [(0, 2), (2, 4), (4, 6), (6, 8), (8, 10), (10, 99)]
MASKA = os.path.join(S1, "n1/maska_v2.png")
sys.path.insert(0, os.path.join(ROOT, "results/NADIR/tools"))
import nadir_gen as NG                                         # READ-ONLY: bryly(), koliduje() (margines podany niżej)
_BR = NG.bryly(open(os.path.join(ROOT, "worlds/world_kont_A3.sdf"), encoding="utf8").read())
NG.MARGIN = 2.0
PRZY_BRYLE = {z["id"] for z in MAN["znaczniki"] if any(NG.koliduje(z["E"], z["N"], b) for b in _BR)}


def load(p, typ=None):
    out = []
    if not os.path.exists(p):
        return out
    for ln in open(p):
        if typ and f'"t": "{typ}"' not in ln:
            continue
        try:
            out.append(json.loads(ln))
        except ValueError:
            pass
    return out


def rotm(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


class GT:
    def __init__(self, trace):
        g = sorted([x for x in load(trace, "gt") if "qw" in x], key=lambda x: x["sim"])
        self.t = np.array([x["sim"] for x in g])
        self.p = np.array([[x["x"], x["y"], x["z"]] for x in g])
        self.q = np.array([[x["qw"], x["qx"], x["qy"], x["qz"]] for x in g])

    def at(self, t):
        i = bisect.bisect_left(self.t, t)
        if i <= 0 or i >= len(self.t) or self.t[i] - self.t[i - 1] > 0.2:
            return None
        a = (t - self.t[i - 1]) / (self.t[i] - self.t[i - 1])
        q0, q1 = self.q[i - 1], self.q[i]
        if np.dot(q0, q1) < 0:
            q1 = -q1
        q = (1 - a) * q0 + a * q1
        return (1 - a) * self.p[i - 1] + a * self.p[i], q / np.linalg.norm(q)


def fazy(demo):
    rows = sorted(load(demo), key=lambda r: r["t_sim"])
    eps = {}
    for r in rows:
        eps.setdefault(r["episode_id"], []).append(r)
    return rows, [r["t_sim"] for r in rows], eps


def faza_at(rows, rt, t):
    i = bisect.bisect_right(rt, t) - 1
    if i < 0:
        return None, None
    r = rows[i]
    ep_rows = None
    return (r["phase"] if t - r["t_sim"] <= 0.2 else None), r


# --- geometria nadir (ENU FLU, kamera w początku base_link; u = W/2 − f·y_b/(−z_b), v = H/2 − f·x_b/(−z_b)) ---
def nadir_uv(R, p, P):
    b = R.T @ (P - p)
    d = -b[2]
    if d <= 0.1:
        return None
    return IW / 2 - F * b[1] / d, IH / 2 - F * b[0] / d


def ray_world(R, u, v):
    return R @ np.array([-(v - IH / 2) / F, -(u - IW / 2) / F, -1.0])


def fix1(R, z_cam, u, v, zn):
    """Pozycja (E, N) drona z jednego znacznika: postawa R (FLU→ENU), wysokość kamery z_cam nad z = 0."""
    r = ray_world(R, u, v)
    t = (zn["z"] - z_cam) / r[2]
    return np.array([zn["E"], zn["N"]]) - t * r[:2]


def fix_para(R, z_cam, obs):
    """Para: wektory poziome znacznik−dron z promieni (R, z_cam) obrócone o δψ i przeskalowane, żeby baza zgadzała się z mapą."""
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


def ekf_R(q_ned):
    """q FRD→NED (PX4) → macierz FLU→ENU."""
    Rn = rotm(q_ned)
    T = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]])        # NED↔ENU
    B = np.diag([1, -1, -1])                                  # FRD↔FLU
    return T @ Rn @ B


def mission_uv(R, p, P):
    cam = p + R @ CAM_MISJI
    b = R.T @ (P - cam)
    if b[0] <= 0.1:
        return None
    return IW / 2 - F * b[1] / b[0], IH / 2 - F * b[2] / b[0]


def plyty_misji(R, p):
    h = PLATE / 2
    out = []
    for z in MAN["znaczniki"]:
        pts = [mission_uv(R, p, np.array([z["E"] + dx, z["N"] + dy, z["z"]])) for dx, dy in ((-h, -h), (h, -h), (h, h), (-h, h))]
        if all(pt is not None for pt in pts):
            out.append((z["id"], np.array(pts, np.float32)))
    return out


def pct(x, p):
    x = sorted(x)
    return round(float(x[min(len(x) - 1, int(p * len(x)))]), 3) if x else None


def model_zmierz(D, cth, rh, alt):
    import nadir_r1 as N
    v = N.WAR["ZMIERZ"]
    a = lambda x: np.array([x])
    return float(N.eps_fix(v, a(D), a(cth), a(rh / max(alt, 0.1)), a(rh), a(alt), None, None)[0])


def boot(d):
    gt = GT(os.path.join(d, "trace.jsonl"))
    rows, rt, eps = fazy(os.path.join(d, "demo.jsonl"))
    kad = cv2.imread(MASKA, 0) > 0 if os.path.exists(MASKA) else None
    nf = [x for x in load(os.path.join(d, "nadir_obs.jsonl"), "nf")]
    summ = load(os.path.join(d, "nadir_obs.jsonl"), "summary")
    R2 = {"fazy": {}, "boki_najblizszego": [], "n_klatek": len(nf), "obs_summary": summ[-1] if summ else None}
    R3 = {"tryb1": [], "para": []}
    R6 = {"przewidziane": 0, "wykryte": 0, "pod_bryla": 0, "kadlub": 0, "za_maly": 0, "przy_bryle": 0, "inne": 0, "wykryte_bok_lt18": 0}
    for fr in nf:
        ph, row = faza_at(rows, rt, fr["sim"])
        if ph is None:
            ph = "poza_epizodem"
        g = gt.at(fr["sim"])
        if g is None:
            continue
        p0, q = g
        R = rotm(q)
        p = p0 + R @ MOUNT                                     # środek kamery nadir (GT)
        acc = []
        det_ids = set()
        for m in fr["det"]:
            if m["id"] not in ZN:
                continue
            det_ids.add(m["id"])
            u, v = m["uv"]
            cen = min(u / IW, 1 - u / IW, v / IH, 1 - v / IH) >= EDGE
            zn = ZN[m["id"]]
            rh = math.hypot(zn["E"] - p[0], zn["N"] - p[1])
            if cen and m["bok"] >= BOK_MIN:
                acc.append((m, zn, rh))
            elif cen:
                R6["wykryte_bok_lt18"] += 1
        f = R2["fazy"].setdefault(ph, {"n": 0, "ge1": 0, "ge2": 0, "ge1_dowolny": 0, "ge1_z_reszta": 0})
        f["n"] += 1
        f["ge1"] += bool(acc)
        f["ge2"] += len(acc) >= 2
        f["ge1_dowolny"] += bool(fr["det"])
        if acc:
            near = min(acc, key=lambda x: x[2])
            R2["boki_najblizszego"].append(near[0]["bok"])
        # R6 per znacznik przewidziany w stożku
        for z in MAN["znaczniki"]:
            uv = nadir_uv(R, p, np.array([z["E"], z["N"], z["z"]]))
            if uv is None or min(uv[0] / IW, 1 - uv[0] / IW, uv[1] / IH, 1 - uv[1] / IH) < EDGE:
                continue
            a_, b_ = nadir_uv(R, p, np.array([z["E"] - .5, z["N"], z["z"]])), nadir_uv(R, p, np.array([z["E"] + .5, z["N"], z["z"]]))
            c_, d_ = nadir_uv(R, p, np.array([z["E"], z["N"] - .5, z["z"]])), nadir_uv(R, p, np.array([z["E"], z["N"] + .5, z["z"]]))
            bok = min(math.dist(a_, b_), math.dist(c_, d_)) if None not in (a_, b_, c_, d_) else 0
            R6["przewidziane"] += 1
            if z["id"] in det_ids:
                R6["wykryte"] += 1
            elif z["kolizje_z_brylami"]:
                R6["pod_bryla"] += 1
            elif kad is not None and kad[int(min(IH - 1, max(0, round(uv[1])))), int(min(IW - 1, max(0, round(uv[0]))))]:
                R6["kadlub"] += 1
            elif bok < BOK_MIN:
                R6["za_maly"] += 1
            elif z["id"] in PRZY_BRYLE:
                R6["przy_bryle"] += 1
            else:
                R6["inne"] += 1
        # R3
        if not acc or ph not in ("approach", "hold", "orbit"):
            continue
        Re = ekf_R(fr["ekf_q"]) if fr.get("ekf_q") else None
        z_ekf = (-fr["ekf_pos"][2] + (Re @ MOUNT)[2]) if (fr.get("ekf_pos") and Re is not None) else None
        off_e = (Re @ MOUNT)[:2] if Re is not None else None   # montaż w EKF
        off_g = (R @ MOUNT)[:2]
        pd = p0[:2]                                            # dron GT (base_link)
        for m, zn, rh in acc:
            u, v = m["uv"]
            rec = {"rh": round(rh, 2), "faza": ph, "id": m["id"], "bok": m["bok"]}
            D = math.dist(p, [zn["E"], zn["N"], zn["z"]])
            rec["model_zmierz"] = round(model_zmierz(D, (p[2] - zn["z"]) / D, rh, p[2]), 3)
            rec["piksel"] = round(float(np.linalg.norm(fix1(R, p[2], u, v, zn) - off_g - pd)), 3)
            if Re is not None:
                rec["ekf_att"] = round(float(np.linalg.norm(fix1(Re, p[2], u, v, zn) - off_e - pd)), 3)
                if z_ekf is not None:
                    fe = fix1(Re, z_ekf, u, v, zn) - off_e
                    rec["ekf"] = round(float(np.linalg.norm(fe - pd)), 3)
                    rec["reszta_do_ekf"] = round(float(np.linalg.norm(fe - np.array([fr["ekf_pos"][1], fr["ekf_pos"][0]]))), 3)
            R3["tryb1"].append(rec)
        if len(acc) >= 2 and Re is not None and z_ekf is not None:
            a2 = sorted(acc, key=lambda x: x[2])
            best = max(((a2[0], o) for o in a2[1:]), key=lambda pr: math.hypot(pr[0][1]["E"] - pr[1][1]["E"], pr[0][1]["N"] - pr[1][1]["N"]))
            obs = [(best[0][0]["uv"][0], best[0][0]["uv"][1], best[0][1]), (best[1][0]["uv"][0], best[1][0]["uv"][1], best[1][1])]
            pp, dpsi, sk = fix_para(Re, z_ekf, obs)
            pg, _, _ = fix_para(R, p[2], obs)
            R3["para"].append({"rh": round(best[0][2], 2), "faza": ph, "ekf": round(float(np.linalg.norm(pp - off_e - pd)), 3),
                               "piksel": round(float(np.linalg.norm(pg - off_g - pd)), 3), "dpsi_deg": round(dpsi, 3), "skala": round(sk, 4),
                               "model_zmierz": round(model_zmierz(math.dist(p, [best[0][1]["E"], best[0][1]["N"], 0.03]),
                                                                  (p[2] - .03) / math.dist(p, [best[0][1]["E"], best[0][1]["N"], 0.03]), best[0][2], p[2]), 3)})
    return R2, R3, R6, gt, rows, rt


def r4(d, gt):
    feed = [x for x in load(os.path.join(d, "percep_feed.jsonl")) if "t_frame" in x]
    intr = sorted(load(os.path.join(d, "gt_intruder.jsonl")), key=lambda r: r["t_sim"])
    it = [r["t_sim"] for r in intr]
    out = {"klatki": 0, "box_na_znaczniku": 0, "box_na_znaczniku_mti": 0, "entry": 0, "entry_na_znaczniku": 0, "refresh": 0,
           "refresh_na_znaczniku": 0, "na_znaczniku_conf": [], "przyklady": []}
    for r in feed:
        g = gt.at(r["t_frame"])
        if g is None or r.get("box") is None:
            continue
        p, q = g
        R = rotm(q)
        out["klatki"] += 1
        bx, by = r["box"][0] * IW, r["box"][1] * IH
        iu = None
        j = bisect.bisect_left(it, r["t_frame"])
        if 0 <= j < len(intr) and abs(intr[j]["t_sim"] - r["t_frame"]) < 0.1:
            n = intr[j]["ned"]
            iu = mission_uv(R, p, np.array([n[1], n[0], -n[2]]))
        na = None
        for zid, poly in plyty_misji(R, p):
            if cv2.pointPolygonTest(poly, (float(bx), float(by)), True) >= -3:
                if iu is None or math.dist(iu, (bx, by)) > 25:
                    na = zid
                    break
        if r["ev"] == "ENTRY":
            out["entry"] += 1
        if r["ev"] == "REFRESH":
            out["refresh"] += 1
        if na is not None:
            out["box_na_znaczniku"] += 1
            out["box_na_znaczniku_mti"] += bool(r.get("mti_ok"))
            out["na_znaczniku_conf"].append(r["conf"])
            if r["ev"] == "ENTRY":
                out["entry_na_znaczniku"] += 1
            if r["ev"] == "REFRESH":
                out["refresh_na_znaczniku"] += 1
            if len(out["przyklady"]) < 10:
                out["przyklady"].append({"t": r["t_frame"], "id": na, "conf": r["conf"], "mti": r.get("mti_ok"), "ev": r["ev"]})
    c = out.pop("na_znaczniku_conf")
    out["conf_na_znaczniku"] = {"n": len(c), "p50": pct(c, .5), "max": max(c) if c else None}
    return out


def tempo(d):
    try:
        from bench.campaign_analyze import judge_boot
        v = judge_boot(d)
        return [{"ep": x["episode_id"], "scenario": x.get("scenario_id"), "V2p_valid": bool(x["valid_campaign_V2p"]), **x["stalls"]} for x in v]
    except Exception as e:                                    # noqa: BLE001
        return {"blad": repr(e)}


def bins(recs, key):
    out = {}
    for lo, hi in RH_BINS:
        r = [x for x in recs if lo <= x["rh"] < hi and key in x]
        if r:
            out[f"{lo}-{hi}"] = {"n": len(r), "p50": pct([x[key] for x in r], .5), "p95": pct([x[key] for x in r], .95),
                                 "model_zmierz_p50": pct([x["model_zmierz"] for x in r], .5),
                                 "p95_le_model": pct([x[key] for x in r], .95) <= pct([x["model_zmierz"] for x in r], .5)}
    return out


def main():
    args = sys.argv[1:]
    kontrola = None
    if "--kontrola" in args:
        i = args.index("--kontrola"); kontrola = args[i + 1]; args = args[:i] + args[i + 2:]
    R2a, R3a, R4a, R6a, T = {}, {"tryb1": [], "para": []}, {}, {}, {}
    for d in args:
        b = os.path.basename(d.rstrip("/"))
        R2, R3, R6, gt, _, _ = boot(d)
        R2a[b] = R2; R6a[b] = R6
        for k in R3a:
            R3a[k] += [dict(x, boot=b) for x in R3[k]]
        R4a[b] = r4(d, gt)
        T[b] = tempo(d)
    r2 = {"per_boot": {}, "laczne": {}}
    tot = {}
    boki = []
    for b, R2 in R2a.items():
        r2["per_boot"][b] = {ph: dict(v, frac_ge1=round(v["ge1"] / v["n"], 4), frac_ge2=round(v["ge2"] / v["n"], 4)) for ph, v in R2["fazy"].items()}
        r2["per_boot"][b]["n_klatek"] = R2["n_klatek"]; r2["per_boot"][b]["obs_summary"] = R2["obs_summary"]
        boki += R2["boki_najblizszego"]
        for ph, v in R2["fazy"].items():
            t = tot.setdefault(ph, {k: 0 for k in v})
            for k in v:
                t[k] += v[k]
    r2["laczne"] = {ph: dict(v, frac_ge1=round(v["ge1"] / v["n"], 4), frac_ge2=round(v["ge2"] / v["n"], 4)) for ph, v in tot.items()}
    r2["bok_najblizszego_px"] = {"n": len(boki), "p5": pct(boki, .05), "p50": pct(boki, .5), "recon_p5_p50": [19.6, 22.2]}
    r6 = {"per_boot": R6a, "laczne": {k: sum(v[k] for v in R6a.values()) for k in next(iter(R6a.values()))}}
    lp = r6["laczne"]
    nw = lp["przewidziane"] - lp["wykryte"]
    r6["laczne"]["frac_niewykryte"] = round(nw / max(lp["przewidziane"], 1), 4)
    for k in ("pod_bryla", "kadlub", "za_maly", "przy_bryle", "inne"):
        r6["laczne"][f"udzial_{k}"] = round(lp[k] / max(nw, 1), 4)
    r2["r6_okluzja"] = r6
    misja = [x for x in R3a["tryb1"] if x["faza"] in ("approach", "hold", "orbit")]
    r3 = {"n_obs_tryb1": len(misja), "n_obs_para": len(R3a["para"]),
          "tryb1": {k: bins(misja, k) for k in ("piksel", "ekf_att", "ekf")},
          "para": {k: bins(R3a["para"], k) for k in ("piksel", "ekf")},
          "laczne": {k: {"p50": pct([x[k] for x in misja if k in x], .5), "p95": pct([x[k] for x in misja if k in x], .95),
                         "max": max((x[k] for x in misja if k in x), default=None)} for k in ("piksel", "ekf_att", "ekf")},
          "para_laczne": {k: {"p50": pct([x[k] for x in R3a["para"]], .5), "p95": pct([x[k] for x in R3a["para"]], .95)}
                          for k in ("piksel", "ekf", "dpsi_deg")},
          "reszta_do_ekf_max": max((x.get("reszta_do_ekf", 0) for x in misja), default=None),
          "obserwacje": R3a}
    if kontrola:
        gk = GT(os.path.join(kontrola, "trace.jsonl"))
        R4a["KONTROLA_" + os.path.basename(kontrola.rstrip("/"))] = r4(kontrola, gk)
    json.dump(r2, open(os.path.join(OUTD, "r2_detekcja.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(r3, open(os.path.join(OUTD, "r3_poprawka.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"r4": R4a, "r5_tempo": T}, open(os.path.join(OUTD, "r4_fp.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"r2": r2["laczne"], "bok": r2["bok_najblizszego_px"], "r6": r6["laczne"], "r3": r3["laczne"],
                      "r3_tryb1_ekf": r3["tryb1"]["ekf"], "r3_para": r3["para_laczne"], "r4": R4a, "tempo": T}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
