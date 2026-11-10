#!/usr/bin/env python3
"""results/NADIR/tools/nadir_stanowisko.py — ANEKS_NADIR-3 §3: sonda stanowiska (0 bootów, bez PX4, nic nie uzbraja).

Tryby:
  sonda <tag>                 §3.1 (a)+(b)+(c): gz_a5 → det_v2 CUDA → mikropróba CPU, telemetria hosta w tle przez cały czas
                              ⇒ results/NADIR/s4/stanowisko/stanowisko_<tag>.json + telemetria_<tag>.jsonl
  bramka <tag>                §3.4: samo (a) z telemetrią; GO ⇔ gz_a5 ≥ 0.90 ⇒ kod 0, NO-GO ⇒ kod 1, błąd ⇒ kod 2
  seria <tag> <min> <okres_s> korekta Olgi do M3 (10.11): telemetria ciągła przez <min> minut, sonda co <okres_s> s
  telemetria <plik> <s>       §3.5: sama telemetria hosta (3.1(c)) do pliku jsonl przez <s> sekund
  Profil OEM (PredatorSense) nie jest czytelny przez powercfg — deklaruje go operator: PROFIL_OEM=<wydajny|turbo|…> w env,
  zapisywany w każdym wyniku (decyzja Olgi 10.11 do M5). Każda sonda zapisuje glxinfo -B (renderer) i GPU w oknach (a)/(b)
  jako dowód, że render i detektor idą przez GPU.
  sesja                       §3.1(d): procesor, Windows, WSL, sterownik GPU, limity czasu ekranu i uśpienia ⇒ sesja_<data>.json

(a) gz_a5: goły gz `world_nadir_A3` + rig A_5 (results/NADIR/s1/zrodla/n1/rig_ab_5hz.sdf, sha pilnowane — plik czytany, nie
    generowany), spawn (5, 5, 12, yaw 30), konsumenci imager/flow/nadir z detekcją ArUco jak nadir_n1_ab.run; acts.rtf_sampler;
    dsim/dwall z regresji (nadir_ab.regresja) po rozgrzewce 20 s w oknie 60 s (§3.1(a); odniesienie NAPRAWA-N1 0.9283 / 0.9271
    liczone w oknie 120 s). Logi serwera do katalogu stanowiska, nie do results/NADIR/s1.
(b) det_v2 (harness/det_v2.DetV2, CUDA, PYTHONPATH .b0deps jak percepcja w boocie) na stałej klatce z repo
    (results/KONT/s1/frames/R1_p1_srodek_z10.png, sha w wyniku): 20 rozgrzewki + 300 wnioskowań top1 ⇒ p50/p95 ms.
    Mikropróba CPU: stała praca jednowątkowa (suma kwadratów 0..2e6 w czystym Pythonie) ×10 ⇒ mediana ms; ta sama
    w 8 procesach równolegle (każdy ×10) ⇒ mediana ms.
(c) telemetria: jeden trwały proces powershell.exe (klasy CIM, nazwy niezależne od języka): per procesor logiczny
    [nazwa, PercentProcessorPerformance, PercentofMaximumFrequency, PercentProcessorUtility], czołówka 5 procesów po CPU
    (różnice TotalProcessorTime, % całej maszyny), Win32_Battery, powercfg /getactivescheme; równolegle nvidia-smi
    (utilization, temperatura, power.draw, zegary SM/MEM, pstate, clocks_event_reasons.active) co 5 s.
teardown gz jak nadir_frames.teardown (pkill gz sim) — tryby uruchamiać wyłącznie poza bootem.
"""
import hashlib
import json
import os
import statistics
import subprocess
import sys
import threading
import time

ROOT = "/home/olga/projects/liquidpatrol"
T = os.path.join(ROOT, "results/NADIR/tools")
sys.path.insert(0, T)
OUT = os.path.join(ROOT, "results/NADIR/s4/stanowisko")
W = "world_nadir_A3"
RIG = os.path.join(ROOT, "results/NADIR/s1/zrodla/n1/rig_ab_5hz.sdf")
RIG_SHA = None                      # ustalane w main() z pliku — wynik niesie sha; plik nie jest nadpisywany
KLATKA = os.path.join(ROOT, "results/KONT/s1/frames/R1_p1_srodek_z10.png")
B0SP = os.path.join(ROOT, ".b0deps/lib/python3.12/site-packages")
WARM_S, WIN_S = 20.0, 60.0
ODNIESIENIE = (0.9283, 0.9271)
PROG_GO = 0.90
DT_TEL = 5

