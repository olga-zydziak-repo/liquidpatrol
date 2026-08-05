# A1 — żywe ogniwa łącza podczas hello-mission (bramka §3 pkt 5)

Data: 2026-08-05. Stack: PX4 SITL v1.16.2 + Gazebo Harmonic + MicroXRCE-DDS-Agent v2.4.3 + ros_gz_bridge, ROS2 Jazzy + px4_msgs (release/1.16).

## Wynik: **PASS** — oba ogniwa żywe przez cały lot (pomiar 60 s obejmujący pełną misję)

| Ogniwo | Temat | Most | avg | min/s | Próg | Werdykt |
|---|---|---|---:|---:|---|:---:|
| PX4 → ROS2 | `/fmu/out/vehicle_odometry` (`px4_msgs/VehicleOdometry`) | **uXRCE-DDS** | 99.9 Hz | 97 Hz | ≥10 Hz przez cały lot | **PASS** |
| gz → ROS2 | `/clock` (`rosgraph_msgs/Clock`) | **ros_gz_bridge** | 249.7 Hz | 243 Hz | niezerowe+raportowane | **PASS** |

Dowodzi jednoczesnego działania **uXRCE-DDS** (PX4↔ROS2) *oraz* **ros_gz_bridge** (Gazebo→ROS2) — nie tylko PX4↔Gazebo.

## Odstępstwo odnotowane jawnie (metoda pomiaru)
Literalne `ros2 topic hz /fmu/out/vehicle_odometry` **nie działa** w ROS2 Jazzy dla tematów PX4: `ros2 topic hz` nie ma opcji QoS (`--help`: tylko `--window/--filter/--wall-time/--spin-time/-s`) → subskrybuje domyślnie RELIABLE, a publishery PX4 `/fmu/out` są **BEST_EFFORT** → niezgodność QoS → zero odbieranych wiadomości. Pomiar wykonano poprawnym, bardziej rygorystycznym narzędziem: `a1_topic_rate.py` (subskrybent rclpy z jawnym QoS best_effort, binowanie per-sekunda → avg + **min/s**, dowód „≥10 Hz przez cały lot", nie tylko średnia). To zaostrzenie, nie złagodzenie kryterium.

## Warunki wstępne (ustanowione w sesji 2)
- MicroXRCE-DDS-Agent v2.4.3 (`install_microxrce.sh`), start: `MicroXRCEAgent udp4 -p 8888`.
- `px4_msgs` release/1.16 zbudowany w `ros2_ws` (colcon) — **wymagane `-DPython3_EXECUTABLE=/usr/bin/python3`**, bo CMake łapał z PATH `~/.local/bin/python3.12` (uv standalone) bez systemowego `em` → build interfejsów padał na `ModuleNotFoundError: No module named 'em'`.
- Most gz→ROS2: `ros2 run ros_gz_bridge parameter_bridge "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"`.
- Artefakty pomiaru: `/tmp/a1_odom.log`, `/tmp/a1_clock.log`; miernik: `a1_topic_rate.py`.
