#!/usr/bin/env python3
"""acts/temporal_sweep_5b.py — ANEKS_D5 §5b: 4b-v2 = MECHANICZNY sweep WSZYSTKICH stałych temporalnych
obu torów (frozen REGATE mti_flight vs tor aktów) + diff. Zastępuje ręczną wyliczankę z §4b, która
POMINĘŁA producenta ruchu (teleport intruza) — kompletność MA pochodzić z KODU.

Metoda: AST (nie regex — pewne wyłapanie KAŻDEGO wywołania sleep/create_timer + jego argumentu i funkcji
otaczającej, oraz każdej modułowej stałej temporalnej). Dla każdego pliku:
  - stałe modułowe numeryczne (NAME = <num>), w tym *_HZ/_DT/PERIOD/RATE;
  - każde `time.sleep(x)` / `asyncio.sleep(x)` / `create_timer(x, …)` z funkcją otaczającą i ROZWIĄZANĄ
    wartością (literał, Name→stała modułowa, BinOp 1.0/HZ itd.).
Następnie DIFF ról semantycznych sterujących pipeline MTI/ENTRY (kadencja: ruchu intruza, decyzji,
MTI-push, publikacji). Różnica harnessowa ⇒ przywrócić REGATE w tym commicie; różnica wymagająca frozen
⇒ STOP dokumentem.

Uruchom: PYTHONPATH=… python3 acts/temporal_sweep_5b.py [OUT.json]
"""
from __future__ import annotations
import ast
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Tory (pliki NIE-współdzielone). Współdzielone (config_r02/target_channel/mti) są IDENTYCZNE z definicji
# (ten sam plik w obu torach) — skanowane osobno jako `shared` dla kompletności, nie do diff.
TRACKS = {
    "regate": ["results/R02/mti/mti_flight.py"],
    "akt":    ["r02/gate_run_r02.py", "r02/detector_node.py", "acts/act_common.py"],
    "shared": ["r02/config_r02.py", "r02/target_channel.py", "r02/mti.py"],
}

SLEEP_FUNCS = {"sleep"}            # time.sleep / asyncio.sleep (po atrybucie .sleep)
TIMER_FUNCS = {"create_timer"}    # rclpy create_timer(period, cb)


