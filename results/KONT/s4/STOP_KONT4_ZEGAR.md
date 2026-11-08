# STOP-KONT4-ZEGAR — kolejka e (ANEKS_KONT-4e) zatrzymana przed pierwszym bootem; alarm fałszywy, wada wykonawcy

8.11.2026 · po ANEKS-4e `b73049f3` (sha 54dd7aa5 PASS, ratyfikowane: S4 ≤ 21) · **0 bootów zużytych: S4 5/21, noga 29/45**

## Co się stało

- 02:07 świeża sesja WSL po `wsl --shutdown` (remedium 4e §CO(1)); 02:10:44 start `kont_s4_campaign_e.py` (uptime 210 s),
  `systemd-timesyncd` zatrzymany; 02:11:44 próbnik zegara przed `nom_b2_r2`: 2 skoki, ok=False ⇒ STOP-KONT4-ZEGAR;
  boot nie ruszył, timesyncd przywrócony w `finally`.
- Skoki (`skan2_zegar.py --check zegar_przed_nom_b2_r2.jsonl`): 15.41 s i 13598.83 s, 530 próbek, okno mono −8004.7 s.

## Mechanizm (zmierzony)

- `skan2_zegar.py` DOPISUJE do pliku (`open(path, "a")`, l. 43). `wolna_nazwa` sprawdza tylko katalog bootu, więc
  kolejka e ponownie użyła nazwy `nom_b2_r2`, której próbnik z przerwanego podejścia 4d (290 próbek, poprzedni boot VM)
  był zacommitowany w `997782fc`. Sprawdzenie liczyło 290 starych + 240 nowych próbek.
- 13598.83 s = granica dwóch bootów VM (inny CLOCK_MONOTONIC), nie skok zegara. 15.41 s leży w całości w starych
  próbkach 4d (stara sesja; `git show 997782fc:…` → 1 skok 15.41 s).
- **Same nowe próbki** (ostatnie 240, `zegar_przed_nom_b2_r2_e_tylko_nowe.jsonl`): okno 59.88 s, **0 skoków, dryf 0.0 s**.
  Stanowisko zegarowo czyste; alarm wynika wyłącznie z kolizji nazwy.

## Wada wykonawcy

Przy pisaniu kolejki e zauważyłam, że pliki `zegar_przed_nom_b2_r2.jsonl` i `shm_nom_b2_r2.txt` istnieją, i zapisałam w
commicie, że zostaną „nadpisane” — bez sprawdzenia trybu zapisu próbnika. Był to dopis, nie nadpis.

## Do decyzji (przed jakąkolwiek edycją i ponownym startem)

Proponowana poprawka (0 bootów): kolejka e omija nazwy, dla których istnieje jakikolwiek plik `*_<nazwa>.*` w s4
(albo: pliki 4d przenieść `git mv` na `*_nom_b2_r2_4d.*`), wyjście `kampania_s4e2.json`; ponowny start w tej samej świeżej
sesji (uptime obecnie < 10 min). Zasada 4e §1.2 (wolny 1. boot po restarcie ⇒ STOP) bez zmian — pierwszy boot nie odbył się.
