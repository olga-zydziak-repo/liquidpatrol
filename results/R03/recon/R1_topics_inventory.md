# R1 — inwentarz źródeł zdrowia pozycji (PX4 v1.16.2, żywe echo XRCE, etykieta Hz=ros2-topic-hz)

| topik (XRCE) | typ | Hz (zmierz.) | pola kluczowe | rola |
|---|---|---|---|---|
| /fmu/out/vehicle_local_position | VehicleLocalPosition | 99.99 | eph[m], epv[m], xy_valid, v_xy_valid, dead_reckoning | ε_pos(eph), age_pos(dead_reckoning) |
| /fmu/out/failsafe_flags | FailsafeFlags | 1.85 | local_position_invalid, global_position_invalid, local_position_accuracy_low, *_relaxed | mapa warstwy-0 |
| /fmu/out/vehicle_gps_position | SensorGps | ~ | fix_type(3=3D), satellites_used, jamming_state, spoofing_state | stan GPS (bonus) |
| /fmu/out/vehicle_status_v1 | VehicleStatus | ~ | nav_state, arming_state, failsafe | akcja natywna |
| /fmu/out/estimator_status_flags | EstimatorStatusFlags | ~ | cs_gnss_pos, reject_hor_pos | zdrowie fuzji |

ROZBIEŻNOŚCI: (1) estimator_status (pełny, pos_horiz_accuracy[m]) NIE publikowany przez XRCE — tylko _flags; eph z VLP to jedyny ε_pos[m]. (2) SensorGps.msg w src nie pokazał jamming/spoofing, ale ŻYWY topic ma je (fix_type,jamming_state,spoofing_state) — żywe echo autorytatywne.
