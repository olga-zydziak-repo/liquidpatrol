# STOP-NADIR4-STANOWISKO (2) — pierwszy boot po pełnym restarcie komputera przerwany bramką tempa 0.7811 ⇒ STOP; siatka nie mieści się już w nodze

Wykonawca · 10.11.2026 · łańcuch NADIR, PROMPT_NADIR_S4.

Stan wyjściowy:
- STOP-NADIR4-STANOWISKO `f8f87657` został wypchnięty.
- Sygnał Olgi 10.11: budżet S4 = 19 (cały luz nogi), restart całego komputera, tryb zasilania turbo.
- Commit `83af4bc1` (BUDZET 19).

## Przed kolejką (0 bootów)

- Uptime WSL ok. 3 min. `systemd-timesyncd` zatrzymany na sesję. Sieroty 0, origin = `f8f87657`.
- **Goły gz** (`wk4_b0_ab.sh` wariant iii, kopia z wyjściem do scratchpadu, świat `world_wk3_p2`, 120 s): tempo **0.9944**, 0 zacięć, sim 117.14 s.
- Plan na sucho: księga 4/19, ważny nom_b1, 15 pozycji w kolejce, noga 15/30.

## Boot

| boot S4 / noga | pozycja | tempo settle | wynik |
|---|---|---|---|
| 5 / 16 | c01_s01_r3 | **0.7811** | przerwany przed uzbrojeniem (kod 9). Pierwszy boot po restarcie ⇒ **STOP-NADIR4-STANOWISKO** |

Przebieg bootu:
- Strażnik stanowiska przytrzymał boot o ok. 2 min (LOADAVG 2.24 > 1.5, ślad startu systemu i kontroli gz), potem SUSTAINED CLEAN.
- Faza OK, sonda 14.71 Hz PASS, próbnik zegara 0 skoków.
- Profil tempa w oknach 10 s: 0.90 → 0.80 → 0.79 … 0.77. Spowolnienie jest równe od ok. 10 s po starcie gz, nie narasta.

## Co wiadomo o spowolnieniu (opis, mechanizm niezmierzony)

| boot | tempo settle |
|---|---|
| S2, cięcia (c02_s01, c05_s01 ×2, c08_s02, c11_s02 ×2) | 0.910–0.966 |
| S4 nom_b1 (uptime 2.6 h) | 0.928 |
| S4 nom_b1_r2 | 0.960 |
| S4 c01_s01 / c01_s01_r2 / c01_s01_r3 | **0.734 / 0.740 / 0.781** |

- **Wszystkie trzy wolne booty to ta sama pozycja c01_s01.** Sprawdziłam jednak ścieżkę do bramki i nie ma w niej nic zależnego od epizodu:
  - Bramka tempa jest pierwszą instrukcją `main()` drivera (`nadir_s4_flight.py:288`), przed manifestem i przed `set_pose` intruza.
  - `BENCH_EPISODE_IDS`, `BENCH_EPISODES` i `KONT_INJECT_T` czyta tylko driver. Launcher, harness i r03 ich nie czytają.
  - Stos przed bramką jest więc ten sam dla nominału i cięcia. Zbieżność z c01_s01 uznaję za nierozstrzygniętą, nie za mechanizm.
- **Goły gz jest zdrowy (0.994), a pełny stos wolny (0.78).** Spowolnienie dotyczy kosztu stosu (PX4, kamera, percepcja, nadir_obs), nie samego serwera gz. To ten sam obraz co STOP-NADIR1-TEMPO (kamera nadir −11% tempa).
- **Restart całego komputera i turbo nie przywróciły tempa** z wieczora 9.11 (0.96 w nom_b1_r2).

## Rachunek

- **Księga:** 5 bootów S4 zużytych, ważny 1 (nom_b1). Noga 16/30.
- **Pozostało 15 pozycji** (12 cięć i nom_b2–b4) na 14 bootów do końca nogi. **Siatki nie da się już domknąć w nodze**, nawet bez żadnego kolejnego nieważnego bootu. Dokończenie S4 wymaga budżetu ponad nogę, czyli decyzji CC.

## Do decyzji (Olga / CC)

1. **Budżet ponad nogę** (≥ 1 boot na samą siatkę, plus rezerwa) albo zamknięcie nogi z tym, co jest: S4 ma 1 ważny nominał, 0 cięć.
2. **Diagnoza stanowiska przed kolejnymi bootami.** Proponuję kontrolę bez zużycia bootu: pełny stos (gz z kamerą nadir, PX4, percepcja, nadir_obs) na 90 s bez drivera, z samym pomiarem tempa. Najpierw na pozycji nominalnej, potem na c01_s01. To rozstrzygnie, czy wolne jest stanowisko, czy pozycja. Taka kontrola nie jest bootem kampanii, ale uruchamia stos, więc jej status bootowy musi określić CC.
3. Ewentualnie odwrócić kolejność kolejki, tak by c01_s01 nie szło pierwsze. To tylko obejście; jeśli spowolnienie dotyczy stanowiska, nic nie da.

## Pliki

- `c01_s01_r3/` (`kont_tempo.json`, `rtf_stream.jsonl`, logi stosu).
- `kampania_ksiega.jsonl`, `kampania_s4.json`, `kampania_s4.log`, `nadir_s4_monitor.log`.

Sygnał: **STOP-NADIR4-STANOWISKO**. Push = Olga.
