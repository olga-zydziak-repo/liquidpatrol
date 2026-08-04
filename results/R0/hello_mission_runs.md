# HELLO-MISSION — wyniki (R0.0 §1/§3.1/A4)

Data: 2026-08-05. Stack: PX4 SITL **v1.16.2** + Gazebo **Harmonic 8.14.0** + MAVSDK-Python, headless (server), WSL2/RTX 5070 Ti.
Skrypt: `run_hello_mission.py` (arm → misja: 4 waypointy ~20 m @ 5 m → RTL/land → disarm; monitor przerw pozycji A4).

| Run | Waypointy | Land+Disarm | Czas (wall) | Max przerwa poz. (A4) | Wynik |
|----:|:---------:|:-----------:|:-----------:|:---------------------:|:-----:|
| #1  | 4/4       | ✅           | 42.9 s      | 0.02 s (≤1 s ✓)        | **PASS** |
| #2  | 4/4       | ✅           | 42.9 s      | 0.02 s (≤1 s ✓)        | **PASS** |
| #3  | 4/4       | ✅           | 42.9 s      | 0.02 s (≤1 s ✓)        | **PASS** |

**§3.1 (3× z rzędu bez pada):** ✅ 3/3 na jednej instancji SITL, brak crasha PX4/Gazebo.
**§3.3 (telemetria offboard z Pythona):** ✅ MAVSDK health armable=True, strumień pozycji ciągły.
**A4 (misja domknięta + brak przerwy >1 s):** ✅ każdy run: wszystkie itemy + RTL land + disarm; max gap 0.02 s.
(Czasy identyczne bo SITL lockstep = deterministyczny.)

## Pozostaje do pełnej bramki (następna sesja):
- **§3.2 render GPU PODCZAS misji** — dotąd headless (bez renderu); potrzebny wspólny run PX4+gz z GUI/D3D12. Render sam w sobie udowodniony osobno (A3, `results/R0/render_fingerprint.md`).
- **A1** — `ros2 topic hz /fmu/out/vehicle_odometry` ≥10 Hz + ≥1 topik gz→ROS2; wymaga **MicroXRCE-DDS Agent** + `ros_gz_bridge` uruchomionych.
- **A2** — soak ≥15 min z `gz_x500_mono_cam` mostkowaną do ROS2, bez pada.
- **A4 RTF** — dołożyć raportowany współczynnik real-time (sim/wall), niebramkujący.
- Powtarzalność bootów: 3× niezależny launch (nie tylko 3 misje na 1 instancji).
