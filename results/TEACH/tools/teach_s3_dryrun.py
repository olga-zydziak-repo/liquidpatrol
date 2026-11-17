#!/usr/bin/env python3
"""results/TEACH/tools/teach_s3_dryrun.py — PROMPT_TEACH_S3 §1 „Próba na sucho” przed pierwszym bootem S3 (0 bootów).

(1) plan i strażnik: kolejka teach_s3_run --sucho (14 pozycji: łata, epizod, cięcie albo cień z chwilą); asercja pozycja = numer
    (teach_s3_run.niezmiennik) dla każdej pozycji; strażnik boota teach_boot.sh pod `bash -uo pipefail` z env każdej pozycji
    (TEACH_ETAP=s3) dochodzi do kontroli profilu FastDDS (kod 5 „brak PERC2_FASTDDS_PROFILE” — wszystkie strażniki TEACH przed nim
    zielone); `bash -n` obu skryptów.
(2) światy M i J (i S): `gz sdf -k` bez błędów; zasoby (albedo_map, uri) obecne; sumy SDF i tekstur = results/TEACH/s1/swiaty.json.
(3) sprawdzian lotu teach_s3_spr na SM (kopia results/TEACH/s2/sm_smoke_S_c05, katalog tymczasowy): 100%. Ostrość, każda zmiana
    osobno na świeżej kopii, każda musi być wykryta przez właściwą część: (a) jedna przyjęta poprawka p_fix_ne przesunięta o 0.001 m
    ⇒ poprawki; (b) wiązania ostatniego kadru mapy usunięte z rejestru zamknięcia ⇒ georeferencja; (c) jedna decyzja osłony w misji
    odwrócona w rama.jsonl ⇒ osłona.
(4) lot syntetyczny bez żadnej przyjętej poprawki: epizod syntetyczny teach_s2_dryrun (p01, łata S, flaga z ULG) z producentem,
    którego lokalizacja nie znajduje dopasowania (atrapa Producent._lokalizuj: powód brak_dopasowania); osłona odtworzona przez
    nad3_krok, ticki trace „tk” przepisane decyzjami odtworzonej osłony (dec, rule, ph, cause) i zdarzenie „refuse” w pierwszym
    zatrzasku; analizator kończy, sędzia teach_s3_lot: odmowa w misji z przyczyną τ*, cięcie niedostępne (D1), B1–B4 policzone.
(5) reguły kolejki (teach_s3_run.status_lotu, po_pozycji): naruszenie ⇒ VC; sprawdzian < 100% ⇒ PRZYRZAD; detekcja zgodna /
    mapa po fladze ⇒ SWIAT-KOD; cięcie bez wejścia ⇒ rezerwa (bez STOP); próg łaty S (2/4 dostępne ⇒ STOP-TEACH-3-S, 3/4 ⇒ dalej);
    czwarta rezerwa ⇒ STOP-TEACH-3-REZERWA (trzecia ⇒ dalej); stanowisko w locie ⇒ rezerwa.
Wyjście: results/TEACH/s3/dryrun/dryrun_s3.json; kod 1 przy niepowodzeniu.
"""
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types

ROOT = "/home/olga/projects/liquidpatrol"
T = os.path.join(ROOT, "results/TEACH/tools")
sys.path[:0] = [ROOT, T, os.path.join(ROOT, "results/NAD3/tools"), os.path.join(ROOT, "results/KONT/tools"),
                os.path.join(ROOT, "results/NAD3_RECON/tools"), os.path.join(ROOT, "results/ORTO_RECON/tools")]
OUT = os.path.join(ROOT, "results/TEACH/s3/dryrun")
SM = os.path.join(ROOT, "results/TEACH/s2/sm_smoke_S_c05")
LOT_P01 = os.path.join(ROOT, "results/NAD3/s3/p01_p1_c05_zew")
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


