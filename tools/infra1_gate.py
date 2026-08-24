#!/usr/bin/env python3
"""
tools/infra1_gate.py [--dir results/K1/E/p0_0] [--n 10] [--start 1] — INFRA-1 I3 bramka wyjścia.

Czyta manifesty 10 KOLEJNYCH pustych bootów, buduje tabelę, liczy werdykt ZAMROŻONY teraz:
  PASS ⟺ n_arm ≥ 9/10  ∧  n_habitat_valid ≥ 9/10   (habitat pustego lotu VALID = timejump=0 ∧
  Δsim/Δwall≥0.95 na 60 s oknie hoveru). Wynik <9 ⇒ FAIL (tabela + diagnoza per fail).
Zero wybierania bootów: każdy z 10 slotów trafia do tabeli (brak manifestu = FAIL slotu).
"""
import os, sys, json, argparse

PASS_MIN = 9   # ≥9/10, zamrożone


def load(d):
    p = os.path.join(d, "manifest.json")
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="results/K1/E/p0_0")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--start", type=int, default=1)
    a = ap.parse_args()

    rows = []
    n_arm = n_hab = n_both = 0
    for i in range(a.start, a.start + a.n):
        d = os.path.join(a.dir, f"boot{i}")
        m = load(d)
        if m is None:
            rows.append({"boot": i, "present": False, "arm_ok": False, "habitat": "MISSING",
                         "conv_s": None, "load1": None, "timejump_post": None, "ekf_hits": None,
                         "diag": "brak manifestu (boot nie ukończony / env-block bez slotu)"})
            continue
        arm_ok = bool(m.get("arm_ok"))
        hab = m.get("habitat_verdict")
        hab_ok = (hab == "VALID")
        sess = m.get("session") or {}
        load1 = (sess.get("loadavg") or [None])[0]
        diag = ""
        if m.get("kind") == "env-block":
            diag = "env-block (load>%s) — nie powinien liczyc sie do 10" % m.get("load_max")
        elif not arm_ok:
            diag = "arm-fail: conv_s=%s timejump_post=%s ekf_hits=%s" % (
                m.get("conv_s"), m.get("timejump_post"), m.get("ekf_health_hits"))
        elif not hab_ok:
            hd = {}
            hp = os.path.join(d, "habitat.json")
            if os.path.exists(hp):
                try:
                    hd = json.load(open(hp))
                except Exception:
                    hd = {}
            seg = (hd.get("hover_seg") or {})
            diag = "habitat INVALID: h1=%s dsim_dwall=%s (okno hover)" % (
                (hd.get("h1") or {}).get("pass"), seg.get("dsim_dwall"))
        n_arm += arm_ok
        n_hab += hab_ok
        n_both += (arm_ok and hab_ok)
        rows.append({"boot": i, "present": True, "arm_ok": arm_ok, "habitat": hab,
                     "conv_s": m.get("conv_s"), "load1": load1,
                     "timejump_post": m.get("timejump_post"), "ekf_hits": m.get("ekf_health_hits"),
                     "landed": m.get("landed"), "diag": diag})

    verdict = "PASS" if (n_arm >= PASS_MIN and n_hab >= PASS_MIN) else "FAIL"
    out = {"verdict": verdict, "pass_min": PASS_MIN, "n_total": a.n,
           "n_arm": n_arm, "n_habitat_valid": n_hab, "n_both": n_both, "rows": rows}
    os.makedirs("results/K1/INFRA1", exist_ok=True)
    with open("results/K1/INFRA1/gate.json", "w") as f:
        json.dump(out, f, indent=2)

    print("boot | arm_ok | habitat        | conv_s | load1 | tj_post | ekf | diag")
    print("-----+--------+----------------+--------+-------+---------+-----+-----")
    for r in rows:
        print("%4d | %-6s | %-14s | %6s | %5s | %7s | %3s | %s" % (
            r["boot"], r["arm_ok"], str(r["habitat"]), str(r["conv_s"]), str(r["load1"]),
            str(r["timejump_post"]), str(r["ekf_hits"]), r["diag"]))
    print("\nn_arm=%d/%d  n_habitat_valid=%d/%d  n_both=%d/%d  →  VERDICT=%s (PASS wymaga ≥%d/%d obu)" % (
        n_arm, a.n, n_hab, a.n, n_both, a.n, verdict, PASS_MIN, a.n))
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
