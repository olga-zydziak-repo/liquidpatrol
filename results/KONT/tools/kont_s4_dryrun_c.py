#!/usr/bin/env python3
"""results/KONT/tools/kont_s4_dryrun_c.py — próba na sucho mitygacji ANEKS_KONT-4c §3 (bez bootu). Uzupełnia kont_s4_dryrun.py
(4b, kończy się na connect): prowadzi main() drivera przez preflight KONT, wymuszony reinit EKF2 (atrapa do_reinit/sample
watchdoga), R-2, health, KontShield, selfcheck, meta i ostateczną asercję yaw/bias aż do uzbrojenia (arm_retry = znacznik
końca). Atrapy: MAVSDK System (connect, connection_state, param get/set, telemetry.health), GzNode (pompa zegara 10× i poza
GT drona), EkfSub (heading zadany), rclpy. intruder_motion wyłączony flagą modułu i sprawdzany: nie startuje przed asercją.

Scenariusze (argv[2]): „zdrowy" — po reinicie błąd yaw 6.4°, bias 0.0002 ⇒ 1 reinit, asercja ok, dojście do arm_retry;
„zly" — błąd 51.6° po każdym reinicie ⇒ 2 reinity, kod wyjścia 7, kont_yaw.json ok=false, intruder_motion nie wystartował.
Użycie: kont_s4_dryrun_c.py <katalog wyjścia> <zdrowy|zly>. Wyjście: dryrun_c_<scenariusz>.json (scenariusz „zly" kończy
proces kodem 7 z drivera — wynik zapisuje proces nadrzędny trybem „oba")."""
import asyncio
import json
import math
import os
import subprocess
import sys
import threading
import time
import types

DRIVER = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kont_s4_flight.py"))


class DryRunStop(Exception):
    pass


def run(out, scen):
    os.makedirs(out, exist_ok=True)
    os.environ.update({"GATE_OUT": os.path.join(out, "trace.jsonl"), "BENCH_EPISODE_IDS": "0,1,2,3", "BENCH_EPISODES": "4",
                       "KONT_MODE": "1", "FEED": "V2", "NET_ARM": "ncp", "CONTROLLER": "net_skan2"})
    ns = {"__name__": "kont_s4_dryrun_c_mod", "__file__": DRIVER}
    exec(compile(open(DRIVER, encoding="utf8").read(), DRIVER, "exec"), ns)
    log = {"reinit": 0, "sample": 0, "kroki": []}
    yaw_err = {"zdrowy": 6.4, "zly": 51.6}[scen]
    st = {"sim": 100.0, "heading": math.radians(90.0 + 30.0), "params": {}}    # przed reinitem: błąd 30°

    def fake_reinit(binpath):
        log["reinit"] += 1
        st["heading"] = math.radians(90.0 + yaw_err)
        return {"rc_stop": 0, "rc_start": 0, "cmd_wall_s": 0.0, "atrapa": True}

    def fake_sample(binpath):
        log["sample"] += 1
        return {"sim": round(st["sim"], 3), "bias_absmax": 0.0002 if log["reinit"] else 0.13}

    ns["WD"].do_reinit, ns["WD"].sample = fake_reinit, fake_sample
    ns["INTRUDER_MOTION"] = False
    cbs = []

    class FakeGz:
        def subscribe(self, typ, topic, cb):
            cbs.append((topic, cb))

    def pump():
        while True:
            st["sim"] += 0.1
            sec = int(st["sim"]); nsec = int((st["sim"] - sec) * 1e9)
            stamp = types.SimpleNamespace(sec=sec, nsec=nsec)
            for topic, cb in list(cbs):
                if topic.endswith("/clock"):
                    cb(types.SimpleNamespace(sim=stamp))
                elif topic.endswith("dynamic_pose/info"):
                    p = types.SimpleNamespace(name=ns["MODEL"], position=types.SimpleNamespace(x=0.0, y=0.0, z=0.05),
                                              orientation=types.SimpleNamespace(w=1.0, x=0.0, y=0.0, z=0.0))
                    cb(types.SimpleNamespace(pose=[p], header=types.SimpleNamespace(stamp=stamp)))
            time.sleep(0.01)
    threading.Thread(target=pump, daemon=True).start()

    class FakeEkf:
        flags = None

        @property
        def m(self):
            return types.SimpleNamespace(x=0.0, y=0.0, z=-0.05, vx=0.0, vy=0.0, vz=0.0, heading=st["heading"],
                                         xy_valid=True, dead_reckoning=False)

    async def agen(v):
        yield v

    class FakeParam:
        async def set_param_int(self, k, v):
            st["params"][k] = v

        async def get_param_int(self, k):
            return st["params"].get(k, 0)

    class FakeSystem:
        def __init__(self):
            self.param = FakeParam()
            self.core = types.SimpleNamespace(connection_state=lambda: agen(types.SimpleNamespace(is_connected=True)))
            self.telemetry = types.SimpleNamespace(health=lambda: agen(types.SimpleNamespace(is_global_position_ok=True,
                                                                                               is_home_position_ok=True)))

        async def connect(self, system_address=None):
            log["kroki"].append("connect")

    async def stop_arm(d):
        log["kroki"].append("arm_retry")
        raise DryRunStop("uzbrojenie")

    ns.update(System=FakeSystem, GzNode=FakeGz, EkfSub=lambda: FakeEkf(), arm_retry=stop_arm,
              rclpy=types.SimpleNamespace(init=lambda: None, ok=lambda: True, spin_once=lambda *a, **k: time.sleep(0.01),
                                          shutdown=lambda: None))
    try:
        asyncio.run(ns["main"]())
        wynik = "main() zakończony bez uzbrojenia"
    except DryRunStop as e:
        wynik = f"zatrzymane: {e}"
    res = {"scenariusz": scen, "wynik": wynik, "reinit_wywolan": log["reinit"], "sample_wywolan": log["sample"],
           "kroki": log["kroki"], "params": st["params"],
           "kont_ekf_preflight": json.load(open(os.path.join(out, "kont_ekf_preflight.json"))),
           "kont_yaw": json.load(open(os.path.join(out, "kont_yaw.json")))}
    json.dump(res, open(os.path.join(out, f"dryrun_c_{scen}.json"), "w"), ensure_ascii=False, indent=1)
    return res


