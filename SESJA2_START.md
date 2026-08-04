# SESJA 2 — START (domknięcie bramki R0.0)

Stan wejściowy: stack postawiony i zbudowany, hello-mission **3× PASS** (headless), A3 render GPU udowodniony standalone. Commity do `a55e751`. Szczegóły: `results/R0/hello_mission_runs.md`, `results/R0/render_fingerprint.md`.

## Kolejność prac (ZAMROŻONA — wykonywać po kolei)

1. **MicroXRCE-DDS Agent** — instalacja + uruchomienie (klient `uxrce_dds_client` jest już w firmware PX4 v1.16.2). Warunek wstępny A1.
2. **A1 — żywe ogniwa łącza:** podczas hello-mission `ros2 topic hz /fmu/out/vehicle_odometry` (lub `…/vehicle_local_position`) **≥10 Hz przez cały lot** ORAZ **≥1 topik zmostkowany gz→ROS2** (kamera lub `/clock`) o niezerowej, raportowanej częstotliwości.
3. **§3.2 — misja z renderem GPU (NIE headless):** wspólny run PX4 + Gazebo z GUI pod `env_gpu.sh` (D3D12); potwierdzić renderer podczas lotu.
4. **A2 — soak ≥15 min** z `gz_x500_mono_cam` mostkowaną do ROS2, bez pada; księgowość trójwynikowa.
5. **A4 — RTF** raportowany per bieg (sim/wall), niebramkujący.
6. **3× NIEZALEŻNY boot** (zaostrzenie zaakceptowane 2026-08-05) — trzy osobne uruchomienia stacku, nie 3 misje na jednej instancji.
7. **Fingerprint środowiska** — pin wersji: Mesa / WSL / WSLg / sterownik NVIDIA (rozszerzyć `results/R0/render_fingerprint.md` o stan z sesji 2).
8. **RAPORT_R0.md** — domknięcie: co postawione, wyniki bramki (A1/A2/§3.2/§3.1/A4), stabilność, rozbieżności (w tym push-before-B — patrz szkic `RAPORT_R0.md`).

## Uwagi operacyjne (zmierzone w sesji 1)
- apt IPv6 pada w WSL → `ForceIPv4` już ustawione (`/etc/apt/apt.conf.d/99force-ipv4`).
- `PX4_GZ_STANDALONE=0` WŁĄCZA standalone (sprawdzane jako niepuste) — nie ustawiać wcale.
- Ubijanie PX4 startowanego z tła → exit 144 w subshellu (propagacja grupy procesów), **nie** pad GPU (patrz zaostrzona A5 w PRE_R0 §4).
- `make px4_sitl` zalewa log promptem `pxh>` — stan czytać przez MAVSDK, nie z logu.
- Reguła stopu §4 + A5 obowiązują bez zmian.
