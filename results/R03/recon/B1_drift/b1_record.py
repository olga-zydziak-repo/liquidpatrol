#!/usr/bin/env python3
"""B1 rejestrator: EKF (vehicle_local_position, etykieta nav-local) + GT (gz model -p, etykieta gt_judge)
+ dead_reckoning + eph. Δt=monotonic_local. Loguje jsonl. GT przez subprocess gz model -p ~5 Hz."""
import os, json, time, subprocess, re, threading
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from px4_msgs.msg import VehicleLocalPosition
QOS=QoSProfile(depth=1,history=HistoryPolicy.KEEP_LAST,reliability=ReliabilityPolicy.BEST_EFFORT)
OUT=os.environ.get("B1_OUT","/tmp/r03b/b1_rec.jsonl"); DUR=float(os.environ.get("B1_DUR","120"))
MODEL=os.environ.get("B1_MODEL","x500_mono_cam_0")
class Rec(Node):
    def __init__(self,f):
        super().__init__("b1_rec"); self.f=f; self._n=0
        self.create_subscription(VehicleLocalPosition,"/fmu/out/vehicle_local_position",self.vlp,QOS)
    def vlp(self,m):
        self._n+=1
        if self._n%5==0:  # ~20 Hz
            self.f.write(json.dumps({"t":"ekf","mono":round(time.monotonic(),4),"x":round(float(m.x),4),
                "y":round(float(m.y),4),"eph":round(float(m.eph),4),"dead_reckoning":bool(m.dead_reckoning),
                "xy_valid":bool(m.xy_valid)})+"\n")
def gt_poll(f,stop):
    pat=re.compile(r"\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]")
    while not stop.is_set():
        try:
            out=subprocess.run(["gz","model","-m",MODEL,"-p"],capture_output=True,text=True,timeout=3).stdout
            m=pat.search(out.split("XYZ")[1]) if "XYZ" in out else None
            if m:
                f.write(json.dumps({"t":"gt","mono":round(time.monotonic(),4),"x":float(m.group(1)),
                    "y":float(m.group(2)),"z":float(m.group(3))})+"\n"); f.flush()
        except Exception: pass
        time.sleep(0.2)
def main():
    rclpy.init()
    with open(OUT,"w") as f:
        stop=threading.Event(); th=threading.Thread(target=gt_poll,args=(f,stop),daemon=True); th.start()
        n=Rec(f); t0=time.monotonic()
        while rclpy.ok() and time.monotonic()-t0<DUR: rclpy.spin_once(n,timeout_sec=0.05)
        stop.set(); n.destroy_node()
    rclpy.shutdown(); print("B1 REC done ->",OUT)
if __name__=="__main__": main()
