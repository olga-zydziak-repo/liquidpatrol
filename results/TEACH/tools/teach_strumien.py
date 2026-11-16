#!/usr/bin/env python3
"""results/TEACH/tools/teach_strumien.py — strumień datagramów producenta mapy na 13 lotach reconu (PROMPT_TEACH_S1 §3 P5_teach, §4 W5).

Loty: 12 cięć NAD3 S3 (ważne) i lot długi NAD2 L_c10_s01 — te same, z których recon TEACH wziął kadry (orto_r2.loty_klatek).
Poprawki: wiersze kadrów po cięciu z biegu W2/W4 (results/TEACH/s1/czesci_<wariant>/<lot>_<łata>.json.gz; poprawka_E/N do 1e-4 m,
przyjęta, sim). Datagram kadru: d_ne = p_fix − p_EKF(kadr) (N, E) i t_fix = sim przy przyjętej; inaczej stan poprzedni; przed
cięciem Δ = 0, t_fix = None (faza mapy). Kolejność dostarczenia: seq datagramu zapisanego w tym samym kadrze (wiersz nf
nadir_obs.jsonl lotu, klucz sim) — datagram TEACH zastępuje datagram lotu w tym samym miejscu strumienia (opóźnienie
producenta jak w locie). Wejścia ticku jak fikstura P5_nad3 (rama.jsonl: p_EKF, sp_EKF, seq; trace tk: cs, pf; demo: prędkość).
"""
import gzip
import json
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD3_RECON/tools"), os.path.join(ROOT, "results/ORTO_RECON/tools")]
import nad3_dane as N                                                # noqa: E402

S1 = os.path.join(ROOT, "results/TEACH/s1")
NAD3_S3 = os.path.join(ROOT, "results/NAD3/s3")
LATY = ("S", "M", "J")
M_PATROL = "PATROL"


def loty():
    """[(nazwa, katalog)] — 12 cięć NAD3 S3 (ważne) + lot długi (jak orto_r2.loty_klatek)."""
    import orto_r2 as R2
    return R2.loty_klatek()


def wczytaj_lot(nazwa, d):
    if nazwa == N.LOT_DLUGI[0]:
        return N.wczytaj(nazwa, d, "c10_s01")
    L = N.Lot(nazwa, d, None)
    return L


def czesc(nazwa, lata, wariant):
    tag = "K" if wariant == "K" else "K2"
    return json.load(gzip.open(os.path.join(S1, f"czesci_{tag}", f"{nazwa}_{lata}.json.gz"), "rt"))


def strumien(L, cz):
    """{seq: datagram} — tylko kadry po cięciu (wiersze W2); seq z wiersza nf lotu o tym samym sim."""
    seq_sim = {round(r["sim"], 4): r["fx"]["seq"] for r in N.jl(L.d, "nadir_obs.jsonl", "nf") if r.get("fx")}
    ekf_sim = {round(r["sim"], 4): r.get("ekf_pos") for r in N.jl(L.d, "nadir_obs.jsonl", "nf")}
    out, d_ne, t_fix = {}, [0.0, 0.0], None
    for r in cz["klatki"]["M4/K1_SIFT"]:
        s = round(r[0], 4)
        if s not in seq_sim:
            s = min(seq_sim, key=lambda x: abs(x - r[0]))
            assert abs(s - r[0]) < 1e-3, (L.nazwa, r[0])
        ok = bool(r[9])
        if ok:
            pe = ekf_sim[s]
            d_ne = [r[7] - pe[0], r[6] - pe[1]]
            t_fix = r[0]
        out[seq_sim[s]] = {"seq": seq_sim[s], "sim": r[0], "ok": ok, "d_ne": list(d_ne), "t_fix": t_fix, "kosz": 0 if ok else None,
                           "tryb": "jeden" if ok else None}
    return out


def ticki(L, st):
    """Wejścia ticku (kształt fikstury P5_nad3) z ramą TEACH; zwraca (ticki, ticki_bez_poprawki) — bez poprawki = p_EKF (mutant)."""
    tk = {r["tick"]: r for r in N.jl(L.d, "trace.jsonl", "tk")}
    demo = {r["tick"]: r for r in N.jl(L.d, "demo.jsonl")}
    seqs, ip = sorted(st), 0
    dne, tf = [0.0, 0.0], None
    out, bez = [], []
    for r in L.rama:
        while ip < len(seqs) and seqs[ip] <= r["seq"]:
            m = st[seqs[ip]]
            dne, tf = list(m["d_ne"]), m["t_fix"]
            ip += 1
        t, dm = tk[r["tick"]], demo[r["tick"]]
        pe, se = r["p_ekf"], r["sp_ekf"]
        base = {"pos": pe, "vel": dm["own_vel_ned"], "target": se, "mode": M_PATROL, "pos_flag": t["pf"], "auth_ok": True,
                "cs_gnss_pos": t["cs"], "now": r["sim"], "_tick": r["tick"], "_sim": r["sim"], "_ep": r["ep"]}
        inp = dict(base, pos_corr=[pe[0] + dne[0], pe[1] + dne[1], pe[2]], target_corr=[se[0] + dne[0], se[1] + dne[1], se[2]])
        b = dict(base, pos_corr=list(pe), target_corr=list(se))
        if tf is not None:
            for x in (inp, b):
                x["t_fix"], x["kosz"], x["tryb"] = tf, 0, "jeden"
        out.append(inp)
        bez.append(b)
    return out, bez
