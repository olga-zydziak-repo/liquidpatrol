#!/usr/bin/env python3
"""results/TEACH2/tools/teach2_dryrun.py — próba na sucho budowy TEACH-II (PROMPT_TEACH2_S1 §1; 0 bootów).

(1) manifest wahadła: sprawdziany generatora (results/TEACH2/teach2_manifest.json) — podane jak wyszły, osobno;
(2) plan kolejki i strażnik boota: teach2_run --sucho (env, argumenty, niezmiennik manifestu, limit ULG); kopia boota bash -n
    i różnica wobec teach_boot.sh wyłącznie w trzech wierszach ścieżki wyników; strażnik: (a) bez profilu FastDDS ⇒ rc 5 przed
    czymkolwiek, (b) z profilem i ZŁĄ sumą manifestu ⇒ rc 5 „manifest S4 sha” (stos nie rusza), (c) suma manifestu w env = plik;
(3) regresja: lot results/TEACH/s3/p02_S_c10_a (kopia w katalogu tymczasowym, boot.ulg dowiązany) przez teach2_lot z T_CONT 110 —
    osąd i liczby jak sędzia S3 (sedzia_s3.json); max e′/U′ ticków liczonych w sędzi = analizator;
(4) sprawdzian lotu teach_s3_spr na tym samym locie: 100 %;
(5) reguły §4: status_lotu / decyzja / werdykt na wejściach syntetycznych (naruszenie, sprawdzian < 100 %, cięcie bez wejścia,
    τ* ≤ 3 s od flagi z wolną klatką mapy i bez niej, odmowa późna ⇒ L-B, czwarty boot) oraz pełny sędzia na kopii p02 ze
    wstrzykniętą odmową (rama ph KONT_REFUSE i tk REFUSE/„τ*” od wybranego ticku; w wariancie z wolną klatką — wiersz fazy mapy
    z czasem producenta 0.8 s obejmujący chwilę flagi): odmowa 1.5 s po fladze z wolną klatką ⇒ powtórka; bez ⇒ L-B; odmowa
    100 s po cięciu (lot ma 110 s; „300. sekunda” nieosiągalna na locie bramki) ⇒ L-B z czasem kontynuacji do odmowy. Sprawdzian
    lotu w (5) podmieniony na zgodny (dane zmienione celowo — replay osłony musiałby się różnić).
Wyjście: results/TEACH2/s1/dryrun/dryrun_teach2.json.
"""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT = "/home/olga/projects/liquidpatrol"
T2T = os.path.join(ROOT, "results/TEACH2/tools")
sys.path[:0] = [T2T, os.path.join(ROOT, "results/TEACH/tools"), ROOT]
OUT = os.path.join(ROOT, "results/TEACH2/s1/dryrun")
TMP = os.environ.get("TEACH2_DRY_TMP", "/tmp/teach2_dry")
P02 = os.path.join(ROOT, "results/TEACH/s3/p02_S_c10_a")
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def kopia(nazwa):
    d = os.path.join(TMP, nazwa)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(TMP, exist_ok=True)
    subprocess.run(["rsync", "-a", "--exclude", "boot.ulg", "--exclude", "percep.sock", "--exclude", "kadry", "--exclude", "sedzia_*",
                    P02 + "/", d + "/"], check=True)
    os.symlink(os.path.join(P02, "boot.ulg"), os.path.join(d, "boot.ulg"))
    return d


def czesc1():
    info = json.load(open(os.path.join(ROOT, "results/TEACH2/teach2_manifest.json")))
    return {"sprawdziany_c10_s01": info["sprawdziany_c10_s01"], "sha256": info["sha256"],
            "sha_pliku_zgodna": h(os.path.join(ROOT, info["manifest"])) == info["sha256"], "PASS": info["sprawdziany_c10_s01"]["ok"]}


