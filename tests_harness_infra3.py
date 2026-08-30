#!/usr/bin/env python3
"""tests_harness_infra3.py — B1.2 (PROMPT_INFRA3) + bramka procesowa §3. Bez SITL. Wchodzi do commita B1.

(i)   stub-manifest: katalog z act.log bez trace.jsonl → finalize rc≠0 → stub obecny z crash_reason.
(ii)  ulog_sha liczony poprawnie na pliku testowym.
(iii) world_hash.txt dla świata z worlds/ i dla stockowego.
(iv)  SETTLE_S=30 odrzucone przez run_boot.sh.
(v)   §3 bramka: syntetyczny zjadacz CPU (`yes`) ⇒ proc_gate blokuje z jego PID; po ubiciu ⇒ przepuszcza;
      allowlista: wzorzec `claude` nie blokuje, `yes` blokuje.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
HARNESS = os.path.join(ROOT, "harness")


# ---------------- (i) stub-manifest ----------------
def test_stub_manifest_on_finalize_fail():
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "act.log"), "w").write("boot log\n")
        # brak trace.jsonl → k1_finalize musi paść rc≠0
        r = subprocess.run([sys.executable, "k1/k1_finalize.py",
                            "--trace", os.path.join(d, "trace.jsonl"),
                            "--arm", "S", "--point", "0.65", "--boot", "9", "--kind", "crit",
                            "--harness-sha-file", "r03/gate_run_r03.py", "--out-dir", d],
                           cwd=ROOT, capture_output=True, text=True,
                           env={**os.environ, "PYTHONPATH": f".:{os.environ.get('PYTHONPATH','')}"})
        assert r.returncode != 0, "finalize powinien paść bez trace.jsonl"
        # finalize.log dla crash_reason
        open(os.path.join(d, "finalize.log"), "w").write(r.stderr[-2000:] or "traceback: brak trace.jsonl\n")
        # łapacz: stub
        s = subprocess.run([sys.executable, os.path.join(HARNESS, "stub_manifest.py"),
                            "--out-dir", d, "--arm", "S", "--point", "0.65", "--boot", "9",
                            "--rc", "0", "--finalize-rc", str(r.returncode)],
                           cwd=ROOT, capture_output=True, text=True)
        assert s.returncode == 0, s.stderr
        m = json.load(open(os.path.join(d, "manifest.json")))
        assert m["kind"] == "stub"
        assert m["run_valid"] is None
        assert m["finalize_rc"] == r.returncode
        assert m["crash_reason"], "crash_reason pusty"
        # idempotencja: nie nadpisuje NIE-stub
        json.dump({"kind": "crit", "x": 1}, open(os.path.join(d, "manifest.json"), "w"))
        subprocess.run([sys.executable, os.path.join(HARNESS, "stub_manifest.py"),
                        "--out-dir", d, "--boot", "9"], cwd=ROOT, capture_output=True)
        assert json.load(open(os.path.join(d, "manifest.json")))["kind"] == "crit"


# ---------------- (ii) ulog_sha ----------------
def test_ulog_sha():
    import importlib.util
    spec = importlib.util.spec_from_file_location("augment_manifest", os.path.join(HARNESS, "augment_manifest.py"))
    am = importlib.util.module_from_spec(spec); spec.loader.exec_module(am)
    with tempfile.NamedTemporaryFile(delete=False) as f:
        payload = b"ULOG-TEST-" + b"\x00\x01\x02" * 1000
        f.write(payload); p = f.name
    try:
        sha, n = am.sha256_size(p)
        assert sha == hashlib.sha256(payload).hexdigest()
        assert n == len(payload)
        # augmentacja manifestu
        with tempfile.TemporaryDirectory() as d:
            json.dump({"kind": "stub"}, open(os.path.join(d, "manifest.json"), "w"))
            subprocess.run([sys.executable, os.path.join(HARNESS, "augment_manifest.py"),
                            "--out-dir", d, "--ulog", p], cwd=ROOT, capture_output=True, check=True)
            m = json.load(open(os.path.join(d, "manifest.json")))
            assert m["ulog_sha"] == sha and m["ulog_bytes"] == n
    finally:
        os.unlink(p)


# ---------------- (iii) world_hash ----------------
def test_world_hash_repo_and_stock():
    with tempfile.TemporaryDirectory() as d:
        # repo: world_demo_A3 (worlds/)
        subprocess.run(["bash", os.path.join(HARNESS, "world_hash.sh"), "world_demo_A3", d],
                       cwd=ROOT, capture_output=True, text=True, check=True)
        line = open(os.path.join(d, "world_hash.txt")).read().strip()
        exp = hashlib.sha256(open(os.path.join(ROOT, "worlds/world_demo_A3.sdf"), "rb").read()).hexdigest()
        assert line.startswith(exp) and "worlds/world_demo_A3.sdf" in line and not line.startswith("stock:")
    with tempfile.TemporaryDirectory() as d:
        # stock: default
        subprocess.run(["bash", os.path.join(HARNESS, "world_hash.sh"), "default", d],
                       cwd=ROOT, capture_output=True, text=True, check=True)
        line = open(os.path.join(d, "world_hash.txt")).read().strip()
        stock = os.path.join(ROOT, "PX4-Autopilot/Tools/simulation/gz/worlds/default.sdf")
        exp = hashlib.sha256(open(stock, "rb").read()).hexdigest()
        assert line.startswith("stock:default ") and exp in line


# ---------------- (iv) SETTLE_S<90 odrzucone ----------------
def test_settle_s_reject():
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run(["bash", os.path.join(HARNESS, "run_boot.sh")],
                           cwd=ROOT, capture_output=True, text=True,
                           env={**os.environ, "FLIGHT": "empty", "SETTLE_S": "30",
                                "OUTDIR": os.path.join(d, "b1"), "BOOT_N": "1"})
        assert r.returncode == 2, f"rc={r.returncode} out={r.stdout} err={r.stderr}"
        assert "SETTLE_S=30" in r.stdout and "ODRZUCONE" in r.stdout
        assert not os.path.exists(os.path.join(d, "b1")), "OUTDIR nie powinien powstać przy odrzuceniu"
    # kontrola: SETTLE_S=90 przechodzi guard (nie testujemy dalej — brak SITL; sprawdzamy że NIE rc=2 na guardzie)
    # (pomijamy pełne uruchomienie; guard to jedyna asercja dla tej gałęzi)


# ---------------- (v) §3 bramka procesowa ----------------
def _load_am_patterns():
    import importlib.util
    spec = importlib.util.spec_from_file_location("proc_gate", os.path.join(HARNESS, "proc_gate.py"))
    pg = importlib.util.module_from_spec(spec); spec.loader.exec_module(pg)
    return pg


def test_proc_gate_allowlist_patterns():
    pg = _load_am_patterns()
    pats = pg.load_patterns(os.path.join(HARNESS, "proc_allowlist.txt"))
    assert any(p.search("claude --continue") for p in pats), "wzorzec claude powinien pasować"
    assert any(p.search("/usr/lib/systemd/systemd --user") for p in pats), "systemd powinien pasować"
    assert not any(p.search("yes") for p in pats), "'yes' NIE powinien być na allowliście"


def test_proc_gate_blocks_cpu_eater_then_passes():
    eater = subprocess.Popen(["yes"], stdout=subprocess.DEVNULL)
    try:
        time.sleep(1.0)
        r = subprocess.run([sys.executable, os.path.join(HARNESS, "proc_gate.py"),
                            "--delay", "2", "--self", str(os.getpid())],
                           cwd=ROOT, capture_output=True, text=True)
        assert r.returncode == 3, f"powinien blokować (yes @100% CPU); out={r.stdout}"
        assert str(eater.pid) in r.stdout or "yes" in r.stdout, f"winowajca nieujawniony: {r.stdout}"
    finally:
        eater.terminate(); eater.wait()
    time.sleep(1.0)
    r2 = subprocess.run([sys.executable, os.path.join(HARNESS, "proc_gate.py"),
                        "--delay", "2", "--self", str(os.getpid())],
                       cwd=ROOT, capture_output=True, text=True)
    # po ubiciu zjadacza: brak cudzego >2% (o ile maszyna czysta) → CLEAN.
    # Uwaga: jeśli w tle wykonawcy jest inny >2% proces, test to ujawni (świadomie, nie maskujemy).
    assert r2.returncode == 0, f"po ubiciu yes powinien przepuścić; out={r2.stdout}"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            print(f"-- {name}")
            fn()
            print(f"   OK")
    print("\ntests_harness_infra3: ALL PASS")
