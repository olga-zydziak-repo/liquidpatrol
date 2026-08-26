#!/usr/bin/env python3
"""
tools/infra2_ekf_watchdog.py — INFRA2-6/E1: watchdog reinitu EKF2 wewnątrz bootu (warstwa tools).

E1a  Read-only sampler co ~5 s (wall) od T0, przez klienta daemona PX4 (`px4-listener` po sockecie
     /tmp/px4-sock-<inst>): estimator_status.filter_fault_flags, estimator_status_flags.fs_bad_acc_vertical,
     estimator_sensor_bias.gyro_bias[0..2]. Sim-czas próbki = uORB timestamp (µs) → s (oś lockstepu).
E1b  Trigger zatrzasku (dyskryminator klas z V1, NIE uniwersalny garb ~20 s):
       FAST : filter_fault_flags==1024 ∨ fs_bad_acc_vertical, w 2 KOLEJNYCH próbkach.
       SLOW (fallback): |gyro_bias| > 0.08 bez trendu malejącego przez 30 s (sim) — dopiero po sim 60 s.
     |gyro_bias| = max(|b0|,|b1|,|b2|) (per-oś, zgodnie z Y4: dywergencja osi do 0.14–0.15 rad/s).
E1c  Akcja: `px4-ekf2 stop` → `px4-ekf2 start`. Stemple sim/wall + bias przed/po. MAKS 2 reinity/boot.
     ŻADNEGO abortu, ŻADNEGO relaunchu, ZERO zmian EKF2_* / okna arm. Boot biegnie dalej sam.
E1e  Wynik → ekf_watchdog.json (samples, reinits, n_reinits, bias_max, bias_last, first_fault_sim);
     finalize wstrzykuje blok `watchdog` do manifestu.

R3/G2 (ANEKS_E1-2): PREFLIGHT-ONLY. Watchdog kończy w chwili armed==1 (poll actuator_armed) — PO ARM
zero próbek, zero reinitu, segment roszczenia (denial→touchdown) WOLNY od przyrządu. Bez arm żyje do SIGTERM
(ubijany przez run_k1_boot.sh po module lotu) lub HARD_CAP_S. Read-only na uORB przez listener; jedyny efekt
uboczny = ekf2 stop/start przy potwierdzonym triggerze PRZED arm. Sędzia/osłona/piny/harness lotu K1 NIETKNIĘTE.
"""
import os, sys, re, json, time, signal, argparse, subprocess

FFF_LATCH = 1024          # estimator_status.filter_fault_flags — sygnatura faultu pionu (V1)
BIAS_SLOW = 0.08          # rad/s, |gyro_bias| dla wolnego fallbacku
SLOW_AFTER_SIM = 60.0     # fallback dopiero po sim 60 s
SLOW_WIN_SIM = 30.0       # okno „bez trendu malejącego" [s sim]
SLOW_DROP_TOL = 0.01      # rad/s — spadek < tol w oknie ⇒ „nie maleje"
FAST_CONSEC = 2           # 2 kolejne próbki z faultem
MAX_REINITS = 2           # E1c
POLL_S = 5.0              # E1a — co ~5 s wall
LISTENER_TIMEOUT = 4.0    # s na pojedynczy px4-listener
REINIT_COOLDOWN_SIM = 15.0  # po reinicie: pauza triggera aż sim ruszy o tyle (ekf2 restart+rekonwergencja)
HARD_CAP_S = 900          # bezpiecznik wall (boot E << 900 s)

_RE = {
    "ts": re.compile(r"\btimestamp:\s*(\d+)"),
    "fff": re.compile(r"\bfilter_fault_flags:\s*(\d+)"),
    "fbav": re.compile(r"\bfs_bad_acc_vertical:\s*(True|False|\d+)"),  # listener drukuje bool jako True/False
    "armed": re.compile(r"\barmed:\s*(True|False|\d+)"),  # actuator_armed.armed (nie prearmed — brak \b)
    "gbias": re.compile(r"\bgyro_bias:\s*\[([^\]]+)\]"),
}


def _px4(binpath, cmd_args, timeout):
    """Woła klienta daemona px4-<cmd> (argv[0] symlink → tryb klienta). Zwraca (rc, stdout) lub (None,'')."""
    exe = os.path.join(binpath, "px4-" + cmd_args[0])
    argv = [exe, "--instance", "0"] + cmd_args[1:]
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return None, ""
    except Exception as e:
        return None, f"__exc__ {e}"


def _listen(binpath, topic):
    rc, out = _px4(binpath, ["listener", topic, "1"], LISTENER_TIMEOUT)
    return out if rc == 0 else out  # parsujemy co jest; puste → None w polach