def czesc2():
    import teach2_run as R
    r = subprocess.run([sys.executable, os.path.join(T2T, "teach2_run.py"), "--sucho"], capture_output=True, text=True, cwd=ROOT)
    plan = json.loads(r.stdout.strip().splitlines()[-1])
    oczek = {"BOOT_NADIR_MODE": "1", "BOOT_KONT_MODE": "1", "BOOT_PASSTHROUGH": "0", "TEACH_ETAP": "s3", "BOOT_LATA": "S", "BOOT_CIEN": "0",
             "NAD2_T_CONT_S": "600.5", "NAD2_WALL_MAX_CUT_S": "1000"}
    env_ok = all(plan["env"].get(k) == v for k, v in oczek.items()) and plan["args"] == ["10", "200"] and plan["NAD2_ULG_LIMIT_MB"] == "10"
    info = json.load(open(os.path.join(ROOT, "results/TEACH2/teach2_manifest.json")))
    man_ok = plan["env"]["NAD3_MANIFEST"] == info["manifest"] and plan["env"]["NAD3_MANIFEST_SHA"] == h(os.path.join(ROOT, info["manifest"]))
    diff = subprocess.run(["diff", os.path.join(ROOT, "results/TEACH/tools/teach_boot.sh"), os.path.join(T2T, "teach2_boot.sh")],
                          capture_output=True, text=True).stdout
    zm = [l for l in diff.splitlines() if l.startswith((">", "<"))]
    zm_kod = [l for l in zm if not l.startswith("> #")]
    diff_ok = (len([l for l in zm_kod if l.startswith("<")]) == 3 and len([l for l in zm_kod if l.startswith(">")]) == 3
               and all("TEACH2: ścieżka wyników" in l for l in zm_kod if l.startswith(">")))
    mon = os.path.join(ROOT, "results/TEACH2/s1/teach2_s1_monitor.log")
    byl = os.path.exists(mon)
    base = {k: v for k, v in os.environ.items() if k not in ("PERC2_FASTDDS_PROFILE",) and not k.startswith(("BOOT_", "TEACH_", "NAD3_MANIFEST"))}
    g1 = subprocess.run(["bash", "-uo", "pipefail", R.BOOT, "99", "dryrun_guard_a", "10", "200"], env={**base, **plan["env"]},
                        capture_output=True, text=True, timeout=120, cwd=ROOT)
    g2 = subprocess.run(["bash", "-uo", "pipefail", R.BOOT, "99", "dryrun_guard_b", "10", "200"],
                        env={**base, **plan["env"], "NAD3_MANIFEST_SHA": "0" * 64, "PERC2_FASTDDS_PROFILE": R.G.PROFIL},
                        capture_output=True, text=True, timeout=120, cwd=ROOT)
    for nm in ("dryrun_guard_a", "dryrun_guard_b"):
        shutil.rmtree(os.path.join(ROOT, "results/TEACH2/s1", nm), ignore_errors=True)
    if not byl and os.path.exists(mon):
        os.remove(mon)
    straz = {"a_bez_profilu": {"rc": g1.returncode, "ok": g1.returncode == 5 and "brak PERC2_FASTDDS_PROFILE" in g1.stdout},
             "b_zla_suma_manifestu": {"rc": g2.returncode, "ok": g2.returncode == 5 and "manifest S4 sha" in g2.stdout and "PIN OK" not in g2.stdout,
                                      "komunikat": g2.stdout.strip().splitlines()[-1][-120:] if g2.stdout.strip() else ""}}
    out = {"plan": plan, "env_zgodny": env_ok, "manifest_w_env_zgodny": man_ok, "niezmiennik": plan["niezmiennik"],
           "bash_n": subprocess.run(["bash", "-n", R.BOOT]).returncode == 0, "diff_boot": zm, "diff_tylko_sciezka": diff_ok, "straznik": straz}
    out["PASS"] = env_ok and man_ok and plan["niezmiennik"] and out["bash_n"] and diff_ok and all(v["ok"] for v in straz.values())
    return out


KLUCZE_REG = [("wazny",), ("niewaznosc",), ("litera_ok",), ("wejscie",), ("b1_nieocenione_w_misji",), ("sprawdzian", "procent"),
              ("sprawdzian", "oslona_ticki"), ("sprawdzian", "poprawki"), ("meta", "ok")]
