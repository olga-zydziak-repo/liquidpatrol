#!/usr/bin/env python3
"""results/BLIZNIAK_RECON/tools/bz_tabele.py — tabela per rodzina (R2) i krzywa ceny (PROMPT_BLIZNIAK_S0 §4, §9; 0 bootów).
Źródła: r2_petla_<ster>.json, r2_lawka_<ramię>.json, wagi/<ramię>_krzywe.json, r1_jakobian.json, r3_B30_*.json.
Zapis: r2_tabela_rodzin.json, krzywa_ceny.json."""
import json
import os

OUT = "/home/olga/projects/liquidpatrol/results/BLIZNIAK_RECON"
ST = ("Z", "K", "B90", "B50", "B30", "C3", "C12", "GRU", "MLP")
L = lambda f: json.load(open(os.path.join(OUT, f))) if os.path.exists(os.path.join(OUT, f)) else None
tab = {}
for s in ST:
    w = L(f"r2_petla_{s}.json")
    tab[s] = {"lacznie": w["lacznie"], "pierwsze_30s": w["pierwsze_30s"], "po_30s": w["po_30s"], "okrazenia_po_30s": w["okrazenia_po_30s"],
              "najgorsza_rodzina": w["najgorsza_rodzina_vt"], "H_pamiec": w["H_pamiec"],
              "per_rodzina": {r: {"vt_srednia": v["po_30s"]["vt_srednia"], "udzial_vt_lt_1": v["po_30s"]["udzial_vt_lt_1"],
                                  "d": v["po_30s"]["d"], "d_cech": v["po_30s"]["d_cech"], "okrazenia_na_min": v["okrazenia"]["srednia"]}
                              for r, v in w["per_rodzina"].items()}}
json.dump(tab, open(os.path.join(OUT, "r2_tabela_rodzin.json"), "w"), ensure_ascii=False, indent=1)
jak = L("r1_jakobian.json")
kr = {}
for s in ("Z", "K", "B90", "B50", "B30", "C3", "C12"):
    meta = L(f"wagi/{s}_krzywe.json")["meta"] if s != "Z" else {"val": 0.04852620905712814, "B_z_wag": 32.389668689696684, "epoka": None}
    d = L(f"r3_{s}_A.json")
    kr[s] = {"B_z_wag": meta["B_z_wag"], "val": meta["val"], "epoka": meta.get("epoka"), "vt_po_30s": tab[s]["po_30s"]["vt_srednia"],
             "vt_najgorsza_rodzina": tab[s]["najgorsza_rodzina"][0], "norma_max_kroku_p50": jak[s]["norma_max"]["p50"],
             "lawka": [L(f"r2_lawka_{s}.json")["gate_arm_TEST"], L(f"r2_lawka_{s}.json")["wszystkie"]],
             "dowod_S0_3_d1_DeltaA": d["E3"]["profil_d1"]["0.3"] if d else "nie liczony"}
json.dump(kr, open(os.path.join(OUT, "krzywa_ceny.json"), "w"), ensure_ascii=False, indent=1)
for s, v in kr.items():
    print(s, v)
