#!/usr/bin/env python3
"""harness/proc_gate.py — bramka procesowa (ANEKS_INFRA3-3 §3), env-block PRZED startem stacku.

Semantyka jak I2a: boot się NIE zaczyna, nie liczy się nigdzie. Blok gdy:
  - jakiś proces user-space z %CPU > CPU_MAX (dom. 2.0) NIE pasuje do allowlisty, LUB
  - loadavg(1) > LOAD1_MAX (dom. 1.5).
Allowlista = `harness/proc_allowlist.txt` (regex ERE, w repo, edycja tylko commitem).

Próbka: `top -b -n 2 -d <DELAY>` (druga iteracja = %CPU ustabilizowane w oknie DELAY s).
Dla każdego PID z %CPU>CPU_MAX pobiera PEŁNĄ linię poleceń (`/proc/<pid>/cmdline`) i dopasowuje do allowlisty.

Wyjście: 0 = czysto; 3 = env-block (winowajcy na stdout: `pid cpu cmd`, linia po linii).
Args: --allowlist PATH --cpu-max F --load1-max F --delay S --self PID (własna sesja, zawsze dozwolona).
"""
import argparse
import os
import re
import subprocess
import sys


def load_patterns(path):
    pats = []
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            pats.append(re.compile(ln))
    return pats


def cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            raw = f.read()
        s = raw.replace(b"\x00", b" ").decode("utf-8", "replace").strip()
        if s:
            return s
    except Exception:
        pass
    # fallback: comm
    try:
        with open(f"/proc/{pid}/comm") as f:
            return f.read().strip()
    except Exception:
        return ""


def top_sample(delay):
    """Zwraca listę (pid, cpu) z DRUGIEJ iteracji `top -b -n 2 -d delay`."""
    out = subprocess.run(["top", "-b", "-n", "2", "-d", str(delay)],
                         capture_output=True, text=True, timeout=delay * 2 + 30).stdout
    # top drukuje 2 bloki; bierzemy ostatni (po ostatnim nagłówku 'PID')
    lines = out.splitlines()
    hdr_idx = [i for i, l in enumerate(lines) if re.search(r"^\s*PID\s+USER", l)]
    if not hdr_idx:
        return []
    start = hdr_idx[-1] + 1
    rows = []
    for l in lines[start:]:
        parts = l.split()
        if len(parts) < 12:
            continue
        pid = parts[0]
        # kolumna %CPU: top domyślnie 9. (0-idx 8), ale bywa przesunięcie — szukamy po nagłówku trudno,
        # więc bierzemy pierwszą liczbę zmiennoprzecinkową z pozycji 8 (typowy układ -b).
        try:
            cpu = float(parts[8].replace(",", "."))
            int(pid)
        except (ValueError, IndexError):
            continue
        rows.append((pid, cpu))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allowlist", default=os.path.join(os.path.dirname(__file__), "proc_allowlist.txt"))
    ap.add_argument("--cpu-max", type=float, default=2.0)
    ap.add_argument("--load1-max", type=float, default=1.5)
    ap.add_argument("--delay", type=float, default=5.0)
    ap.add_argument("--self", type=int, default=os.getppid(), help="PID własnej sesji (zawsze dozwolony)")
    a = ap.parse_args()

    pats = load_patterns(a.allowlist)
    self_chain = {a.self, os.getpid(), os.getppid()}

    offenders = []
    for pid, cpu in top_sample(a.delay):
        if cpu <= a.cpu_max:
            continue
        if int(pid) in self_chain:
            continue
        cl = cmdline(pid)
        if not cl:
            continue  # zniknął / kernel thread bez cmdline
        if any(p.search(cl) for p in pats):
            continue
        offenders.append((pid, cpu, cl))

    load1 = os.getloadavg()[0]
    load_block = load1 > a.load1_max

    if offenders or load_block:
        if load_block:
            print(f"LOADAVG {load1:.2f} > {a.load1_max}")
        for pid, cpu, cl in offenders:
            print(f"{pid} {cpu:.1f} {cl}")
        sys.exit(3)
    print(f"CLEAN loadavg={load1:.2f} (cpu_max={a.cpu_max}, load1_max={a.load1_max})")
    sys.exit(0)


if __name__ == "__main__":
    main()
