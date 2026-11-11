#!/usr/bin/env python3
"""results/NAD2/tools/nad2_s3_dryrun.py — PROMPT_NAD2_S3 §0.1/§0.2: próba na sucho kolejki S3 (0 bootów).

(1) kod z bd975df5: `git diff --quiet bd975df5 --` na osłonie, literze, tabeli, certach, driverze, kroku, boocie, launcherze,
    analizatorze, wyciągu ULG i sprawdzianach smoke ⇒ zero zmian.
(2) kolejka `nad2_s3_run.py --sucho` pod `bash -uo pipefail -c` ⇒ 16 pozycji w kolejności NADIR S4, env 1/1/0/NAD2, 0 bootów.
(3) boot z nazwą „../s3/<x>”: strażnik trybów (BOOT_LITERA=NADIR1 przy NADIR_MODE=1 ⇒ kod 5) i REPO-2 na katalogu
    results/NAD2/s3/dryrun/_repo2 z manifestem (⇒ kod 4, komunikat z OUTDIR w s3) — oba przed czymkolwiek ciężkim; dopiski do
    monitora smoke przeniesione (przenies_monitor) do dryrun/monitor_dryrun.log, plik smoke bajtowo jak przed próbą (sha256).
(4) łańcuch po boocie (po_boocie) na kopii smoke c11_s02 (katalog tymczasowy, boot.ulg dowiązany): cięcie ⇒ analizator B1–B4 i D1
    PASS, sprawdziany (s1)–(s3) PASS; nominał syntetyczny (rama i trace obcięte przed cięciem, bez denial) ⇒ (s1)–(s3) PASS;
    negatyw: r_est = |p_EKF| w tickach utraty ⇒ (s3) FAIL, R_k zmienione ⇒ (s2) FAIL i przyrzad_ok False.
Wyjście: results/NAD2/s3/dryrun/dryrun_s3.json.
"""
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = "/home/olga/projects/liquidpatrol"
T = os.path.join(ROOT, "results/NAD2/tools")
OUT = os.path.join(ROOT, "results/NAD2/s3/dryrun")
SMOKE = os.path.join(ROOT, "results/NAD2/s2/c11_s02")
sys.path[:0] = [T, ROOT]
ZAMROZONE = ["r03/nadir_shield.py", "r03/kont_shield.py", "r03", "harness/nadir_fix.py", "harness/nadir_obs.py", "r01/proofs",
             "results/NAD2/s1/freeze_U.json", "results/NAD2/tools/nad2_flight.py", "results/NAD2/tools/nad2_krok.py",
             "results/NAD2/tools/nad2_boot.sh", "results/NAD2/tools/nad2_launch.sh", "results/NAD2/tools/nad2_analyze.py",
             "results/NAD2/tools/nad2_ulg.py", "results/NAD2/tools/nad2_s2_spr.py", "results/NAD2/tools/nad2_certs_selfcheck.py",
             "results/NADIR/s4/scenario_manifest_s4.json"]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def czesc1():
    ist = [p for p in ZAMROZONE if os.path.exists(os.path.join(ROOT, p))]
    r = subprocess.run(["git", "diff", "--quiet", "bd975df5", "--"] + ist, cwd=ROOT)
    u = subprocess.run(["git", "status", "--porcelain", "--"] + ist, cwd=ROOT, capture_output=True, text=True).stdout
    return {"sciezki": ist, "brak": [p for p in ZAMROZONE if p not in ist], "diff_rc": r.returncode, "porcelain": u,
            "PASS": r.returncode == 0 and not u.strip() and len(ist) == len(ZAMROZONE)}


