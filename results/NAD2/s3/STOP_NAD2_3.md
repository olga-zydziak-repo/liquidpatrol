# STOP-NAD2-3 — bramka NADIR-II: PASS — B1–B5 0 naruszeń w 28 epizodach, D1 12/12 cięć dostępnych

12.11.2026 · wykonawca · PROMPT_NAD2_S3 (sha256 c7e294a8 PASS).
- **Bramka §0:** origin = HEAD = `bd975df5`, porcelain czysty poza zastanymi ?? `results/DEMO_C`, dry-run kolejki PASS 4/4 (`dryrun/dryrun_s3.json`).
- **Budowa:** `9720bae0`.
- **Poprawki kolejki w toku:** `6b008eb7` po STOP-NAD2-3-GUARD (`55333eaa`, decyzja Olgi), `e6670f52` (bramka zdrowia w procesie potomnym).
- **Kod lotu, osłona, litera, tabela, driver, launcher i analizator:** jak w `bd975df5` — diff 0.

**Budżet S3: 16/19** (rezerwa 3 nieużyta). Noga NADIR-II: 18/≤22. **Breach 0, REFUSE(POS) fałszywy 0, STOP globalny żaden.**

## Werdykt (mechanicznie, `wyniki_s3.json` → `werdykt`)

| kryterium | epizody z naruszeniem | ocenione |
|---|---|---|
| **(B1)** e_corr ≤ U przedziału osłony | **0** | 12 cięć (ticki z przedziałem) + 16 nominałów |
| **(B2)** margines do R_E > 0 (GT) | **0** | 28 |
| **(B3)** r_est = \|p_corr\| w tickach KONT | **0** | 12 cięć |
| **(B4)** offboard, 0 failsafe, 0 fałszywych REFUSE(POS), REFUSE zgodne z regułą i zakończone zejściem | **0** | 28 |
| **(B5)** nominały: 0 fałszywych wejść, 0 REFUSE | **0** | 16 |
| **(D1)** cięcie dostępne | **12 z 12** (próg ≥ 10), niedostępnych: brak | 12 |

**Litera bezpieczeństwa PASS, litera dostępności PASS ⇒ bramka nogi PASS.**

Sprawdziany przyrządu per boot: (s1), (s2), (s3) = 100% w 16/16 bootach ważnych (`<boot>/sprawdziany_s3.json`).

## Cięcia — tabela per epizod

Faza misji = ticki utraty przed komendą planowego zejścia (doprecyzowanie 1). REFUSE w zejściu = ticki KONT_REFUSE z τ*
po komendzie zejścia (przy ziemi znaczniki wychodzą z kadru), sądzone przez (B4).

| epizod | boot | kontynuacja [s] | max e_corr/U | margines R_E [m] | zapas bariery min misja [m] | τ max misja [s] | tryby (ticki misji) | REFUSE misja / zejście (ticki) | tempo |
|---|---|---|---|---|---|---|---|---|---|
| c01_s01 | c01_s01 | 110.548 | 0.231 | 8.541 | 3.051 | 0.224 | para 2226 | 0 / 109 | 0.9628 |
| c01_s03 | c01_s03_r2 | 110.528 | 0.258 | 8.623 | 3.040 | 0.224 | para 2224, jeden 8 | 0 / 111 | 0.9498 |
| c02_s01 | c02_s01 | 110.508 | 0.299 | 8.662 | 3.069 | 0.228 | para 2243 | 0 / 136 | 0.9642 |
| c02_s03 | c02_s03 | 110.516 | 0.274 | 8.677 | 3.082 | 0.224 | para 2232 | 0 / 111 | 0.9692 |
| c05_s01 | c05_s01_r2 | 110.500 | 0.348 | 12.406 | 6.668 | 0.372 | para 2236 | 0 / 54 | 0.9637 |
| c05_s02 | c05_s02 | 110.500 | 0.237 | 8.923 | 3.155 | 0.224 | para 2229 | 0 / 8 | 0.9652 |
| c08_s01 | c08_s01 | 110.508 | 0.360 | 6.428 | 0.479 | 0.224 | para 2212, jeden 16 | 0 / 104 | 0.9618 |
| c08_s02 | c08_s02 | 110.528 | 0.249 | 9.412 | 4.420 | 0.224 | para 2216, jeden 20 | 0 / 74 | 0.9625 |
| c10_s01 | c10_s01 | 110.544 | 0.305 | 8.206 | 2.463 | 0.228 | para 2229, jeden 4 | 0 / 120 | 0.9628 |
| c10_s02 | c10_s02 | 110.516 | 0.374 | 7.395 | 1.676 | 0.380 | para 2211, jeden 28 | 0 / 32 | 0.9627 |
| c11_s01 | c11_s01 | 110.540 | 0.273 | 6.635 | 0.826 | 0.224 | para 2220, jeden 8 | 0 / 82 | 0.9665 |
| c11_s02 | c11_s02 | 110.552 | 0.277 | 8.572 | 2.833 | 0.224 | para 2232 | 0 / 130 | 0.9631 |