KLUCZE_EP = ["B", "max_e_do_U", "e_corr", "tau", "t_entry", "okno_misji", "r_max_gt_misja", "max_blad_ekf_misja", "odmowa_w_misji"]
KLUCZE_ZR = ["blad_poprawki", "blad_poprawki_polowy", "udzial_przyjetych_okna", "przerwy", "os_czasu", "opoznienie_pierwszej_poprawki_s",
             "skok_delta_pierwsza_m", "georef", "czas_ms", "n_drop", "detekcje", "kurs_kf"]


def czesc3_4():
    import teach2_lot as L
    d = kopia("p02_reg")
    n = L.sedzia(d, 110.0, None, parametry=False)
    s = json.load(open(os.path.join(P02, "sedzia_s3.json")))
    roz = {}
    for k in KLUCZE_REG:
        a, b = n, s
        for x in k:
            a, b = (a or {}).get(x), (b or {}).get(x)
        if a != b:
            roz[".".join(k)] = [a, b]
    e, f = n["epizod"], s["epizody"][0]
    for k in KLUCZE_EP:
        if k == "max_blad_ekf_misja":
            continue
        if e.get(k) != f.get(k):
            roz["epizod." + k] = [e.get(k), f.get(k)]
    if e["D_L"] != f["D1"]:
        roz["D_L"] = [e["D_L"], f["D1"]]
    if n["DL_dostepne"] != s["D1_dostepne"]:
        roz["DL_dostepne"] = [n["DL_dostepne"], s["D1_dostepne"]]
    for k in KLUCZE_ZR:
        if json.dumps(n["zrodlo"].get(k), sort_keys=True, default=str) != json.dumps(s["zrodlo"].get(k), sort_keys=True, default=str):
            roz["zrodlo." + k] = "różne"
    mis = n["misja"]["blad_poprawki"]
    zg_bp = abs(mis["max"] - s["zrodlo"]["blad_poprawki"]["max"]) < 1e-4
    out3 = {"werdykt_nowy": n["werdykt"], "D1_s3": s["D1_dostepne"], "roznice": roz, "regresja_eU": n["regresja_eU"],
            "blad_poprawki_misja_max_rowny_s3": zg_bp, "okna": len(n["okna_100s"]),
            "poprawek_w_pliku": sum(1 for _ in open(os.path.join(d, "poprawki_teach2.jsonl"))),
            "georef_z_wiazaniami": len(json.load(open(os.path.join(d, "georef_teach2.json")))["wiazania"])}
    out3["PASS"] = not roz and n["regresja_eU"]["zgodne"] and zg_bp and n["werdykt"] == "L-A" and out3["poprawek_w_pliku"] > 0
    out4 = {"procent": n["sprawdzian"]["procent"], "oslona_ticki": n["sprawdzian"]["oslona_ticki"], "poprawki": n["sprawdzian"]["poprawki"],
            "georef": n["sprawdzian"]["georef"], "PASS": n["sprawdzian"]["procent"] == 100.0}
    return out3, out4