def czesc2():
    r = subprocess.run(["bash", "-uo", "pipefail", "-c", f"python3 {T}/nad2_s3_run.py --sucho"], cwd=ROOT, capture_output=True, text=True)
    try:
        j = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        j = None
    oczek = ["nom_b1", "c01_s01", "c01_s03", "c02_s01", "c02_s03", "c05_s01", "c05_s02", "c08_s01", "c08_s02", "c10_s01", "c10_s02",
             "c11_s01", "c11_s02", "nom_b2", "nom_b3", "nom_b4"]
    kol = [k[0] for k in (j or {}).get("kolejka", [])]
    ep = {k[0]: (k[1], k[2]) for k in (j or {}).get("kolejka", [])}
    ok = (r.returncode == 0 and kol == oczek and j["budzet"] == 19 and j["uzyte"] == 0
          and j["env"] == {"BOOT_NADIR_MODE": "1", "BOOT_KONT_MODE": "1", "BOOT_PASSTHROUGH": "0", "BOOT_LITERA": "NAD2"}
          and ep["c11_s02"] == ("23", "30") and ep["c01_s01"] == ("1", "30") and ep["nom_b4"] == ("12,13,14,15", "-"))
    return {"rc": r.returncode, "kolejka": kol, "epizody": ep, "PASS": ok}


def czesc3():
    import nad2_s3_run as Q
    sys.path.insert(0, os.path.join(ROOT, "results/KONT/tools"))
    mon0 = sha(Q.MON_S2)
    rep = os.path.join(ROOT, "results/NAD2/s3/dryrun/_repo2")
    os.makedirs(rep, exist_ok=True)
    json.dump({"dryrun": "REPO-2"}, open(os.path.join(rep, "manifest.json"), "w"))
    wyn = {}
    log_d = os.path.join(OUT, "monitor_dryrun.log")
    for tag, envb, oczek in (("guard_litera", {**Q.ENV_BOOT, "BOOT_LITERA": "NADIR1"}, 5), ("repo2", dict(Q.ENV_BOOT), 4)):
        env = {**os.environ, **envb, "PERC2_FASTDDS_PROFILE": Q.G.PROFIL}
        n0 = os.path.getsize(Q.MON_S2)
        r = subprocess.run(["bash", "-uo", "pipefail", Q.BOOT, "0", "../s3/dryrun/_repo2", "23", "30"], cwd=ROOT, env=env,
                           capture_output=True, text=True, timeout=60)
        with open(Q.MON_S2, "rb") as f:
            f.seek(n0)
            nowe = f.read()
        open(log_d, "ab").write(nowe)
        os.truncate(Q.MON_S2, n0)
        wyn[tag] = {"rc": r.returncode, "oczekiwany": oczek, "wyjscie": (r.stdout + r.stderr)[-300:], "ok": r.returncode == oczek}
    wyn["repo2"]["ok"] &= "REPO-2" in wyn["repo2"]["wyjscie"] and not os.path.exists(os.path.join(ROOT, "results/NAD2/s2/dryrun/_repo2"))
    # przenies_monitor z kolejki: dopisek testowy ⇒ do MON_S3 zastępczego, plik smoke wraca
    n0 = os.path.getsize(Q.MON_S2)
    Q.MON_S3 = os.path.join(OUT, "monitor_przenies_test.log")
    open(Q.MON_S2, "ab").write(b"[dryrun] linia testowa przenies_monitor\n")
    Q.przenies_monitor(n0)
    wyn["przenies_monitor"] = {"ok": open(Q.MON_S3, "rb").read().endswith(b"linia testowa przenies_monitor\n")}
    wyn["monitor_smoke_nietkniety"] = sha(Q.MON_S2) == mon0
    shutil.rmtree(rep)
    wyn["PASS"] = all(v["ok"] for v in wyn.values() if isinstance(v, dict)) and wyn["monitor_smoke_nietkniety"]
    return wyn


def kopia(tmp, nazwa):
    d = os.path.join(tmp, nazwa)
    os.makedirs(d)
    for f in ("trace.jsonl", "rama.jsonl", "nadir_obs.jsonl", "kont_tempo.json"):
        shutil.copy(os.path.join(SMOKE, f), d)
    os.symlink(os.path.join(SMOKE, "boot.ulg"), os.path.join(d, "boot.ulg"))
    return d


