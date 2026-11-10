#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s4_tel.py — ANEKS_NADIR-4 §3.3: telemetria hosta w tle (bramka 3.1 wariant C, test 3.4, boot S4).

Trzy trwałe procesy, każdy wiersz jsonl z polem src i t_guest (time.time() gościa w chwili odbioru — jeden zegar dla
korelacji z rtf_stream; zegar Windows obok jako t_win):
  src=gpu   nvidia-smi --query-gpu=<NV_Q> -lms 1000 (1 Hz): pstate, zegary SM/MEM, moc, obciążenie, temperatura,
            clocks_event_reasons.active;
  src=gpuproc  powershell.exe: Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine — suma UtilizationPercentage per pid,
            czołówka 5 z nazwą procesu (zapytanie CIM trwa ~6 s, kadencja = max(Dt, czas zapytania));
  src=win   powershell.exe: próbnik hosta jak nadir_stanowisko.PS_LOOP (procesory logiczne, czołówka 5 po CPU, bateria;
            powercfg co 12. próbka) — naprawa kadencji z ANEKS_NADIR-4 §1.6: lista zamiast konkatenacji tablic, sen do
            terminu (nie Dt po pracy), pole dur_s = czas zapytań w próbce.
Użycie samodzielne: nadir_s4_tel.py <plik.jsonl> <sekundy>
"""
import json
import subprocess
import sys
import threading
import time

NV_Q = "pstate,clocks.sm,clocks.mem,power.draw,utilization.gpu,temperature.gpu,clocks_event_reasons.active"

PS_HOST = r"""
param([int]$Secs = 60, [int]$Dt = 5)
$ncpu = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
$prev = @{}; foreach ($p in Get-Process) { $prev[$p.Id] = $p.TotalProcessorTime.TotalSeconds }
$t0 = Get-Date; $last = $t0; $k = 0; $sch = ""
while (((Get-Date) - $t0).TotalSeconds -lt $Secs) {
  $next = $last.AddSeconds($Dt); $w = ($next - (Get-Date)).TotalMilliseconds; if ($w -gt 0) { Start-Sleep -Milliseconds ([int]$w) }
  $now = Get-Date; $dt = ($now - $last).TotalSeconds; $last = $now
  $cpu = New-Object System.Collections.Generic.List[object]
  foreach ($c in (Get-CimInstance Win32_PerfFormattedData_Counters_ProcessorInformation)) {
    if ($c.Name -notlike "*_Total") { $cpu.Add(@($c.Name, $c.PercentProcessorPerformance, $c.PercentofMaximumFrequency, $c.PercentProcessorUtility)) } }
  $cur = @{}; $rows = New-Object System.Collections.Generic.List[object]
  foreach ($p in Get-Process) { $c = $p.TotalProcessorTime.TotalSeconds; $cur[$p.Id] = $c
    if ($prev.ContainsKey($p.Id)) { $rows.Add([pscustomobject]@{n=$p.ProcessName; pid=$p.Id; pct=[math]::Round(100*($c-$prev[$p.Id])/($dt*$ncpu),2)}) } }
  $prev = $cur
  $top = $rows | Sort-Object pct -Descending | Select-Object -First 5
  $bat = Get-CimInstance Win32_Battery | Select-Object -First 1 BatteryStatus, EstimatedChargeRemaining
  if ($k % 12 -eq 0) { $sch = ((powercfg /getactivescheme) -join " ") -replace ".*GUID: ", "" }
  $k++
  $o = [ordered]@{t_win=[math]::Round(([DateTimeOffset]$now).ToUnixTimeMilliseconds()/1000.0,2); dur_s=[math]::Round(((Get-Date)-$now).TotalSeconds,2); cpu=$cpu; top=$top; bat=$bat; scheme=$sch}
  [Console]::Out.WriteLine(($o | ConvertTo-Json -Compress -Depth 4)); [Console]::Out.Flush()
}
"""

PS_GPUPROC = r"""
param([int]$Secs = 60, [int]$Dt = 5)
$t0 = Get-Date; $last = $t0
while (((Get-Date) - $t0).TotalSeconds -lt $Secs) {
  $next = $last.AddSeconds($Dt); $w = ($next - (Get-Date)).TotalMilliseconds; if ($w -gt 0) { Start-Sleep -Milliseconds ([int]$w) }
  $now = Get-Date; $last = $now
  $agg = @{}
  foreach ($e in (Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine)) {
    if ($e.UtilizationPercentage -gt 0 -and $e.Name -match "^pid_(\d+)_.*engtype_(.+)$") {
      $key = $matches[1]; if (-not $agg.ContainsKey($key)) { $agg[$key] = @{} }
      $et = $matches[2]; $agg[$key][$et] = [int]$agg[$key][$et] + [int]$e.UtilizationPercentage } }
  $rows = New-Object System.Collections.Generic.List[object]
  foreach ($k in $agg.Keys) { $s = 0; foreach ($v in $agg[$k].Values) { $s += $v }
    $n = (Get-Process -Id ([int]$k) -ErrorAction SilentlyContinue).ProcessName
    $rows.Add([pscustomobject]@{pid=[int]$k; n=$n; util=$s; eng=$agg[$k]}) }
  $top = $rows | Sort-Object util -Descending | Select-Object -First 5
  $o = [ordered]@{t_win=[math]::Round(([DateTimeOffset]$now).ToUnixTimeMilliseconds()/1000.0,2); dur_s=[math]::Round(((Get-Date)-$now).TotalSeconds,2); top=$top}
  [Console]::Out.WriteLine(($o | ConvertTo-Json -Compress -Depth 4)); [Console]::Out.Flush()
}
"""


def _ps(script, secs, dt):
    p = subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                          f"& ([scriptblock]::Create([Console]::In.ReadToEnd())) -Secs {int(secs) + 10} -Dt {dt}"],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, cwd="/mnt/c")
    p.stdin.write(script); p.stdin.close()
    return p


class Telemetria2:
    def __init__(self, path, secs, dt_host=5):
        self.f, self.lock = open(path, "a"), threading.Lock()
        self.procs = {"win": _ps(PS_HOST, secs, dt_host), "gpuproc": _ps(PS_GPUPROC, secs, dt_host),
                      "gpu": subprocess.Popen(["nvidia-smi", f"--query-gpu={NV_Q}", "--format=csv,noheader,nounits", "-lms", "1000"],
                                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)}
        self.th = [threading.Thread(target=self._read, args=(k, p), daemon=True) for k, p in self.procs.items()]
        for t in self.th:
            t.start()

    def _read(self, src, p):
        keys = NV_Q.split(",")
        for line in p.stdout:
            line = line.strip()
            t = round(time.time(), 3)
            if src == "gpu":
                v = [x.strip() for x in line.split(",")]
                if len(v) != len(keys):
                    continue
                d = dict(zip(keys, v))
            else:
                if not line.startswith("{"):
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
            d["src"], d["t_guest"] = src, t
            with self.lock:
                self.f.write(json.dumps(d, ensure_ascii=False) + "\n"); self.f.flush()

    def close(self):
        for p in self.procs.values():
            p.kill()
        for t in self.th:
            t.join(timeout=10)
        self.f.close()


def podsumuj(path, t0=None, t1=None):
    """Okno [t0, t1] zegara gościa: udział pstate, mediany zegarów/mocy, udział flagi 0x4, kadencje, czołówki."""
    import statistics as st
    rows = [json.loads(l) for l in open(path) if l.strip()]
    rows = [r for r in rows if (t0 is None or r["t_guest"] >= t0) and (t1 is None or r["t_guest"] <= t1)]
    out = {}
    g = [r for r in rows if r["src"] == "gpu"]
    if g:
        n = len(g)
        ps = {}
        for r in g:
            ps[r["pstate"]] = ps.get(r["pstate"], 0) + 1
        fl = lambda k: [float(r[k]) for r in g if r.get(k) not in (None, "", "[N/A]", "N/A")]
        out["gpu"] = {"n": n, "pstate_udzial": {k: round(v / n, 3) for k, v in sorted(ps.items())},
                      "sm_med": st.median(fl("clocks.sm")), "mem_med": st.median(fl("clocks.mem")), "moc_med": st.median(fl("power.draw")),
                      "util_med": st.median(fl("utilization.gpu")),
                      "flaga_0x4_udzial": round(sum(int(r["clocks_event_reasons.active"], 16) & 0x4 > 0 for r in g) / n, 3)}
    for src in ("win", "gpuproc"):
        w = [r for r in rows if r["src"] == src]
        if not w:
            continue
        ts = [r["t_guest"] for r in w]
        o = {"n": len(w), "kadencja_med_s": round(st.median([b - a for a, b in zip(ts, ts[1:])]), 2) if len(ts) > 1 else None,
             "dur_med_s": st.median([r.get("dur_s", 0) for r in w])}
        cnt = {}
        for r in w:
            top = r.get("top") or []
            for p in ([top] if isinstance(top, dict) else top):     # ConvertTo-Json: jeden element ⇒ obiekt, nie lista
                cnt.setdefault(p.get("n") or str(p.get("pid")), []).append(p.get("pct", p.get("util")))
        o["czolowka"] = sorted(((k, st.median(v), len(v)) for k, v in cnt.items()), key=lambda x: -x[1])[:6]
        if src == "win":
            o["maxfreq_med"] = round(st.median(st.mean(c[2] for c in r["cpu"]) for r in w), 1)
        out[src] = o
    return out


if __name__ == "__main__":
    tel = Telemetria2(sys.argv[1], float(sys.argv[2]))
    try:
        time.sleep(float(sys.argv[2]))
    finally:
        tel.close()
    print(json.dumps(podsumuj(sys.argv[1]), ensure_ascii=False, indent=1))