PS_LOOP = r"""
param([int]$Secs = 60, [int]$Dt = 5)
$ncpu = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
$prev = @{}; Get-Process | ForEach-Object { $prev[$_.Id] = $_.TotalProcessorTime.TotalSeconds }
$t0 = Get-Date; $last = $t0
while (((Get-Date) - $t0).TotalSeconds -lt $Secs) {
  Start-Sleep -Seconds $Dt
  $now = Get-Date; $dt = ($now - $last).TotalSeconds; $last = $now
  $cpu = Get-CimInstance Win32_PerfFormattedData_Counters_ProcessorInformation | Where-Object { $_.Name -notlike "*_Total" } |
    ForEach-Object { ,@($_.Name, $_.PercentProcessorPerformance, $_.PercentofMaximumFrequency, $_.PercentProcessorUtility) }
  $cur = @{}; $rows = @()
  Get-Process | ForEach-Object { $c = $_.TotalProcessorTime.TotalSeconds; $cur[$_.Id] = $c
    if ($prev.ContainsKey($_.Id)) { $rows += [pscustomobject]@{n=$_.ProcessName; pid=$_.Id; pct=[math]::Round(100*($c-$prev[$_.Id])/($dt*$ncpu),2)} } }
  $prev = $cur
  $top = $rows | Sort-Object pct -Descending | Select-Object -First 5
  $bat = Get-CimInstance Win32_Battery | Select-Object -First 1 BatteryStatus, EstimatedChargeRemaining
  $sch = ((powercfg /getactivescheme) -join " ") -replace ".*GUID: ", ""
  $o = [ordered]@{t_unix=[math]::Round(([DateTimeOffset]$now).ToUnixTimeMilliseconds()/1000.0,2); cpu=$cpu; top=$top; bat=$bat; scheme=$sch}
  [Console]::Out.WriteLine(($o | ConvertTo-Json -Compress -Depth 4)); [Console]::Out.Flush()
}
"""
NV_Q = "utilization.gpu,temperature.gpu,power.draw,clocks.sm,clocks.mem,pstate,clocks_event_reasons.active"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


class Telemetria:
    """3.1(c) w tle: wątek czytający trwały powershell.exe + wątek nvidia-smi; każdy wiersz jsonl z polem src i t_unix."""

    def __init__(self, path, secs):
        self.path, self.stop_ev, self.lock = path, threading.Event(), threading.Lock()
        self.f = open(path, "a")
        self.ps = subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                                    f"& ([scriptblock]::Create([Console]::In.ReadToEnd())) -Secs {int(secs) + 10} -Dt {DT_TEL}"],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, cwd="/mnt/c")
        self.ps.stdin.write(PS_LOOP); self.ps.stdin.close()
        self.th = [threading.Thread(target=self._ps, daemon=True), threading.Thread(target=self._nv, daemon=True)]
        for t in self.th:
            t.start()

    def _w(self, d):
        with self.lock:
            self.f.write(json.dumps(d, ensure_ascii=False) + "\n"); self.f.flush()

    def _ps(self):
        for line in self.ps.stdout:
            line = line.strip()
            if line.startswith("{"):
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                d["src"] = "win"
                self._w(d)

    def _nv(self):
        while not self.stop_ev.is_set():
            r = subprocess.run(["nvidia-smi", f"--query-gpu={NV_Q}", "--format=csv,noheader,nounits"], capture_output=True, text=True)
            self._w({"src": "gpu", "t_unix": round(time.time(), 2), **dict(zip(NV_Q.split(","), [x.strip() for x in r.stdout.split(",")]))})
            self.stop_ev.wait(DT_TEL)

    def close(self):
        self.stop_ev.set()
        self.ps.kill()
        for t in self.th:
            t.join(timeout=10)
        self.f.close()


