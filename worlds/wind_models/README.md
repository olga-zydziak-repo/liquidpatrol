# worlds/wind_models — nadpisania modeli dla nogi W (wiatr)

## x500_base (enable_wind)
Kopia stockowego `PX4-Autopilot/Tools/simulation/gz/models/x500_base` z JEDYNĄ zmianą:
na linku `base_link` dodane `<enable_wind>true</enable_wind>` (po `<velocity_decay/>`).
Powód: stockowy x500 nie ma `enable_wind` na żadnym linku → system gz `WindEffects` nie
przykłada siły do drona (RECON_W §R1.5). Bez tej kopii sonda wiatru jest bezczynna dla drona.

### Jak jest używana (bez edycji frozen `harness/run_boot.sh` ani stocka)
`GZ_SIM_RESOURCE_PATH` z shella idzie PIERWSZY (gz_env.sh:19 DOPISUJE), więc `model://x500_base`
rozwiązuje się do TEJ kopii. Launcher: `results/W_RECON/run_sonda_boot.sh` ustawia
`GZ_SIM_RESOURCE_PATH=.../worlds/wind_models`. Model top-level x500_mono_cam/x500 pozostają stock.

### Regeneracja binariów (meshes/materials/thumbnails NIE są w gicie — duplikat ~25 MB)
```
cp -rn ../../PX4-Autopilot/Tools/simulation/gz/models/x500_base/{meshes,materials,thumbnails,LICENSE} x500_base/
```
Trackowane w gicie: tylko `x500_base/model.sdf` (z diffem enable_wind) + `x500_base/model.config`.
`gz sdf --check` i suchy load potwierdzają rozwiązywanie `model://x500_base/meshes/...` po regeneracji.