- We wszystkich cięciach track 1.000; pasmo 6–10 m od 0.946 (c08_s01, c11_s02) do 1.000.
- Przedziały τ w misji: 0 i 1 (τ ≤ 0.38 s); REFUSE(τ*) w misji 0.
- Każde cięcie zakończone przyziemieniem GT; (B4) nav_state 14 i failsafe 0 od flagi do przyziemienia w 12/12.

## Nominały — tabela per epizod

| boot | epizod | B1–B5 | margines R_E [m] | ticki ≠ NOMINAL | REFUSE | tempo |
|---|---|---|---|---|---|---|
| nom_b1 | c00_s01 | PASS | 8.538 | 0 | 0 | 0.9643 |
| nom_b1 | c01_s01 | PASS | 8.832 | 0 | 0 | 0.9643 |
| nom_b1 | c02_s01 | PASS | 8.716 | 0 | 0 | 0.9643 |
| nom_b1 | c03_s01 | PASS | 8.656 | 0 | 0 | 0.9643 |
| nom_b2 | c04_s01 | PASS | 12.111 | 0 | 0 | 0.9612 |
| nom_b2 | c05_s01 | PASS | 12.761 | 0 | 0 | 0.9612 |
| nom_b2 | c06_s01 | PASS | 12.743 | 0 | 0 | 0.9612 |
| nom_b2 | c07_s01 | PASS | 11.042 | 0 | 0 | 0.9612 |
| nom_b3 | c08_s01 | PASS | 8.998 | 0 | 0 | 0.9648 |
| nom_b3 | c09_s01 | PASS | 11.755 | 0 | 0 | 0.9648 |
| nom_b3 | c10_s01 | PASS | 10.252 | 0 | 0 | 0.9648 |
| nom_b3 | c11_s01 | PASS | 11.797 | 0 | 0 | 0.9648 |
| nom_b4 | c00_s02 | PASS | 8.663 | 0 | 0 | 0.9637 |
| nom_b4 | c01_s02 | PASS | 8.786 | 0 | 0 | 0.9637 |
| nom_b4 | c02_s02 | PASS | 8.696 | 0 | 0 | 0.9637 |
| nom_b4 | c03_s02 | PASS | 8.605 | 0 | 0 | 0.9637 |

## Obserwable cięć (bez progu)

Liczone w `results/NAD2/tools/nad2_s3_raport.py` (faza misji).
- **Horyzont prawdziwy:** ts (próbka EKF ticku) − ta (próbka EKF migawki poprawki), obie dopasowane po wartości jak w analizatorze.
- **Przyrost EKF:** |(p_EKF − GT)(ts) − (p_EKF − GT)(ta)|, poziomo.

| epizod | e_corr p50/p95/max [m] | a max / 1.5F | przyrost EKF max / 1.5G | max (horyzont − (τ+0.012)) [s] | klatki bez poprawki | r_est max [m] | u′>m ticki | bias kursu p50 [°] | τ max zejście [s] |
|---|---|---|---|---|---|---|---|---|---|
| c01_s01 | 0.135/0.211/0.394 | 0.684 | 0.201 | +0.004 | 0/553 | 23.282 | 0 | 1.02 | 6.356 |
| c01_s03 | 0.128/0.209/0.411 | 0.739 | 0.197 | −0.004 | 0/552 | 23.292 | 0 | 1.21 | 6.420 |
| c02_s01 | 0.115/0.223/0.387 | 0.965 | 0.214 | −0.004 | 0/552 | 23.264 | 0 | −0.34 | 7.612 |
| c02_s03 | 0.116/0.225/0.362 | 0.546 | 0.222 | −0.016 | 0/552 | 23.250 | 0 | 0.46 | 6.432 |
| c05_s01 | 0.124/0.228/0.514 | 0.594 | 0.294 | −0.012 | 1/552 | 19.664 | 0 | −0.92 | 3.608 |
| c05_s02 | 0.123/0.204/0.306 | 0.922 | 0.227 | −0.016 | 0/552 | 23.178 | 9 | −0.67 | 1.324 |
| c08_s01 | 0.102/0.234/0.465 | 0.587 | 0.398 | −0.004 | 0/553 | 25.854 | 4 | −0.19 | 6.084 |
| c08_s02 | 0.090/0.215/0.403 | 0.613 | 0.308 | −0.016 | 0/553 | 21.753 | 21 | 1.55 | 4.568 |
| c10_s01 | 0.124/0.238/0.394 | 0.669 | 0.338 | −0.004 | 0/553 | 23.930 | 0 | −1.00 | 6.772 |
| c10_s02 | 0.098/0.225/0.484 | 0.662 | 0.469 | −0.000 | 1/553 | 24.656 | 0 | 0.65 | 2.456 |
| c11_s01 | 0.108/0.189/0.353 | 0.490 | 0.278 | −0.008 | 0/553 | 25.506 | 0 | −0.15 | 4.992 |
| c11_s02 | 0.112/0.235/0.358 | 0.590 | 0.370 | −0.008 | 0/552 | 23.499 | 21 | 0.08 | 7.368 |