# ---------------------------------------------------------------- (1)
def czesc1():
    import teach_s3_run as R
    R.log = lambda *a, **k: None
    r = subprocess.run([sys.executable, os.path.join(T, "teach_s3_run.py"), "--sucho"], capture_output=True, text=True, cwd=ROOT)
    plan = json.loads(r.stdout.strip().splitlines()[-1])
    poz = {int(k): v for k, v in plan["pozycje"].items()}
    out = {"plan": {p: {k: poz[p][k] for k in ("nazwa", "env", "args")} for p in sorted(poz)}, "n_pozycji": len(poz)}
    nz = {p: R.niezmiennik(p, list(range(p, 15))) for p in range(1, 15)}
    nz_zle = R.niezmiennik(2, [1, 2])                                # pozycja ≠ pierwsza w planie ⇒ fałsz
    out["niezmiennik"] = {"wszystkie": all(nz.values()), "zla_kolejnosc_odrzucona": not nz_zle}
    mon = os.path.join(ROOT, "results/TEACH/s3/teach_s3_monitor.log")
    byl_mon = os.path.exists(mon)
    guard = {}
    for p in range(1, 15):
        env = {k: v for k, v in os.environ.items() if k not in ("PERC2_FASTDDS_PROFILE",) and not k.startswith(("BOOT_", "TEACH_"))}
        env.update(R.env_poz(p))
        eps, inj = R.args_poz(p)
        g = subprocess.run(["bash", "-uo", "pipefail", os.path.join(T, "teach_boot.sh"), "99", f"dryrun_guard_{p:02d}", eps, inj], env=env,
                           capture_output=True, text=True, timeout=120, cwd=ROOT)
        kom = (g.stdout.strip().splitlines() or [""])[-1][-160:]
        guard[p] = {"rc": g.returncode, "komunikat": kom, "ok": g.returncode == 5 and "brak PERC2_FASTDDS_PROFILE" in g.stdout
                    and "GUARD: " not in g.stdout.replace("GUARD: brak PERC2", "")}
        shutil.rmtree(os.path.join(ROOT, f"results/TEACH/s3/dryrun_guard_{p:02d}"), ignore_errors=True)
    zly = dict(os.environ); zly.update({**R.env_poz(1), "TEACH_ETAP": "s9"}); zly.pop("PERC2_FASTDDS_PROFILE", None)
    g = subprocess.run(["bash", "-uo", "pipefail", os.path.join(T, "teach_boot.sh"), "99", "dryrun_guard_zly", "5", "30"], env=zly,
                       capture_output=True, text=True, timeout=120, cwd=ROOT)
    shutil.rmtree(os.path.join(ROOT, "results/TEACH/s9"), ignore_errors=True)
    if not byl_mon and os.path.exists(mon):
        os.remove(mon)
    out["straznik"] = {"pozycje": guard, "etap_s9_odrzucony": g.returncode == 5 and "TEACH_ETAP" in g.stdout}
    out["bash_n"] = all(subprocess.run(["bash", "-n", os.path.join(T, f)]).returncode == 0 for f in ("teach_boot.sh", "teach_launch.sh"))
    oczek = {p: (("S", "5", "30", "0"), ("S", "10", "30", "0"), ("S", "5", "30", "0"), ("S", "10", "30", "0"), ("S", "10", "-", "1"),
                 ("M", "5", "30", "0"), ("M", "10", "30", "0"), ("M", "5", "30", "0"), ("M", "10", "30", "0"), ("J", "5", "-", "1"),
                 ("J", "5", "30", "0"), ("J", "10", "30", "0"), ("J", "5", "30", "0"), ("J", "10", "30", "0"))[p - 1] for p in range(1, 15)}
    zg = {p: (out["plan"][p]["env"]["BOOT_LATA"], out["plan"][p]["args"][0], out["plan"][p]["args"][1], out["plan"][p]["env"]["BOOT_CIEN"])
          == oczek[p] and out["plan"][p]["env"]["TEACH_ETAP"] == "s3" for p in range(1, 15)}
    zg[5] = zg[5] and out["plan"][5]["env"].get("BOOT_T_CIEN") == "176.5"
    zg[10] = zg[10] and out["plan"][10]["env"].get("BOOT_T_CIEN") == "173.6"
    out["plan_zgodny_z_promptem"] = zg
    out["PASS"] = (out["n_pozycji"] == 14 and all(zg.values()) and out["niezmiennik"]["wszystkie"] and out["niezmiennik"]["zla_kolejnosc_odrzucona"]
                   and all(v["ok"] for v in guard.values()) and out["straznik"]["etap_s9_odrzucony"] and out["bash_n"])
    return out


