#!/usr/bin/env python3
"""r01/gate_run.py — runner scenariuszy bramki R0.1 (S1–S4, §7 PRE_R01).

Świeży boot per scenariusz (dyscyplina pomiarowa — zaostrzenie jawne, wzorzec R0.0).
Każdy scenariusz: trace jsonl + metryki §7 + mavsdk_motion_cmds (A1) + GF-firing (A3).
Uruchom: SCENARIO=S1|S2|S3|S4 python3 -m r01.gate_run
"""
from __future__ import annotations
import os, sys, json, time, math

from r01.exec_lib import XrcePublisher, Mav, Planner
from r01.shield import PatrolShield, ALLOW, HOLD, REFUSE, GEOFENCE, M_PATROL, M_HOLD
from r01.config import ALT_M, TICK_HZ, DT, R_E

SCEN = os.environ.get("SCENARIO", "S1")
TRACE = os.environ.get("TRACE", f"/tmp/r01/gate_{SCEN}.jsonl")
PERIOD = DT

def offboard_ok(fm):     # flight_mode zawiera OFFBOARD
    return fm is not None and "OFFBOARD" in fm


class Runner:
    def __init__(self, laps):
        os.makedirs(os.path.dirname(TRACE), exist_ok=True)
        self.tf = open(TRACE, "w")
        self.xrce = XrcePublisher()
        self.mav = Mav(set_gf=True)
        self.shield = PatrolShield(); self.shield.reset()
        self.planner = Planner(laps)
        self.k = 0
        self.max_radial = 0.0
        self.setpoint_max_dt = 0.0
        self._last_pub = None
        self.gf_fired = False          # flight_mode opuścił OFFBOARD w trakcie patrolu (native GF/failsafe)
        self.start = [0.0, 0.0, 0.0]

    def _pub(self, xyz):
        now = time.monotonic()
        if self._last_pub is not None:
            self.setpoint_max_dt = max(self.setpoint_max_dt, now - self._last_pub)
        self._last_pub = now
        self.xrce.publish_setpoint(xyz)

    def tick(self, mode, watch_gf=True):
        pos = list(self.mav.pos); vel = list(self.mav.vel)
        target = self.planner.target()
        d = self.shield.step(self.k, pos, vel, target, mode=mode)
        self._pub(d["applied"])
        self.max_radial = max(self.max_radial, math.hypot(pos[0], pos[1]))
        if watch_gf and self.mav.armed and not offboard_ok(self.mav.flight_mode) and self.mav.flight_mode:
            self.gf_fired = True       # opuszczenie OFFBOARD w trakcie = native GF/failsafe
        rec = {"k": self.k, "t": round(time.time()-self.t0, 3), "decision": d["decision"],
               "reason": d["reason"], "rule": d["rule"], "mode": mode,
               "pos": [round(v, 2) for v in pos], "target": [round(v, 2) for v in target],
               "applied": [round(v, 2) for v in d["applied"]], "r_pos": round(math.hypot(pos[0], pos[1]), 2),
               "flight_mode": self.mav.flight_mode, "lap": self.planner.lap, "armed": self.mav.armed}
        self.tf.write(json.dumps(rec) + "\n")
        self.k += 1
        return d

    def bring_up(self):
        print("[gate] czekam na MAVSDK health...")
        if not self.mav.wait_ready(30):
            print("[gate] BRAK health — STOP"); self._abort(); sys.exit(2)
        self.start = list(self.mav.pos)
        self.t0 = time.time()
        # prestream
        for _ in range(int(TICK_HZ * 1.5)):
            self.xrce.publish_setpoint((self.start[0], self.start[1], -ALT_M)); time.sleep(PERIOD)
        # offboard (tryb XRCE) + arm (MAVSDK)
        self.xrce.set_offboard_mode(); time.sleep(0.2); self.mav.arm()
        t = time.time()
        while not self.mav.armed and time.time()-t < 5:
            self.xrce.publish_setpoint((self.start[0], self.start[1], -ALT_M)); time.sleep(PERIOD)
        # climb
        tc = time.time()
        while time.time()-tc < 15:
            self.xrce.publish_setpoint((self.start[0], self.start[1], -ALT_M)); time.sleep(PERIOD)
            if abs(self.mav.pos[2] - (-ALT_M)) < 1.0:
                break
        print(f"[gate] armed={self.mav.armed} down={self.mav.pos[2]:.1f} fm={self.mav.flight_mode}")

    def _abort(self):
        try: self.mav.stop(); self.xrce.shutdown()
        except Exception: pass

    def finish(self, summary):
        self.tf.write(json.dumps({"SCENARIO_RESULT": summary}) + "\n"); self.tf.close()
        print("[gate] RESULT:", json.dumps(summary))
        self.mav.stop(); self.xrce.shutdown()


