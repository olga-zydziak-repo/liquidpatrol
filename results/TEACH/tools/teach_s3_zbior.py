"""Zbiór S3: 14 werdyktów sędziego → podsumowanie_s3.json (tabele STOP-TEACH-3, pary, liczby do P-TEACH)."""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import teach_s3_lot as L

D = os.path.join(os.path.dirname(__file__), "..", "s3")


def wiersz(s):
    e = s["epizody"][0]
    z = s["zrodlo"]
    g = z.get("georef") or {}
    o = e.get("obserwable") or {}
    return {
        "poz": s["pozycja"], "boot": s["boot"], "rodzaj": s["rodzaj"], "lata": s["lata"], "ep": s["epizod"],
        "wazny": s["wazny"], "niewaznosc": s["niewaznosc"], "sprawdzian": s["sprawdzian"]["procent"],
        "sprawdzian_n": [s["sprawdzian"].get("oslona_ticki"), s["sprawdzian"].get("poprawki")],
        "georef_spr": s["sprawdzian"].get("georef"), "meta_ok": s["meta"]["ok"], "tempo": s["tempo"],
        "B": e["B"], "b1_nieocenione": s["b1_nieocenione"], "b1_nieocenione_w_misji": s["b1_nieocenione_w_misji"],
        "B_szczegoly": e.get("B_szczegoly"), "D1": e.get("D1"), "odmowa_w_misji": e.get("odmowa_w_misji"),
        "refuse_misja": o.get("refuse_misja"), "max_e_do_U": e["max_e_do_U"], "e_corr": e.get("e_corr"),
        "tau_misja": o.get("tau_misja"), "blad_poprawki": z.get("blad_poprawki"),
        "polowy": z.get("blad_poprawki_polowy"), "udzial": z.get("udzial_przyjetych_okna"),
        "przerwy": z.get("przerwy"), "os_czasu": z.get("os_czasu"), "chwila_waznosci": z.get("chwila_waznosci"),
        "opoznienie_pierwszej": z.get("opoznienie_pierwszej_poprawki_s"), "skok_pierwsza": z.get("skok_delta_pierwsza_m"),
        "mapa": {k: g.get(k) for k in ("n_kadrow_mapy", "n_kf", "n_wiazan", "n_wiazan_przyjetych", "ms_zamkniecie",
                                       "ms_rozwiazanie", "ms_od_flagi_do_georef", "t_flagi")},
        "czas_ms": z.get("czas_ms"), "n_drop": z.get("n_drop"), "n_img": z.get("n_img"), "kurs_kf": z.get("kurs_kf"),
        "detekcje": z.get("detekcje"), "max_blad_ekf_misja": e.get("max_blad_ekf_misja"),
        "r_max_gt_misja": e.get("r_max_gt_misja"), "track": e.get("track"), "pasmo": e.get("pasmo"),
        "t_entry": e.get("t_entry"), "n_pred_odrzut": o.get("n_pred_odrzut"), "cien": s.get("cien"),
        "akwizycja": e.get("akwizycja"), "B5_pusty": e.get("B5_pusty"),
    }


def main():
    sd = {}
    for f in sorted(glob.glob(os.path.join(D, "p[0-9][0-9]_*", "sedzia_s3.json"))):
        s = json.load(open(f))
        sd[s["pozycja"]] = s
    assert sorted(sd) == list(range(1, 15)), sorted(sd)
    w = [wiersz(sd[p]) for p in sorted(sd)]
    ci = [r for r in w if r["rodzaj"] == "ciecie"]
    per_lata = {}
    for la in ("S", "M", "J"):
        rr = [r for r in ci if r["lata"] == la]
        per_lata[la] = {"dostepne": sum(bool(r["D1"] and r["D1"]["dostepne"]) for r in rr), "z": len(rr),
                        "max_blad": max(r["blad_poprawki"]["max"] for r in rr),
                        "max_eU": max(r["max_e_do_U"] for r in rr)}
    agg = {
        "wazne": sum(r["wazny"] for r in w), "litera_naruszenia": sum(not all(r["B"].values()) for r in w),
        "dostepne_ciecia": sum(bool(r["D1"] and r["D1"]["dostepne"]) for r in ci), "ciecia": len(ci),
        "refuse_misja_ciecia": sum(len(r["refuse_misja"] or []) for r in ci),
        "max_eU_ciecia": max(r["max_e_do_U"] for r in ci), "max_blad_ciecia": max(r["blad_poprawki"]["max"] for r in ci),
        "max_ms_zamkniecie": max(r["mapa"]["ms_zamkniecie"] for r in ci),
        "n_drop_14": [r["n_drop"] for r in w], "per_lata": per_lata,
        "J_minus_S_max": round(per_lata["J"]["max_blad"] - per_lata["S"]["max_blad"], 4),
        "detekcje_zgodne": sum(r["detekcje"]["zgodne"]["n"] for r in w),
        "detekcje_surowe": sum(r["detekcje"]["surowe"]["n"] for r in w),
    }
    out = {"wiersze": w, "zbior": agg, "pary": L.pary(sd)}
    json.dump(out, open(os.path.join(D, "podsumowanie_s3.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(agg, ensure_ascii=False, indent=1))
    print(json.dumps(out["pary"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
