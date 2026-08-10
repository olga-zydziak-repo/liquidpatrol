# ZNALEZISKO — degradacja środowiska gz (SR-C4) blokuje S4/S1/S3 live

Data: 2026-08-10 (sesja PROMPT_R03A_CLOSE). **NIE jest to FAIL projektu — awaria infrastruktury.**

## Objaw
Po długiej serii bootów/killów gz (S2 z poprzedniej sesji + próby S4 tej sesji) **serwer `gz sim`
przestał startować**: żaden `/clock` nie jest publikowany → PX4 nie dostaje sensorów/GPS → health
(`is_global_position_ok ∧ is_home_position_ok`) nigdy nie przechodzi → HEALTH TIMEOUT.

## Diagnostyka (izolacja przyczyny)
- `gz sim --version` → **OK** (Gazebo Sim 8.14.0) — binarka ładuje się.
- `gz sim -s -r empty.sdf` (server-only, pusty świat) → **0 wierszy logu, 0 `/clock`**.
- `gz sim -s -v 4 empty.sdf` (max verbose) → **0 wierszy** → hang PRZED jakimkolwiek logiem (wczesna
  inicjalizacja: transport/biblioteka, nie render).
- Software render (`LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe`) → **też 0 `/clock`**.
- Wyczyszczenie IPC (`/dev/shm/gz*`, `/tmp/gz*`) → bez efektu.
- Pamięć OK (26 GiB wolne), load OK. → NIE zasoby; to zawieszenie stosu gz/graphics WSL2 po ~godzinach
  powtarzanych bootów (kontekst GPU/kompozytor WSLg lub gz-transport w złym stanie).

**Nienaprawialne w sesji** (wymaga restartu WSL2/systemu — poza moim zasięgiem).

## Wpływ na bramkę R0.3a
- **S4** (cięcie narożnik v_max): **3/3 boot-y ODRZUCONE** (HEALTH TIMEOUT; przyczyna: brak `/clock` gz).
  `results/R03/gate/S4/boot{1,2,3}/run.log`. Zero biegów zaliczonych (bieg liczony dopiero po uzbrojeniu).
- **S1, S3**: nie uruchomione (ta sama blokada gz).
- **S2** (poprzednia sesja, `results/R03/gate/S2_run.jsonl`): **LIVE PASS** — pozostaje ważne.

## Stan gotowości (do domknięcia po restarcie środowiska)
Executor `r03/gate_run_r03.py` ULEPSZONY w tej sesji i GOTOWY:
- bounded health-wait (45 s) + **hard-exit `os._exit(2/3)`** na arm/health fail (bez zawieszania cleanupu);
- **S3**: recovery `0→7` w locie + re-ALLOW po M (histereza) — pętla shield-driven przez zejście;
- **S4**: denial wyzwalany PRZY NAROŻNIKU na v_max (naprawiony bug `dist` przed definicją);
- higiena wrappera `r03/run_gate_one.sh`: artefakty w `results/R03/gate/<SCEN>/boot<N>/` (NIE /tmp),
  90 s konwergencji EKF jako PREFLIGHT, retry bootu ≤3 (bieg dopiero po uzbrojeniu), dropped-boot logowane,
  dmesg per bieg, teardown+zombie-check.
Sędzia `r03/gate_judge.py` rozszerzony: S1 (histogram flipów flagi, SR-B3), S3 (re-ALLOW po M, brak
oscylacji, skok resetu EKF/ε), S4 (r_est przy cięciu, min margines zawierania).

**Wznowienie:** po restarcie WSL2/gz uruchomić kolejno `bash r03/run_gate_one.sh S4`, `... S1 5`,
`... S3`, potem `python3 -m r03.gate_judge results/R03/gate/S4/run.jsonl ...`.

---
## ADDENDUM 2026-08-11 (sesja DIAG) — rozdzielenie dwóch awarii
Po restarcie WSL2 gz DZIAŁA (`/clock` 2 s) — awaria środowiskowa gz minęła. Ale bloker health, który
ZAINICJOWAŁ serię odrzutów S4, NIE był gz: to **zatruty `EKF2_GPS_CTRL=0` utrwalony w rootfs/parameters.bson**
(px4.log S4/boot1 z 08-10 pokazuje ZDROWY sim: `tone_alarm home set`, `partner IP` — nie „0 /clock").
Pełna diagnoza + naprawa uprzęży: `results/R03/recon/DIAG/FINDING_health_blocker.md`. SR-C4 spięło dwie
różne przyczyny; addendum je rozdziela. Bramka jest odblokowana po naprawie preflight-sanitize.
