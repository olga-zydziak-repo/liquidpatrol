#!/usr/bin/env python3
"""results/NADIR/tools/nadir_stanowisko_przyrzad.py — rozszerzenie diagnozy ANEKS_NADIR-3 po M3 (sygnał CC 10.11), 0 bootów:
test przyrządu. Kolejność A, C, B, A, C, B:
  A = oryginalne nadir_n1_ab.run(i, "A5", e) (import READ-ONLY, rig A_5, WARM 20 s + okno 120 s jak 9.11), bez telemetrii hosta
      i bez dodatkowych procesów; jedyna zmiana: katalogi wyjścia N1/ZRN modułu przekierowane do results/NADIR/s4/stanowisko/przyrzad
      (oryginał pisałby do results/NADIR/s1/n1 i nadpisał pliki odniesienia; rig generowany tą samą funkcją rig(5) — sha porównane
      z results/NADIR/s1/zrodla/n1/rig_ab_5hz.sdf);
  C = to samo co A z włączoną samą telemetrią hosta (nadir_stanowisko.Telemetria: powershell.exe + nvidia-smi co 5 s);
  B = nowa sonda nadir_stanowisko.sonda tak, jak szła w matrycy (gz_a5 60 s + det_v2 + CPU + telemetria, PROFIL_OEM z env).
Tempo każdego przebiegu: nadir_ab.regresja (rozgrzewka 20 s) w oknie 120 s (metoda 9.11) i 60 s (metoda sondy); dla B dostępne
tylko okno 60 s (sonda zapisuje 83 s). Profil tempa co 10 s ściany (Δsim/Δwall kolejnych przedziałów). Odniesienie 9.11 z plików
results/NADIR/s1/n1/rtf_{1,7}_A5.jsonl przeliczone tą samą funkcją.
Na końcu: zmiany w Windows od 9.11 10:00 (historia Windows Update, Get-HotFix, zdarzenia MsiInstaller 11707/1033, sterownik GPU
z Win32_VideoController, wsl --version).
Wyjście: results/NADIR/s4/stanowisko/przyrzad/przyrzad.json
"""
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = "/home/olga/projects/liquidpatrol"
T = os.path.join(ROOT, "results/NADIR/tools")
sys.path.insert(0, T)
OUT = os.path.join(ROOT, "results/NADIR/s4/stanowisko/przyrzad")
ORDER = ["A", "C", "B", "A", "C", "B"]
REF = [os.path.join(ROOT, f"results/NADIR/s1/n1/rtf_{i}_A5.jsonl") for i in (1, 7)]
RIG_REF = os.path.join(ROOT, "results/NADIR/s1/zrodla/n1/rig_ab_5hz.sdf")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def okna(p):
    import nadir_ab as AB
    out = {}
    for w in (120.0, 60.0):
        AB.WARM_S, AB.WIN_S = 20.0, w
        out[f"okno{int(w)}"] = AB.regresja(p)[0]
    AB.WARM_S, AB.WIN_S = 20.0, 120.0
    return out


def profil10(p):
    r = [json.loads(l) for l in open(p) if l.strip()]
    w0, out, i = r[0]["wall"], [], 0
    for j, x in enumerate(r):
        if x["wall"] - r[i]["wall"] >= 10:
            out.append([round(r[i]["wall"] - w0), round((x["sim"] - r[i]["sim"]) / (x["wall"] - r[i]["wall"]), 3)])
            i = j
    return out


def ps(cmd):
    r = subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd], capture_output=True, cwd="/mnt/c", timeout=300)
    return r.stdout.decode("cp852", "replace").strip()