def wstrzyk(d, t_ref, slow):
    """Odmowa od pierwszego ticku misji z sim ≥ t_ref: rama ph KONT_REFUSE do zejścia, tk dec REFUSE / cause τ*; opcjonalnie wiersz
    fazy mapy z czasem producenta 0.8 s obejmujący chwilę flagi ULG."""
    import teach2_lot as L
    rp = os.path.join(d, "rama.jsonl")
    rama = [json.loads(l) for l in open(rp)]
    zp = min((json.loads(l)["sim"] for l in open(os.path.join(d, "trace.jsonl")) if '"zejscie_planowe"' in l), default=1e18)
    ticks = {r["tick"] for r in rama if t_ref <= r["sim"] < zp and r.get("phase") in L.MISJA and r.get("ph") in L.UTRATA}
    t0 = min(r["sim"] for r in rama if r["tick"] in ticks)
    for r in rama:
        if r["tick"] in ticks:
            r["ph"] = "KONT_REFUSE"
    open(rp, "w").write("".join(json.dumps(r) + "\n" for r in rama))
    tp = os.path.join(d, "trace.jsonl")
    lines = []
    for l in open(tp):
        if '"tk"' in l:
            r = json.loads(l)
            if r.get("t") == "tk" and r.get("tick") in ticks:
                r["dec"], r["cause"] = "REFUSE", "τ*"
                l = json.dumps(r) + "\n"
        lines.append(l)
    open(tp, "w").write("".join(lines))
    if slow:
        np_ = os.path.join(d, "nadir_obs.jsonl")
        nf = [json.loads(l) for l in open(np_)]
        s = json.load(open(os.path.join(P02, "sedzia_s3.json")))
        t_fl = s["zrodlo"]["os_czasu"]["flaga_ulg"]
        r = max((x for x in nf if x.get("t") == "nf" and (x.get("teach") or {}).get("wlaczony") and x["sim"] <= t_fl), key=lambda x: x["sim"])
        r["teach"]["wlaczony"]["ms_dop"] = 800.0 - r["teach"]["wlaczony"]["ms_cechy"]
        r["sim_oryg"] = r["sim"]
        r["sim"] = round(t_fl - 0.3, 4)
        nf = sorted(nf, key=lambda x: x.get("sim", -1) if x.get("t") == "nf" else -1)
        open(np_, "w").write("".join(json.dumps(x) + "\n" for x in nf))
    return t0


