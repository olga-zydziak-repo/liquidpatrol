# RAPORT_R0 — SZKIC (w toku, domknięcie w sesji 2)

Status: **NIEKOMPLETNY** — stack postawiony i hello-mission 3× PASS (sesja 1, 2026-08-05); bramka domykana w sesji 2 (A1/§3.2/A2/A4-RTF/3× niezależny boot). Kolejność: `SESJA2_START.md`.

## Co postawione (sesja 1)
- Gazebo Harmonic 8.14.0, ROS2 Jazzy + `ros_gz`, PX4 v1.16.2 SITL (build OK), MAVSDK-Python.
- A3 render GPU: `GL_RENDERER=D3D12 (RTX 5070 Ti)`, GL 4.6 (standalone) — `results/R0/render_fingerprint.md`.
- hello-mission 3× PASS (headless): `results/R0/hello_mission_runs.md`.

## Wyniki bramki (uzupełnić w sesji 2)
- §3.1 (3× bez pada): częściowo — 3 misje na 1 instancji ✅; **3× niezależny boot** — DO ZROBIENIA (zaostrzenie zaakceptowane).
- §3.2 render GPU podczas misji: DO ZROBIENIA (dotąd headless).
- §3.3 telemetria z Pythona: ✅.
- A1 / A2 / A4-RTF: DO ZROBIENIA.

## Rozbieżności (rejestr — uzupełniać)
1. **Ionic → Harmonic** — zaakceptowane w PRE (LTS 2028 vs EOL Ionic 09.2026).
2. **RAM 15 GB** — build PX4 z `-j6` (nie `-j24`), by nie OOM-ować. Zadziałało.
3. **Render GPU nie domyślny** — wymaga `env_gpu.sh` (D3D12); domyślnie llvmpipe.
4. **apt IPv6 w WSL** — pada; wymuszony `ForceIPv4`.
5. **Push przed etapem B — NIEZREALIZOWANY.** Warunek wejścia w B (PRE §„Warunki wejścia") wymagał push do remote przed budową. Wykonanie push nieinteraktywne było niemożliwe (brak poświadczeń GitHub po stronie asystenta; skan magazynu poświadczeń słusznie zablokowany). **Konsekwencja:** znacznik zewnętrzny (push) jest **post-hoc**, nie pre-B. **Mitygacja dowodowa:** kolejność PRE → build jest udowodniona **łańcuchem commitów** w repo — `a720cd6` (PRE, „STOP na ratyfikację") → `22d997f` (RATYFIKOWANE + aneksy) **poprzedzają** commity budowy `aa9c6cc`/`a910845`/`a55e751`; historia git (rodzic→dziecko, monotoniczne czasy) świadczy o porządku niezależnie od momentu push. Push wykonywany przez użytkownika po sesji. **Ocena:** rozbieżność proceduralna bez wpływu na integralność porządku PRE→B; odnotowana jawnie.

## Stabilność / ryzyko GPU
- Główne ryzyko (exit-144 / `dxg ioctl -22`) w renderze gz: **nie wystąpiło** (gz 35 s render, exit=timeout). `exit 144` obserwowany w sesji 1 = propagacja sygnału przy ubijaniu PX4 z tła, **bez** wpisu dxg w dmesg → nie pad (patrz zaostrzona A5, PRE §4). Realny stress GPU: A2 (soak 15 min z kamerą) — sesja 2.

## Fingerprint środowiska
- `results/R0/render_fingerprint.md` (rozszerzyć w sesji 2 o stan końcowy: Mesa/WSL/WSLg/NVIDIA).