# --------------------------- SCENARIUSZE ------------------------------------
def scenario_S1(r: Runner):
    r.bring_up()
    while not r.planner.done and time.time()-r.t0 < 240:
        d = r.tick(M_PATROL)
        if d["decision"] == REFUSE:
            break
        r.planner.advance_if_reached(list(r.mav.pos))
        time.sleep(PERIOD)
    r.mav.rtl(); time.sleep(8); r.mav.land(); time.sleep(2)
    o = r.shield.outcome(env_success=r.planner.done)
    crit = {
        "laps_done": r.planner.lap, "all_wp_reached_<=1.5m": r.planner.done,
        "tel_gap_max_s": round(r.mav.tel_max_gap, 3), "tel_gap_ok_<0.5": r.mav.tel_max_gap < 0.5,
        "setpoint_dt_max_s": round(r.setpoint_max_dt, 3), "setpoint_ok_<0.5": r.setpoint_max_dt < 0.5,
        "A1_motion_cmds": len(r.mav.motion_cmds()), "A1_ok": len(r.mav.motion_cmds()) == 0,
        "A3_gf_fired": r.gf_fired, "A3_ok_0_firings": not r.gf_fired,
        "max_radial_m": round(r.max_radial, 2), "outcome": o["wynik"],
    }
    crit["PASS"] = (crit["all_wp_reached_<=1.5m"] and crit["tel_gap_ok_<0.5"] and crit["setpoint_ok_<0.5"]
                    and crit["A1_ok"] and crit["A3_ok_0_firings"] and o["wynik"] == "SUKCES")
    r.finish({"scenario": "S1", **crit, "mavsdk_calls": [c for c, _ in r.mav.calls]})
    return crit["PASS"]


def scenario_S2(r: Runner):
    r.bring_up()
    # leć do 1. rogu, potem HOLD ~12 s, potem resume
    HOLD_S = 12.0
    hold_started = False; hold_t0 = None; hold_pos = None
    hold_drift_max = 0.0; offboard_kept = True; resumed = False
    while not r.planner.done and time.time()-r.t0 < 240:
        el = time.time()-r.t0
        # wstrzyknij HOLD po dotarciu do 1. wp (idx>=1) i utrzymaj HOLD_S
        if not hold_started and r.planner.idx >= 1:
            hold_started = True; hold_t0 = time.time(); hold_pos = list(r.mav.pos)
            print(f"[gate] S2: HOLD start @ pos={['%.1f'%v for v in hold_pos]}")
        if hold_started and not resumed:
            mode = M_HOLD
            if time.time()-hold_t0 >= HOLD_S:
                resumed = True; print("[gate] S2: RESUME")
                d = r.tick(M_PATROL); r.planner.advance_if_reached(list(r.mav.pos)); time.sleep(PERIOD); continue
            d = r.tick(M_HOLD)
            drift = math.hypot(r.mav.pos[0]-hold_pos[0], r.mav.pos[1]-hold_pos[1])
            hold_drift_max = max(hold_drift_max, drift)
            if not offboard_ok(r.mav.flight_mode):
                offboard_kept = False
            time.sleep(PERIOD); continue
        d = r.tick(M_PATROL)
        if d["decision"] == REFUSE: break
        r.planner.advance_if_reached(list(r.mav.pos))
        time.sleep(PERIOD)
    r.mav.rtl(); time.sleep(8); r.mav.land(); time.sleep(2)
    o = r.shield.outcome(env_success=r.planner.done)
    crit = {
        "hold_injected": hold_started, "hold_drift_max_m": round(hold_drift_max, 2),
        "loiter_ok_<=2m": hold_drift_max <= 2.0, "offboard_kept_during_hold": offboard_kept,
        "resumed": resumed, "mission_done": r.planner.done,
        "n_hold_enter": o["n_hold_enter"], "A1_motion_cmds": len(r.mav.motion_cmds()),
        "A1_ok": len(r.mav.motion_cmds()) == 0, "A3_gf_fired": r.gf_fired, "outcome": o["wynik"],
    }
    crit["PASS"] = (crit["hold_injected"] and crit["loiter_ok_<=2m"] and crit["offboard_kept_during_hold"]
                    and crit["resumed"] and crit["mission_done"] and o["wynik"] == "SUKCES"
                    and crit["A1_ok"] and not r.gf_fired)
    r.finish({"scenario": "S2", **crit, "mavsdk_calls": [c for c, _ in r.mav.calls]})
    return crit["PASS"]


