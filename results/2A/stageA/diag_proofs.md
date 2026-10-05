# diag_proofs — przechwycone wyjścia diagnostyki habitatu 05.10 (etap A, zero lotów)

Zapis z sesji CC (stack po diagnozie storn, więc wyjścia nie-reprodukowalne offline; surowe logi
stacków w `diag0_stack/`, `diag1_imu/`, `diag2_gzip/`). Kontekst: 3× HEALTH TIMEOUT pre-arm
(A1_c08_s03, _r2, _r3) — px4 bez sensorów gz przy żywym gz (rtf_stream: sim idzie, RTF ~1.0).

## diag0_stack (stack ręczny, bez GZ_IP) — topiki SĄ, model SPAWNUJE
- `gz topic -l`: imu/air_pressure/magnetometer/imager — pełna lista w `diag0_stack/topics_all.txt`
- `gz model --list`: … x500_mono_cam_0, film_cam (świat kompletny)
- px4.log: 0× "Preflight Fail" — FAŁSZYWIE zdrowy (commander bez GCS nie drukuje ocen);
  UWAGA: plik 4.6 MB = 2×~23 000 powtórzeń `ERROR [vehicle_imu] 0 - accel/gyro 1310988
  timestamp error timestamp_sample: 0, previous timestamp_sample: 0` (integrator bez ani
  jednej ważnej próbki) — commitowany (git pakuje powtórzenia; sygnatura = te 2 linie)

## diag1_imu (stack ręczny, bez GZ_IP) — gz PUBLIKUJE, px4 NIE DOSTAJE
- `gz topic -e -t .../imu_sensor/imu -n 2` → dane płyną (header stamp sec:11, frame_id x500_mono_cam_0)
- `px4-listener sensor_combined` → TOPIC bez ani jednej próbki
- `px4-listener sensor_gyro` → `timestamp: 0` (urządzenie skonfigurowane, zero danych)
- `px4-ekf2 status` → `attitude: 0, local position: 0, global position: 0; EKF update: 0 events`
- `ss -tnp`: połączenia TCP px4↔gz ESTAB na 172.28.149.173 (eth0) — kanał jest, dane nie idą
- host: `docker ps` → `vks_postgres` Up ~1h (od reboota); `ip -br addr`: 16× br-* + veth UP

## diag2_gzip (stack ręczny, GZ_IP=127.0.0.1) — FIX DOWIEDZIONY
- `px4-ekf2 status` → `attitude: 1, local position: 1, global position: 1; EKF update: 1473 events`
- `px4-listener sensor_gyro` → świeże próbki (timestamp 13252000, 0.00 s ago)

Wniosek operacyjny: mitygacja środowiskowa `export GZ_IP=127.0.0.1` w driverze etapu
(`results/2A/tools/stageA_boot.sh`), dla CAŁEGO drzewa bootu; echo per boot w `.gz_ip_proof`.
Zero zmian w frozen kodzie/świecie/modelu/parametrach PX4. Kontener dockera nietknięty (infra Olgi).
Potwierdzenie w locie: A1_c08_s03_r4 armed @99.5 s, A2_c11_s01 armed @97.1 s — 2/2 po fixie
(0/3 przed), dsw 0.9907/0.9951 w paśmie LIQ.