def main():
    out, scen = os.path.abspath(sys.argv[1]), sys.argv[2]
    if scen != "oba":
        run(os.path.join(out, scen), scen)
        return
    wyn = {}
    for sc in ("zdrowy", "zly"):
        r = subprocess.run([sys.executable, __file__, out, sc], capture_output=True, text=True, timeout=600)
        d = os.path.join(out, sc)
        ky = json.load(open(os.path.join(d, "kont_yaw.json"))) if os.path.exists(os.path.join(d, "kont_yaw.json")) else None
        kp = json.load(open(os.path.join(d, "kont_ekf_preflight.json"))) if os.path.exists(os.path.join(d, "kont_ekf_preflight.json")) else None
        wyn[sc] = {"rc": r.returncode, "kont_yaw": ky, "n_podejsc": len(kp["podejscia"]) if kp else None,
                   "stdout_ogon": r.stdout[-600:], "stderr_ogon": r.stderr[-600:]}
    ok_z = (wyn["zdrowy"]["rc"] == 0 and wyn["zdrowy"]["kont_yaw"]["ok"] and wyn["zdrowy"]["n_podejsc"] == 1)
    ok_n = (wyn["zly"]["rc"] == 7 and wyn["zly"]["kont_yaw"]["ok"] is False and wyn["zly"]["n_podejsc"] == 2
            and "intruder" not in wyn["zly"]["stdout_ogon"])
    wyn["PASS"] = ok_z and ok_n
    json.dump(wyn, open(os.path.join(out, "dryrun_c.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"PASS": wyn["PASS"], "zdrowy": [wyn["zdrowy"]["rc"], wyn["zdrowy"]["n_podejsc"]],
                      "zly": [wyn["zly"]["rc"], wyn["zly"]["n_podejsc"]]}, ensure_ascii=False))
    sys.exit(0 if wyn["PASS"] else 1)


if __name__ == "__main__":
    main()