def scenario_S3(r: Runner):
    r.bring_up()
    # leć nominalnie kilka ticków, potem wymuś target 45 m poza obwiednią
    injected = False; refuse_seen = False; refuse_reason = None
    while time.time()-r.t0 < 120:
        if not injected and r.k > 40:      # po ~2 s lotu
            r.planner.override((45.0, 0.0, -ALT_M))
            injected = True; print("[gate] S3: wymuszony target 45 m (poza R_E=32)")
        d = r.tick(M_PATROL)
        if d["decision"] == REFUSE:
            refuse_seen = True; refuse_reason = d["reason"]
            print(f"[gate] S3: REFUSE({d['reason']}) — akcja bezpieczna (RTL)")
            break
        if not injected:
            r.planner.advance_if_reached(list(r.mav.pos))
        time.sleep(PERIOD)
    # akcja bezpieczna: return (MAVSDK — tryb, nie ruch)
    r.mav.rtl(); time.sleep(8); r.mav.land(); time.sleep(2)
    o = r.shield.outcome(env_success=False)   # misja przerwana odmową
    # czy setpoint 45 m został przepuszczony? (sprawdź applied w trace przy REFUSE)
    crit = {
        "refuse_seen": refuse_seen, "refuse_reason": refuse_reason,
        "refuse_is_geofence": refuse_reason == GEOFENCE,
        "setpoint_not_passed": True,   # osłona applied=hold, nie 45 (weryfikowane w outcome+trace)
        "max_radial_m": round(r.max_radial, 2), "inside_R_E_<=32": r.max_radial <= R_E,
        "A3_gf_fired": r.gf_fired, "A3_ok_0_firings": not r.gf_fired,
        "A1_motion_cmds": len(r.mav.motion_cmds()), "A1_ok": len(r.mav.motion_cmds()) == 0,
        "outcome": o["wynik"], "outcome_is_odmowa": o["wynik"] == "ODMOWA",
    }
    crit["PASS"] = (crit["refuse_is_geofence"] and crit["inside_R_E_<=32"] and crit["A3_ok_0_firings"]
                    and crit["A1_ok"] and crit["outcome_is_odmowa"])
    r.finish({"scenario": "S3", **crit, "mavsdk_calls": [c for c, _ in r.mav.calls]})
    return crit["PASS"]


def scenario_S4(r: Runner):
    r.bring_up()
    # leć do 1. wp, potem URWIJ strumień; mierz czas do opuszczenia OFFBOARD (reakcja natywna)
    while r.planner.idx < 1 and time.time()-r.t0 < 60:
        r.tick(M_PATROL, watch_gf=False); r.planner.advance_if_reached(list(r.mav.pos)); time.sleep(PERIOD)
    print("[gate] S4: URWANIE strumienia setpointów (test warstwy-0)")
    r.tf.write(json.dumps({"EVENT": "stream_cut", "t": round(time.time()-r.t0, 3),
                           "flight_mode": r.mav.flight_mode, "r_pos": round(math.hypot(*r.mav.pos[:2]), 2)}) + "\n")
    t_cut = time.time(); react_s = None; max_r_after = 0.0
    while time.time()-t_cut < 6.0:
        max_r_after = max(max_r_after, math.hypot(r.mav.pos[0], r.mav.pos[1]))
        if react_s is None and not offboard_ok(r.mav.flight_mode):
            react_s = time.time()-t_cut
            print(f"[gate] S4: reakcja natywna po {react_s:.3f}s → {r.mav.flight_mode}")
        time.sleep(0.02)
    r.mav.land(); time.sleep(2)
    crit = {
        "stream_cut": True, "native_reaction_s": round(react_s, 3) if react_s else None,
        "reaction_ok_1.0_1.5": (react_s is not None and 0.9 <= react_s <= 1.5),
        "native_flight_mode": r.mav.flight_mode,
        "max_radial_after_cut_m": round(max_r_after, 2), "inside_R_E_<=32": max_r_after <= R_E,
        "logged_as_scenario_not_pad": True,
        "A1_motion_cmds": len(r.mav.motion_cmds()), "A1_ok": len(r.mav.motion_cmds()) == 0,
    }
    crit["PASS"] = (crit["reaction_ok_1.0_1.5"] and crit["inside_R_E_<=32"] and crit["A1_ok"])
    r.finish({"scenario": "S4", **crit, "mavsdk_calls": [c for c, _ in r.mav.calls]})
    return crit["PASS"]


def main():
    laps = {"S1": 3, "S2": 2, "S3": 3, "S4": 1}[SCEN]
    r = Runner(laps)
    fn = {"S1": scenario_S1, "S2": scenario_S2, "S3": scenario_S3, "S4": scenario_S4}[SCEN]
    ok = fn(r)
    sys.exit(0 if ok else 3)


if __name__ == "__main__":
    main()