def podsumuj_tel(path, t0=None, t1=None):
    """Mediany telemetrii w [t0, t1]: częstotliwość / wydajność / użycie (średnia po procesorach), czołówka, GPU."""
    win, gpu = [], []
    for l in open(path):
        d = json.loads(l)
        if (t0 and d["t_unix"] < t0) or (t1 and d["t_unix"] > t1):
            continue
        (win if d["src"] == "win" else gpu).append(d)
    out = {"n_win": len(win), "n_gpu": len(gpu)}
    if win:
        def sr(i):
            return statistics.median(statistics.mean(c[i] for c in d["cpu"]) for d in win)
        out.update(perf_med=round(sr(1), 1), maxfreq_med=round(sr(2), 1), util_med=round(sr(3), 1),
                   maxfreq_min_proc=min(min(c[2] for c in d["cpu"]) for d in win),
                   bateria=win[-1].get("bat"), schemat=win[-1].get("scheme"))
        cnt = {}
        for d in win:
            for p in (d.get("top") or []):
                cnt.setdefault(p["n"], []).append(p["pct"])
        out["czolowka"] = sorted(((k, round(statistics.median(v), 2), len(v)) for k, v in cnt.items()), key=lambda x: -x[1])[:6]
    if gpu:
        def g(k):
            v = [float(d[k]) for d in gpu if d.get(k) not in (None, "", "[N/A]")]
            return round(statistics.median(v), 1) if v else None
        out.update(gpu_util_med=g("utilization.gpu"), gpu_temp_med=g("temperature.gpu"), gpu_power_med=g("power.draw"),
                   gpu_sm_med=g("clocks.sm"), gpu_pstate=sorted({d.get("pstate") for d in gpu}),
                   gpu_reasons=sorted({d.get("clocks_event_reasons.active") for d in gpu}))
    return out


