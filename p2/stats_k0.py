"""p2/stats_k0.py — statystyki deterministyczne kroku 0 (A2). Uruchom po wrzuceniu etykiet.

Liczy: rozkład długości, drabinę progu długości ≥T_min (§9 [A2]), rate naturalnych dziur
(„duch G2": frakcja exist=0 + rozkład długości dziur), porównanie z syntetyczną siatką L.
Reguły Z GÓRY (nietykalne): T_min drabina {30,20,15,10}s, N_min=30 test, horyzont 2s=50 kl.
"""
from __future__ import annotations
import numpy as np
from p2.io_labels import load_split
from p2.protocol import hole_segments

FPS = 25
T_LADDER_S = [30, 20, 15, 10]
N_MIN = 30                     # min. sekwencji kwalifikujących w teście
HORIZON_MAX = 50              # 2 s @25fps — sekwencja musi pomieścić dziurę + kontekst


def natural_holes(seq):
    """Segmenty naturalnych dziur (exist=0) — „duch G2"."""
    observed = seq["exist"]
    return hole_segments(observed, 0)


def split_stats(seqs):
    lens = np.array([s["n_frames"] for s in seqs])
    lens_s = lens / FPS
    exist_frac = np.array([s["exist"].mean() for s in seqs])
    hole_lens = []
    for s in seqs:
        for a, b in natural_holes(s):
            hole_lens.append(b - a)
    hole_lens = np.array(hole_lens) if hole_lens else np.array([0])
    return {
        "n_seq": len(seqs),
        "len_frames": {"min": int(lens.min()), "max": int(lens.max()),
                       "mean": float(lens.mean()), "median": float(np.median(lens))} if len(lens) else {},
        "len_seconds": {"min": float(lens_s.min()), "max": float(lens_s.max()),
                        "mean": float(lens_s.mean()), "median": float(np.median(lens_s))} if len(lens) else {},
        "natural_hole_rate": float(1.0 - exist_frac.mean()) if len(exist_frac) else 0.0,
        "natural_hole_len": {"n": int(len(hole_lens)), "mean": float(hole_lens.mean()),
                             "median": float(np.median(hole_lens)), "max": int(hole_lens.max())},
        "ge30s_count": int((lens >= 30 * FPS).sum()),
    }


def ladder_Tmin(test_seqs):
    """Deterministyczna drabina progu długości → wybrane T_min (s) i licznik kwalifikujących."""
    lens = np.array([s["n_frames"] for s in test_seqs])
    for T in T_LADDER_S:
        need = T * FPS
        qual = int(((lens >= need) & (lens >= HORIZON_MAX + 25)).sum())
        if qual >= N_MIN:
            return {"T_min_s": T, "qualifying_test": qual, "drop_2s_horizon": T < 20 and qual < N_MIN}
    # nie osiągnięto N_MIN nawet przy 10s → najniższy próg, odrzuć horyzont 2s
    T = T_LADDER_S[-1]; need = T * FPS
    qual = int((lens >= need).sum())
    return {"T_min_s": T, "qualifying_test": qual, "drop_2s_horizon": True,
            "note": "N_MIN nieosiągnięte — horyzont 2s odrzucony (§9 [A2])"}


def compute():
    res = {}
    for split in ("train", "val", "test"):
        seqs = load_split(split)
        res[split] = split_stats(seqs) if seqs else {"n_seq": 0}
    test_seqs = load_split("test")
    res["ladder"] = ladder_Tmin(test_seqs) if test_seqs else {"note": "brak danych test"}
    # porównanie naturalnych dziur z syntetyczną siatką L
    if res.get("test", {}).get("natural_hole_len", {}).get("n", 0):
        nh = res["test"]["natural_hole_len"]
        res["duch_G2_vs_grid"] = {"natural_mean_hole": nh["mean"], "natural_median_hole": nh["median"],
                                  "synthetic_L_grid": [13, 25, 50],
                                  "komentarz": "porównanie: czy syntetyczne L pokrywają realny rozkład dziur"}
    return res


if __name__ == "__main__":
    import json
    r = compute()
    print(json.dumps(r, indent=2, ensure_ascii=False))
    if r.get("test", {}).get("n_seq", 0) == 0:
        print("\n[stats] BRAK DANYCH — wrzuć etykiety do p2/data/antiuav_B/<split>/ (patrz p2/data/README.md)")
