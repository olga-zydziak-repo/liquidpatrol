#!/usr/bin/env python3
"""r01/brake_test.py — S3-1: pomiar a_brake (hamowanie w ruchu przy granicy) + walidacja A2.

Lot na v_max wzdłuż +x, override targetu za granicę → osłona REFUSE(GEOFENCE) w PĘDZIE →
hold-setpoint → dron hamuje. Mierzy: v w chwili REFUSE, droga zatrzymania, min/peak deceleracja.
a_brake = v_refuse²/(2·d_stop). Walidacja A2: R_route + v_max·t_react + v_max²/(2·a_brake) ≤ R_E.
Uruchom: python3 -m r01.brake_test   (stack gz_x500 żywy)
"""
from __future__ import annotations
import os, sys, json, time, math

from r01.exec_lib import XrcePublisher, Mav
from r01.shield import PatrolShield, REFUSE, M_PATROL
from r01.config import ALT_M, TICK_HZ, DT, R_E, R_ROUTE, V_MAX, T_REACT_S

TRACE = "/tmp/r01/brake_test.jsonl"
TRIGGER_X = 14.0      # przy pos_x ≥ 14 (cruise v_max, daleko od R_E) wymuś REFUSE
STOP_V = 0.15


def main():
    os.makedirs(os.path.dirname(TRACE), exist_ok=True)
    tf = open(TRACE, "w")
    xrce = XrcePublisher(); mav = Mav(set_gf=True)
    shield = PatrolShield(); shield.reset()
    if not mav.wait_ready(30):
        print("[brake] BRAK health"); sys.exit(2)
    start = list(mav.pos); period = DT
    # prestream + offboard + arm + climb
    for _ in range(int(TICK_HZ*1.5)):
        xrce.publish_setpoint((start[0], start[1], -ALT_M)); time.sleep(period)
    xrce.set_offboard_mode(); time.sleep(0.2); mav.arm()
    t = time.time()
    while not mav.armed and time.time()-t < 5:
        xrce.publish_setpoint((start[0], start[1], -ALT_M)); time.sleep(period)
    tc = time.time()
    while time.time()-tc < 15:
        xrce.publish_setpoint((start[0], start[1], -ALT_M)); time.sleep(period)
        if abs(mav.pos[2]-(-ALT_M)) < 1.0: break
    print(f"[brake] armed={mav.armed} down={mav.pos[2]:.1f}")

    # faza rozpędzania: cel (30,0,-10) w obwiedni; leć aż pos_x≥TRIGGER
    accel_target = (30.0, 0.0, -ALT_M)
    k = 0; refuse_done = False; v_refuse = None; pos_refuse = None
    t0 = time.time(); brake_samples = []; peak_decel = 0.0; last_v = None; max_radial = 0.0
    stop_dist = None; t_refuse = None
    while time.time()-t0 < 40:
        pos = list(mav.pos); vel = list(mav.vel)
        vh = math.hypot(vel[0], vel[1])
        max_radial = max(max_radial, math.hypot(pos[0], pos[1]))
        if not refuse_done:
            target = accel_target
            if pos[0] >= TRIGGER_X:
                target = (50.0, 0.0, -ALT_M)      # za granicą → wymuś REFUSE w pędzie
        else:
            target = (pos[0], pos[1], -ALT_M)      # nieistotne (terminal → hold)
        d = shield.step(k, pos, vel, target, mode=M_PATROL)
        xrce.publish_setpoint(d["applied"])
        if d["decision"] == REFUSE and not refuse_done:
            refuse_done = True; v_refuse = vh; pos_refuse = pos[:]; t_refuse = time.time()
            print(f"[brake] REFUSE w pedzie: v={vh:.2f} m/s pos_x={pos[0]:.2f}")
        if refuse_done:
            if last_v is not None:
                decel = (last_v - vh) / period
                peak_decel = max(peak_decel, decel)
            brake_samples.append({"t": round(time.time()-t_refuse, 3), "v": round(vh, 3),
                                  "x": round(pos[0], 2), "r": round(math.hypot(pos[0], pos[1]), 2)})
            if vh < STOP_V:
                stop_dist = math.hypot(pos[0]-pos_refuse[0], pos[1]-pos_refuse[1])
                print(f"[brake] zatrzymany: d_stop={stop_dist:.2f} m")
                break
        last_v = vh; k += 1; time.sleep(period)
    mav.land(); time.sleep(2)

    a_brake = (v_refuse**2)/(2*stop_dist) if (v_refuse and stop_dist and stop_dist > 0.01) else None
    # walidacja A2 z parametrami PRE + zmierzonym a_brake
    t_react = T_REACT_S
    A_min = (V_MAX**2)/(2*(R_E - R_ROUTE - V_MAX*t_react))
    delta_meas = V_MAX*t_react + (V_MAX**2)/(2*a_brake) if a_brake else None
    a2_holds = (R_ROUTE + delta_meas <= R_E) if delta_meas else None
    res = {"v_refuse_ms": round(v_refuse, 3) if v_refuse else None,
           "stop_dist_m": round(stop_dist, 3) if stop_dist else None,
           "a_brake_meas_ms2": round(a_brake, 3) if a_brake else None,
           "peak_decel_ms2": round(peak_decel, 3), "max_radial_m": round(max_radial, 2),
           "A_min_threshold_ms2": round(A_min, 3), "a_brake_ge_A_min": (a_brake >= A_min) if a_brake else None,
           "a_brake_ge_2.0": (a_brake >= 2.0) if a_brake else None,
           "delta_margin_meas_m": round(delta_meas, 3) if delta_meas else None,
           "A2_containment_holds_R_E32": a2_holds, "R_route": round(R_ROUTE, 3), "R_E": R_E,
           "t_react_s": t_react, "brake_curve": brake_samples}
    tf.write(json.dumps({"BRAKE_RESULT": res}) + "\n"); tf.close()
    print("[brake] RESULT:", json.dumps({k: v for k, v in res.items() if k != "brake_curve"}))
    mav.stop(); xrce.shutdown()


if __name__ == "__main__":
    main()
