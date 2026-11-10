#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s4_bramka.py — ANEKS_NADIR-4 §3.1/§3.2/§3.4/§3.5 (0 bootów, bez PX4, nic nie uzbraja).

Tryby:
  bramka <tag> [--tel]   §3.1: przyrząd A = nadir_n1_ab.run(i, "A5", e) BEZ ZMIAN KODU (rig A_5, rozgrzewka 20 s + okno 120 s,
                         odniesienie 0.9283 / 0.9271); jedyna zmiana: katalogi wyjścia modułu (N1, ZRN) przekierowane do
                         results/NADIR/s4/bramka/<tag>/ (rig generowany tą samą rig(5), sha porównane z odniesieniem).
                         --tel = wariant C (telemetria §3.3 nadir_s4_tel.Telemetria2 w tle). GO ⇔ tempo ≥ 0.90 ⇒ kod 0;
                         NO-GO ⇒ kod 1; błąd / odmowa zegara ⇒ kod 2. Wynik bramka/<tag>/bramka.json.
  seria <tag> <n>        §3.4: n × A z telemetrią (wariant C) ⇒ bramka/<tag>_<k>/ + bramka/seria_<tag>.json (tempo, udział P8 itd.).
  zegar <tag>            §3.5: tempo zegara gościa wobec zegara Windows — 120 s bezczynnie, potem przyrząd A (≈143 s pod rigiem);
                         sondowanie trwałego powershell.exe (Stopwatch QPC + DateTime.UtcNow), punkt = środek najkrótszego
                         round-trip z 15 pingów; ⇒ bramka/zegar_<tag>.json.
