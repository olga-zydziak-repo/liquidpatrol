#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_v3_post.py — posthoc AKTU 4 (PROMPT_DEMOC_V3 §1/§3).

Dwa rachunki, oba przyrządami zamrożonymi IMPORTEM (zero edycji FROZEN):
  • ETYKIETA: wabik_sig v1 475c972e (classify/feed_rows 1:1) na percep_feed
    lotu, okno epizodu z trace; czasy summary (względem pierwszej ważnej klatki
    trk) przeliczone na ABSOLUTNE t_flag_abs/t_revoke_abs dla overlay;
    per-frame jsonl przez classify(out_f) — litera identyczna z CLI.
  • WERDYKT 4b: perc2_s2_analyze.analyze_boot (sędzia FROZEN 8ec0fcfb, GT
    manifest + świadek OBOK) ze SCEN.update(wabik_manifest_s2) — wzór 1:1
    wabik_s2_analyze; zapis WYŁĄCZNIE do s3_wabik/ (artefakty WABIK nietknięte).

Użycie: democ_v3_post.py <bootdir_4a> <bootdir_4b>
"""
import hashlib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "PERC2", "tools"),
          os.path.join(ROOT, "results", "WABIK", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

import wabik_sig as WS                      # FROZEN 475c972e — importem
import perc2_s2_analyze as PA               # przyrząd S2 — SCEN update wzorem wabik_s2

MAN2 = json.load(open(os.path.join(ROOT, "results", "WABIK", "wabik_manifest_s2.json")))
PA.SCEN.update({e["scenario_id"]: e for e in MAN2["episodes"]})
OUTD = os.path.join(ROOT, "results", "DEMO_C", "s3_wabik")


def sig_sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def sig_for(d, tag):
    ep = WS.episodes_of(d)[0]
    rows = WS.feed_rows(os.path.join(d, "percep_feed.jsonl"), ep["t0"], ep["t1"])
    jl = os.path.join(OUTD, f"akt{tag}_sig.jsonl")
    if os.path.exists(jl):
        os.remove(jl)
    with open(jl, "a") as f:
        res = WS.classify(rows, f)
    t_first = rows[0][0] if rows else None
    out = {"sid": ep["sid"], "t0_sim": ep["t0"], "t_first_trk": t_first,
           "wabik_sig_sha16": sig_sha16(WS.__file__),
           "summary": res,
           "t_flag_abs": (round(t_first + res["t_do_flagi_s"], 3)
                          if res["t_do_flagi_s"] is not None else None),
           "t_revoke_abs": (round(t_first + res["t_odwolania_s"], 3)
                            if res["t_odwolania_s"] is not None else None)}
    jp = os.path.join(OUTD, f"akt{tag}_sig.json")
    json.dump(out, open(jp, "w"), indent=1)
    print(f"[sig {tag}] {ep['sid']}: etykieta={res['etykieta']}/{res['etykieta_koncowa']} "
          f"t_do_flagi={res['t_do_flagi_s']} t_odwolania={res['t_odwolania_s']} "
          f"abs flag={out['t_flag_abs']} revoke={out['t_revoke_abs']} → {jp}")
    return out


def judge(d):
    rows = PA.analyze_boot(d)
    man = json.load(open(os.path.join(d, "manifest.json")))
    pokl = {e["scenario_id"]: e for e in man["episodes"]}
    out = []
    for r in rows:
        p = pokl.get(r["sid"], {})
        out.append({"sid": r["sid"], "valid": p.get("valid_V2p"), "breach": p.get("breach"),
                    "refuse_count": p.get("refuse_count"),
                    "D6_sedzia_manifest_GT": r["sedzia_D6_opisowo"]["success_D6"],
                    "fail_reasons": r["sedzia_D6_opisowo"]["fail_reasons"],
                    "d_min_sedzia": r["sedzia_D6_opisowo"]["d_min_m"],
                    "t_entry": r["sedzia_D6_opisowo"]["t_entry_s"],
                    "D6_pokladowo": p.get("success_D6"), "d_min_pokladowo": p.get("d_min_m"),
                    "swiadek": r["swiadek_erratum"], "t_acq_s": r["t_acq_s"],
                    "kadencja_lotu": r["kadencja_lotu"],
                    "gt_val_p50_m": r["gt_manifest_val_p50_m"]})
        print(f"[judge {r['sid']}] valid={out[-1]['valid']} breach={out[-1]['breach']} "
              f"refuse={out[-1]['refuse_count']} D6={out[-1]['D6_sedzia_manifest_GT']} "
              f"d_min={out[-1]['d_min_sedzia']} t_acq={out[-1]['t_acq_s']} "
              f"świadek={out[-1]['swiadek']['n_artefakt']}/{out[-1]['swiadek']['n_wierszy']}")
    return out


def main():
    d4a, d4b = sys.argv[1], sys.argv[2]
    res = {"zrodla": "etykieta: wabik_sig v1 475c972e importem (classify/feed_rows 1:1, "
                     "czasy przeliczone na absolutne); werdykt 4b: perc2_s2_analyze."
                     "analyze_boot + SCEN.update(wabik_manifest_s2) — wzor wabik_s2_analyze",
           "akt4a": {"sig": sig_for(d4a, "4a"),
                     "tor": judge(d4a)},       # 4a: tor/kadencja/świadek opisowo (bez D6 — wabik)
           "akt4b": {"sig": sig_for(d4b, "4b"),
                     "werdykt": judge(d4b)}}
    jp = os.path.join(OUTD, "akt4_werdykty.json")
    json.dump(res, open(jp, "w"), indent=1)
    print(f"zapisano {jp}")


if __name__ == "__main__":
    main()
