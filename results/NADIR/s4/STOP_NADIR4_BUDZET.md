# STOP-NADIR4-BUDZET — pierwszy boot S4 (nom_b1) przerwany bramką tempa 0.9281 < 0.93; zero rezerwy etapu ⇒ STOP przed lotem

Wykonawca · 9.11.2026 · łańcuch NADIR, PROMPT_NADIR_S4.

Bramka §0:
- origin = HEAD = `6e12bb82`, porcelain czysty poza nazwanymi `??` (DEMO_C).
- Budowa S4 `055c4a6d` (prerejestracja przed pierwszym bootem). Dry-run §0.1 PASS pod `set -uo pipefail` (`dryrun/dryrun_s4.json`).

## Co zaszło

- **Kolejka** (`nadir_s4_campaign.py`) ruszyła o 17:26 przy uptime WSL 9399 s (≈ 2.6 h, czyli nie zaraz po restarcie). Próbnik zegara 0 skoków, sieroty 0, PIN i profil OK, faza OK, sonda 14.71 Hz PASS.
- **Driver przed połączeniem z PX4:** bramka tempa settle Δsim/Δwall = **0.9281** (okno 59.9 s, n = 727, próg 0.93) ⇒ kod 9, boot przerwany przed uzbrojeniem. 0 lotów, 0 epizodów, breach 0, REFUSE 0.
- **Profil tempa w settle** (`nom_b1/rtf_stream.jsonl`, okna ~7 s): 0.95 → 0.94 → 0.92–0.93 pod koniec. To ten sam obraz co dwa przerwania w S2 (0.910 / 0.925).
- **Liczenie wg §1:** przerwanie bramką tempa to boot zużyty (wzór 4e). Budżet S4 wynosi 1/16, noga 12/30.
- **Zero rezerwy etapu**, a 16 pozycji siatki nie mieści się w 15 pozostałych bootach. Kolejka stanęła więc literą STOP-NADIR4-BUDZET, bez dalszych prób.

## Do decyzji Olgi

1. **Remedium operatora (wzór 4e):** restart WSL (`wsl --shutdown`), tryb zasilania „wydajny”.
2. **Rezerwa z luzu nogi:** pozostało 18 bootów (30 − 12), siatka zużyje 16, więc luz to 2 booty. Prompt mówi o 3, ale jeden zjadło to przerwanie. Kolejka liczy pozycje z dysku (`kampania_ksiega.jsonl`: siatka minus booty ważne), więc wznowienie to to samo polecenie po podniesieniu `BUDZET` w skrypcie. Wolny pierwszy boot po restarcie oznacza STOP-NADIR4-STANOWISKO.

## Pliki

- `nom_b1/` (`kont_tempo.json`, `rtf_stream.jsonl`, logi)
- `kampania_ksiega.jsonl`, `kampania_s4.json`, `kampania_s4.log`, `nadir_s4_monitor.log`, `zegar_przed_nom_b1.jsonl`, `shm_nom_b1.txt`

Sygnał: **STOP-NADIR4-BUDZET**. Push = Olga.