§3.2: każdy tryb odmawia pracy (kod 2), gdy `systemctl is-active systemd-timesyncd` ≠ inactive.
teardown gz jak nadir_frames.teardown (pkill gz sim) — uruchamiać wyłącznie poza bootem.
"""
import base64
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = "/home/olga/projects/liquidpatrol"
T = os.path.join(ROOT, "results/NADIR/tools")
sys.path.insert(0, T)
OUT = os.path.join(ROOT, "results/NADIR/s4/bramka")
RIG_REF = os.path.join(ROOT, "results/NADIR/s1/zrodla/n1/rig_ab_5hz.sdf")
PROG = 0.90
ODNIESIENIE = (0.9283, 0.9271)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def zegar_ok():
    s = subprocess.run(["systemctl", "is-active", "systemd-timesyncd"], capture_output=True, text=True).stdout.strip()
    if s != "inactive":
        print(f"ODMOWA (ANEKS_NADIR-4 §3.2): systemd-timesyncd = {s!r} ≠ inactive — pomiar tempa nieważny", flush=True)
        sys.exit(2)
    return s


def przyrzad_a(tag, tel):
    import nadir_n1_ab as N
    import nadir_frames as NF
    import nadir_s4_tel as TL
    d = os.path.join(OUT, tag)
    os.makedirs(d, exist_ok=True)
    N.N1, N.ZRN = d, d
    N.AB.WARM_S, N.AB.WIN_S = 20.0, 120.0
    e = NF.env()
    NF.teardown()
    tp = os.path.join(d, "telemetria.jsonl")
    tl = TL.Telemetria2(tp, 220) if tel else None
    t0 = time.time()
    try:
        r = N.run(0, "A5", e)
    finally:
        if tl:
            tl.close()
    rp = os.path.join(d, "rtf_0_A5.jsonl")
    w0 = json.loads(open(rp).readline())["wall"]
    res = {"tag": tag, "wariant": "C" if tel else "A", "t": time.strftime("%Y-%m-%d %H:%M:%S"), "tempo": r["dsim_dwall"],
           "prog": PROG, "odniesienie": ODNIESIENIE, "n1_run": r, "rig_zgodny": sha(os.path.join(d, "rig_ab_5hz.sdf")) == sha(RIG_REF),
           "timesyncd": "inactive", "okno_t_guest": [round(w0 + 20, 2), round(w0 + 140, 2)], "profil10": profil10(rp)}
    if tel:
        res["tel_okno"] = TL.podsumuj(tp, *res["okno_t_guest"])
    res["GO"] = r["dsim_dwall"] is not None and r["dsim_dwall"] >= PROG and res["rig_zgodny"]
    json.dump(res, open(os.path.join(d, "bramka.json"), "w"), ensure_ascii=False, indent=1)
    return res


def profil10(p):
    r = [json.loads(l) for l in open(p) if l.strip()]
    w0, out, i = r[0]["wall"], [], 0
    for j, x in enumerate(r):
        if x["wall"] - r[i]["wall"] >= 10:
            out.append([round(r[i]["wall"] - w0), round((x["sim"] - r[i]["sim"]) / (x["wall"] - r[i]["wall"]), 3)])
            i = j
    return out


PS_ZEGAR = ("[Console]::Out.WriteLine([Diagnostics.Stopwatch]::Frequency); [Console]::Out.Flush(); "
            "while (($l = [Console]::In.ReadLine()) -ne $null) { [Console]::Out.WriteLine(('{0} {1}' -f "
            "[Diagnostics.Stopwatch]::GetTimestamp(), [DateTime]::UtcNow.Ticks)); [Console]::Out.Flush() }")


class ZegarWin:
    def __init__(self):
        enc = base64.b64encode(PS_ZEGAR.encode("utf-16-le")).decode()
        self.p = subprocess.Popen(["powershell.exe", "-NoProfile", "-EncodedCommand", enc], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True, cwd="/mnt/c", bufsize=1)
        self.freq = int(self.p.stdout.readline())

    def punkt(self, n=15):
        best = None
        for _ in range(n):
            a = time.monotonic(); ra = time.time()
            self.p.stdin.write("x\n"); self.p.stdin.flush()
            qpc, ticks = map(int, self.p.stdout.readline().split())
            b = time.monotonic(); rb = time.time()
            rtt = b - a
            if best is None or rtt < best["rtt"]:
                best = {"rtt": rtt, "mono": (a + b) / 2, "real": (ra + rb) / 2, "qpc_s": qpc / self.freq, "utc_s": ticks / 1e7}
            time.sleep(0.05)
        return best

    def close(self):
        self.p.stdin.close(); self.p.kill()


def tempo_zegara(p0, p1):
    dq, du = p1["qpc_s"] - p0["qpc_s"], p1["utc_s"] - p0["utc_s"]
    dm, dr = p1["mono"] - p0["mono"], p1["real"] - p0["real"]
    return {"dt_win_qpc_s": round(dq, 4), "dt_win_utc_s": round(du, 4), "dt_gosc_mono_s": round(dm, 4), "dt_gosc_real_s": round(dr, 4),
            "mono_do_qpc": round(dm / dq, 5), "real_do_utc": round(dr / du, 5), "blad_mono_proc": round(100 * (dm / dq - 1), 3),
            "rtt_ms": [round(1000 * p0["rtt"], 2), round(1000 * p1["rtt"], 2)]}


def zegar(tag):
    os.makedirs(OUT, exist_ok=True)
    z = ZegarWin()
    res = {"tag": tag, "t": time.strftime("%Y-%m-%d %H:%M:%S"), "timesyncd": "inactive",
           "clocksource": open("/sys/devices/system/clocksource/clocksource0/current_clocksource").read().strip()}
    try:
        p0 = z.punkt(); time.sleep(120); p1 = z.punkt()
        res["bezczynnie_120s"] = tempo_zegara(p0, p1)
        p2 = z.punkt()
        a = przyrzad_a(f"{tag}_rigA", tel=False)
        p3 = z.punkt()
        res["pod_rigiem_A"] = tempo_zegara(p2, p3)
        res["pod_rigiem_A"]["tempo_A_zegar_goscia"] = a["tempo"]
        res["pod_rigiem_A"]["tempo_A_w_czasie_windows"] = round(a["tempo"] * res["pod_rigiem_A"]["mono_do_qpc"], 4) if a["tempo"] else None
    finally:
        z.close()
    json.dump(res, open(os.path.join(OUT, f"zegar_{tag}.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1), flush=True)


def main():
    a = sys.argv[1:]
    zegar_ok()
    os.makedirs(OUT, exist_ok=True)
    if a[0] == "bramka":
        try:
            r = przyrzad_a(a[1], "--tel" in a)
        except SystemExit:
            raise
        except Exception as ex:
            print("BRAMKA BŁĄD", repr(ex), flush=True); sys.exit(2)
        print("BRAMKA", "GO" if r["GO"] else "NO-GO", r["wariant"], r["tempo"], flush=True)
        sys.exit(0 if r["GO"] else 1)
    elif a[0] == "seria":
        wyn = []
        for k in range(int(a[2])):
            zegar_ok()
            r = przyrzad_a(f"{a[1]}_{k}", tel=True)
            g = r.get("tel_okno", {}).get("gpu", {})
            wyn.append({"k": k, "t": r["t"], "tempo": r["tempo"], "pstate": g.get("pstate_udzial"), "sm_med": g.get("sm_med"),
                        "moc_med": g.get("moc_med"), "flaga_0x4": g.get("flaga_0x4_udzial"), "util_med": g.get("util_med")})
            print("SERIA", json.dumps(wyn[-1], ensure_ascii=False), flush=True)
        json.dump({"tag": a[1], "seria": wyn}, open(os.path.join(OUT, f"seria_{a[1]}.json"), "w"), ensure_ascii=False, indent=1)
    elif a[0] == "zegar":
        zegar(a[1])


if __name__ == "__main__":
    main()