# ---------------------------------------------------------------- (2)
def czesc2():
    sw = json.load(open(os.path.join(ROOT, "results/TEACH/s1/swiaty.json")))["swiaty"]
    out = {}
    for L in ("S", "M", "J"):
        w = f"worlds/world_teach_{L}.sdf"
        r = subprocess.run(["bash", "-c", f"source harness/gz_env.sh >/dev/null 2>&1; gz sdf -k {w}"], capture_output=True, text=True,
                           cwd=ROOT, timeout=120)
        txt = open(os.path.join(ROOT, w)).read()
        zas = sorted(set(re.findall(r"<(?:albedo_map|uri)>([^<]+)</", txt)))
        brak = [z for z in zas if z.startswith("/") and not os.path.exists(z)]
        v = sw[w]
        out[L] = {"gz_sdf_k": r.stdout.strip()[-80:], "valid": r.returncode == 0 and "Valid" in r.stdout, "zasoby": len(zas), "brak": brak,
                  "sha_sdf": h(os.path.join(ROOT, w)) == v["sha256"], "tekstura_w_sdf": os.path.join(ROOT, v["tekstura"]) in zas,
                  "sha_tekstury": h(os.path.join(ROOT, v["tekstura"])) == v["tekstura_sha256"]}
        out[L]["ok"] = out[L]["valid"] and not brak and out[L]["sha_sdf"] and out[L]["tekstura_w_sdf"] and out[L]["sha_tekstury"]
    out["PASS"] = all(out[L]["ok"] for L in ("S", "M", "J"))
    return out


# ---------------------------------------------------------------- (3)
def kopia(tmp, nm):
    d = os.path.join(tmp, nm)
    shutil.copytree(SM, d, ignore=shutil.ignore_patterns("boot.ulg", "kadry", "percep.sock"))
    return d