def czesc5():
    import teach2_run as R
    import teach2_lot as L
    import teach_s3_spr as SPR
    ok_sd = {"litera_ok": True, "niewaznosc": [], "wazny": True, "powtorka_dopuszczona": False, "werdykt": "L-A"}
    sc = {}
    sc["naruszenie"] = R.status_lotu(0, ["episode_start", "denial"], {"ok": True}, dict(ok_sd, litera_ok=False))
    sc["sprawdzian_ponizej_100"] = R.status_lotu(0, ["episode_start", "denial"], {"ok": True}, dict(ok_sd, niewaznosc=["przyrzad"], wazny=False))
    sc["swiat_kod"] = R.status_lotu(0, ["episode_start", "denial"], {"ok": True}, dict(ok_sd, niewaznosc=["swiat_kod"], wazny=False))
    sc["bez_wejscia"] = R.status_lotu(0, ["episode_start"], {"ok": True}, dict(ok_sd, niewaznosc=["wejscie"], wazny=False))
    sc["stanowisko"] = R.status_lotu(0, [], {"ok": False}, None)
    sc["tau_wolna"] = R.status_lotu(0, ["episode_start", "denial"], {"ok": True}, dict(ok_sd, powtorka_dopuszczona=True, werdykt="powtorka"))
    sc["L_B"] = R.status_lotu(0, ["episode_start", "denial"], {"ok": True}, dict(ok_sd, werdykt="L-B"))
    sc["L_A"] = R.status_lotu(0, ["episode_start", "denial"], {"ok": True}, ok_sd)
    dec = {"bez_wejscia_boot1": R.decyzja("bez_wejscia", 1), "tau_wolna_boot2": R.decyzja("powtorka_tau_wolna", 2),
           "czwarty_boot": R.decyzja("niewazny_stanowisko", 3), "L_B": R.decyzja("L-B", 1), "L_A": R.decyzja("L-A", 1),
           "L_C": R.decyzja("L-C", 1)}
    oczek_sc = {"naruszenie": ("L-C", "STOP-TEACH2-1-LC"), "sprawdzian_ponizej_100": ("niewazny_przyrzad", "STOP-TEACH2-1-PRZYRZAD"),
                "swiat_kod": ("niewazny_swiat_kod", "STOP-TEACH2-1-SWIAT-KOD"), "bez_wejscia": ("bez_wejscia", None),
                "stanowisko": ("niewazny_stanowisko", None), "tau_wolna": ("powtorka_tau_wolna", None), "L_B": ("L-B", None), "L_A": ("L-A", None)}
    oczek_dec = {"bez_wejscia_boot1": ("dalej", None), "tau_wolna_boot2": ("dalej", None), "czwarty_boot": ("stop", "STOP-TEACH2-1-BUDZET"),
                 "L_B": ("koniec", None), "L_A": ("koniec", None), "L_C": ("stop", None)}
    f_ok = {k: tuple(v) == oczek_sc[k] for k, v in sc.items()}
    d_ok = {k: tuple(v) == oczek_dec[k] for k, v in dec.items()}
    # pełny sędzia na kopii ze wstrzykniętą odmową
    s3 = json.load(open(os.path.join(P02, "sedzia_s3.json")))
    t_fl = s3["zrodlo"]["os_czasu"]["flaga_ulg"]
    t_inj = next(json.loads(l)["t_inj_sim"] for l in open(os.path.join(P02, "trace.jsonl")) if '"denial"' in l)
    orig = SPR.sprawdz
    SPR.sprawdz = lambda d, zapis=True: dict(orig(P02, zapis=False), ok=True, procent=100.0)
    pelne = {}
    try:
        for nm, tref, slow in (("tau_1p5s_wolna", t_fl + 1.5, True), ("tau_1p5s_bez_wolnej", t_fl + 1.5, False),
                               ("odmowa_100s_po_cieciu", t_inj + 100.0, False)):
            d = kopia(f"p02_{nm}")
            t0 = wstrzyk(d, tref, slow)
            n = L.sedzia(d, 110.0, None, parametry=False)
            st = R.status_lotu(0, ["episode_start", "denial"], {"ok": True}, n)
            odm = n["epizod"]["odmowa_w_misji"] or {}
            pelne[nm] = {"t_odmowy": t0, "werdykt": n["werdykt"], "status": st, "powtorka": n["powtorka_dopuszczona"],
                         "wolna_w_chwili_flagi": n["faza_mapy"]["wolna_gt_0p5s_w_chwili_flagi"],
                         "klatka_w_chwili_flagi": n["faza_mapy"]["klatka_trwajaca_w_chwili_flagi"], "odmowa_od_flagi_s": odm.get("od_flagi_s"),
                         "kontynuacja_do_odmowy_s": odm.get("kontynuacja_do_odmowy_s"), "przyczyna": odm.get("przyczyna"),
                         "DL": n["DL_dostepne"], "litera_ok": n["litera_ok"], "przerwa_zrodla": odm.get("przerwa_zrodla")}
    finally:
        SPR.sprawdz = orig
    p_ok = {"tau_1p5s_wolna": pelne["tau_1p5s_wolna"]["status"][0] == "powtorka_tau_wolna" and pelne["tau_1p5s_wolna"]["powtorka"],
            "tau_1p5s_bez_wolnej": pelne["tau_1p5s_bez_wolnej"]["status"][0] == "L-B" and not pelne["tau_1p5s_bez_wolnej"]["powtorka"],
            "odmowa_100s_po_cieciu": pelne["odmowa_100s_po_cieciu"]["status"][0] == "L-B"
            and abs((pelne["odmowa_100s_po_cieciu"]["kontynuacja_do_odmowy_s"] or 0) - 100.0) < 0.5}
    return {"funkcje": sc, "funkcje_ok": f_ok, "decyzja": dec, "decyzja_ok": d_ok, "pelny_sedzia": pelne, "pelny_ok": p_ok,
            "PASS": all(f_ok.values()) and all(d_ok.values()) and all(p_ok.values())}


def main():
    os.makedirs(OUT, exist_ok=True)
    out = {"1_manifest": czesc1(), "2_plan_straznik": czesc2()}
    out["3_regresja"], out["4_sprawdzian"] = czesc3_4()
    out["5_reguly"] = czesc5()
    out["PASS_czesci"] = {k: v["PASS"] for k, v in out.items() if isinstance(v, dict) and "PASS" in v}
    json.dump(out, open(os.path.join(OUT, "dryrun_teach2.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(out["PASS_czesci"], ensure_ascii=False))
    shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