def windows_zmiany():
    od = "2026-11-09 10:00"
    return {
        "od": od,
        "windows_update_historia": ps(
            "$s=New-Object -ComObject Microsoft.Update.Session; $h=$s.CreateUpdateSearcher(); $n=$h.GetTotalHistoryCount();"
            "$h.QueryHistory(0,[math]::Min($n,60)) | Where-Object { $_.Date -ge [datetime]'" + od + "' } |"
            " Select-Object @{n='Date';e={$_.Date.ToString('s')}},Title,ResultCode,Operation | ConvertTo-Json -Compress"),
        "hotfix": ps("Get-HotFix | Where-Object { $_.InstalledOn -ge [datetime]'" + od + "' } | Select-Object HotFixID,Description,"
                     "@{n='InstalledOn';e={$_.InstalledOn.ToString('s')}} | ConvertTo-Json -Compress"),
        "msi_instalacje": ps("Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='MsiInstaller'; Id=11707,1033;"
                             " StartTime=[datetime]'" + od + "'} -ErrorAction SilentlyContinue | Select-Object "
                             "@{n='t';e={$_.TimeCreated.ToString('s')}},Id,Message | ConvertTo-Json -Compress"),
        "sterownik_gpu": ps("Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,"
                            "@{n='DriverDate';e={$_.DriverDate.ToString('s')}} | ConvertTo-Json -Compress"),
        "wsl_version": subprocess.run(["wsl.exe", "--version"], capture_output=True, cwd="/mnt/c").stdout
                       .decode("utf-16-le", "replace").replace("\x00", "").strip(),
        "nvidia_smi_driver": subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
                                            capture_output=True, text=True).stdout.strip(),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    import nadir_n1_ab as N
    import nadir_frames as NF
    import nadir_stanowisko as S
    N.N1, N.ZRN = OUT, OUT
    S.OUT = os.path.join(OUT, "sonda")
    os.makedirs(S.OUT, exist_ok=True)
    S.RIG_SHA = sha(S.RIG)
    e = NF.env()
    NF.teardown()
    res = {"opis": __doc__.split("\n\n")[0], "kolejnosc": ORDER, "profil_oem": os.environ.get("PROFIL_OEM", "nie podany"),
           "odniesienie_9_11": {os.path.relpath(p, ROOT): {**okna(p), "profil10": profil10(p)} for p in REF},
           "przebiegi": []}
    for i, tag in enumerate(ORDER):
        t0 = time.strftime("%H:%M:%S")
        if tag in ("A", "C"):
            tel = S.Telemetria(os.path.join(OUT, f"telemetria_{i}_{tag}.jsonl"), 400) if tag == "C" else None
            N.AB.WARM_S, N.AB.WIN_S = 20.0, 120.0          # sonda B przestawia okno modułu na 60 s — A/C zawsze jak 9.11
            try:
                r = N.run(i, "A5", e)
            finally:
                if tel:
                    tel.close()
            rp = os.path.join(OUT, f"rtf_{i}_A5.jsonl")
            os.replace(rp, os.path.join(OUT, f"rtf_{i}_{tag}.jsonl"))
            rp = os.path.join(OUT, f"rtf_{i}_{tag}.jsonl")
            wpis = {"i": i, "tag": tag, "t": t0, "n1_run": r, **okna(rp), "profil10": profil10(rp)}
            if tag == "C":
                wpis["c"] = S.podsumuj_tel(os.path.join(OUT, f"telemetria_{i}_{tag}.jsonl"))
        else:
            r = S.sonda(f"P{i}_B")
            rp = os.path.join(S.OUT, f"rtf_P{i}_B.jsonl")
            wpis = {"i": i, "tag": tag, "t": t0, "okno120": None, "okno60": r["a"]["gz_a5"], "profil10": profil10(rp),
                    "det_p50_ms": r["b_det_v2"].get("p50_ms"), "cpu": r["b_cpu"], "c": r.get("c_okno_a")}
        res["przebiegi"].append(wpis)
        print("PRZEBIEG", json.dumps({k: wpis.get(k) for k in ("i", "tag", "t", "okno120", "okno60")}), flush=True)
    res["rig_sha_wygenerowany"] = sha(os.path.join(OUT, "rig_ab_5hz.sdf"))
    res["rig_sha_odniesienia"] = sha(RIG_REF)
    res["rig_zgodny"] = res["rig_sha_wygenerowany"] == res["rig_sha_odniesienia"]
    res["windows"] = windows_zmiany()
    json.dump(res, open(os.path.join(OUT, "przyrzad.json"), "w"), ensure_ascii=False, indent=1)
    print("KONIEC", json.dumps({t: [p["okno120"] or p["okno60"] for p in res["przebiegi"] if p["tag"] == t] for t in "ACB"}), flush=True)


if __name__ == "__main__":
    main()