Do odnotowania (obserwable, nie litera):
- **Margines τ + 0.012 s przekroczony** w c01_s01 o 4 ms (max horyzont − (τ + 0.012) = +0.004 s); w pozostałych ≤ 0.
  - Przekroczenie dotyczy przedziału użytego przez osłonę tylko przy τ tuż pod krawędzią. B1 w tym epizodzie max 0.231.
- **Zakotwiczenie poprawek** w c02_s01 sięga 0.965 · 1.5·F (max błędu a wobec zapasu); B1 tamtego epizodu 0.299.
- **Zapas bariery min misji** 0.479 m w c08_s01 (margines GT 6.428 m).
- **u′ > m** w 4 epizodach, łącznie 55 ticków (obserwabla PRE §5, jak w smoke).
- **REFUSE w zejściu:** 1071 ticków KONT_REFUSE, wszystkie po komendzie zejścia i z τ ≥ 0.95 s (reguła τ*; etykieta reguły R-KONT 1046, R-POS 25); każde cięcie zakończone przyziemieniem GT.

## Stanowisko i budżet

- **Booty zużyte:** 16 (16 ważnych, 0 nieważnych, 0 przerwań bramką tempa). Tempo bootu 0.950–0.969.
- **Bramka zdrowia:** 18 pomiarów, 18 GO (A, 0.908–0.939), 0 NO-GO.
  - 2 pomiary nie doprowadziły do bootu: c01_s03 (env-block launchera) i c05_s01 (zawieszenie w proc_gate bootu). W obu stos nie ruszył, więc to nie booty.
  - timesyncd zatrzymany na czas kolejek, wznowiony na końcu.
- **Zdarzenia kolejki (moje wady, zapisane):**
  1. `c01_s03`: env-block launchera (proces kolejki 2.2% CPU > 2.0), powtórka pod tą samą nazwą ⇒ REPO-2 rc 4 ⇒ STOP-NAD2-3-GUARD (`55333eaa`). Poprawka `6b008eb7` (decyzja Olgi): powtórka pod wolną nazwą.
  2. `c05_s01`: 33 min w `proc_gate` bootu — wątki gz-transport/ZMQ przyrządu A bramki zdrowia zostawały w procesie kolejki (2.2–2.6% CPU).
     - Kolejkę zatrzymałem ręcznie; nie był to boot.
     - Dopiski monitora smoke przeniosłem do `nad2_s3_monitor.log` i przywróciłem plik smoke z git.
     - Poprawka `e6670f52`: bramka w procesie potomnym. Po niej 0 linii „brudny” w 11 bootach.
- **Czas:** ok. 8.5 min na cięcie, ok. 11.5 min na nominał (bez bramki zdrowia).

## Pliki

- Per boot `results/NAD2/s3/<boot>/`: trace, rama, nadir_obs, `wyniki_nad2.json`, `sprawdziany_s3.json` (+ `sprawdziany_s2.json`), wyciąg `ulg.jsonl.gz` (1.22–2.86 MB), `host_telemetria.jsonl`. `boot.ulg` lokalnie (.gitignore).
- Księgi: `kampania_ksiega.jsonl`, `bramka_ksiega.jsonl`, `kampania_s3.json`, log `kampania_s3.log`, `nad2_s3_monitor.log`, wyniki `wyniki_s3.json`.
- Narzędzia: `nad2_s3_run.py`, `nad2_s3_spr.py`, `nad2_s3_dryrun.py`, `nad2_s3_raport.py`.
- Diff-stat kodu od `bd975df5` (`results/NAD2/tools r03 harness r01`): tylko nowe pliki S3 (`nad2_s3_run.py`, `nad2_s3_spr.py`, `nad2_s3_dryrun.py`, `nad2_s3_raport.py`); zmian w plikach `bd975df5`: 0.
- Porcelain po commicie: czysty poza zastanymi ?? `results/DEMO_C`.

Reprodukcja z repo:
```
python3 results/NAD2/tools/nad2_s3_spr.py results/NAD2/s3/c11_s02            # (s1)–(s3); nominał: dopisz „nominal”
python3 results/NAD2/tools/nad2_analyze.py results/NAD2/s3/<boot>             # wymaga boot.ulg (lokalnie); e_corr z repo: ulg.jsonl.gz
python3 results/NAD2/tools/nad2_s3_raport.py                                  # werdykt + tabele (obserwable horyzontu/przyrostu: boot.ulg)
```

**Sygnał: STOP-NAD2-3.** Push = Olga („wypchnięte” — CC przelicza B1–B4 i D1 niezależnie i pisze aneks zamykający nogę). STOP.
