# STOP-KONT4-DRIVER — pierwszy boot S4 bez lotu: błąd ścieżki ROOT w kopii drivera (wada wykonawcy), 1/16 bootów, 0 epizodów

Wykonawca · 7.11.2026 · łańcuch KONT, S4 po S3b (`9222bd36`) i S4-build (`019fc4d9`). Podstawa STOP: PROMPT_KONT_S4 §2
„cokolwiek wymaga zmiany ⇒ STOP z opisem" — poprawka wymaga edycji pliku, który już wyprodukował boot.

## Co się stało

- Kolejka (`kont_s4_campaign.py`) uruchomiła `nom_b1` (boot 25 nogi, epizody c00–c03_s01, bez cięcia). Stos wstał poprawnie:
  faza dołączenia 7.604 s (`px4_join.json`, initial absolute time 7 604 000 µs), sonda kadencji ponad podłogą, uzbrojenie
  sondy OK, settle 90 s.
- Driver `results/KONT/tools/kont_s4_flight.py` padł przy starcie `main()` (`act.log`):
  `FileNotFoundError: …/results/KONT/results/BENCH/scenario_manifest.json`.
- **Przyczyna (wada wykonawcy):** driver jest kopią `bench/bench_flight.py`, który liczy
  `ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` (`kont_s4_flight.py:31`) — dla pliku w `bench/` to
  korzeń repo, dla pliku w `results/KONT/tools/` to `results/KONT`. Moja kontrola przed bootem (pyflakes + wykonanie modułu
  bez `main()`) tego nie złapała; ścieżki zależne od ROOT czytane są dopiero w `main()`. To powtórka lekcji ANEKS_KONT-1d §2.3:
  przyrząd trzeba sprawdzić uruchomieniem samego skryptu.
- Kolejka oznaczyła boot jako nieważny i zaplanowała dolecenie; zatrzymałem ją po PID (SIGINT, blok `finally`) w trakcie
  próbnika zegara przed `c08_s01`, przed jakimkolwiek kolejnym bootem. timesyncd przywrócony (`active`), sierot brak.

## Stan

- Budżet S4: **1/16** zużyty (boot wstał, więc się liczy), noga **25/45**. Lotów: 0, epizodów: 0, cięć: 0. Twarde STOPy
  §2 nie zaszły (brak lotu). Rezerwa budżetu (16 = 12 + 3 + 1) jest tym bootem skonsumowana: zostaje 15 bootów na 12 cięć +
  3 nominały, bez miejsca na dolecenie.
- Artefakty bootu w `results/KONT/s4/nom_b1/` (bez ulogu — `.gitignore`), log kolejki `kampania_s4.log`, stan
  `kampania_s4.json`.

## Propozycja (do decyzji CC)

1. **Poprawka jednej linii w miejscu** (wzór wyjątku ANEKS_KONT-1d §2.2; plik nie wyprodukował żadnego lotu):
   `ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))`
   (identycznie jak `kont_s2_probe_y.py:26`). Inne użycia ROOT w driverze (manifest, `executor_params.json`, sha plików,
   `cwd` selfchecku i `intruder_motion`) naprawia ta sama linia.
2. **Próba na sucho bez bootu przed lotami:** uruchomienie `main()` drivera do pierwszego wywołania sieciowego z atrapą
   MAVSDK/ROS (albo asercja wszystkich ścieżek z ROOT w osobnym skrypcie), artefakt do `results/KONT/s4/dryrun/`.
3. **Budżet:** albo bez zmian (15 bootów na 15 pozycji, zero dolecenia — nieważny epizod oznacza wtedy STOP budżetu), albo
   +1 rezerwy dokumentem CC (noga 41/45 mieści się w PRE ≤ 45).

Bez rozstrzygnięcia nie edytuję drivera i nie bootuję. **STOP-KONT4-DRIVER.** Push = Olga.
