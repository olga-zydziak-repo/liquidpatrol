#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_v8_bramka.py — bramka FROZEN aktu 8 (PROMPT_DEMOC_V8 §0.4), wykonaniem, przed bootem.

Sprawdza: testy nogi TEACH (pytest test_teach_s1 + test_teach_s2), selfcheck certów (teach_certs_selfcheck), tabelę U TEACH
(sha256_tabeli w pliku = 7a56ba1b…), producenta (harness/nadir_obs.py db96a4a7, harness/teach_map.py 4eefedda), tor mapy
(results/TEACH/s1/tor.json: kan_sha(tor) = sha256_toru), światy i tekstury S/J (results/TEACH/s1/swiaty.json), model
x500_teach_flow (źródło = zainstalowany), wagi net/frozen/ncp.npz, brak zmian kodu lotu/osłony/narzędzi TEACH od STOP-TEACH-3
(5ad2555e) w ścieżkach toru lotu, timesyncd. Zapis: results/DEMO_C/s8_mapa/bramka_frozen.json; kod wyjścia 0 = PASS.
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = "/home/olga/projects/liquidpatrol"
OUT = os.path.join(ROOT, "results/DEMO_C/s8_mapa/bramka_frozen.json")
sys.path.insert(0, ROOT)


def sha(p):
    return hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()


def run(cmd, timeout=1200):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr).strip().splitlines()[-3:]


def main():
    w = {}
    rc, ogon = run([sys.executable, "-m", "pytest", "-q", "results/TEACH/tools/test_teach_s1.py", "results/TEACH/tools/test_teach_s2.py"])
    w["testy_teach"] = {"rc": rc, "ogon": ogon, "ok": rc == 0}
    rc, ogon = run([sys.executable, "results/TEACH/tools/teach_certs_selfcheck.py"])
    w["certs_selfcheck"] = {"rc": rc, "ogon": ogon, "ok": rc == 0 and any("PASS (24/24" in l for l in ogon)}
    tab = json.load(open(os.path.join(ROOT, "results/TEACH/s1/freeze_U_TEACH.json")))
    w["tabela"] = {"sha256_tabeli": tab["sha256_tabeli"], "ok": tab["sha256_tabeli"].startswith("7a56ba1b")}
    w["producent"] = {"harness/nadir_obs.py": sha("harness/nadir_obs.py"), "harness/teach_map.py": sha("harness/teach_map.py")}
    w["producent"]["ok"] = w["producent"]["harness/nadir_obs.py"].startswith("db96a4a7") and w["producent"]["harness/teach_map.py"].startswith("4eefedda")
    from harness import teach_map as T
    tor = json.load(open(os.path.join(ROOT, "results/TEACH/s1/tor.json")))
    w["tor_mapy"] = {"sha256_toru": tor["sha256_toru"], "kan_sha": T.kan_sha(tor["tor"])}
    w["tor_mapy"]["ok"] = w["tor_mapy"]["sha256_toru"] == w["tor_mapy"]["kan_sha"]
    sw = json.load(open(os.path.join(ROOT, "results/TEACH/s1/swiaty.json")))
    sv = {}
    for k in ("S", "J"):
        p = f"worlds/world_teach_{k}.sdf"
        e = sw["swiaty"][p]
        sv[k] = {"swiat": sha(p), "swiat_ok": sha(p) == e["sha256"], "swiat_px4_ok": sha("PX4-Autopilot/Tools/simulation/gz/" + p) == e["sha256"],
                 "tekstura": sha(e["tekstura"]), "tekstura_ok": sha(e["tekstura"]) == e["tekstura_sha256"]}
    w["swiaty"] = sv
    msrc = "results/TEACH/s1/zrodla/x500_teach_flow/model.sdf"; minst = "PX4-Autopilot/Tools/simulation/gz/models/x500_teach_flow/model.sdf"
    w["model"] = {"zrodlo": sha(msrc), "zainstalowany": sha(minst), "ok": sha(msrc) == sha(minst) == sw["model"][msrc]}
    w["wagi_ncp"] = {"sha": sha("net/frozen/ncp.npz"), "ok": sha("net/frozen/ncp.npz").startswith("0337d5ea")}
    sciezki = ["harness", "r03", "r01", "net", "bench", "results/TEACH/tools", "results/NAD3/tools", "results/NAD2/tools", "results/NADIR/tools",
               "results/KONT/tools", "results/SKAN2/tools", "results/PERC2/tools", "worlds/world_teach_S.sdf", "worlds/world_teach_J.sdf"]
    d = subprocess.run(["git", "diff", "--stat", "5ad2555e", "HEAD", "--"] + sciezki, cwd=ROOT, capture_output=True, text=True).stdout.strip()
    w["kod_lotu_od_5ad2555e"] = {"diff_stat": d or "(pusty)", "ok": d == ""}
    ts = subprocess.run(["systemctl", "is-active", "systemd-timesyncd"], capture_output=True, text=True).stdout.strip()
    w["timesyncd"] = {"stan": ts, "uwaga": "przed bootem ma być nieaktywny (kolejka sprawdza)"}
    w["PASS"] = all(v.get("ok", True) for v in w.values() if isinstance(v, dict) and "ok" in v) and \
        all(x["swiat_ok"] and x["swiat_px4_ok"] and x["tekstura_ok"] for x in sv.values())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(w, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(w, ensure_ascii=False, indent=1))
    sys.exit(0 if w["PASS"] else 1)


if __name__ == "__main__":
    main()
