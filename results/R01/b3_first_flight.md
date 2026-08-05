# B3 — pierwszy lot offboard: perymetr pod osłoną — 2026-08-05

Sesja 1 budowy R0.1 (B1 rdzeń → B2 egzekutor → B3 lot). Stack: PX4 SITL v1.16.2 (`gz_x500`) + uXRCE-DDS Agent + MAVSDK, WSL2/RTX 5070 Ti. Egzekutor: `r01/patrol_exec.py`.

## Wynik: **SUKCES** — hybryda płaszczyzn potwierdzona, A1 utrzymany

| Metryka | Wynik |
|---|---|
| Uzbrojenie przez MAVSDK (heartbeat GCS) | **armed=True** — hybryda działa (recon R1: arm czysto-XRCE był blokowany) |
| Wznoszenie do wysokości patrolu | down = -9.0 m (cel -10) |
| Patrol | 1 okrążenie (4 waypointy), `planner_done=True` |
| Maks. promień od Home | **27.73 m < R_E=32 m** — bariera osłony nietknięta |
| Osłona | 977 ticków, **wszystkie ALLOW** (nominal); 0 HOLD, 0 REFUSE |
| Księgowość (`outcome`) | **SUKCES** |
| **[A1] `mavsdk_motion_cmds`** | **0** — wywołania MAVSDK: `param×3, arm, return_to_launch, land` (arm/tryby/param), **żadnej komendy ruchu**; setpointy wyłącznie XRCE |
| Higiena dmesg | CaptureCrash=0, oops=0 (0 padów) |

## Płaszczyzna (potwierdzenie §3 + A1)
- **MAVSDK:** telemetria NED (pos/vel), `arm`, `return_to_launch`, `land`, `param set` (MPC_XY_VEL_MAX=3 dla clampu v_max — spójne z barierą A2). Heartbeat MAVSDK spełnia arming-check GCS (rozwiązanie znaleziska recon R1).
- **XRCE (rclpy publisher):** `OffboardControlMode` + `TrajectorySetpoint` = jedyna ścieżka setpointów, przez osłonę. Wejście w offboard = `VehicleCommand DO_SET_MODE` (komenda TRYBU przez XRCE, nie ruch — MAVSDK offboard.start() sprzęga setpoint, więc wejście przez XRCE zachowuje A1).
- rclpy bez spin (publish nie wymaga spinowania); telemetria z MAVSDK → jedna pętla, brak wątkowania sub/pub.

## Artefakty
- `results/R01/b3_patrol_trace.jsonl` — trace per tick (977 + SUMMARY); dowód A1 (0 motion-komend MAVSDK) i przebiegu osłony.
- Kod: `r01/patrol_exec.py` (egzekutor), `r01/{shield,language,authz,memory,config}.py` (rdzeń, B1, testy 43/43).

## Zakres sesji 1 (jawnie)
- Potwierdzono: płaszczyzna hybrydowa + osłona-w-pętli + A1. Slot uczonego pilota PUSTY (planer proceduralny).
- NIE w sesji 1 (→ sesja 2/3): kamera-load w tle (A4), scenariusze bramki S1–S4, geofence natywny GF_* (A3), certy P1/P4/P5/P2-analog, clamp prędkości zmierzony (`a_brake` do P2). Lot na `gz_x500` (bez kamery) — izolacja płaszczyzny.
