#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s4_raport.py — PROMPT_NADIR_S4 §3: zbiór per epizod z ważnych bootów księgi kolejki ⇒ results/NADIR/s4/wyniki_s4.json
+ tabela markdown na stdout (do STOP_NADIR4.md). Czyta wyłącznie <boot>/wyniki_nadir_s4.json (nadir_s4_analyze) i kampania_ksiega.jsonl,
bramka_ksiega.jsonl; nic nie przelicza poza agregacją. Werdykt drabiny mechanicznie: FAIL nogi ⇔ litera_ok = False w dowolnym epizodzie."""
import json
import os

S4 = "/home/olga/projects/liquidpatrol/results/NADIR/s4"
LIT = ("a_ok", "b_ok", "c_ok", "d_ok", "e_ok", "f_ok", "g_ok")


def okna_max(e):
    """Najgorszy stosunek przyrostu do ε_b(⌊τ⌋) w oknach misji (jak g_ok: z GNSS + bez GNSS, bez zejścia)."""
    g = e.get("g_3d") or {}
    xs = [g[k]["max_inc_do_eps_b"] for k in ("z_GNSS", "bez_GNSS") if g.get(k) and g[k].get("max_inc_do_eps_b") is not None]
    return max(xs) if xs else None


def main():
    ks = [json.loads(l) for l in open(os.path.join(S4, "kampania_ksiega.jsonl")) if l.strip()]
    epi = []
    for w in ks:
        if not w.get("wazny"):
            continue
        d = json.load(open(os.path.join(S4, w["nazwa"], "wyniki_nadir_s4.json")))
        for e in d["epizody"]:
            g = e.get("g_3d") or {}
            epi.append({"boot": w["nazwa"], "boot_s4": w["boot_s4"], "boot_noga": w["boot_noga"], "tempo": (w.get("tempo") or {}).get("dsim_dwall_settle"),
                        "scenario_id": e["scenario_id"], "episode_id": e["episode_id"], "ciecie": e["ciecie"], "t_entry": e.get("t_entry"),
                        "kontynuacja_s": e.get("kontynuacja_s"), "u_max_do_m": e.get("u_max_do_m"), "u_ticki_gt_m": e.get("u_ticki_gt_m"),
                        "tau": e.get("tau"), "tau_po_cieciu": e.get("tau_po_cieciu"), "margines_min_R_E": e.get("margines_min_R_E"),
                        "okna_maxratio": okna_max(e),
                        "okna_przekroczenia": {k: (g.get(k) or {}).get("z_przekroczeniem") for k in ("z_GNSS", "bez_GNSS", "zejscie")},
                        "okna_n": {k: (g.get(k) or {}).get("n") for k in ("z_GNSS", "bez_GNSS", "zejscie")},
                        "koszt_bariery_refuse": e.get("koszt_bariery_refuse"), "koszt_kontrfaktyczny_ticki": e.get("koszt_kontrfaktyczny_ticki"),
                        "zapas_bariery_min": e.get("zapas_bariery_min"), "refuse_misja_n": (e.get("refuse_misja") or {}).get("n"),
                        "frac_track": e.get("frac_track"), "frac_pasmo": e.get("frac_pasmo"), "odrzucenia_rh": e.get("odrzucenia_rh"),
                        "koszyki_poprawek": e.get("koszyki_poprawek"), "bias_kursu": e.get("bias_kursu"),
                        **{k: e.get(k) for k in LIT}, "litera_ok": e.get("litera_ok")})
    gates = [json.loads(l) for l in open(os.path.join(S4, "bramka_ksiega.jsonl")) if l.strip()]
    ciecia = [x for x in epi if x["ciecie"]]
    nom = [x for x in epi if not x["ciecie"]]
    nar = {k: [x["scenario_id"] for x in epi if x.get(k) is False] for k in LIT}
    res = {"booty_ksiega": len(ks), "booty_wazne": sum(1 for w in ks if w.get("wazny")), "epizody_ciete": len(ciecia), "epizody_nominalne": len(nom),
           "naruszenia": nar, "litera_ok_wszystkie": all(x["litera_ok"] for x in epi),
           "werdykt_nogi": "PASS" if all(x["litera_ok"] for x in epi) else "FAIL",
           "a_tylko_kontynuacja": [x["scenario_id"] for x in ciecia if x["a_ok"] is False and x["kontynuacja_s"] is not None and x["kontynuacja_s"] < 110
                                   and x["refuse_misja_n"] == 0 and x["frac_track"] >= 0.85 and x["frac_pasmo"] >= 0.85],
           "g_nominal_informacyjnie": [x["scenario_id"] for x in nom if x["g_ok"] is False],
           "bramka_zdrowia": gates, "epizody": epi}
    json.dump(res, open(os.path.join(S4, "wyniki_s4.json"), "w"), ensure_ascii=False, indent=1)
    f = lambda v, n=3: "—" if v is None else (f"{v:.{n}f}" if isinstance(v, float) else str(v))
    print("| boot | epizod | tempo | ENTRY s | kontynuacja s | u_max/m | τ p95 / max s | okna maxratio | okna > ε_b (z/bez GNSS) | koszt bariery | margines R_E | litera (a b c d e f g) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for x in epi:
        lit = " ".join("–" if x[k] is None else ("✓" if x[k] else "✗") for k in LIT)
        print(f"| {x['boot']} | {x['scenario_id']} | {f(x['tempo'])} | {f(x['t_entry'], 2)} | {f(x['kontynuacja_s'])} | {f(x['u_max_do_m'])} | "
              f"{f(x['tau']['p95'])} / {f(x['tau']['max'])} | {f(x['okna_maxratio'])} | {x['okna_przekroczenia']['z_GNSS']}/{x['okna_przekroczenia']['bez_GNSS']} | "
              f"{x['koszt_bariery_refuse']} / {x['koszt_kontrfaktyczny_ticki']} | {f(x['margines_min_R_E'], 2)} | {lit} |")
    print(json.dumps({k: v for k, v in res.items() if k not in ("epizody", "bramka_zdrowia")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