def rw(p, fn):
    rows = [json.loads(l) for l in open(p)]
    rows = fn(rows)
    with open(p, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def czesc3():
    import teach_s3_spr as SPR
    tmp = tempfile.mkdtemp(prefix="teach_s3_ostr_")
    out = {}
    d = kopia(tmp, "czysty")
    s = SPR.sprawdz(d, zapis=False)
    out["SM"] = {"ok": s["ok"], "procent": s["procent"], "oslona_ticki": s["oslona"]["n"], "poprawki": s["poprawki"]["n"],
                 "max_abs_m": s["poprawki"]["max_abs_m"], "georef": {k: s["georef"][k] for k in ("d_theta_deg", "d_t_m")}}

    def mut_a(rows):
        for r in rows:
            if r.get("t") == "nf" and (r.get("fx") or {}).get("ok"):
                r["fx"]["p_fix_ne"][0] = round(r["fx"]["p_fix_ne"][0] + 0.001, 6); out["a_seq"] = r["fx"]["seq"]; break
        return rows

    def mut_b(rows):
        for r in rows:
            g = (r.get("teach") or {}).get("georef")
            if g:
                t_ost = max(w[0] for w in g["wiazania"])
                n0 = len(g["wiazania"])
                g["wiazania"] = [w for w in g["wiazania"] if w[0] != t_ost]
                out["b_usuniete"] = {"kadr": t_ost, "wiazan": n0 - len(g["wiazania"])}
        return rows

    def mut_c(rows):
        mis = [r for r in rows if r.get("phase") in ("approach", "hold", "orbit") and not r.get("desc") and r.get("ph") == "KONT"]
        r = mis[len(mis) // 2]
        r["dec"] = "REFUSE" if r["dec"] == "ALLOW" else "ALLOW"
        out["c_tick"] = r["tick"]
        return rows
    for nm, plik, fn, czesc in (("a_poprawka_0001", "nadir_obs.jsonl", mut_a, "poprawki"), ("b_wiazania_ostatniego", "nadir_obs.jsonl", mut_b, "georef"),
                                ("c_decyzja", "rama.jsonl", mut_c, "oslona")):
        d = kopia(tmp, nm)
        rw(os.path.join(d, plik), fn)
        s = SPR.sprawdz(d, zapis=False)
        inne = [k for k in ("oslona", "poprawki", "georef") if k != czesc and not s[k]["ok"]]
        szcz = {"poprawki": {k: s["poprawki"].get(k) for k in ("niezgodne", "max_abs_m")},
                "georef": {k: s["georef"].get(k) for k in ("d_theta_deg", "d_t_m")},
                "oslona": {k: s["oslona"].get(k) for k in ("dec", "rule", "faza")}}[czesc]
        out[nm] = {"wykryte": not s["ok"] and not s[czesc]["ok"], "czesc": czesc, "szczegoly": szcz, "inne_czesci_czerwone": inne}
    shutil.rmtree(tmp, ignore_errors=True)
    out["PASS"] = out["SM"]["ok"] and all(out[k]["wykryte"] for k in ("a_poprawka_0001", "b_wiazania_ostatniego", "c_decyzja"))
    return out


# ---------------------------------------------------------------- (4)
def czesc4():
    import teach_s2_dryrun as D
    import teach_s3_lot as LOT
    import nad3_krok
    import nad3_dane as N
    from harness import teach_map as TM
    from r03 import config as C
    from r03 import nadir_shield as NS

    def lok_bez(self, t_frame, obraz, ekf_q, ekf_pos, rec):            # atrapa: brak dopasowania przy każdej klatce
        rec["powod"] = "brak_dopasowania"
        return {"faza": "lok", "tau": round(t_frame - self.t_fix_int, 6), "kand": [], "k": None, "r": None, "zgodne": None,
                "innowacja": None, "ok": 0, "ms_cechy": 0.0, "ms_dop": 0.0}
    TM.Producent._lokalizuj = lok_bez
    tmpd = []
    mk0 = D.tempfile.mkdtemp

    def mk(*a, **k):
        p = mk0(*a, **k)
        if k.get("prefix") == "teach_syn_lot_":
            tmpd.append(p)
        return p
    D.tempfile = types.SimpleNamespace(**{**{n: getattr(tempfile, n) for n in dir(tempfile) if not n.startswith("_")}, "mkdtemp": mk})
    import teach_analyze as A
    w = D.syntetyczny_lot()
    d = tmpd[0]
    # osłona odtworzona ⇒ ticki tk (dec, rule, ph, cause) i zdarzenie refuse w pierwszym zatrzasku
    m = next(r for r in A.jl(os.path.join(d, "trace.jsonl"), "meta"))
    ml = (m.get("teach") or {}).get("oslona") or {}
    nf = A.jl(os.path.join(d, "nadir_obs.jsonl"), "nf")
    fx = {r["fx"]["seq"]: r["fx"] for r in nf}
    rama = sorted(A.jl(os.path.join(d, "rama.jsonl")), key=lambda r: r["tick"])
    tk = {r["tick"]: r for r in A.jl(os.path.join(d, "trace.jsonl"), "tk")}
    demo = {r["tick"]: r for r in A.jl(os.path.join(d, "demo.jsonl"))}
    sh = NS.NadirShield(nadir_mode=True, kont_mode=True, nad3=True, tabela=ml.get("tabela"), tabela_sha=ml.get("sha256_tabeli"))
    sh.reset(); sh.pos_debounce_ticks = C.DEBOUNCE_TICKS; sh.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))

    class Kl:
        d_ne, t_fix, kosz, tryb = [0.0, 0.0], None, None, None
    kl, nowe, ref_ev = Kl(), {}, None
    for r in rama:
        for ob in r.get("obs") or []:
            mm = fx[ob["seq"]]
            kl.d_ne, kl.t_fix = list(mm["d_ne"]), mm["t_fix"]
        t, dm = tk.get(r["tick"]), demo.get(r["tick"])
        if t is None or dm is None:
            continue
        pe = r["p_ekf"]
        dd, _ = nad3_krok.krok(sh, r["tick"], pe, [pe[0] + kl.d_ne[0], pe[1] + kl.d_ne[1], pe[2]], dm["own_vel_ned"], r["sp_ekf"], r["sp_net"],
                               "PATROL", t["pf"], t["cs"], r["sim"], t.get("dr"), kl)
        k = dd.get("kont") or {}
        nowe[r["tick"]] = {"dec": dd["decision"], "rule": dd.get("rule"), "ph": k.get("phase"), "cause": dd.get("detail")}
        if ref_ev is None and dd["decision"] == "REFUSE":
            ref_ev = {"t": "event", "sim": r["sim"], "ev": "refuse", "episode_id": r["ep"], "reason": dd.get("reason"), "detail": dd.get("detail"),
                      "rule": dd.get("rule")}
    linie = []
    for l in open(os.path.join(d, "trace.jsonl")):
        x = json.loads(l)
        if x.get("t") == "tk" and x["tick"] in nowe:
            x.update(nowe[x["tick"]])
        linie.append(x)
        if ref_ev is not None and x.get("t") == "tk" and x["sim"] >= ref_ev["sim"] and not ref_ev.get("_w"):
            ref_ev["_w"] = True; linie.append({k: v for k, v in ref_ev.items() if k != "_w"})
    with open(os.path.join(d, "trace.jsonl"), "w") as f:
        for x in linie:
            f.write(json.dumps(x) + "\n")
    for f in ("manifest.json", "ulg.jsonl.gz", "boot.ulg", "nadir_obs.jsonl.summary.json"):
        if not os.path.exists(os.path.join(d, f)) and os.path.exists(os.path.join(LOT_P01, f)):
            os.symlink(os.path.join(LOT_P01, f), os.path.join(d, f))
    sd = LOT.sedzia(d, 1)
    e = next(x for x in sd["epizody"] if x["ciecie"])
    o = {"analizator_skonczyl": os.path.exists(os.path.join(d, "wyniki_teach.json")), "przyjete": sum(1 for r in nf if r["fx"]["ok"]),
         "zamkniecia": w["zamkniecia"], "B": e["B"], "B1": {k: e["B_szczegoly"]["B1"][k] for k in ("przekroczenia", "ticki_ocenione", "max_e_do_U")},
         "D1": e["D1"], "odmowa_w_misji": e["odmowa_w_misji"], "litera_ok": sd["litera_ok"],
         "b1_nieocenione_w_misji": sd["b1_nieocenione_w_misji"], "b1_nieocenione_przyczyny": sd["b1_nieocenione"]["przyczyny"],
         "uwaga": "trajektoria syntetyczna (p01) nie schodzi po zatrzasku — ticki KONT_REFUSE zostają w fazie misji; w locie zejście "
                  "D5 wyłącza je z misji (desc)"}
    o["PASS"] = (o["analizator_skonczyl"] and o["przyjete"] == 0 and o["zamkniecia"] == 1 and set(e["B"]) >= {"B1", "B2", "B3", "B4"}
                 and all(v is not None for v in e["B"].values()) and e["odmowa_w_misji"] is not None
                 and e["odmowa_w_misji"]["przyczyna"] == "τ*" and not (e["D1"] or {}).get("dostepne", True))
    shutil.rmtree(d, ignore_errors=True)
    return o