def _num(node):
    """Zwraca wartość liczbową węzła AST jeśli to stała liczbowa, else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        v = _num(node.operand)
        return -v if v is not None else None
    return None


def _module_consts(tree):
    """Mapa modułowych stałych numerycznych {NAME: value} (proste NAME = <num> lub NAME = <num>/<num>)."""
    consts = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            name = n.targets[0].id
            v = _resolve(n.value, consts)
            if v is not None:
                consts[name] = v
    return consts


def _resolve(node, consts):
    """Rozwiąż węzeł do wartości liczbowej: literał, Name→consts, BinOp (+,-,*,/) rekurencyjnie."""
    v = _num(node)
    if v is not None:
        return v
    if isinstance(node, ast.Name) and node.id in consts:
        return consts[node.id]
    if isinstance(node, ast.BinOp):
        l = _resolve(node.left, consts); r = _resolve(node.right, consts)
        if l is None or r is None:
            return None
        if isinstance(node.op, ast.Div) and r != 0:
            return l / r
        if isinstance(node.op, ast.Mult):
            return l * r
        if isinstance(node.op, ast.Add):
            return l + r
        if isinstance(node.op, ast.Sub):
            return l - r
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "round" and node.args:
        inner = _resolve(node.args[0], consts)
        return round(inner, 1) if inner is not None else None
    return None


def _scan_file(relpath):
    path = os.path.join(ROOT, relpath)
    src = open(path).read()
    tree = ast.parse(src, filename=relpath)
    consts = _module_consts(tree)

    sleeps = []   # {func, lineno, kind, arg_src, value}
    # mapa lineno→nazwa funkcji otaczającej
    func_ranges = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = max((getattr(c, "lineno", node.lineno) for c in ast.walk(node)), default=node.lineno)
            func_ranges.append((node.lineno, end, node.name))

    def enclosing(lineno):
        best = None
        for s, e, name in func_ranges:
            if s <= lineno <= e:
                if best is None or s > best[0]:
                    best = (s, name)
        return best[1] if best else "<module>"

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            fn = node.func.attr
            if fn in SLEEP_FUNCS or fn in TIMER_FUNCS:
                arg = node.args[0] if node.args else None
                val = _resolve(arg, consts) if arg is not None else None
                sleeps.append({
                    "func": enclosing(node.lineno), "lineno": node.lineno,
                    "kind": ("timer" if fn in TIMER_FUNCS else "sleep"),
                    "arg_src": ast.unparse(arg) if arg is not None else None,
                    "value_s": val,
                })
    # stałe temporalne (nazwa sugeruje czas/kadencję)
    temporal_consts = {k: v for k, v in consts.items()
                       if any(t in k.upper() for t in ("HZ", "_DT", "DT_", "PERIOD", "RATE", "SEC", "_S", "AGE", "DWELL", "DELIVER", "TICK"))}
    return {"file": relpath, "module_temporal_consts": temporal_consts,
            "sleeps_timers": sorted(sleeps, key=lambda r: r["lineno"])}


def _loop_rate_sleep(relpath, func_names, consts_by_file):
    """Kadencja GŁÓWNEJ pętli funkcji = `time.sleep` będący BEZPOŚREDNIM dzieckiem ciała `while`
    (nie w gałęzi if/continue trybu off/far). To odróżnia producenta ruchu (osc @track) od idle-sleepów.
    Zwraca (lineno, value) głównopętlowego sleepa albo (None, None)."""
    path = os.path.join(ROOT, relpath)
    tree = ast.parse(open(path).read(), filename=relpath)
    consts = consts_by_file.get(relpath) or _module_consts(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in func_names:
            for w in ast.walk(node):
                if isinstance(w, (ast.While, ast.For)):
                    for stmt in w.body:                       # TYLKO bezpośrednie dzieci ciała pętli
                        if (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
                                and isinstance(stmt.value.func, ast.Attribute)
                                and stmt.value.func.attr == "sleep" and stmt.value.args):
                            v = _resolve(stmt.value.args[0], consts)
                            if v is not None:
                                return stmt.lineno, v
    return None, None


def _motion_cadence(scan_regate, scan_akt, consts_by_file):
    """Rola KLUCZOWA (pominięta w §4b): kadencja RUCHU intruza. REGATE=replacer, akt=_telethread.
    Bierze sleep GŁÓWNEJ pętli (bezpośrednie dziecko while) — pomija continue-sleepy trybów off/far."""
    def all_sleeps(scans, func_names):
        out = []
        for sc in scans:
            for s in sc["sleeps_timers"]:
                if s["func"] in func_names and s["value_s"] is not None:
                    out.append((sc["file"], s["lineno"], s["value_s"]))
        return out
    reg_all = all_sleeps(scan_regate, {"replacer"})
    akt_all = all_sleeps(scan_akt, {"_telethread"})
    reg_line, reg_dt = None, None
    for sc in scan_regate:
        reg_line, reg_dt = _loop_rate_sleep(sc["file"], {"replacer"}, consts_by_file)
        if reg_dt is not None:
            reg_line = (sc["file"], reg_line); break
    akt_line, akt_dt = None, None
    for sc in scan_akt:
        akt_line, akt_dt = _loop_rate_sleep(sc["file"], {"_telethread"}, consts_by_file)
        if akt_dt is not None:
            akt_line = (sc["file"], akt_line); break
    return {"regate_main_loop_sleep_s": reg_dt, "regate_main_loop_site": reg_line,
            "akt_main_loop_sleep_s": akt_dt, "akt_main_loop_site": akt_line,
            "regate_all_replacer_sleeps": reg_all, "akt_all_teleport_sleeps": akt_all}


def main():
    scans = {trk: [_scan_file(f) for f in files] for trk, files in TRACKS.items()}

    # --- role semantyczne (diff) ---
    def const_across(scans_list, names):
        for sc in scans_list:
            for nm in names:
                if nm in sc["module_temporal_consts"]:
                    return sc["file"], nm, sc["module_temporal_consts"][nm]
        return None, None, None

    consts_by_file = {sc["file"]: sc["module_temporal_consts"]
                      for trk in TRACKS for sc in scans[trk]}
    # decyzja
    rf, rn, rv = const_across(scans["regate"], ["DECISION_HZ"])
    af, an, av = const_across(scans["akt"], ["DEMO_DECISION_HZ"])
    # ruch intruza (KLUCZOWE — producent, §4b go pominął): sleep GŁÓWNEJ pętli (nie continue-branch)
    motion = _motion_cadence(scans["regate"], scans["akt"], consts_by_file)
    # teleport akt jako stała modułowa (DEMO_TELEPORT_DT) + Hz
    tf, tn, tv = const_across(scans["akt"], ["DEMO_TELEPORT_DT"])
    thf, thn, thv = const_across(scans["akt"], ["DEMO_TELEPORT_HZ"])

    reg_motion_dt = motion["regate_main_loop_sleep_s"]
    akt_motion_dt = motion["akt_main_loop_sleep_s"] if motion["akt_main_loop_sleep_s"] is not None else tv

    def row(param, reg, akt, unit, note):
        eq = (reg is not None and akt is not None and abs(float(reg) - float(akt)) < 1e-9)
        return {"param": param, "regate": reg, "akt": akt, "unit": unit, "equal": eq, "note": note}

    semantic = [
        row("intruder_motion_dt_s", reg_motion_dt, akt_motion_dt, "s",
            "KADENCJA RUCHU intruza (producent — pominięty w §4b): REGATE replacer sleep vs akt _telethread/DEMO_TELEPORT_DT"),
        row("intruder_motion_hz", round(1.0/reg_motion_dt, 1) if reg_motion_dt else None,
            thv if thv is not None else (round(1.0/akt_motion_dt, 1) if akt_motion_dt else None), "Hz",
            "= 1/dt; REGATE ~16.7 == akt DEMO_TELEPORT_HZ (§5a)"),
        row("decision_hz", rv, av, "Hz", "REGATE DECISION_HZ vs akt DEMO_DECISION_HZ (§4a)"),
    ]
    diffs = [r["param"] for r in semantic if not r["equal"]]

    result = {
        "aneks": "D5 §5b (4b-v2)", "method": "AST sweep (kompletność z kodu)",
        "tracks": {trk: [ {"file": sc["file"],
                            "module_temporal_consts": sc["module_temporal_consts"],
                            "sleeps_timers": sc["sleeps_timers"]} for sc in scans[trk]]
                   for trk in TRACKS},
        "motion_cadence": motion,
        "semantic_diff": semantic,
        "diffs": diffs,
        "verdict": ("ZGODNE — zero różnic kadencji semantycznej po §5a" if not diffs
                    else f"RÓŻNICE: {diffs} → klasyfikacja harness/frozen → STOP jeśli frozen"),
    }

    # --- wypis ---
    print("=== ANEKS_D5 §5b — SWEEP STAŁYCH TEMPORALNYCH (AST, kompletność z kodu) ===")
    for trk in ("regate", "akt", "shared"):
        print(f"\n[{trk.upper()}]")
        for sc in scans[trk]:
            print(f"  {sc['file']}")
            if sc["module_temporal_consts"]:
                print(f"    stałe: {sc['module_temporal_consts']}")
            for s in sc["sleeps_timers"]:
                v = f"{s['value_s']:.4f}s" if s["value_s"] is not None else "?"
                print(f"    L{s['lineno']:>4} {s['kind']:5} in {s['func']:<22} arg={s['arg_src']} → {v}")
    print("\n--- DIFF ról semantycznych (sterujące pipeline MTI/ENTRY) ---")
    print(f"{'param':22} {'REGATE':>10} {'AKT':>10} {'==':>3}  uwaga")
    for r in semantic:
        mark = "OK" if r["equal"] else "!!"
        print(f"{r['param']:22} {str(r['regate']):>10} {str(r['akt']):>10} {mark:>3}  {r['note']}")
    print(f"\nWERDYKT §5b: {result['verdict']}")

    out = sys.argv[1] if len(sys.argv) > 1 else None
    if out:
        json.dump(result, open(out, "w"), indent=2, ensure_ascii=False)
        print(f"[temporal_sweep_5b] → {out}")
    return 0 if not diffs else 3


if __name__ == "__main__":
    sys.exit(main())