def zapisz_jl(p, rows):
    with open(p, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def czesc4():
    import nad2_s3_run as Q
    import nad2_s3_spr as SP
    tmp = tempfile.mkdtemp(prefix="nad2s3dry_")
    wyn = {}
    try:
        d = kopia(tmp, "c11_s02")
        po = Q.po_boocie(d, False)
        o = po["an"]["epizody"][0]
        wyn["ciecie"] = {"B": {b: o[b]["ok"] for b in ("B1", "B2", "B3", "B4")}, "D1": o["D1"], "spr": po["spr"]["ok"],
                         "ulg": po["ulg"].get("MB"), "ok": all(o[b]["ok"] for b in ("B1", "B2", "B3", "B4")) and o["D1"]["dostepne"]
                         and all(po["spr"]["ok"].values()) and po["spr"]["przyrzad_ok"]}
        # nominał syntetyczny: wszystko przed cięciem, bez denial
        dn = kopia(tmp, "nom_syn")
        ev = [json.loads(l) for l in open(os.path.join(dn, "trace.jsonl"))]
        t_cut = next(r["sim"] for r in ev if r.get("t") == "event" and r.get("ev") == "denial")
        zapisz_jl(os.path.join(dn, "trace.jsonl"), [r for r in ev if r.get("sim", 0) < t_cut and r.get("ev") != "denial"])
        rama = [json.loads(l) for l in open(os.path.join(dn, "rama.jsonl"))]
        zapisz_jl(os.path.join(dn, "rama.jsonl"), [r for r in rama if r["sim"] < t_cut])
        nf = [json.loads(l) for l in open(os.path.join(dn, "nadir_obs.jsonl"))]
        zapisz_jl(os.path.join(dn, "nadir_obs.jsonl"), [r for r in nf if r.get("t") != "nf" or r["sim"] < t_cut])
        sn = SP.sprawdz(dn, True)
        wyn["nominal_syn"] = {"spr": sn["ok"], "ticki_nominal": sn["szczegoly"]["s3"]["ticki_nominal"], "ok": all(sn["ok"].values())}
        # negatywy na cięciu
        dneg = kopia(tmp, "neg")
        rama = [json.loads(l) for l in open(os.path.join(dneg, "rama.jsonl"))]
        for r in rama:
            if r.get("ph") in ("KONT", "KONT_REFUSE") and r.get("nad2"):
                r["nad2"]["r_est"] = round(math.hypot(r["p_ekf"][0], r["p_ekf"][1]), 4)
                if r.get("R_k") is not None:
                    r["R_k"] = round(r["R_k"] + 0.5, 3)
        zapisz_jl(os.path.join(dneg, "rama.jsonl"), rama)
        sg = SP.sprawdz(dneg, False)
        wyn["negatyw"] = {"spr": sg["ok"], "przyrzad_ok": sg["przyrzad_ok"],
                          "ok": sg["ok"]["s3"] is False and sg["ok"]["s2"] is False and sg["przyrzad_ok"] is False}
    finally:
        shutil.rmtree(tmp)
    wyn["PASS"] = all(v["ok"] for v in wyn.values() if isinstance(v, dict))
    return wyn


def main():
    os.makedirs(OUT, exist_ok=True)
    w = {"1_kod_bd975df5": czesc1(), "2_kolejka_sucho": czesc2(), "3_boot_s3": czesc3(), "4_lancuch": czesc4()}
    w["PASS"] = all(v["PASS"] for v in w.values())
    json.dump(w, open(os.path.join(OUT, "dryrun_s3.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: (v["PASS"] if isinstance(v, dict) else v) for k, v in w.items()}))


if __name__ == "__main__":
    main()