def sample(binpath):
    """Jedna próbka: fff, fbav, gyro_bias[3], sim (µs→s). None gdy listener nie oddał pola."""
    s_es = _listen(binpath, "estimator_status")
    s_fl = _listen(binpath, "estimator_status_flags")
    s_bi = _listen(binpath, "estimator_sensor_bias")

    def _i(rx, txt):
        m = _RE[rx].search(txt or "")
        return int(m.group(1)) if m else None

    fff = _i("fff", s_es)
    mfb = _RE["fbav"].search(s_fl or "")
    fbav = None
    if mfb:
        g = mfb.group(1)
        fbav = 1 if (g == "True" or (g.isdigit() and int(g) != 0)) else 0
    gbias = None
    mb = _RE["gbias"].search(s_bi or "")
    if mb:
        try:
            gbias = [float(x) for x in mb.group(1).split(",")][:3]
        except Exception:
            gbias = None
    # sim: preferuj stempel estimator_sensor_bias, potem estimator_status
    sim = None
    for txt in (s_bi, s_es, s_fl):
        m = _RE["ts"].search(txt or "")
        if m:
            sim = int(m.group(1)) / 1e6
            break
    absmax = max(abs(x) for x in gbias) if gbias else None
    norm = (sum(x * x for x in gbias) ** 0.5) if gbias else None
    return {"wall": round(time.time(), 3), "sim": (round(sim, 3) if sim is not None else None),
            "fff": fff, "fbav": fbav, "gyro_bias": ([round(x, 6) for x in gbias] if gbias else None),
            "bias_absmax": (round(absmax, 6) if absmax is not None else None),
            "bias_norm": (round(norm, 6) if norm is not None else None)}


def poll_armed(binpath):
    """R3/G2: (armed_bool, sim) z actuator_armed. Watchdog=PREFLIGHT-ONLY → kończy przy armed==1."""
    rc, out = _px4(binpath, ["listener", "actuator_armed", "1"], LISTENER_TIMEOUT)
    m = _RE["armed"].search(out or "")
    armed = None
    if m:
        g = m.group(1)
        armed = 1 if (g == "True" or (g.isdigit() and int(g) != 0)) else 0
    sim = None
    mt = _RE["ts"].search(out or "")
    if mt:
        sim = round(int(mt.group(1)) / 1e6, 3)
    return armed, sim


def is_fault(s):
    return (s["fff"] == FFF_LATCH) or (s["fbav"] not in (None, 0))


def slow_trip(samples, now_sim):
    """SLOW: po sim 60 s, |bias|>0.08 i w oknie 30 s (sim) nie maleje (spadek < tol)."""
    if now_sim is None or now_sim < SLOW_AFTER_SIM:
        return False
    win = [s for s in samples if s["sim"] is not None and s["bias_absmax"] is not None
           and (now_sim - SLOW_WIN_SIM) <= s["sim"] <= now_sim]
    if len(win) < 3:
        return False
    if any(s["bias_absmax"] <= BIAS_SLOW for s in win):
        return False
    drop = win[0]["bias_absmax"] - win[-1]["bias_absmax"]  # >0 gdy maleje
    return drop < SLOW_DROP_TOL