# ---------------------------------------------------------------- (5)
def czesc5():
    import teach_s3_run as R
    R.log = lambda *a, **k: None
    sd = lambda **k: {"litera_ok": True, "wazny": True, "niewaznosc": [], **k}
    ev = ["episode_start", "denial"]
    sc = {"naruszenie": (R.status_lotu(0, "ciecie", ev, {"ok": True}, sd(litera_ok=False)), ("naruszenie", "STOP-TEACH-3-VC")),
          "sprawdzian_ponizej_100": (R.status_lotu(0, "ciecie", ev, {"ok": True}, sd(wazny=False, niewaznosc=["przyrzad"])),
                                     ("niewazny_przyrzad", "STOP-TEACH-3-PRZYRZAD")),
          "detekcja_zgodna": (R.status_lotu(0, "ciecie", ev, {"ok": True}, sd(wazny=False, niewaznosc=["swiat_kod"])),
                              ("niewazny_swiat_kod", "STOP-TEACH-3-SWIAT-KOD")),
          "ciecie_bez_wejscia": (R.status_lotu(0, "ciecie", ["episode_start"], {"ok": True}, sd(wazny=False, niewaznosc=["wejscie"])),
                                 ("bez_wejscia", None)),
          "stanowisko_w_locie": (R.status_lotu(0, "ciecie", [], {"ok": False}, None), ("niewazny_stanowisko", None)),
          "breach": (R.status_lotu(0, "ciecie", ev + ["breach"], {"ok": True}, sd()), ("breach", "STOP-TEACH-3-BREACH")),
          "wazny": (R.status_lotu(0, "ciecie", ev, {"ok": True}, sd()), ("wazny", None))}
    ks = lambda dost: [{"pozycja": p, "status": "wazny", "sedzia": {"D1_dostepne": p <= dost}} for p in (1, 2, 3, 4)]
    sc["prog_S_2z4"] = (R.po_pozycji(4, ks(2), 0, 4), "STOP-TEACH-3-S")
    sc["prog_S_3z4"] = (R.po_pozycji(4, ks(3), 0, 4), None)
    sc["czwarta_rezerwa"] = (R.po_pozycji(6, ks(4), 4, 9), "STOP-TEACH-3-REZERWA")
    sc["trzecia_rezerwa"] = (R.po_pozycji(6, ks(4), 3, 8), None)
    sc["noga_23"] = (R.po_pozycji(13, ks(4), 3, 18), "STOP-TEACH-3-NOGA")
    out = {k: {"wynik": list(v[0]) if isinstance(v[0], tuple) else v[0], "oczek": list(v[1]) if isinstance(v[1], tuple) else v[1],
               "ok": v[0] == v[1]} for k, v in sc.items()}
    out["PASS"] = all(v["ok"] for v in out.values())
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    os.environ.setdefault("NAD3_CACHE", tempfile.mkdtemp(prefix="nad3_cache_"))
    wyn = {}
    for nm, f in (("1_plan_straznik", czesc1), ("2_swiaty", czesc2), ("3_sprawdzian_ostrosc", czesc3), ("4_lot_bez_poprawek", czesc4),
                  ("5_reguly", czesc5)):
        print(f"({nm})", flush=True)
        wyn[nm] = f()
        print("  PASS", wyn[nm]["PASS"], flush=True)
    wyn["PASS"] = all(v["PASS"] for v in wyn.values())
    json.dump(wyn, open(os.path.join(OUT, "dryrun_s3.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print("PASS", wyn["PASS"])
    sys.exit(0 if wyn["PASS"] else 1)


if __name__ == "__main__":
    main()
