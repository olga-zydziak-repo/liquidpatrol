#!/usr/bin/env python3
"""results/KONT/tools/kont_s4_dryrun.py — próba na sucho drivera S4 (ANEKS_KONT-4b §1.2), bez bootu.

(i) Ścieżki zależne od ROOT: ROOT drivera == korzeń repo (git rev-parse); każdy literał `os.path.join(ROOT, "…")` i każdy
    argument `_sha("…")` w źródle drivera istnieje i jest plikiem; MANIFEST i executor_params istnieją; selfchecki uruchomione
    z cwd=ROOT tak jak w driverze (rc 0); `harness.intruder_motion` importowalny z cwd=ROOT (driver woła `-m` z tym cwd).
(ii) `main()` drivera do pierwszego wywołania sieciowego (`System().connect`) z atrapami rclpy/GzNode/EkfSub/System; atrapa
    connect rzuca znacznik i zapisuje, dokąd doszedł main().
Użycie: kont_s4_dryrun.py <katalog wyjścia> [<plik drivera, kontrola negatywna>]. Wyjście: dryrun.json; kod 0 ⇔ (i) ∧ (ii) PASS."""
import asyncio
import json
import os
import re
import subprocess
import sys

DRIVER = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else
                         os.path.join(os.path.dirname(os.path.abspath(__file__)), "kont_s4_flight.py"))   # argv[2]: kontrola negatywna


class DryRunStop(Exception):
    pass


def main():
    out = os.path.abspath(sys.argv[1])
    os.makedirs(out, exist_ok=True)
    os.environ.update({"GATE_OUT": os.path.join(out, "trace.jsonl"), "BENCH_EPISODE_IDS": "0,1,2,3",
                       "BENCH_EPISODES": "4", "KONT_MODE": "1", "FEED": "V2", "NET_ARM": "ncp", "CONTROLLER": "net_skan2"})
    src = open(DRIVER, encoding="utf8").read()
    ns = {"__name__": "kont_s4_dryrun_mod", "__file__": DRIVER}
    exec(compile(src, DRIVER, "exec"), ns)
    root = ns["ROOT"]
    git_root = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=os.path.dirname(DRIVER),
                              capture_output=True, text=True).stdout.strip()
    lit = sorted(set(re.findall(r'os\.path\.join\(ROOT, "([^"]+)"\)', src)) | set(re.findall(r'_sha\("([^"]+)"\)', src)))
    lit.append(ns["MANIFEST"])
    sciezki = {p: os.path.isfile(os.path.join(root, p)) for p in lit}
    sc = {}
    for nm, cmd in (("certs_selfcheck", [sys.executable, "-m", "r01.proofs.certs_selfcheck"]),
                    ("kont_certs_selfcheck", [sys.executable, "results/KONT/s3/tools/kont_certs_selfcheck.py"])):
        r = subprocess.run(cmd, cwd=root, capture_output=True, text=True,
                           env={**os.environ, "PYTHONPATH": f".:.certdeps:{os.environ.get('PYTHONPATH', '')}"})
        sc[nm] = {"rc": r.returncode, "werdykt": [l for l in r.stdout.splitlines() if "WERDYKT" in l]}
    im = subprocess.run([sys.executable, "-c", "import harness.intruder_motion"], cwd=root, capture_output=True, text=True,
                        env={**os.environ, "PYTHONPATH": f".:{os.environ.get('PYTHONPATH', '')}"})
    czesc_i = {"ROOT": root, "git_root": git_root, "root_ok": root == git_root, "sciezki": sciezki,
               "selfchecki": sc, "intruder_motion_import_rc": im.returncode,
               "intruder_motion_stderr": im.stderr[-400:]}
    ok_i = (czesc_i["root_ok"] and all(sciezki.values()) and all(v["rc"] == 0 for v in sc.values())
            and im.returncode == 0)

    # (ii) main() do pierwszego wywołania sieciowego
    doszedl = []

    class FakeSystem:
        async def connect(self, system_address=None):
            doszedl.append(f"System.connect({system_address})")
            raise DryRunStop("pierwsze wywołanie sieciowe")

    class FakeGz:
        def subscribe(self, *a, **k):
            doszedl.append("GzNode.subscribe przed connect (nieoczekiwane)")

    class FakeEkf:
        m = None
        flags = None

    ns["System"] = FakeSystem
    ns["GzNode"] = lambda: (doszedl.append("GzNode()"), FakeGz())[1]
    ns["EkfSub"] = lambda: (doszedl.append("EkfSub()"), FakeEkf())[1]
    ns["rclpy"] = type("R", (), {"init": staticmethod(lambda: doszedl.append("rclpy.init()")),
                                 "ok": staticmethod(lambda: False)})
    wynik_ii, blad = None, None
    try:
        asyncio.run(ns["main"]())
        wynik_ii = "main() zakończył się bez wywołania sieciowego (nieoczekiwane)"
    except DryRunStop as e:
        wynik_ii = f"zatrzymane: {e}"
    except Exception as e:
        blad = f"{type(e).__name__}: {e}"
    czesc_ii = {"kroki": doszedl, "wynik": wynik_ii, "blad": blad,
                "epizody": os.environ["BENCH_EPISODE_IDS"]}
    ok_ii = blad is None and wynik_ii is not None and wynik_ii.startswith("zatrzymane") and doszedl[-1].startswith("System.connect")
    res = {"driver": os.path.relpath(DRIVER, root),
           "driver_sha256": __import__("hashlib").sha256(open(DRIVER, "rb").read()).hexdigest(),
           "czesc_i": czesc_i, "czesc_i_ok": ok_i, "czesc_ii": czesc_ii, "czesc_ii_ok": ok_ii, "PASS": ok_i and ok_ii}
    json.dump(res, open(os.path.join(out, "dryrun.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"PASS": res["PASS"], "i": ok_i, "ii": ok_ii, "kroki": doszedl, "blad": blad,
                      "brakujace": [p for p, v in sciezki.items() if not v]}, ensure_ascii=False))
    sys.exit(0 if res["PASS"] else 1)


if __name__ == "__main__":
    main()