def do_reinit(binpath):
    t0 = time.time()
    rc_stop, out_stop = _px4(binpath, ["ekf2", "stop"], 6.0)
    time.sleep(2.0)
    rc_start, out_start = _px4(binpath, ["ekf2", "start"], 6.0)
    return {"rc_stop": rc_stop, "rc_start": rc_start,
            "cmd_wall_s": round(time.time() - t0, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--px4-bin", required=True, help="katalog build/px4_sitl_default/bin (symlinki px4-*)")
    ap.add_argument("--out", required=True, help="ścieżka ekf_watchdog.json")
    a = ap.parse_args()

    state = {
        "spec": "INFRA2-6/E1", "instance": 0, "px4_bin": a.px4_bin,
        "params": {"FFF_LATCH": FFF_LATCH, "BIAS_SLOW": BIAS_SLOW, "SLOW_AFTER_SIM": SLOW_AFTER_SIM,
                   "SLOW_WIN_SIM": SLOW_WIN_SIM, "FAST_CONSEC": FAST_CONSEC, "MAX_REINITS": MAX_REINITS,
                   "POLL_S": POLL_S, "bias_metric": "max_abs_axis"},
        "started_wall": round(time.time(), 3),
        "samples": [], "reinits": [], "n_reinits": 0,
        "bias_max": None, "bias_last": None,
        "first_fault_sim": {"filter_fault_1024": None, "fs_bad_acc_vertical": None},
        "n_poll_fail": 0,
        "preflight_only": True, "armed_sim": None, "stopped_reason": None,  # R3/G2
    }

    def flush():
        # bias_max / bias_last z próbek które miały odczyt
        bvals = [s["bias_absmax"] for s in state["samples"] if s["bias_absmax"] is not None]
        state["bias_max"] = round(max(bvals), 6) if bvals else None
        last_ok = next((s for s in reversed(state["samples"]) if s["bias_absmax"] is not None), None)
        state["bias_last"] = last_ok
        tmp = a.out + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, a.out)

    stop_flag = {"v": False}

    def _term(*_):
        stop_flag["v"] = True
    signal.signal(signal.SIGTERM, _term)
    signal.signal(signal.SIGINT, _term)

    consec_fault = 0
    cooldown_until_sim = None
    t_start = time.time()
    flush()

    while not stop_flag["v"]:
        if time.time() - t_start > HARD_CAP_S:
            state["stopped_reason"] = "hard_cap"
            break
        # R3/G2: PREFLIGHT-ONLY — sprawdź arm PRZED próbką/triggerem. armed⇒kończ, segment roszczenia wolny od przyrządu.
        armed, arm_sim = poll_armed(a.px4_bin)
        if armed == 1:
            state["armed_sim"] = arm_sim
            state["stopped_reason"] = "ARMED_preflight_only"
            print(f"[WD] ARMED @sim={arm_sim} — sampler STOP (PREFLIGHT-ONLY, R3/G2). "
                  f"n_samples={len(state['samples'])} n_reinits={state['n_reinits']}", flush=True)
            flush()
            break
        s = sample(a.px4_bin)
        state["samples"].append(s)
        if s["fff"] is None and s["gyro_bias"] is None:
            state["n_poll_fail"] += 1

        # first-fault sim (dziennik faultów z czasami — E1e)
        if s["sim"] is not None:
            if s["fff"] == FFF_LATCH and state["first_fault_sim"]["filter_fault_1024"] is None:
                state["first_fault_sim"]["filter_fault_1024"] = s["sim"]
            if s["fbav"] not in (None, 0) and state["first_fault_sim"]["fs_bad_acc_vertical"] is None:
                state["first_fault_sim"]["fs_bad_acc_vertical"] = s["sim"]

        # trigger tylko gdy budżet reinitów jest i minął cooldown po ostatnim reinicie
        can_trigger = state["n_reinits"] < MAX_REINITS
        if can_trigger and cooldown_until_sim is not None and s["sim"] is not None \
                and s["sim"] < cooldown_until_sim:
            can_trigger = False

        # FAST: 2 kolejne próbki faultu
        if is_fault(s):
            consec_fault += 1
        else:
            consec_fault = 0

        reason = None
        if can_trigger:
            if consec_fault >= FAST_CONSEC:
                reason = "FAST_fault2x(fff==1024|fs_bad_acc_vertical)"
            elif slow_trip(state["samples"], s["sim"]):
                reason = "SLOW_bias>0.08_no_decrease_30s"

        if reason:
            before = s
            act = do_reinit(a.px4_bin)
            time.sleep(5.0)  # daj ekf2 wstać
            after = sample(a.px4_bin)
            state["samples"].append(after)
            state["n_reinits"] += 1
            state["reinits"].append({
                "idx": state["n_reinits"], "reason": reason,
                "sim": s["sim"], "wall": round(time.time(), 3),
                "consec_fault": consec_fault, "action": act,
                "bias_before": {"absmax": before["bias_absmax"], "norm": before["bias_norm"],
                                "xyz": before["gyro_bias"], "fff": before["fff"], "fbav": before["fbav"]},
                "bias_after": {"absmax": after["bias_absmax"], "norm": after["bias_norm"],
                               "xyz": after["gyro_bias"], "fff": after["fff"], "fbav": after["fbav"]},
            })
            consec_fault = 0
            cooldown_until_sim = (after["sim"] + REINIT_COOLDOWN_SIM) if after["sim"] is not None \
                else ((s["sim"] + REINIT_COOLDOWN_SIM) if s["sim"] is not None else None)
            print(f"[WD] REINIT #{state['n_reinits']} reason={reason} sim={s['sim']} "
                  f"bias {before['bias_absmax']}→{after['bias_absmax']} act={act}", flush=True)
            flush()
        else:
            flush()

        # sen 5 s wall, ale reaguj na SIGTERM
        for _ in range(int(POLL_S * 10)):
            if stop_flag["v"]:
                break
            time.sleep(0.1)

    flush()
    print(f"[WD] KONIEC n_reinits={state['n_reinits']} samples={len(state['samples'])} "
          f"bias_max={state['bias_max']} first_fault={state['first_fault_sim']}", flush=True)


if __name__ == "__main__":
    main()