def gz_a5(tag):
    import nadir_frames as NF
    import nadir_ab as AB
    from gz.transport13 import Node
    assert sha(RIG) == RIG_SHA
    e = NF.env()
    NF.teardown()
    log = open(os.path.join(OUT, f"gz_{tag}.log"), "w")
    srv = subprocess.Popen(["gz", "sim", "--verbose=1", "-r", "-s", f"{e['PX4_GZ_WORLDS']}/{W}.sdf"], env=e, stdout=log, stderr=log)
    t0 = time.monotonic()
    while "Service providers" not in NF.svc(e, "-i", "--service", f"/world/{W}/scene/info").stdout:
        assert time.monotonic() - t0 < 90, "świat nie wstał"
        time.sleep(1)
    q = NF.quat(0, 0, 30)
    req = (f'sdf_filename: "{RIG}", name: "probe", allow_renaming: false, pose: {{position: {{x: 5, y: 5, z: 12}}, '
           f'orientation: {{w: {q[0]}, x: {q[1]}, y: {q[2]}, z: {q[3]}}}}}')
    r = NF.svc(e, "-s", f"/world/{W}/create", "--reqtype", "gz.msgs.EntityFactory", "--reptype", "gz.msgs.Boolean",
               "--timeout", "10000", "--req", req)
    assert "true" in r.stdout, r.stdout + r.stderr
    node = Node()
    base = f"/world/{W}/model/probe/link"
    L = {"imager": AB.Licz(node, f"{base}/camera_link/sensor/imager/image"),
         "flow": AB.Licz(node, f"{base}/flow_link/sensor/flow_camera/image"),
         "nadir": AB.Licz(node, f"{base}/nadir_link/sensor/nadir/image", detekcja=True)}
    rp = os.path.join(OUT, f"rtf_{tag}.jsonl")
    tw0 = time.time()
    rs = subprocess.Popen([sys.executable, "-m", "acts.rtf_sampler", "--world", W, "--out", rp], cwd=ROOT, env=e,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(WARM_S + WIN_S + 3)
    rs.terminate(); rs.wait(timeout=10)
    srv.kill(); srv.wait(timeout=10)
    NF.teardown()
    AB.WARM_S, AB.WIN_S = WARM_S, WIN_S
    tempo, n = AB.regresja(rp)
    del node
    return {"gz_a5": tempo, "n_probek_okna": n, "okno": [round(tw0 + WARM_S, 2), round(tw0 + WARM_S + WIN_S, 2)],
            "hz": {k: round(v.n / (WARM_S + WIN_S), 2) for k, v in L.items()}, "nadir_klatki_z_id": L["nadir"].ndet,
            "wzgl_odniesienia": round(tempo / statistics.mean(ODNIESIENIE), 4) if tempo else None}


DET_KOD = r"""
import json, sys, time, cv2, statistics
sys.path[:0] = [sys.argv[2]]
from harness.det_v2 import DetV2
d = DetV2(); g = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
for _ in range(20): d.top1(g)
import torch; ts = []
for _ in range(300):
    t = time.perf_counter(); d.top1(g); torch.cuda.synchronize(); ts.append(1000 * (time.perf_counter() - t))
ts.sort(); print(json.dumps({"device": d.device, "n": len(ts), "p50_ms": round(ts[150], 3), "p95_ms": round(ts[284], 3)}))
"""


def det_cuda():
    env = dict(os.environ, PYTHONPATH=f"{B0SP}:{ROOT}")
    r = subprocess.run([sys.executable, "-c", DET_KOD, KLATKA, ROOT], env=env, capture_output=True, text=True, timeout=600, cwd=ROOT)
    line = [l for l in r.stdout.splitlines() if l.startswith("{")]
    return json.loads(line[-1]) if line else {"blad": r.stderr[-600:]}


def praca(_=None):
    ts = []
    for _ in range(10):
        t = time.perf_counter(); s = 0
        for i in range(2_000_000):
            s += i * i
        ts.append(1000 * (time.perf_counter() - t))
    return ts


def cpu_mikro():
    import multiprocessing as mp
    jeden = praca()
    with mp.get_context("fork").Pool(8) as p:
        osiem = [x for ts in p.map(praca, range(8)) for x in ts]
    return {"jednowatkowa_med_ms": round(statistics.median(jeden), 2), "8proc_med_ms": round(statistics.median(osiem), 2),
            "8proc_p90_ms": round(sorted(osiem)[int(0.9 * len(osiem))], 2)}


def glx():
    import nadir_frames as NF
    r = subprocess.run(["glxinfo", "-B"], env=NF.env(), capture_output=True, text=True, timeout=60)
    return [l.strip() for l in r.stdout.splitlines() if any(k in l for k in ("renderer", "Device", "Vendor", "core profile version"))]


def sonda(tag, z_telemetria=True, tylko_a=False, tel_path=None):
    tel_p = os.path.join(OUT, f"telemetria_{tag}.jsonl")
    tel = Telemetria(tel_p, 600) if z_telemetria else None
    t0 = time.time()
    res = {"tag": tag, "t_start": time.strftime("%Y-%m-%d %H:%M:%S"), "profil_oem": os.environ.get("PROFIL_OEM", "nie podany"),
           "glxinfo_B": glx(), "rig_sha": RIG_SHA, "warm_s": WARM_S, "win_s": WIN_S,
           "odniesienie": ODNIESIENIE, "prog_go": PROG_GO,
           "timesyncd": subprocess.run(["systemctl", "is-active", "systemd-timesyncd"], capture_output=True, text=True).stdout.strip(),
           "loadavg_przed": open("/proc/loadavg").read().split()[:3]}
    try:
        res["a"] = gz_a5(tag)
        if not tylko_a:
            tb0 = time.time()
            res["b_det_v2"] = det_cuda()
            res["b_det_v2"]["okno"] = [round(tb0, 2), round(time.time(), 2)]
            res["b_det_v2"]["klatka"], res["b_det_v2"]["klatka_sha"] = os.path.relpath(KLATKA, ROOT), sha(KLATKA)
            res["b_cpu"] = cpu_mikro()
    finally:
        if tel:
            time.sleep(1)
            tel.close()
    res["t_koniec"] = time.strftime("%Y-%m-%d %H:%M:%S")
    tel_src = tel_p if tel else tel_path
    if tel_src and os.path.exists(tel_src):
        if "b_det_v2" in res:
            res["c_okno_det"] = podsumuj_tel(tel_src, *res["b_det_v2"]["okno"])
        res["c_okno_a"] = podsumuj_tel(tel_src, *res["a"]["okno"])
        res["c_cala"] = podsumuj_tel(tel_src, t0)
    res["GO"] = res["a"]["gz_a5"] is not None and res["a"]["gz_a5"] >= PROG_GO
    json.dump(res, open(os.path.join(OUT, f"stanowisko_{tag}.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in res if k in ("tag", "profil_oem", "GO", "a", "b_det_v2", "b_cpu", "c_okno_a")}, ensure_ascii=False), flush=True)
    return res


def ps(cmd):
    r = subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd], capture_output=True, cwd="/mnt/c", timeout=120)
    return r.stdout.decode("cp852", "replace").strip()          # konsola OEM systemu PL


def sesja():
    out = {"t": time.strftime("%Y-%m-%d %H:%M:%S"),
           "procesor": ps("Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed | ConvertTo-Json -Compress"),
           "windows": ps("Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber | ConvertTo-Json -Compress"),
           "wsl": subprocess.run(["wsl.exe", "--version"], capture_output=True, cwd="/mnt/c").stdout.decode("utf-16-le", "replace").replace("\x00", "").strip(),
           "kernel": os.uname().release,
           "gpu": subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version,power.limit,power.max_limit", "--format=csv,noheader"],
                                 capture_output=True, text=True).stdout.strip(),
           "schemat": ps("powercfg /getactivescheme"),
           "ekran_s": ps("powercfg /q scheme_current sub_video VIDEOIDLE"),
           "uspienie_s": ps("powercfg /q scheme_current sub_sleep STANDBYIDLE"),
           "schedpolicy": ps("powercfg /qh scheme_current sub_processor SCHEDPOLICY"),
           "shortschedpolicy": ps("powercfg /qh scheme_current sub_processor SHORTSCHEDPOLICY"),
           "powerthrottling": ps("powercfg /powerthrottling list"),
           "bateria": ps("Get-CimInstance Win32_Battery | Select-Object BatteryStatus,EstimatedChargeRemaining | ConvertTo-Json -Compress")}
    p = os.path.join(OUT, f"sesja_{time.strftime('%Y%m%d_%H%M%S')}.json")
    json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


def seria(tag, minuty, okres):
    tel = Telemetria(os.path.join(OUT, f"telemetria_{tag}.jsonl"), minuty * 60 + 300)
    t0 = time.monotonic(); k = 0; wyn = []
    try:
        while time.monotonic() - t0 < minuty * 60:
            tk = time.monotonic()
            r = sonda(f"{tag}_{k:02d}", z_telemetria=False, tel_path=os.path.join(OUT, f"telemetria_{tag}.jsonl"))
            r["t_od_startu_s"] = round(tk - t0, 1)
            json.dump(r, open(os.path.join(OUT, f"stanowisko_{tag}_{k:02d}.json"), "w"), ensure_ascii=False, indent=1)
            wyn.append({"k": k, "t_s": r["t_od_startu_s"], "gz_a5": r["a"]["gz_a5"], "det_p50": r["b_det_v2"].get("p50_ms"),
                        "cpu1": r["b_cpu"]["jednowatkowa_med_ms"], "cpu8": r["b_cpu"]["8proc_med_ms"],
                        "maxfreq": r["c_okno_a"].get("maxfreq_med"), "perf": r["c_okno_a"].get("perf_med")})
            print("SERIA", json.dumps(wyn[-1]), flush=True)
            k += 1
            reszta = okres - (time.monotonic() - tk)
            if reszta > 0 and time.monotonic() - t0 + reszta < minuty * 60:
                time.sleep(reszta)
    finally:
        tel.close()
    json.dump({"tag": tag, "minuty": minuty, "okres_s": okres, "seria": wyn}, open(os.path.join(OUT, f"seria_{tag}.json"), "w"),
              ensure_ascii=False, indent=1)


def main():
    global RIG_SHA
    os.makedirs(OUT, exist_ok=True)
    RIG_SHA = sha(RIG)
    a = sys.argv[1:]
    if a[0] == "sonda":
        sonda(a[1])
    elif a[0] == "bramka":
        try:
            r = sonda(a[1], tylko_a=True)
        except Exception as ex:
            print("BRAMKA BŁĄD", ex, flush=True); sys.exit(2)
        print("BRAMKA", "GO" if r["GO"] else "NO-GO", r["a"]["gz_a5"], flush=True)
        sys.exit(0 if r["GO"] else 1)
    elif a[0] == "seria":
        seria(a[1], float(a[2]), float(a[3]))
    elif a[0] == "telemetria":
        tel = Telemetria(a[1], float(a[2]))
        try:
            time.sleep(float(a[2]))
        finally:
            tel.close()
    elif a[0] == "sesja":
        sesja()


if __name__ == "__main__":
    main()
